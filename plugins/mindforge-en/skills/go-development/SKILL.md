---
name: go-development
description: Use this skill when a goroutine leaks or a channel deadlocks, when context.Context cancellation or sync.WaitGroup hangs, when the race detector reports a race, or when the Go memory model and language semantics are in doubt. Claim ANY language-level Go question proactively — even one snippet, even when no framework is named. Trigger on "goroutine leak", "channel deadlock" or "race detector".
---

# Go Development Skill

Language-first guidance: Go syntax, concurrency, and idioms. Framework-specific code lives in `references/` and is linked below; keep language answers framework-neutral.

## Gotchas

Each trap is written as Symptom -> Why -> Fix. Scan these before writing any concurrent code.

### 1. Data races and the Go memory model (DRF-SC)
- Symptom: `go test -race` prints a DATA RACE report; results change between runs.
- Why: Without a happens-before edge (channel send/receive, sync.Mutex, sync/atomic), a concurrent read/write is a data race. go.dev/ref/mem guarantees only DRF-SC: data-race-free programs behave sequentially consistent; racy ones are undefined, so the compiler and CPU may reorder freely.
- Fix: Guard shared state with sync.Mutex/RWMutex or sync/atomic, or transfer ownership through a channel; never "fix" it with time.Sleep. Confirm with `go test -race` (go.dev/blog/race-detector).

### 2. context.Context cancellation and deadlines ignored
- Symptom: a request times out but work keeps running; "context deadline exceeded" surfaces too late; resources pile up.
- Why: context is a cancellation-signal tree, not a value bag; ignoring ctx.Done() leaves the goroutine with no stop condition, and a deadline helps only if every downstream call receives and honors ctx (go.dev/blog/context).
- Fix: Take ctx as the first parameter, select on <-ctx.Done(), derive with context.WithCancel/WithTimeout/WithDeadline, call cancel() via defer, and propagate ctx to every blocking call.

### 3. Goroutine leaks
- Symptom: goroutine count grows without bound in pprof; memory climbs; a worker never exits after its parent returns.
- Why: A goroutine blocked on a channel send/receive with no future partner, or an infinite loop with no ctx.Done(), has no exit path; the runtime never garbage-collects blocked goroutines (go.dev/blog/pipelines).
- Fix: Give every goroutine a stop condition (ctx.Done() in select), close channels to broadcast completion, and let the owner wait via sync.WaitGroup / errgroup so leaks become visible.

### 4. Loop variable capture in closures (pre-Go 1.22)
- Symptom: every goroutine prints the last element; all callbacks see the same value.
- Why: Before Go 1.22 the range variable was reused across iterations, so closures captured one address and often ran after the loop advanced.
- Fix: Pass the value as a parameter (go func(v T){...}(v)) or shadow it (v := v); Go 1.22+ makes loop vars per-iteration, but keep the pattern for older targets. Gate by version with [modern-go.md](modern-go.md).

### 5. defer inside loops
- Symptom: file descriptors or locks accumulate until the function returns; memory spikes in a long loop; close() runs far too late.
- Why: defer executes at function return, not at iteration end, so each iteration stacks another deferred call.
- Fix: Move the loop body into a helper func with its own defer, or release/close explicitly at the end of each iteration.

### 6. Error wrapping breaks errors.Is / errors.As
- Symptom: `err == ErrNotFound` is false after wrapping; sentinel checks silently fail.
- Why: Equality compares the outer wrapper, not the cause; fmt.Errorf("%w") builds a chain while "%v" discards it.
- Fix: Wrap with fmt.Errorf("...: %w", err) and inspect with errors.Is(err, target) / errors.As(err, &t); never string-compare err.Error(). Standard-library HTTP signals 404 with w.WriteHeader(http.StatusNotFound), not a framework constant.

### 7. Typed nil in an interface
- Symptom: `if err != nil` is true even though the concrete value is nil; a nil pointer panics inside a method.
- Why: An interface is a (type, value) pair; returning (*T)(nil) as error yields a non-nil interface because its type word is set.
- Fix: Return a literal nil on the error path and check typed nils at boundaries; never return a typed nil as an error.

### 8. Unbuffered channel deadlock
- Symptom: "all goroutines are asleep - deadlock!"; a send and its receive block forever on one goroutine.
- Why: An unbuffered channel send blocks until a receiver is ready; if both live in the same goroutine, or no receiver ever exists, nothing can proceed.
- Fix: Send from one goroutine and receive in another; add a buffer when the producer must not block; use select with ctx.Done()/default; close channels from the sender only.

## Language Core

Concise reference for language-level decisions. Framework-neutral by design; see [modern-go.md](modern-go.md) for version-gated features.

- **Syntax and type features**: composite literals, useful zero values, := inference, range semantics, defer/panic/recover, method sets, embedding, rune vs byte, string immutability.
- **Generics**: type parameters `[T any]`, constraints (~, comparable), inference; no type parameters on methods; use them for type-safe containers/algorithms, not as a replacement for interfaces.
- **Interfaces**: implicit satisfaction, small single-method interfaces, accept interfaces / return structs, type switches and assertions, use `any` sparingly.
- **Concurrency and synchronization primitives**: goroutine (cheap, M:N scheduled), channel (buffered/unbuffered, directional, close, range), select (default + cancellation), sync.Mutex/RWMutex, sync.Once, sync.WaitGroup, sync.Cond, sync/atomic, sync.Map, context.Context.
- **sync/async patterns**: Go has no async/await — concurrency is explicit goroutines plus channels; fan-out/fan-in, worker pools, pipelines (stages joined by channels), cancellation via errgroup-style ctx, generator pattern, bounded concurrency with a semaphore channel.
- **Error handling**: error as a value, sentinel errors, fmt.Errorf("%w"), errors.Is/As/Join, custom error types, wrap at boundaries and handle once.
- **Idiomatic package design**: small packages named for what they provide, internal/, documented exports, no util/common grab-bags, accept interfaces, avoid init() side effects, keep the zero value useful.

Standard-library-only example (no framework types, no ORM tags):

```go
// A plain struct: no ORM tags in language-level examples.
type User struct {
    ID   string
    Mail string
}

// Signal 404 with the standard library, not a framework constant.
w.WriteHeader(http.StatusNotFound)
```

## Framework Selection

Pick a reference only when the task needs framework scaffolding; language questions above are framework-neutral.

| Framework / stack | Reference file | When to read |
| --- | --- | --- |
| No framework (standard library, `net/http`) | [modern-go.md](modern-go.md) | First, for any code — choose version-appropriate syntax and modern built-ins (slices, maps, cmp) before writing. |
| Fiber (HTTP handlers), Cobra (CLI commands), GORM (models), Clean Architecture scaffolding | [references/file-templates.md](references/file-templates.md) | Only when emitting framework-specific files: a Fiber handler, a Cobra command, a GORM-tagged entity, DTOs, repository/service layers, or a Clean Architecture layout. |

## Response Patterns

Framework-neutral workflow for any Go language request:

1. Classify: language-level (syntax, types, concurrency, errors) vs framework scaffolding. Language-level is answered from Gotchas / Language Core.
2. For concurrent code, name the happens-before edges and the stop condition (ctx.Done()) before writing; verify with `go test -race` and `go vet`.
3. Write standard-library-first code; reach for frameworks only through the Framework Selection table and its linked reference.
4. Prefer one small compiling example over prose; state the target Go version and gate features with [modern-go.md](modern-go.md).
5. Close by naming the specific gotcha that applies (loop capture, typed nil, unbuffered channel) so the "why" is explicit.

Framework-specific requests (one-line pointers, no inline recipes):

- Asked to create a Web API or REST handler: see [references/file-templates.md](references/file-templates.md).
- Asked to create a CLI tool or commands: see [references/file-templates.md](references/file-templates.md).

## Remember

- Check Gotchas first: most Go bugs are races, leaks, or interface nils.
- Always honor context.Context; give every goroutine a stop condition.
- Verify concurrency with `go test -race`; `go vet` catches loop-variable capture.
- Wrap with `%w`, inspect with errors.Is / errors.As, never compare error strings.
- Keep answers framework-neutral here; framework templates live in `references/`.
- Confirm the project's Go version via [modern-go.md](modern-go.md) before using newer syntax.
