# 现代 Go 指南

## 检测到的 Go 版本

!`grep -rh "^go " --include="go.mod" . 2>/dev/null | cut -d' ' -f2 | sort | uniq -c | sort -nr | head -1 | xargs | cut -d' ' -f2 | grep . || echo unknown`

## 如何使用此参考

不要自己搜索 go.mod 文件或尝试检测版本。只使用上面显示的版本。

**如果检测到版本（不是 "unknown"）：**
- 说："This project is using Go X.XX, so I'll stick to modern Go best practices and freely use language features up to and including this version. If you'd prefer a different target version, just let me know."
- 不要列出特性，不要请求确认

**如果版本是 "unknown"：**
- 说："Could not detect Go version in this repository"
- 使用 AskUserQuestion: "Which Go version should I target?" → [1.23] / [1.24] / [1.25] / [1.26]

**编写 Go 代码时**，使用本文档中直到目标版本的所有特性：
- 优先使用现代内置函数和包（`slices`、`maps`、`cmp`）而不是旧模式
- 不要使用比目标版本更新的 Go 特性
- 当有现代替代方案时，不要使用过时的模式

---

## 各 Go 版本特性

### Go 1.0+

- `time.Since`: `time.Since(start)` 而不是 `time.Now().Sub(start)`

### Go 1.8+

- `time.Until`: `time.Until(deadline)` 而不是 `deadline.Sub(time.Now())`

### Go 1.13+

- `errors.Is`: `errors.Is(err, target)` 而不是 `err == target`（支持包装的错误）

### Go 1.18+

- `any`: 使用 `any` 而不是 `interface{}`
- `bytes.Cut`: `before, after, found := bytes.Cut(b, sep)` 而不是 Index+slice
- `strings.Cut`: `before, after, found := strings.Cut(s, sep)`

### Go 1.19+

- `fmt.Appendf`: `buf = fmt.Appendf(buf, "x=%d", x)` 而不是 `[]byte(fmt.Sprintf(...))`
- `atomic.Bool`/`atomic.Int64`/`atomic.Pointer[T]`: 类型安全的原子操作而不是 `atomic.StoreInt32`

```go
var flag atomic.Bool
flag.Store(true)
if flag.Load() { ... }

var ptr atomic.Pointer[Config]
ptr.Store(cfg)
```

### Go 1.20+

- `strings.Clone`: `strings.Clone(s)` 复制字符串而不共享内存
- `bytes.Clone`: `bytes.Clone(b)` 复制字节切片
- `strings.CutPrefix/CutSuffix`: `if rest, ok := strings.CutPrefix(s, "pre:"); ok { ... }`
- `errors.Join`: `errors.Join(err1, err2)` 组合多个错误
- `context.WithCancelCause`: `ctx, cancel := context.WithCancelCause(parent)` 然后 `cancel(err)`
- `context.Cause`: `context.Cause(ctx)` 获取导致取消的错误

### Go 1.21+

**内置函数:**
- `min`/`max`: `max(a, b)` 而不是 if/else 比较
- `clear`: `clear(m)` 删除所有 map 条目，`clear(s)` 将切片元素置零

**slices 包:**
- `slices.Contains`: `slices.Contains(items, x)` 而不是手动循环
- `slices.Index`: `slices.Index(items, x)` 返回索引（未找到返回 -1）
- `slices.IndexFunc`: `slices.IndexFunc(items, func(item T) bool { return item.ID == id })`
- `slices.SortFunc`: `slices.SortFunc(items, func(a, b T) int { return cmp.Compare(a.X, b.X) })`
- `slices.Sort`: `slices.Sort(items)` 用于可排序类型
- `slices.Max`/`slices.Min`: `slices.Max(items)` 而不是手动循环
- `slices.Reverse`: `slices.Reverse(items)` 而不是手动交换循环
- `slices.Compact`: `slices.Compact(items)` 就地删除连续重复项
- `slices.Clip`: `slices.Clip(s)` 移除未使用的容量
- `slices.Clone`: `slices.Clone(s)` 创建副本

**maps 包:**
- `maps.Clone`: `maps.Clone(m)` 而不是手动遍历 map
- `maps.Copy`: `maps.Copy(dst, src)` 将条目从 src 复制到 dst
- `maps.DeleteFunc`: `maps.DeleteFunc(m, func(k K, v V) bool { return condition })`

**sync 包:**
- `sync.OnceFunc`: `f := sync.OnceFunc(func() { ... })` 而不是 `sync.Once` + 包装器
- `sync.OnceValue`: `getter := sync.OnceValue(func() T { return computeValue() })`

**context 包:**
- `context.AfterFunc`: `stop := context.AfterFunc(ctx, cleanup)` 在取消时运行清理
- `context.WithTimeoutCause`: `ctx, cancel := context.WithTimeoutCause(parent, d, err)`
- `context.WithDeadlineCause`: 类似，但使用截止时间而不是持续时间

### Go 1.22+

**循环:**
- `for i := range n`: `for i := range len(items)` 而不是 `for i := 0; i < len(items); i++`
- 循环变量现在可以安全地在 goroutine 中捕获（每次迭代都有自己的副本）

**cmp 包:**
- `cmp.Or`: `cmp.Or(flag, env, config, "default")` 返回第一个非零值

```go
// 旧写法:
name := os.Getenv("NAME")
if name == "" {
    name = "default"
}
// 新写法:
name := cmp.Or(os.Getenv("NAME"), "default")
```

**reflect 包:**
- `reflect.TypeFor`: `reflect.TypeFor[T]()` 而不是 `reflect.TypeOf((*T)(nil)).Elem()`

**net/http:**
- 增强的 `http.ServeMux` 模式: `mux.HandleFunc("GET /api/{id}", handler)` 支持方法和路径参数
- `r.PathValue("id")` 获取路径参数

### Go 1.23+

- `maps.Keys(m)` / `maps.Values(m)` 返回迭代器
- `slices.Collect(iter)` 不要用手动循环从迭代器构建切片
- `slices.Sorted(iter)` 一步完成收集和排序

```go
keys := slices.Collect(maps.Keys(m))       // 不要: for k := range m { keys = append(keys, k) }
sortedKeys := slices.Sorted(maps.Keys(m))  // 收集 + 排序
for k := range maps.Keys(m) { process(k) } // 直接迭代
```

**time 包**

- `time.Tick`: 可以放心使用 `time.Tick` — 从 Go 1.23 开始，垃圾回收器可以回收未引用的 ticker，即使它们没有被停止。Stop 方法不再需要帮助垃圾回收器。当 Tick 够用时，没有理由再优先使用 NewTicker。

### Go 1.24+

- `t.Context()` 而不是 `context.WithCancel(context.Background())` 用于测试。
  当测试函数需要 context 时，始终使用 t.Context()。

之前:
```go
func TestFoo(t *testing.T) {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    result := doSomething(ctx)
}
```
之后:
```go
func TestFoo(t *testing.T) {
    ctx := t.Context()
    result := doSomething(ctx)
}
```

- `omitzero` 而不是 `omitempty` 在 JSON 结构体标签中。
  对于 time.Duration、time.Time、结构体、切片、map，始终使用 omitzero。

之前:
```go
type Config struct {
    Timeout time.Duration `json:"timeout,omitempty"` // 对 Duration 不起作用！
}
```
之后:
```go
type Config struct {
    Timeout time.Duration `json:"timeout,omitzero"`
}
```

- `b.Loop()` 而不是 `for i := 0; i < b.N; i++` 在基准测试中。
  在基准测试函数的主循环中，始终使用 b.Loop()。

之前:
```go
func BenchmarkFoo(b *testing.B) {
    for i := 0; i < b.N; i++ {
        doWork()
    }
}
```
之后:
```go
func BenchmarkFoo(b *testing.B) {
    for b.Loop() {
        doWork()
    }
}
```

- `strings.SplitSeq` 而不是 `strings.Split` 在迭代时。
  在 for-range 循环中迭代分割结果时，始终使用 SplitSeq/FieldsSeq。

之前:
```go
for _, part := range strings.Split(s, ",") {
    process(part)
}
```
之后:
```go
for part := range strings.SplitSeq(s, ",") {
    process(part)
}
```
还有: `strings.FieldsSeq`, `bytes.SplitSeq`, `bytes.FieldsSeq`.

### Go 1.25+

- `wg.Go(fn)` 而不是 `wg.Add(1)` + `go func() { defer wg.Done(); ... }()`。
  使用 sync.WaitGroup 启动 goroutine 时，始终使用 wg.Go()。

之前:
```go
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func() {
        defer wg.Done()
        process(item)
    }()
}
wg.Wait()
```
之后:
```go
var wg sync.WaitGroup
for _, item := range items {
    wg.Go(func() {
        process(item)
    })
}
wg.Wait()
```

### Go 1.26+

- `new(val)` 而不是 `x := val; &x` — 返回任意值的指针。
  Go 1.26 扩展了 new() 以接受表达式，而不仅仅是类型。
  类型推断: new(0) → *int, new("s") → *string, new(T{}) → *T。
  不要使用 `x := val; &x` 模式 — 始终直接使用 new(val)。
  不要使用冗余转换如 new(int(0)) — 只写 new(0)。
  常见用例: 指针类型的结构体字段。

之前:
```go
timeout := 30
debug := true
cfg := Config{
    Timeout: &timeout,
    Debug:   &debug,
}
```
之后:
```go
cfg := Config{
    Timeout: new(30),   // *int
    Debug:   new(true), // *bool
}
```

- `errors.AsType[T](err)` 而不是 `errors.As(err, &target)`。
  检查错误是否匹配特定类型时，始终使用 errors.AsType。

之前:
```go
var pathErr *os.PathError
if errors.As(err, &pathErr) {
    handle(pathErr)
}
```
之后:
```go
if pathErr, ok := errors.AsType[*os.PathError](err); ok {
    handle(pathErr)
}
```
