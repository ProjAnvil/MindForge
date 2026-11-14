---
name: javascript-typescript
description: Use this skill when TypeScript type narrowing misfires, when Promise or async/await ordering and rejection handling go wrong, or when ES6+ / JavaScript module and generics semantics are in doubt. Claim ANY language-level JS/TS question proactively — even a single snippet, even when no framework is named.
---

# JavaScript & TypeScript — Language Skill

Language-first guidance: JS/TS syntax, the type system, concurrency, and idioms. Framework-specific code lives in `references/` and is linked below; keep language answers framework-neutral.

## Gotchas

Each trap is written as Symptom -> Why -> Fix. Scan these before writing any async or typed code.

### 1. `any` propagation
- Symptom: One `any` (e.g. from untyped JSON) silently strips types from everything downstream; checks and autocomplete vanish.
- Why: `any` opts out of checking and is contagious — it propagates through inference, assignments, and return types.
- Fix: Type external data as `unknown` and narrow at the boundary; keep `any` out of public signatures.

### 2. `as` assertions vs narrowing
- Symptom: `const u = data as User` compiles, then `u.name` throws because the runtime shape differs.
- Why: `as` only silences the compiler — there is no runtime check. Narrowing (`typeof`, `in`, discriminant unions, type guards) actually proves the shape; `satisfies` validates literals without widening.
- Fix: Replace assertions with a type guard or control-flow narrowing; reserve `as` for uncheckable cases such as `as const`.

### 3. Unhandled promise rejection
- Symptom: An async failure is swallowed, or the process reports an opaque unhandled rejection with no useful stack.
- Why: A rejected promise with no `catch`/`try` escapes; `await` outside try/catch rethrows into the caller chain.
- Fix: Wrap `await` in try/catch, attach `.catch()`, or use `Promise.allSettled`; never leave a rejection unobserved.

### 4. Sequential `await` vs `Promise.all`
- Symptom: Three independent async calls take the sum of their latencies instead of the maximum.
- Why: Back-to-back or in-loop `await` serializes — the next promise is created only after the previous resolves.
- Fix: Start them together and `await Promise.all([...])`; use `allSettled` when partial failures are acceptable.

### 5. Floating promises
- Symptom: Fire-and-forget work sometimes never completes and its errors disappear without a log.
- Why: Calling an `async` function without `await`, `return`, or `.catch()` detaches it from the caller's lifecycle.
- Fix: `await` it, or explicitly `void` it with a `.catch()`; enable a no-floating-promises lint rule.

### 6. `unknown` vs `any`
- Symptom: `JSON.parse(raw).id` "works" until the payload is not an object, then throws with no compile-time warning.
- Why: `any` permits every operation; `unknown` forbids all of them until narrowed, forcing an explicit check.
- Fix: Treat parsed/dynamic values as `unknown`, then narrow with `typeof`/`in`/guards before access.

### 7. `==` coercion
- Symptom: `[] == false`, `"" == 0`, and `null == undefined` behave unexpectedly; coercion bugs hide in conditionals.
- Why: `==` applies the abstract equality algorithm with implicit type conversion; `===` compares type and value directly.
- Fix: Default to `===`; the one tolerated exception is `x == null` to test for both null and undefined.

### 8. ES module cycles
- Symptom: An imported binding is `undefined` or throws "Cannot access before initialization" (TDZ).
- Why: ESM uses live bindings evaluated once; a cycle can read a binding before its module body has initialized it.
- Fix: Move shared constants/helpers into a third module, avoid top-level side effects, and import functions rather than evaluated values across a cycle.

### 9. `this` binding
- Symptom: `const f = obj.method; f()` fails because `this` is `undefined` or the wrong object.
- Why: `this` is set by the call site, not the definition; in strict mode and ESM a bare call leaves it `undefined`.
- Fix: Use arrow functions for callbacks, `.bind(obj)`, or call as `obj.method()`; pass context explicitly when extracting handlers.

### 10. Structural typing surprises
- Symptom: An object with extra properties is accepted where a narrower type is expected, and two nominally different interfaces are interchangeable.
- Why: TypeScript is structural — compatibility is by shape, not declared name; excess property checks apply only to fresh object literals.
- Fix: Add a brand (unique symbol or private field) for nominal-like distinctions, and use `satisfies` to validate literals while keeping their narrow type.

## Language Core

Concise reference for language-level decisions. Framework-neutral by design; see the Framework Selection table for scaffolding. Grounded in the TypeScript Handbook (narrowing, satisfies, unknown vs any), MDN Promise / async-await, and ECMAScript module semantics.

- **Type system and narrowing**: structural typing, `unknown` vs `any`, control-flow narrowing (`typeof`, `in`, `instanceof`, discriminated unions), user-defined guards (`x is T`), `satisfies` vs `as const`, excess property checks.
- **Generics**: `function first<T>(xs: readonly T[]): T | undefined`, constraints (`T extends { id: string }`), defaults, inference, `keyof`/mapped/conditional types — parameterize types, not values.
- **ES6+ syntax and module semantics**: destructuring, spread/rest, optional chaining (`?.`), nullish coalescing (`??`), template literals, `for...of`; ESM static imports are hoisted with live read-only bindings and a single module instance, `export`/`export default`, top-level `await` — no `require` here.
- **Event loop and async/await**: one call stack; macrotasks (timers, I/O) vs microtasks (promise jobs, `queueMicrotask`); `await` yields and resumes as a microtask; async is not parallel — CPU-bound work still blocks.
- **Promise combinators**: `Promise.all` (fail-fast), `allSettled` (all outcomes), `race` (first settle), `any` (first fulfil); choose by failure semantics, not habit.
- **Error handling**: `try/catch/finally`, `catch (e)` is `unknown` under `strict`, typed error guards, `cause` for wrapping, reject with `Error` not strings; handle once at the boundary.
- **Immutability and idiom**: prefer `const` and `as const`, copy with spread/`map`/`filter`, avoid in-place mutation, compare with `===`, small pure functions.

Standard-library-only example (no framework types, no runtime globals):

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

Pick a reference only when the task needs framework scaffolding; language questions above are framework-neutral.

| Framework / runtime | Reference file | When to read |
| --- | --- | --- |
| Express (REST API backend: controllers, services, routes, middleware) | [references/express-api-patterns.md](references/express-api-patterns.md) | Only when emitting a backend REST API — project structure, controllers, repository/service layers, or middleware scaffolding. |
| React (components, custom hooks, context) | [references/react-patterns.md](references/react-patterns.md) | Only when writing React components, custom hooks, or Context-based state with TypeScript. |
| Jest / testing utilities | [references/testing-patterns.md](references/testing-patterns.md) | Only when writing unit/integration tests or test configuration for JS/TS utilities. |

## Response Patterns

Framework-neutral workflow for any JS/TS language request:

1. Classify: language-level (syntax, types, async, modules) vs framework scaffolding; language-level is answered from Gotchas / Language Core.
2. For async code, name the concurrency shape first — independent work via `Promise.all`, partial failures via `allSettled` — and confirm every promise is awaited or handled.
3. Write standard-library-only code; reach for frameworks only through the Framework Selection table and its linked reference.
4. Prefer one small typed example (with `<T>` where generics apply) over prose; state whether the target is ESM or CommonJS.
5. Close by naming the specific gotcha that applies (`any`, `as`, `==`, `this`, cycles) so the "why" is explicit.

Framework-specific requests (one-line pointers, no inline recipes):

- Asked to create a backend REST API / Express project structure: see [references/express-api-patterns.md](references/express-api-patterns.md).
- Asked to create a React component or custom hook: see [references/react-patterns.md](references/react-patterns.md).
- Asked to set up tests or a test configuration: see [references/testing-patterns.md](references/testing-patterns.md).

## Remember

- Check Gotchas first: most JS/TS bugs are `any`, `as`, unhandled rejections, `==`, or `this`.
- Narrow `unknown` at boundaries; keep `any` out of signatures; prefer `satisfies` and `as const` over `as`.
- `await` every promise you start; `Promise.all` for independent work, `allSettled` for partial failures.
- Default to `===`, `const`, and immutable copies.
- Keep answers framework-neutral here; framework templates live in `references/`.
- Read the linked reference before emitting framework scaffolding; language questions never need it.
