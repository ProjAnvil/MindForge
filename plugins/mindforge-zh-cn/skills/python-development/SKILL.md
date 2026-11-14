---
name: python-development
description: 使用此技能处理生成器惰性求值或被耗尽、GIL 与 CPU 密集任务、类型提示或上下文管理器行为异常，以及任何 Python 语言层面疑问（哪怕只有一段代码、哪怕没有点名任何框架）时使用。
---

# Python 开发 —— 语言核心

本技能聚焦 Python 语言本身：语法、类型系统、并发与 async 模型、GIL、generator、context manager，以及源自数据模型的惯用法与陷阱。刻意保持框架中立。应用与框架相关的范例放在 `references/`，见下文的 Framework Selection。

## Gotchas

每条陷阱按「症状 → 原因 → 修复」组织，因为真正值得记住的是「原因」。

### 1. Mutable default arguments
- 症状：函数在多次调用之间「记住」了数据；`def add(x, bucket=[])` 里的列表不断增长。
- 原因：默认值在 `def` 执行时求值一次，之后一直复用同一个对象。
- 修复：默认设为 `None`，在函数体内新建对象。
```python
def add(x, bucket=None):
    if bucket is None:            # a fresh object on every call
        bucket = []
    bucket.append(x)
    return bucket
```

### 2. Late-binding closures in loops
- 症状：一组 lambda 全部返回循环的最后一个值。
- 原因：闭包捕获的是「变量」而非「值」，并在调用时才解析——此时循环早已结束。
- 修复：用默认参数在定义时把值固定下来。
```python
funcs = [lambda i=i: i for i in range(3)]  # bind i at definition time
```

### 3. GIL and CPU-bound work
- 症状：加线程并不能加速 CPU 密集循环，甚至更慢。
- 原因：GIL 同一时刻只允许一个线程执行字节码，CPU 密集的线程会串行化。
- 修复：CPU 密集用进程（`concurrent.futures.ProcessPoolExecutor`）；线程与 `asyncio` 留给 I/O 等待。

### 4. Blocking calls inside `async def`
- 症状：一个协程卡住整个事件循环，其他任务全部停滞。
- 原因：`time.sleep`、阻塞 I/O 与 CPU 循环从不 `await`，控制权不会交回事件循环。
- 修复：延迟用 `await asyncio.sleep(...)`，阻塞调用用 `await asyncio.to_thread(...)`。
```python
result = await asyncio.to_thread(blocking_read, path)  # run off the loop
```

### 5. Generator laziness and exhaustion
- 症状：第二次迭代什么都没有，或「算好的」值从未出现。
- 原因：generator 惰性且一次性；一旦耗尽便一直为空。`map`/`filter` 与生成器表达式同理。
- 修复：需要复用就 `list(...)`，或重新创建 generator；别假设它「存着」结果。

### 6. `is` vs `==`
- 症状：`x is 1000` 有时成立有时不成立；小整数/字符串看起来没问题。
- 原因：`is` 比较身份，`==` 比较值；interning 与缓存会掩盖这个 bug，直到不再掩盖。
- 修复：`is` 只用于单例（`None`、`True`、`False`、`...`）；值比较一律用 `==`。

### 7. Broad `except`
- 症状：真正的 bug 凭空消失；`except Exception: pass` 把错误吞掉。
- 原因：裸捕获或过宽捕获会吞下一切，包括拼写错误与自身逻辑错误（`KeyboardInterrupt`/`SystemExit` 继承自 `BaseException`，不是 `Exception`）。
- 修复：捕获最窄的类型，用 `as exc` 绑定后重新抛出或记录；绝不静默 `pass`。

### 8. `asyncio` task cancellation and shielding
- 症状：`task.cancel()` 停不掉关键区段，或取消落在某个 `await` 中途而破坏状态。
- 原因：取消以 `CancelledError` 的形式在下一个 `await` 处投递，并传播到正在等待的对象。
- 修复：用 `await asyncio.shield(critical())` 保护，在 `finally` 里清理，清理后让 `CancelledError` 继续传播。

### 9. Context manager `__exit__` return value
- 症状：异常悄无声息地消失，没有 traceback。
- 原因：`__exit__` 返回真值会抑制进行中的异常；返回 `None`/`False` 才会让它继续传播。
- 修复：默认返回 `False`/`None`；在 `@contextmanager` 里把 `yield` 包进 `try/finally`，只在明确要抑制时才抑制（或用 `contextlib.suppress`）。

## Language Core

语言全景——够用来选对工具，不是教程。示例一律只用标准库。

### Type hints and typing features
内建泛型（`list[T]`、`dict[K, V]`）、`TypeVar`、`Union`/`|`、`Optional`、`Literal`、`Annotated`、`TypedDict` 与 `Self` 来自 `typing` 及 PEP 585/604。注解在运行时并不强制；请交给静态检查器，并用 `from __future__ import annotations` 延迟求值。
```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:          # parametrized, framework-free
    return items[0]
```

### Dataclasses and protocols
`@dataclass` 自动生成 `__init__`/`__repr__`/`__eq__`；`frozen=True` 得到值对象，`slots=True` 省内存。`Protocol` 提供结构化子类型（静态检查的 duck typing），无需继承。
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
`async def` 返回 coroutine，在被 await 或调度之前什么都不做。`asyncio.create_task` 并发调度，`await asyncio.gather` 汇合结果，`TaskGroup`（3.11+）提供结构化并发。只有 `await` 点才会把控制权交回事件循环。
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
`yield` 把函数变成惰性迭代器；`yield from` 用于委托。迭代器是单次的，generator 是惰性的，`itertools` 覆盖各类组合子。数据大或无限时优先用 generator。
```python
def read_lines(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip()          # nothing is materialized in memory
```

### Context managers
`with` 调用 `__enter__`/`__exit__` 并保证清理；`contextlib.contextmanager` 可用 generator 构造一个，`closing`/`suppress`/`ExitStack` 覆盖常见场景。`__enter__` 返回的对象就是 `as` 的目标。
```python
from contextlib import contextmanager

@contextmanager
def open_upper(path: str):
    with open(path, encoding="utf-8") as f:   # builtins.open, not an async file lib
        yield (line.upper() for line in f)    # a plain stdlib context manager
```

### Error handling and exception chaining
捕获最窄的类型，用 `raise NewError(...) from exc` 保留 cause，`from None` 隐藏它；裸 `raise` 重新抛出。自定义异常应继承合适内建类型（`ValueError`，而非 HTTP 层）。没有 schema 库时手动校验。
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
包内优先绝对导入；相对导入（`.`、`..`）只在包内使用。`__init__.py` 标记包，`__all__` 控制 `from x import *`，`if __name__ == "__main__":` 保护脚本。避免循环导入与通配导入，别在导入时产生副作用（PEP 8）。

### Idioms
对有竞态的检查优先 EAFP（`try`/`except`）而非 LBYL，推导式优先于手写 `append` 循环，`enumerate`/`zip` 优先于下标，格式化用 f-string，灵活赋值用解包与 `*_`，任何资源都用 `with`。先想到 `pathlib`、`itertools`、`functools`、`collections`，再写自定义代码。

## Framework Selection

框架与测试范例**不是**语言内容——在写应用级代码*之前*先读对应文件。每个文件都直接链接，只有一层深度。

| Framework / library | Reference file | When to read |
| --- | --- | --- |
| Django | [django-patterns.md](references/django-patterns.md) | 构建 model、view 或 Django 应用 |
| FastAPI | [fastapi-patterns.md](references/fastapi-patterns.md) | 创建 endpoint 或请求校验 |
| pytest / testing | [testing-patterns.md](references/testing-patterns.md) | 用 fixture 编写测试 |

## Response Patterns

- 语言层面的问题，就在这里用标准库代码回答；先讲「原因」再给修复。
- 如果请求其实是完整应用、服务、endpoint 或测试套件，那是框架任务：去读 Framework Selection 里链接的对应文件，而不要在此内联生成。
- 比较方案（线程 vs 进程 vs `asyncio`）时按工作负载（CPU vs I/O）而非偏好，并引用对应的陷阱条目。
- 优先最小可运行片段而非样板；遇到版本相关特性（如 3.11+ 的 `TaskGroup`）要注明 Python 版本。

## Remember

- 语言及其数据模型优先；框架是下游选择。
- `is` 比较身份，`==` 比较值；默认值只求值一次；闭包捕获变量而非值。
- `asyncio` 帮 I/O，GIL 限制 CPU 线程；绝不在 `async def` 里阻塞。
- generator 惰性且一次性；context manager 保证清理。
- 捕获最窄异常，用 `from` 链接，清理后让 `CancelledError` 继续传播。
- 示例只用标准库；框架细节推到 `references/`。
- 拿不准时从「原因」（PEP 8、数据模型、asyncio/typing 文档）推理，而非凭经验法则。
