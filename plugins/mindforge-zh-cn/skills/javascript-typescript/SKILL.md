---
name: javascript-typescript
description: 使用此技能处理 TypeScript 类型收窄失效、泛型或类型守卫难写、ES6+ / JavaScript 模块与 Promise 语义存疑，以及任何 JS/TS 语言层面问题（哪怕只有一段代码、哪怕没有点名任何框架）时使用。当用户只给出代码片段时也触发本 skill。
---

# JavaScript 与 TypeScript 语言技能

以语言本身为核心：JS/TS 语法、类型系统、异步与惯用法。框架相关代码放在 `references/` 并在下方给出链接；语言层面的回答保持框架无关。

## Gotchas

每条陷阱按「现象 → 原因 → 修复」组织。写任何异步或带类型的代码前先过一遍。

### 1. `any` 扩散
- 现象：一个 `any`（例如来自未标注类型的 JSON）会悄悄抹掉下游所有类型；类型检查与自动补全随之失效。
- 原因：`any` 会关闭类型检查并具有传染性，经由类型推断、赋值和返回类型一路传播。
- 修复：把外部数据标为 `unknown` 并在边界处收窄；公开签名里不要出现 `any`。

### 2. `as` 断言与收窄
- 现象：`const u = data as User` 能通过编译，但运行时形状不符时 `u.name` 会抛错。
- 原因：`as` 只是让编译器「信你」，没有任何运行时校验；收窄（`typeof`、`in`、可辨识联合、类型守卫）才真正证明形状，`satisfies` 能在不放宽类型的前提下校验字面量。
- 修复：用类型守卫或控制流收窄替代断言；`as` 只留给无法校验的场景，例如 `as const`。

### 3. 未处理的 Promise 拒绝
- 现象：异步失败被吞掉，或进程报出信息含糊、没有有效堆栈的未处理拒绝。
- 原因：没有 `catch` / `try` 的拒绝会逃逸；`await` 若不在 try/catch 中，会把错误抛给调用链。
- 修复：在 try/catch 中 `await`、挂上 `.catch()`，或改用 `Promise.allSettled`；绝不让拒绝无人接管。

### 4. 顺序 `await` 与 `Promise.all`
- 现象：三个彼此独立的异步调用耗时是各自之和，而不是最慢的那个。
- 原因：连续或在循环里 `await` 会串行化——下一个 Promise 要等上一个 resolve 后才创建。
- 修复：一起发起后用 `await Promise.all([...])`；允许部分失败时用 `allSettled`。

### 5. 游离的 Promise
- 现象：fire-and-forget 的任务有时根本没跑完，错误也不留任何日志就消失。
- 原因：调用 `async` 函数却不加 `await`、`return` 或 `.catch()`，会把它从调用方生命周期里剥离。
- 修复：`await` 它，或显式 `void` 并补一个 `.catch()`；启用 no-floating-promises 之类的 lint 规则。

### 6. `unknown` 与 `any`
- 现象：`JSON.parse(raw).id` 看似能用，直到载荷不是对象就抛错，且编译期毫无警告。
- 原因：`any` 允许任何操作；`unknown` 在收窄前禁止一切操作，强制你显式检查。
- 修复：把解析/动态值当作 `unknown`，访问前用 `typeof` / `in` / 守卫收窄。

### 7. `==` 隐式转换
- 现象：`[] == false`、`"" == 0`、`null == undefined` 结果反直觉，条件判断里藏着转换 bug。
- 原因：`==` 走的是带隐式类型转换的抽象相等算法；`===` 直接比较类型与值。
- 修复：一律默认 `===`；唯一可容忍的例外是 `x == null`，用于同时判断 null 与 undefined。

### 8. ES 模块循环依赖
- 现象：导入的绑定是 `undefined`，或抛出 "Cannot access before initialization"（TDZ）。
- 原因：ESM 使用一次性求值的 live binding；循环依赖可能在模块体初始化完成前就读取该绑定。
- 修复：把共享常量/工具抽到第三个模块、避免顶层副作用，跨循环时导入函数而非已求值的值。

### 9. `this` 绑定
- 现象：`const f = obj.method; f()` 失败，因为 `this` 是 `undefined` 或指向了错误对象。
- 原因：`this` 由调用点决定，而非定义处；严格模式与 ESM 下裸调用会让它变成 `undefined`。
- 修复：回调改用箭头函数、`.bind(obj)`，或写成 `obj.method()`；提取 handler 时显式传入上下文。

### 10. 结构化类型的意外
- 现象：带多余属性的对象被当成更窄的类型接受，两个名义上不同的 interface 可以互换。
- 原因：TypeScript 是结构化类型——兼容性看形状而非声明名字；多余属性检查只作用于新鲜的对象字面量。
- 修复：用 brand（unique symbol 或私有字段）区分名义类型，并用 `satisfies` 在校验字面量的同时保留其窄类型。

## Language Core

语言层面决策的速查。刻意保持框架无关；框架脚手架见下方 Framework Selection 表。依据 TypeScript Handbook（narrowing、satisfies、unknown vs any）、MDN Promise / async-await 与 ECMAScript 模块语义。

- **类型系统与收窄**：结构化类型、`unknown` 与 `any`、控制流收窄（`typeof`、`in`、`instanceof`、可辨识联合）、自定义守卫（`x is T`）、`satisfies` 与 `as const`、多余属性检查。
- **泛型**：`function first<T>(xs: readonly T[]): T | undefined`、约束（`T extends { id: string }`）、默认值、类型推断、`keyof` / 映射 / 条件类型——参数化的是类型而非值。
- **ES6+ 语法与模块语义**：解构、展开/剩余、可选链 `?.`、空值合并 `??`、模板字符串、`for...of`；ESM 静态 import 会被提升，采用只读 live binding 且模块单例，`export` / `export default`、顶层 `await`——此处不涉及 `require`。
- **事件循环与 async/await**：单一调用栈；宏任务（定时器、I/O）与微任务（Promise 回调、`queueMicrotask`）；`await` 让出并在微任务中恢复；异步不等于并行，CPU 密集任务仍会阻塞。
- **Promise 组合器**：`Promise.all`（快速失败）、`allSettled`（收齐全部结果）、`race`（最先敲定）、`any`（最先兑现）；按失败语义选择，而非凭习惯。
- **错误处理**：`try/catch/finally`、`strict` 下 `catch (e)` 为 `unknown`、类型化错误守卫、用 `cause` 包装、以 `Error` 而非字符串 reject；在边界处只处理一次。
- **不可变性与惯用法**：优先 `const` 与 `as const`，用展开 / `map` / `filter` 复制，避免原地修改，用 `===` 比较，写小而纯的函数。

仅使用标准库的示例（无框架类型、无运行时专属全局量）：

```typescript
// A type guard narrows `unknown` to a concrete shape at the boundary.
function isUser(value: unknown): value is { id: string; name: string } {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value
  );
}

// A generic function preserves the element type without `any`.
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}

// `satisfies` validates a literal while keeping its narrow type.
const config = { retries: 3, mode: 'strict' } satisfies Record<string, number | string>;

// Plain config object, never a runtime-specific global.
const retries = config.retries ?? 0;
```

## Framework Selection

仅当任务需要框架脚手架时才查对应参考；上面的语言问题与框架无关。

| 框架 / 运行时 | 参考文件 | 何时阅读 |
| --- | --- | --- |
| Express（REST API 后端：controllers、services、routes、middleware） | [references/express-api-patterns.md](references/express-api-patterns.md) | 仅在产出后端 REST API 时——项目结构、控制器、repository/service 分层或中间件脚手架。 |
| React（组件、自定义 Hook、Context） | [references/react-patterns.md](references/react-patterns.md) | 仅在用 TypeScript 编写 React 组件、自定义 Hook 或基于 Context 的状态时。 |
| Jest / 测试工具 | [references/testing-patterns.md](references/testing-patterns.md) | 仅在为 JS/TS 工具函数编写单元/集成测试或测试配置时。 |

## Response Patterns

面向任何 JS/TS 语言请求的框架无关工作流：

1. 先分类：语言层面（语法、类型、异步、模块）还是框架脚手架；语言层面用 Gotchas / Language Core 回答。
2. 写异步代码前，先点明并发形态——独立任务用 `Promise.all`、允许部分失败用 `allSettled`——并确认每个 Promise 都被 await 或妥善处理。
3. 优先写标准库代码；只有经由 Framework Selection 表及其链接的参考才引入框架。
4. 宁可给一个带类型的小例子（泛型处用 `<T>`）也不要长篇大论；说明目标是 ESM 还是 CommonJS。
5. 结尾点出具体命中的陷阱（`any`、`as`、`==`、`this`、循环依赖），把「为什么」讲透。

框架专属请求（仅一行指针，不内联具体做法）：

- 被要求创建后端 REST API / Express 项目结构：见 [references/express-api-patterns.md](references/express-api-patterns.md)。
- 被要求创建 React 组件或自定义 Hook：见 [references/react-patterns.md](references/react-patterns.md)。
- 被要求搭建测试或测试配置：见 [references/testing-patterns.md](references/testing-patterns.md)。

## Remember

- 先查 Gotchas：多数 JS/TS bug 出在 `any`、`as`、未处理拒绝、`==` 或 `this`。
- 在边界处收窄 `unknown`；公开签名里不放 `any`；优先 `satisfies` 与 `as const`，少用 `as`。
- 发起的每个 Promise 都要 `await`；独立任务用 `Promise.all`，允许部分失败用 `allSettled`。
- 一律默认 `===`、`const` 与不可变复制。
- 这里的回答保持框架无关；框架模板放在 `references/`。
- 产出框架脚手架前先读对应参考；语言层面的问题无需读它。
