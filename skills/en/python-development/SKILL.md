---
name: python-development
description: Use this skill when a generator is exhausted or lazy, when asyncio task cancellation or GIL-bound CPU work confuses, or when type hints or a context manager misbehave. Claim ANY language-level Python question proactively — even one snippet, even when no framework is named. Trigger on "generator exhausted", "asyncio cancellation" or "type hints".
---

# Python Development — Language Core

This skill is about the Python language itself: its syntax, type system, concurrency and async model, the GIL, generators, context managers, and the idioms and gotchas that follow from the data model. It is deliberately framework-neutral. App-level and framework recipes live in `references/`; see the Framework Selection section below.

## Gotchas

Each trap is written as symptom → why → fix, because the *why* is the part worth remembering.

### 1. Mutable default arguments
- Symptom: a function "remembers" data across calls; `def add(x, bucket=[])` keeps growing.
- Why: default values are evaluated once, when the `def` executes, and that one object is reused.
- Fix: default to `None` and build the object inside the body.
```python
def add(x, bucket=None):
    if bucket is None:            # a fresh object on every call
        bucket = []
    bucket.append(x)
    return bucket
```

### 2. Late-binding closures in loops
- Symptom: a list of lambdas all return the last loop value.
- Why: closures capture the *variable*, not its value, and resolve it when called — after the loop ends.
- Fix: freeze the value now with a default argument.
```python
funcs = [lambda i=i: i for i in range(3)]  # bind i at definition time
```

### 3. GIL and CPU-bound work
- Symptom: adding threads does not speed up a CPU-heavy loop; it can even be slower.
- Why: the GIL lets one thread execute bytecode at a time, so CPU-bound threads serialize.
- Fix: use processes (`concurrent.futures.ProcessPoolExecutor`) for CPU work; reserve threads and `asyncio` for I/O-bound waits.

### 4. Blocking calls inside `async def`
- Symptom: one coroutine freezes the whole event loop; unrelated tasks stall.
- Why: `time.sleep`, blocking I/O and CPU loops never `await`, so control never returns to the loop.
- Fix: `await asyncio.sleep(...)` for delays and `await asyncio.to_thread(...)` for blocking calls.
```python
result = await asyncio.to_thread(blocking_read, path)  # run off the loop
```

### 5. Generator laziness and exhaustion
- Symptom: a second iteration yields nothing, or a "computed" value never appears.
- Why: generators are lazy and single-use; once exhausted they stay empty. `map`/`filter` and generator expressions behave the same.
- Fix: call `list(...)` if you need to reuse the data, or recreate the generator; never assume it "holds" results.

### 6. `is` vs `==`
- Symptom: `x is 1000` works in one place and fails in another; small ints/strings seem fine.
- Why: `is` compares identity, `==` compares value; interning and caching hide the bug until they don't.
- Fix: use `is` only for singletons (`None`, `True`, `False`, `...`); use `==` for values.

### 7. Broad `except`
- Symptom: real bugs disappear; `except Exception: pass` hides errors.
- Why: a bare or broad catch swallows everything, including typos and your own logic errors (`KeyboardInterrupt`/`SystemExit` derive from `BaseException`, not `Exception`).
- Fix: catch the narrowest type, bind `as exc`, and re-raise or log; never silently `pass`.

### 8. `asyncio` task cancellation and shielding
- Symptom: `task.cancel()` does not stop a critical section, or cancellation lands mid-`await` and corrupts state.
- Why: cancellation is delivered as `CancelledError` at the next `await`, and it propagates into whatever you are awaiting.
- Fix: protect with `await asyncio.shield(critical())`, clean up in `finally`, and let `CancelledError` propagate after cleanup.

### 9. Context manager `__exit__` return value
- Symptom: an exception vanishes with no traceback.
- Why: `__exit__` returning a truthy value suppresses the in-flight exception; `None`/`False` propagates it.
- Fix: return `False`/`None` by default; in `@contextmanager` wrap `yield` in `try/finally` and suppress only deliberately (or use `contextlib.suppress`).

## Language Core

A map of the language surface — enough to pick the right tool, not a tutorial. Keep examples standard-library-only.

### Type hints and typing features
Builtin generics (`list[T]`, `dict[K, V]`), `TypeVar`, `Union`/`|`, `Optional`, `Literal`, `Annotated`, `TypedDict` and `Self` come from `typing` and PEP 585/604. Annotations are not enforced at runtime; run a static checker, and use `from __future__ import annotations` to postpone evaluation.
```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:          # parametrized, framework-free
    return items[0]
```

### Dataclasses and protocols
`@dataclass` generates `__init__`/`__repr__`/`__eq__`; `frozen=True` gives value objects, `slots=True` saves memory. `Protocol` provides structural subtyping (duck typing checked statically) with no inheritance.
```python
from dataclasses import dataclass
from typing import Protocol

class Sized(Protocol):
    def __len__(self) -> int: ...

@dataclass(frozen=True, slots=True)
class Config:                            # a plain object, no ORM session
    retries: int = 3
    timeout: float = 1.0
```

### async/await and asyncio task semantics
`async def` returns a coroutine that does nothing until awaited or scheduled. `asyncio.create_task` schedules concurrently, `await asyncio.gather` joins them, and `TaskGroup` (3.11+) gives structured concurrency. Only `await` points yield to the loop.
```python
import asyncio

async def fetch_all(urls: list[str]) -> list[str]:
    async def one(url: str) -> str:      # stdlib only, no third-party client
        await asyncio.sleep(0)           # a yield point
        return url
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(one(u)) for u in urls]
    return [t.result() for t in tasks]
```

### Generators and iterators
`yield` turns a function into a lazy iterator; `yield from` delegates. Iterators are single-pass, generators are lazy, and `itertools` covers the combinators. Prefer a generator for large or infinite data.
```python
def read_lines(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip()          # nothing is materialized in memory
```

### Context managers
`with` calls `__enter__`/`__exit__` and guarantees cleanup; `contextlib.contextmanager` builds one from a generator, and `closing`/`suppress`/`ExitStack` cover common cases. The object from `__enter__` is the `as` target.
```python
from contextlib import contextmanager

@contextmanager
def open_upper(path: str):
    with open(path, encoding="utf-8") as f:   # builtins.open, not an async file lib
        yield (line.upper() for line in f)    # a plain stdlib context manager
```

### Error handling and exception chaining
Catch narrow types, use `raise NewError(...) from exc` to preserve the cause and `from None` to hide it; bare `raise` re-raises. Custom exceptions should subclass a sensible builtin (`ValueError`, not an HTTP layer). Validate manually when no schema library is involved.
```python
class NotFoundError(ValueError):
    pass

def require(condition: bool, message: str) -> None:   # manual validation
    if not condition:
        raise NotFoundError(message)                   # plain ValueError subclass
try:
    require(user is not None, "user not found")
except ValueError as exc:
    raise RuntimeError("load failed") from exc         # chaining preserves the cause
```

### Packaging and imports
Prefer absolute imports inside packages; keep relative imports (`.`, `..`) within a package. `__init__.py` marks a package, `__all__` controls `from x import *`, and `if __name__ == "__main__":` guards scripts. Avoid circular and wildcard imports, and keep import-time side effects out (PEP 8).

### Idioms
Prefer EAFP (`try`/`except`) over LBYL for racy checks, comprehensions over manual `append` loops, `enumerate`/`zip` over index juggling, f-strings for formatting, unpacking and `*_` for flexible assignment, and `with` for any resource. Reach for `pathlib`, `itertools`, `functools` and `collections` before writing custom code.

## Framework Selection

Framework and testing recipes are **not** language material — read the matching file *before* writing app-level code. Each is linked directly, one level deep.

| Framework / library | Reference file | When to read |
| --- | --- | --- |
| Django | [django-patterns.md](references/django-patterns.md) | Building models, views, or a Django app |
| FastAPI | [fastapi-patterns.md](references/fastapi-patterns.md) | Creating endpoints or request validation |
| pytest / testing | [testing-patterns.md](references/testing-patterns.md) | Writing tests with fixtures |

## Response Patterns

- For a language-level question, answer here with stdlib code; explain the *why* before the fix.
- If the request is really for a full app, service, endpoint, or test suite, it is a framework task: read the linked reference in Framework Selection instead of generating it inline.
- Compare options (threads vs processes vs `asyncio`) by the workload (CPU vs I/O), not by taste, and cite the relevant gotcha.
- Prefer a minimal runnable snippet over boilerplate; state the Python version when a feature is version-gated (e.g. `TaskGroup` on 3.11+).

## Remember

- The language and its data model come first; frameworks are downstream choices.
- `is` is identity, `==` is value; defaults are evaluated once; closures capture variables, not values.
- `asyncio` helps I/O, the GIL limits CPU threads; never block inside `async def`.
- Generators are lazy and single-use; context managers guarantee cleanup.
- Catch narrow exceptions, chain with `from`, and let `CancelledError` propagate after cleanup.
- Keep examples standard-library-only; push framework specifics into `references/`.
- When unsure, reason from the why (PEP 8, the data model, asyncio/typing docs) rather than a rule of thumb.
