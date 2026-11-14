---
name: enterprise-java
description: Use this skill when virtual threads pin or stall under synchronized, when CompletableFuture work silently lands on the common pool, or when the Java Memory Model and structured concurrency are in doubt. Claim ANY language-level Java question proactively — even one snippet, even when no framework is named. Trigger on "virtual thread pinning", "CompletableFuture" or "memory model".
---

# Enterprise Java — Language Skill

This skill is about the Java language and runtime itself: syntax, the type system, concurrency, virtual threads, the JVM memory model, and the idioms and gotchas that follow from them. It is deliberately framework-neutral. Framework and app-level recipes live in `references/`; see Framework Selection below. Grounded in the Oracle JDK 21 virtual threads guide, JEP 444 (virtual threads), JEP 480/505 (structured concurrency), the Java Memory Model (JSR-133), and the `java.util.concurrent` package docs.

## Gotchas

Each trap is written as symptom -> why -> fix, because the *why* is the part worth remembering.

### 1. Virtual-thread pinning under `synchronized`
- Symptom: throughput collapses when a virtual thread blocks while holding a monitor; adding more virtual threads does not help.
- Why: on JDK 21 a virtual thread inside a `synchronized` block/method that blocks is pinned to its carrier platform thread (JEP 444) — the scheduler cannot unmount it, so the carrier stays occupied for the whole block.
- Fix: replace the monitor with `java.util.concurrent.locks.ReentrantLock`, or move the blocking call out of the synchronized region; never pool virtual threads.
```java
// ReentrantLock lets the virtual thread unmount while waiting.
private final ReentrantLock lock = new ReentrantLock();
lock.lock();
try {
    doWork();
} finally {
    lock.unlock();
}
```

### 2. Carrier-thread pool starvation
- Symptom: virtual threads stop making progress even though the code is "mostly idle"; the whole process feels frozen.
- Why: the default scheduler mounts virtual threads on a small, fixed ForkJoinPool of carrier platform threads (parallelism ~ CPU cores, `jdk.virtualThreadScheduler.parallelism`). If every carrier is pinned or stuck in a long CPU loop, no virtual thread can be mounted.
- Fix: remove pinning (gotcha 1), offload CPU-bound work to a bounded platform-thread pool, and cap concurrency with a `Semaphore` instead of a thread pool.
```java
// Bound concurrency without pooling virtual threads.
Semaphore permits = new Semaphore(64);
permits.acquire();
try {
    handle(request);
} finally {
    permits.release();
}
```

### 3. `CompletableFuture` running on the common pool
- Symptom: `supplyAsync` callbacks silently run on `ForkJoinPool.commonPool()`; a blocking I/O call inside one stalls unrelated work, and parallelism tracks CPU count, not I/O.
- Why: async stages without an explicit `Executor` default to the process-wide common pool, sized for CPU-bound work and shared by everything (including parallel streams).
- Fix: always pass a dedicated `Executor` (`supplyAsync(..., executor)`, `thenApplyAsync(..., executor)`); on JDK 21+ use `Executors.newVirtualThreadPerTaskExecutor()` for blocking I/O.
```java
ExecutorService io = Executors.newVirtualThreadPerTaskExecutor();
CompletableFuture<String> f = CompletableFuture.supplyAsync(() -> blockingRead(), io)
    .thenApplyAsync(String::trim, io);
```

### 4. `Optional` used as a field or parameter
- Symptom: `Optional` fields/parameters complicate serialization and reflection-based mapping, and callers can still pass `null`.
- Why: `Optional` was designed as a return type for "may be absent" results, not as a general null-guard; it is not `Serializable` and adds a wrapper with no null-safety benefit on the way in.
- Fix: return `Optional` from methods, but keep fields and parameters as plain nullable references (validate with `Objects.requireNonNull`); never store `Optional` in a collection or field.
```java
// Return type: fine. Parameter: keep it a plain reference.
public Optional<User> find(String id) { return Optional.ofNullable(cache.get(id)); }
public String label(User user) { return user == null ? "unknown" : user.name(); }
```

### 5. `==` on boxed types
- Symptom: `Integer a = 1000, b = 1000; a == b` is false, yet `100 == 100` compares true; small values seem to work.
- Why: `==` on wrappers compares reference identity; the `Integer` cache (-128..127) makes small values share instances and hides the bug until values exceed the cache.
- Fix: compare with `Objects.equals(a, b)` or unbox to primitives first; never use `==` on wrappers.
```java
Integer a = 1000, b = 1000;
System.out.println(Objects.equals(a, b));         // true: value comparison
System.out.println(a.intValue() == b.intValue()); // true: unboxed
```

### 6. Broken `equals`/`hashCode` contract
- Symptom: a `HashMap`/`HashSet` "loses" a key — `containsKey` returns false right after `put`, or duplicates appear.
- Why: hashing picks a bucket by `hashCode` and confirms identity by `equals`; overriding one without the other, or using mutable fields, violates the `Object` contract and the entry becomes unreachable after mutation.
- Fix: override both from the same immutable fields (`Objects.hash`/`Objects.equals`), or use a `record`, which generates both.
```java
public record Point(int x, int y) {}   // equals/hashCode/toString generated
```

### 7. try-with-resources suppression
- Symptom: the exception from the body seems to vanish, or the stack trace shows an unexpected "Suppressed" line.
- Why: try-with-resources closes resources in reverse order; if the body already threw, a failing `close()` is attached via `Throwable.addSuppressed` (JLS 14.20.3) instead of masking the primary exception.
- Fix: let the primary propagate, inspect `getSuppressed()`, and keep `close()` idempotent and non-throwing where possible.
```java
try (var in = Files.newInputStream(path)) {
    return parse(in);
}   // close() failure is attached as suppressed, not thrown over the primary
```

### 8. Checked-exception wrapping
- Symptom: a checked exception inside a lambda or `CompletableFuture` cannot be thrown; wrapping it in `RuntimeException` loses the original type and the cause chain.
- Why: functional interfaces (`Supplier`, `Function`, `Runnable`) declare no checked exceptions, so callers wrap; `new RuntimeException(e.getMessage())` drops the stack trace and defeats `catch (SpecificException e)`.
- Fix: preserve the cause (`new CompletionException(exc)`, `throw new RuntimeException(exc)`), unwrap with `getCause()`, and handle once at the boundary (`join()` throws `CompletionException`).
```java
CompletableFuture<String> f = CompletableFuture.supplyAsync(() -> {
    try { return read(); }
    catch (IOException e) { throw new CompletionException(e); } // keep the cause
});
```

### 9. Visibility without happens-before
- Symptom: a `boolean` flag set by one thread is never observed by another; a spin loop runs forever or reads stale data.
- Why: without a happens-before edge (JSR-133), the JIT and CPU may reorder or cache reads; a plain field write is not a synchronization action, so this is a data race, not a timing issue.
- Fix: make the flag `volatile`, or guard it with a lock / `AtomicBoolean` / `CountDownLatch`; do not rely on "eventually".
```java
private volatile boolean ready;   // write->read happens-before edge
```

## Language Core

A map of the language surface — enough to pick the right tool, not a tutorial. Keep examples standard-library-only.

### Records, sealed classes, and pattern matching
A `record` is an immutable carrier with generated accessors, `equals`/`hashCode`/`toString`; `sealed` hierarchies (`permits`) close the set of subtypes so `switch` can be exhaustive. Pattern matching for `instanceof` (JDK 16) and `switch` (JDK 21, JEP 441) supports type patterns, record patterns and guards.
```java
sealed interface Shape permits Circle, Box {}
record Circle(double r) implements Shape {}
record Box(double w, double h) implements Shape {}

// Exhaustive switch with a record pattern and a guard (JDK 21).
double area(Shape s) {
    return switch (s) {
        case Circle c -> Math.PI * c.r() * c.r();
        case Box b when b.w() == b.h() -> b.w() * b.h();
        case Box b -> b.w() * b.h();
    };
}
```

### Virtual threads and structured concurrency
JDK 21 virtual threads (JEP 444) are cheap, abundant, and mounted onto carrier platform threads by the scheduler; create one per task with `Thread.ofVirtual()` or `Executors.newVirtualThreadPerTaskExecutor()` and never pool them. Structured concurrency (JEP 480/505, preview) binds related subtasks to a single `StructuredTaskScope` — one join point, cancellation and failure propagate to the whole group, and results are collected there.
```java
// One virtual thread per task; the executor is AutoCloseable (JDK 21).
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> a = executor.submit(() -> fetch("a"));
    Future<String> b = executor.submit(() -> fetch("b"));
    String result = a.get() + b.get();
}
```

### `java.util.concurrent` primitives
Pick by semantics, not habit: `ExecutorService`/`CompletableFuture` for async work, `ReentrantLock`/`StampedLock` for locking, `Semaphore`/`CountDownLatch`/`CyclicBarrier`/`Phaser` for coordination, `ConcurrentHashMap`/`BlockingQueue` for shared data, `Atomic*`/`VarHandle`/`LongAdder` for lock-free counters.
```java
ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
counts.merge("key", 1, Integer::sum);   // atomic compound update
CountDownLatch done = new CountDownLatch(2);
done.countDown();
done.await();
```

### The Java Memory Model
JSR-133 defines happens-before: `volatile` writes/reads, monitor unlock/lock, thread `start`/`join`, and transitive program order create visibility and ordering guarantees. `final` fields are safely published after construction. Without such an edge there is a data race; `Atomic*` and `VarHandle` give volatile/compare-and-set semantics explicitly.
```java
// Safe publication: a volatile write happens-before a volatile read.
volatile Holder holder;
void init() { holder = new Holder(42); }   // other threads see fully built state
```

### Generics
Type erasure means no primitive type arguments and no runtime `instanceof List<String>`; use `? extends T` for producers and `? super T` for consumers (PECS), bounded type parameters for constraints, and `Class<T>` tokens where runtime type info is needed.
```java
static <T> T first(List<? extends T> xs) { return xs.isEmpty() ? null : xs.get(0); }

// Plain config object, no injected value.
Map<String, String> config = Map.of("api.url", "https://example.test");
String url = config.getOrDefault("api.url", "https://localhost");
```

### Exceptions and try-with-resources
Checked exceptions are part of the method contract; `AutoCloseable` drives try-with-resources, which closes in reverse order and attaches suppressed exceptions (gotcha 7). Prefer multi-catch, `Objects.requireNonNull`, and cause-preserving wrappers; handle a failed operation at one boundary.
```java
// Plain transaction boundary with the standard library (java.sql).
try (Connection c = DriverManager.getConnection(url)) {
    c.setAutoCommit(false);
    try {
        update(c);
        c.commit();
    } catch (SQLException e) {
        c.rollback();
        throw e;
    }
}
```

### Streams and idioms
Streams are lazy: intermediate ops (`filter`, `map`) do nothing until a terminal op runs; avoid side effects, prefer `Collectors`/`toList()`, use primitive streams to avoid boxing, and return `Optional` from terminal lookups. Prefer `Map.computeIfAbsent` for a plain cache, `Objects.equals`, and small immutable value objects.
```java
// Plain map cache, no caching annotation.
Map<String, User> cache = new HashMap<>();
User u = cache.computeIfAbsent(id, this::load);

List<String> names = users.stream()
    .filter(User::active)
    .map(User::name)
    .toList();                     // JDK 16+ unmodifiable result
```

## Framework Selection

Framework and app-level recipes are **not** language material — read the matching file *before* emitting framework scaffolding. Each is linked directly, one level deep.

| Framework / concern | Reference file | When to read |
| --- | --- | --- |
| Spring class templates & layered architecture | [class-templates.md](references/class-templates.md) | Asked to create a Spring Service class for creating orders (`OrderService.createOrder`), a Repository or Controller, or to apply the standard class template |
| Code review, architecture design, performance optimization & problem diagnosis | [response-patterns.md](references/response-patterns.md) | Asked to "Review this Java code", design an architecture, tune performance, or diagnose a production issue |

Framework-only sections were removed from this document; each now points to one reference:

- Configuration (`@Value` / externalized config): see [class-templates.md](references/class-templates.md).
- Transaction boundaries (`@Transactional`) and lazy loading: see [class-templates.md](references/class-templates.md) and [response-patterns.md](references/response-patterns.md).
- Cache consistency (`@Cacheable` / `@CacheEvict`): see [response-patterns.md](references/response-patterns.md).
- "When asked to..." Spring code generation, review, architecture, performance or diagnosis: see [response-patterns.md](references/response-patterns.md).

## Response Patterns

- Classify the request first: language-level (syntax, concurrency, JVM, generics, streams) is answered here from Gotchas / Language Core; a full app, service, or endpoint is a framework task and goes to a linked reference.
- For concurrency questions, name the mechanism first — virtual threads for blocking I/O, a bounded platform pool for CPU work, `CompletableFuture` with an explicit `Executor` — and cite the relevant gotcha.
- Write standard-library-only code; never reach for a framework annotation in a language answer (config is a plain `Map`, a transaction is a plain `Connection` boundary, a cache is a plain `Map`).
- Explain the *why* (JMM happens-before, pinning, the `equals` contract) before the fix; prefer one small runnable snippet over boilerplate.
- State the JDK version for version-gated features (virtual threads JDK 21, `switch` patterns JDK 21, structured concurrency preview).

## Remember

- The language, the JVM and the JMM come first; frameworks are downstream choices.
- Virtual threads are cheap and must not be pooled; `synchronized` blocking pins them, so use `ReentrantLock`.
- `CompletableFuture` defaults to `ForkJoinPool.commonPool()` — always pass an explicit `Executor`.
- Return `Optional`, never store it in a field or parameter; compare boxed types with `equals`, and override `equals`/`hashCode` together.
- Visibility needs a happens-before edge: `volatile`, a lock, or an `Atomic*`.
- Keep examples standard-library-only; push framework specifics into `references/`.
- When unsure, reason from the why (JEP 444, JEP 480/505, JSR-133, `java.util.concurrent` docs) rather than a rule of thumb.
