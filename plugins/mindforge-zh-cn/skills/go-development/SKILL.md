---
name: go-development
description: 使用此技能处理协程泄漏、通道死锁、context.Context 取消失效、sync.WaitGroup 卡死、竞态检测报告，或 Go memory model 与语言语义存疑，以及任何 Go 语言层面疑问（哪怕只有一段代码、哪怕没有点名任何框架）时使用。当用户只给出代码片段时也触发本 skill。
---

# Go 开发技能

以语言本身为核心：Go 语法、并发与惯用法。框架相关代码放在 `references/` 并在下方给出链接；语言层面的回答保持框架无关。

## Gotchas

每条陷阱按「现象 → 原因 → 修复」组织。写任何并发代码前先过一遍。

### 1. 数据竞争与 Go memory model（DRF-SC）
- 现象：`go test -race` 报出 DATA RACE；多次运行结果不一致。
- 原因：没有 happens-before 边（通道收发、sync.Mutex、sync/atomic）时，并发读写就是数据竞争。go.dev/ref/mem 只保证 DRF-SC：无数据竞争的程序表现为顺序一致，有竞争的程序行为未定义，编译器与 CPU 可自由重排。
- 修复：用 sync.Mutex/RWMutex 或 sync/atomic 保护共享状态，或通过通道转移所有权；绝不要用 time.Sleep「修复」。用 `go test -race` 验证（go.dev/blog/race-detector）。

### 2. 忽略 context.Context 取消与超时
- 现象：请求已超时但工作仍在跑；"context deadline exceeded" 出现得太晚；资源不断堆积。
- 原因：context 是取消信号树，不是值容器；忽略 ctx.Done() 会让 goroutine 没有停止条件，而 deadline 只有在每个下游调用都接收并遵守 ctx 时才有意义（go.dev/blog/context）。
- 修复：把 ctx 作为第一个参数，select 监听 <-ctx.Done()，用 context.WithCancel/WithTimeout/WithDeadline 派生，defer 调用 cancel()，并把 ctx 透传给每个阻塞调用。

### 3. Goroutine 泄漏
- 现象：pprof 里 goroutine 数量无限增长；内存持续上升；父函数返回后 worker 永不退出。
- 原因：阻塞在通道收发且不会再有配对方、或没有 ctx.Done() 的死循环，都没有退出路径；运行时不会回收阻塞中的 goroutine（go.dev/blog/pipelines）。
- 修复：给每个 goroutine 一个停止条件（select 中的 ctx.Done()），用 close 广播完成，并让持有者通过 sync.WaitGroup / errgroup 等待，使泄漏可见。

### 4. 闭包捕获循环变量（Go 1.22 之前）
- 现象：每个 goroutine 都打印最后一个元素；所有回调看到同一个值。
- 原因：Go 1.22 之前 range 变量在迭代间复用，闭包捕获的是同一个地址，且往往在循环推进后才执行。
- 修复：把值作为参数传入（go func(v T){...}(v)）或用 v := v 遮蔽；Go 1.22+ 的循环变量按迭代独立，但面向旧版本仍保留该写法。按 [modern-go.md](modern-go.md) 判断版本。

### 5. 循环里写 defer
- 现象：文件描述符或锁一直累积到函数返回；长循环内存飙升；close() 执行得太晚。
- 原因：defer 在函数返回时执行，而非迭代结束，所以每次迭代都会再压入一个延迟调用。
- 修复：把循环体抽到带自己 defer 的辅助函数，或在每次迭代末尾显式释放/关闭。

### 6. 错误包装让 errors.Is / errors.As 失效
- 现象：包装之后 `err == ErrNotFound` 为 false；哨兵错误判断静默失败。
- 原因：相等比较的是外层包装而非根因；fmt.Errorf("%w") 会构建链，"%v" 会丢掉链。
- 修复：用 fmt.Errorf("...: %w", err) 包装，用 errors.Is(err, target) / errors.As(err, &t) 检查；绝不比较 err.Error() 字符串。标准库 HTTP 用 w.WriteHeader(http.StatusNotFound) 表示 404，不用框架常量。

### 7. interface 里的 typed nil
- 现象：具体值是 nil，但 `if err != nil` 仍为 true；方法内空指针 panic。
- 原因：interface 是 (type, value) 二元组；把 (*T)(nil) 作为 error 返回时，type 字段非空，整个 interface 就非 nil。
- 修复：错误路径直接返回字面量 nil，在边界处检查 typed nil；绝不把 typed nil 当作 error 返回。

### 8. 无缓冲通道死锁
- 现象："all goroutines are asleep - deadlock!"；发送与接收在同一个 goroutine 上永久阻塞。
- 原因：无缓冲通道的发送要等到接收方就绪才返回；若收发都在同一 goroutine，或根本不存在接收方，就谁也无法推进。
- 修复：在一个 goroutine 发送、另一个接收；生产者不该阻塞时加缓冲；用带 ctx.Done()/default 的 select；只由发送方 close 通道。

## Language Core

语言层面决策的速查。刻意保持框架无关；版本相关特性见 [modern-go.md](modern-go.md)。

- **语法与类型特性**：复合字面量、有用的零值、:= 类型推断、range 语义、defer/panic/recover、方法集、内嵌、rune 与 byte、字符串不可变。
- **泛型**：类型参数 `[T any]`、约束（~、comparable）、类型推断；方法不能有类型参数；用于类型安全的容器/算法，而非替代接口。
- **接口**：隐式实现、小的单方法接口、接受接口/返回结构体、type switch 与类型断言、谨慎使用 `any`。
- **并发与同步原语**：goroutine（轻量、M:N 调度）、通道（有/无缓冲、单向、close、range）、select（default + 取消）、sync.Mutex/RWMutex、sync.Once、sync.WaitGroup、sync.Cond、sync/atomic、sync.Map、context.Context。
- **同步/异步模式**：Go 没有 async/await —— 并发就是显式的 goroutine 加通道；fan-out/fan-in、worker pool、pipeline（阶段由通道相连）、errgroup 式 ctx 取消、生成器模式、用信号量通道限制并发。
- **错误处理**：error 即值、哨兵错误、fmt.Errorf("%w")、errors.Is/As/Join、自定义错误类型、在边界包装且只处理一次。
- **惯用的包设计**：小而按职责命名的包、internal/、导出标识符写文档、不要 util/common 大杂烩、接受接口、避免 init() 副作用、让零值可用。

仅使用标准库的示例（无框架类型、无 ORM 标签）：

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

仅当任务需要框架脚手架时才查对应参考；上面的语言问题与框架无关。

| 框架 / 技术栈 | 参考文件 | 何时阅读 |
| --- | --- | --- |
| 无框架（标准库，`net/http`） | [modern-go.md](modern-go.md) | 最先看，任何代码都适用 —— 写之前先确定与目标版本匹配的语法和现代内置包（slices、maps、cmp）。 |
| Fiber（HTTP handler）、Cobra（CLI 命令）、GORM（模型）、整洁架构脚手架 | [references/file-templates.md](references/file-templates.md) | 仅在需要产出框架专属文件时：Fiber handler、Cobra 命令、带 GORM 标签的实体、DTO、repository/service 分层，或整洁架构目录。 |

## Response Patterns

面向任何 Go 语言请求的框架无关工作流：

1. 先分类：语言层面（语法、类型、并发、错误）还是框架脚手架；语言层面用 Gotchas / Language Core 回答。
2. 写并发代码前，先点明 happens-before 边和停止条件（ctx.Done()），再用 `go test -race` 与 `go vet` 验证。
3. 优先写标准库代码；只有经由 Framework Selection 表及其链接的参考才引入框架。
4. 宁可给一个能编译的小例子，也不要长篇大论；说明目标 Go 版本并用 [modern-go.md](modern-go.md) 约束特性。
5. 结尾点出具体命中的陷阱（循环变量捕获、typed nil、无缓冲通道），把「为什么」讲透。

框架专属请求（仅一行指针，不内联具体做法）：

- 被要求创建 Web API 或 REST handler：见 [references/file-templates.md](references/file-templates.md)。
- 被要求创建 CLI 工具或命令：见 [references/file-templates.md](references/file-templates.md)。

## Remember

- 先查 Gotchas：多数 Go bug 是竞争、泄漏或 interface nil。
- 始终尊重 context.Context；给每个 goroutine 一个停止条件。
- 用 `go test -race` 验证并发；`go vet` 能抓到循环变量捕获。
- 用 `%w` 包装，用 errors.Is / errors.As 检查，绝不比较错误字符串。
- 这里的回答保持框架无关；框架模板放在 `references/`。
- 用 [modern-go.md](modern-go.md) 确认项目的 Go 版本后再用新语法。
