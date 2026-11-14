---
name: enterprise-java
description: 使用此技能处理虚拟线程被 synchronized 钉住或载体线程池饥饿、CompletableFuture 落在公共线程池、内存模型可见性与结构化并发存疑，以及任何 Java 语言层面疑问（哪怕只有一段代码、哪怕没有点名任何框架）时使用。当用户只给出代码片段时也触发本 skill。
---

# 企业级 Java —— 语言技能

本技能聚焦 Java 语言与运行时本身：语法、类型系统、并发、虚拟线程、JVM 内存模型，以及由此衍生的惯用法与陷阱。刻意保持框架中立。框架与应用级范例放在 `references/`，见下文的 Framework Selection。依据 Oracle JDK 21 虚拟线程指南、JEP 444（虚拟线程）、JEP 480/505（结构化并发）、Java Memory Model（JSR-133）与 `java.util.concurrent` 包文档。

## Gotchas

每条陷阱按「症状 → 原因 → 修复」组织，因为真正值得记住的是「原因」。

### 1. 虚拟线程在 `synchronized` 下被钉住
- 症状：虚拟线程持有 monitor 时阻塞会令吞吐量骤降；增加虚拟线程数量并无帮助。
- 原因：在 JDK 21 中，虚拟线程在 `synchronized` 块/方法内阻塞时会被钉在其 carrier 平台线程上（JEP 444）——调度器无法将其卸载，整个阻塞期间 carrier 都被占用。
- 修复：用 `java.util.concurrent.locks.ReentrantLock` 取代 monitor，或把阻塞调用移出同步区；绝不池化虚拟线程。
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

### 2. carrier 线程池饥饿
- 症状：虚拟线程即便「大多空闲」也不再推进，整个进程像被冻住。
- 原因：默认调度器把虚拟线程挂载到一个小而固定的 carrier 平台线程 ForkJoinPool 上（并行度约等于 CPU 核数，`jdk.virtualThreadScheduler.parallelism`）。一旦所有 carrier 都被钉住或卡在长 CPU 循环里，就没有虚拟线程能被挂载。
- 修复：消除钉住（见陷阱 1），把 CPU 密集任务交给有界的平台线程池，并用 `Semaphore` 限制并发而非线程池。
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

### 3. `CompletableFuture` 跑在公共线程池上
- 症状：`supplyAsync` 的回调悄悄跑在 `ForkJoinPool.commonPool()` 上；其中一次阻塞 I/O 会拖住无关任务，且并行度按 CPU 核数而非 I/O 计算。
- 原因：未显式传入 `Executor` 的异步 stage 默认使用进程级共享的 common pool，它按 CPU 密集负载定尺寸，也被并行流等所有东西共用。
- 修复：始终传入专用 `Executor`（`supplyAsync(..., executor)`、`thenApplyAsync(..., executor)`）；JDK 21+ 的阻塞 I/O 用 `Executors.newVirtualThreadPerTaskExecutor()`。
```java
ExecutorService io = Executors.newVirtualThreadPerTaskExecutor();
CompletableFuture<String> f = CompletableFuture.supplyAsync(() -> blockingRead(), io)
    .thenApplyAsync(String::trim, io);
```

### 4. `Optional` 被用作字段或参数
- 症状：`Optional` 字段/参数让序列化与基于反射的映射变复杂，调用方依然可以传 `null`。
- 原因：`Optional` 是为「可能缺失」的返回值设计的，不是通用的 null 防护；它不实现 `Serializable`，且只是多包一层，入参侧没有任何 null 安全收益。
- 修复：方法返回 `Optional`，但字段与参数保持普通可空引用（用 `Objects.requireNonNull` 校验）；绝不把 `Optional` 存进集合或字段。
```java
// Return type: fine. Parameter: keep it a plain reference.
public Optional<User> find(String id) { return Optional.ofNullable(cache.get(id)); }
public String label(User user) { return user == null ? "unknown" : user.name(); }
```

### 5. 对包装类型用 `==`
- 症状：`Integer a = 1000, b = 1000; a == b` 为 false，而 `100 == 100` 却为 true；小值看起来没问题。
- 原因：包装类型上的 `==` 比较的是引用身份；`Integer` 缓存（-128..127）让小值共享实例，直到数值超出缓存才暴露 bug。
- 修复：用 `Objects.equals(a, b)` 比较，或先拆箱为基本类型；绝不在包装类型上用 `==`。
```java
Integer a = 1000, b = 1000;
System.out.println(Objects.equals(a, b));         // true: value comparison
System.out.println(a.intValue() == b.intValue()); // true: unboxed
```

### 6. `equals`/`hashCode` 契约被破坏
- 症状：`HashMap`/`HashSet`「弄丢」了一个键——刚 `put` 完 `containsKey` 就返回 false，或出现重复元素。
- 原因：哈希先用 `hashCode` 选桶，再用 `equals` 确认；只重写其中一个、或在其中使用可变字段，都会违反 `Object` 契约，字段变更后该条目便再也找不到。
- 修复：基于同一组不可变字段同时重写两者（`Objects.hash`/`Objects.equals`），或直接用 `record`，它会自动生成两者。
```java
public record Point(int x, int y) {}   // equals/hashCode/toString generated
```

### 7. try-with-resources 的抑制异常
- 症状：方法体里的异常似乎消失了，或堆栈里冒出一行意外的 "Suppressed"。
- 原因：try-with-resources 按逆序关闭资源；若方法体已抛异常，失败的 `close()` 会通过 `Throwable.addSuppressed`（JLS 14.20.3）挂到主异常上，而不是覆盖它。
- 修复：让主异常继续传播，检查 `getSuppressed()`，并尽量让 `close()` 幂等且不抛异常。
```java
try (var in = Files.newInputStream(path)) {
    return parse(in);
}   // close() failure is attached as suppressed, not thrown over the primary
```

### 8. 受检异常的包装
- 症状：lambda 或 `CompletableFuture` 里的受检异常无法抛出；包成 `RuntimeException` 后又丢了原始类型与 cause 链。
- 原因：函数式接口（`Supplier`、`Function`、`Runnable`）不声明受检异常，调用方只能包装；`new RuntimeException(e.getMessage())` 会丢掉堆栈，也让 `catch (SpecificException e)` 失效。
- 修复：保留 cause（`new CompletionException(exc)`、`throw new RuntimeException(exc)`），用 `getCause()` 解包，并在边界处一次性处理（`join()` 抛 `CompletionException`）。
```java
CompletableFuture<String> f = CompletableFuture.supplyAsync(() -> {
    try { return read(); }
    catch (IOException e) { throw new CompletionException(e); } // keep the cause
});
```

### 9. 缺少 happens-before 的可见性
- 症状：一个线程设置的 `boolean` 标志另一个线程永远看不到；自旋循环停不下来，或读到旧数据。
- 原因：没有 happens-before 边（JSR-133）时，JIT 与 CPU 可以重排或缓存读；普通字段写入不是同步动作，所以这是 data race，不是时序问题。
- 修复：把标志声明为 `volatile`，或用锁 / `AtomicBoolean` / `CountDownLatch` 保护；不要指望「最终会看到」。
```java
private volatile boolean ready;   // write->read happens-before edge
```

## Language Core

语言全景——够用来选对工具，不是教程。示例一律只用标准库。

### Records、sealed classes 与模式匹配
`record` 是不可变载体，自动生成访问器、`equals`/`hashCode`/`toString`；`sealed` 层次（`permits`）封闭子类型集合，使 `switch` 可穷尽。`instanceof` 模式匹配（JDK 16）与 `switch` 模式匹配（JDK 21，JEP 441）支持类型模式、record 模式与 guard。
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

### 虚拟线程与结构化并发
JDK 21 虚拟线程（JEP 444）廉价且数量充足，由调度器挂载到 carrier 平台线程上；用 `Thread.ofVirtual()` 或 `Executors.newVirtualThreadPerTaskExecutor()` 为每个任务建一个，绝不池化。结构化并发（JEP 480/505，预览）把相关子任务绑定到同一个 `StructuredTaskScope`——单一 join 点，取消与失败传播到整组，结果在该点汇总。
```java
// One virtual thread per task; the executor is AutoCloseable (JDK 21).
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> a = executor.submit(() -> fetch("a"));
    Future<String> b = executor.submit(() -> fetch("b"));
    String result = a.get() + b.get();
}
```

### `java.util.concurrent` 原语
按语义而非习惯挑选：`ExecutorService`/`CompletableFuture` 管异步，`ReentrantLock`/`StampedLock` 管加锁，`Semaphore`/`CountDownLatch`/`CyclicBarrier`/`Phaser` 管协作，`ConcurrentHashMap`/`BlockingQueue` 管共享数据，`Atomic*`/`VarHandle`/`LongAdder` 管无锁计数。
```java
ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
counts.merge("key", 1, Integer::sum);   // atomic compound update
CountDownLatch done = new CountDownLatch(2);
done.countDown();
done.await();
```

### The Java Memory Model
JSR-133 定义 happens-before：`volatile` 写/读、monitor unlock/lock、线程 `start`/`join` 以及可传递的程序顺序，都会建立可见性与有序性保证。`final` 字段在构造完成后被安全发布。没有这类边就是 data race；`Atomic*` 与 `VarHandle` 显式提供 volatile/CAS 语义。
```java
// Safe publication: a volatile write happens-before a volatile read.
volatile Holder holder;
void init() { holder = new Holder(42); }   // other threads see fully built state
```

### Generics
类型擦除意味着没有基本类型实参、也没有运行期的 `instanceof List<String>`；生产者用 `? extends T`、消费者用 `? super T`（PECS），约束用有界类型参数，需要运行期类型信息时用 `Class<T>` 令牌。
```java
static <T> T first(List<? extends T> xs) { return xs.isEmpty() ? null : xs.get(0); }

// Plain config object, no injected value.
Map<String, String> config = Map.of("api.url", "https://example.test");
String url = config.getOrDefault("api.url", "https://localhost");
```

### Exceptions 与 try-with-resources
受检异常是方法契约的一部分；`AutoCloseable` 驱动 try-with-resources，它逆序关闭并附加抑制异常（见陷阱 7）。优先用 multi-catch、`Objects.requireNonNull` 与保留 cause 的包装；失败操作在单一边界处理。
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

### Streams 与惯用法
Stream 是惰性的：中间操作（`filter`、`map`）在终止操作执行前什么都不做；避免副作用，优先 `Collectors`/`toList()`，用基本类型流避免装箱，终止查找返回 `Optional`。缓存用 `Map.computeIfAbsent`，比较用 `Objects.equals`，值对象尽量小而不可变。
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

框架与应用级范例**不是**语言内容——在生成框架脚手架*之前*先读对应文件。每个文件都直接链接，只有一层深度。完整代码与模板索引见 [code-examples.md](./references/code-examples.md)。

| Framework / concern | Reference file | When to read |
| --- | --- | --- |
| Spring 标准类模板与分层架构 | [code-examples.md](./references/code-examples.md#标准类模板) | 要求写一个创建订单的 Spring Service 类（`OrderService`，方法 `createOrder`）、Repository 或 Controller，或套用标准类模板时 |
| 分层架构目录约定 | [code-examples.md](./references/code-examples.md#分层架构模式) | 需要 controller/service/repository/domain 分层目录约定时 |
| 异常处理、空值安全、资源配置、日志 | [code-examples.md](./references/code-examples.md#最佳实践代码示例) | 需要这些框架代码实践的具体示例时 |
| 事务边界、懒加载、缓存一致性 | [code-examples.md](./references/code-examples.md#常见陷阱示例) | 遇到 `@Transactional`、懒加载异常或缓存过期等框架陷阱时 |
| 代码审查、架构设计、性能优化、问题诊断 | [response-patterns.md](./references/response-patterns.md) | 被要求评审 Java 代码、设计架构、调优性能或排查线上问题时 |

被移除的框架专属章节，现各自指向一处 reference：

- 配置（`@Value` / 外部化配置）：见 [code-examples.md](./references/code-examples.md#最佳实践代码示例)。
- 事务边界（`@Transactional`）与懒加载问题：见 [code-examples.md](./references/code-examples.md#常见陷阱示例)。
- 缓存一致性（`@Cacheable` / `@CacheEvict`）：见 [code-examples.md](./references/code-examples.md#常见陷阱示例)。
- 「被要求……」的 Spring 代码生成、评审、架构、性能或诊断：见 [response-patterns.md](./references/response-patterns.md)。

## Response Patterns

- 先分类请求：语言层面（语法、并发、JVM、泛型、Stream）在此用 Gotchas / Language Core 回答；完整应用、服务或 endpoint 属于框架任务，转去链接的 reference。
- 并发问题先点明机制——阻塞 I/O 用虚拟线程、CPU 密集用有界平台线程池、`CompletableFuture` 配显式 `Executor`——并引用对应的陷阱条目。
- 一律写标准库代码；语言答案里绝不出现框架注解（配置就是普通 `Map`，事务就是普通 `Connection` 边界，缓存就是普通 `Map`）。
- 先讲「原因」（JMM happens-before、钉住、`equals` 契约）再给修复；优先最小可运行片段而非样板。
- 遇到版本相关特性要注明 JDK 版本（虚拟线程 JDK 21、`switch` 模式 JDK 21、结构化并发为预览特性）。

## Remember

- 语言、JVM 与 JMM 优先；框架是下游选择。
- 虚拟线程廉价且绝不能池化；`synchronized` 阻塞会钉住它，改用 `ReentrantLock`。
- `CompletableFuture` 默认用 `ForkJoinPool.commonPool()`——始终显式传入 `Executor`。
- `Optional` 只做返回值，不放进字段或参数；包装类型用 `equals` 比较，`equals`/`hashCode` 成对重写。
- 可见性需要 happens-before 边：`volatile`、锁或 `Atomic*`。
- 示例只用标准库；框架细节推到 `references/`。
- 拿不准时从「原因」（JEP 444、JEP 480/505、JSR-133、`java.util.concurrent` 文档）推理，而非凭经验法则。
