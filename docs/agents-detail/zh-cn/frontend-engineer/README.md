# 前端工程师 Agent - 详细指南

本文档包含使用 Svelte 和 SvelteKit 进行现代前端开发的综合示例、模板和最佳实践。

## 项目设置

```bash
# 使用 Bun 创建新的 SvelteKit 项目
bun create svelte@latest my-app
cd my-app
bun install

# 添加 shadcn-svelte
bunx shadcn-svelte@latest init

# 添加组件
bunx shadcn-svelte@latest add button
bunx shadcn-svelte@latest add card
```

## 项目结构

```
src/
├── lib/
│   ├── components/     # 可重用组件
│   │   ├── ui/        # shadcn-svelte 组件
│   │   └── custom/    # 自定义组件
│   ├── stores/        # Svelte stores
│   ├── utils/         # 辅助函数
│   ├── types/         # TypeScript 类型
│   └── server/        # 服务器端代码
├── routes/            # SvelteKit 路由
│   ├── +page.svelte
│   ├── +layout.svelte
│   └── api/          # API 路由
└── app.html          # HTML 模板
```

## 组件结构模板

```svelte
<script lang="ts">
  import { onMount } from 'svelte';

  // Props with TypeScript types
  export let title: string;
  export let count: number = 0;

  // Local state
  let isLoading = false;

  // Reactive declarations
  $: doubledCount = count * 2;

  // Lifecycle
  onMount(() => {
    // Initialization
    return () => {
      // Cleanup
    };
  });

  // Functions
  function handleClick() {
    count += 1;
  }
</script>

<!-- Template -->
<div class="container">
  <h1>{title}</h1>
  <button on:click={handleClick}>
    Count: {count}
  </button>
</div>

<!-- Styles (scoped by default) -->
<style>
  .container {
    padding: 1rem;
  }
</style>
```

## 使用 shadcn-svelte 处理表单

```svelte
<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";

  let formData = {
    email: '',
    password: ''
  };

  let errors: Record<string, string> = {};

  function validateForm() {
    errors = {};
    if (!formData.email.includes('@')) {
      errors.email = 'Invalid email address';
    }
    if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (!validateForm()) return;

    // Submit logic
  }
</script>

<form on:submit={handleSubmit}>
  <div class="space-y-4">
    <div>
      <Label for="email">Email</Label>
      <Input
        id="email"
        type="email"
        bind:value={formData.email}
        aria-invalid={!!errors.email}
      />
      {#if errors.email}
        <p class="text-sm text-destructive">{errors.email}</p>
      {/if}
    </div>

    <Button type="submit">Submit</Button>
  </div>
</form>
```

## Store 管理

```typescript
// stores/user.ts
import { writable, derived } from 'svelte/store';

export const user = writable<User | null>(null);

export const isAuthenticated = derived(
  user,
  $user => $user !== null
);

export const userDisplayName = derived(
  user,
  $user => $user ? `${$user.firstName} ${$user.lastName}` : 'Guest'
);
```

## API 集成

```typescript
// routes/api/users/+server.ts
import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

export const GET: RequestHandler = async ({ fetch, url }) => {
  const page = url.searchParams.get('page') || '1';

  const response = await fetch(`https://api.example.com/users?page=${page}`);
  const data = await response.json();

  return json(data);
};
```

## 使用 Vitest 测试

```typescript
import { render, screen, fireEvent } from '@testing-library/svelte';
import { expect, test } from 'vitest';
import Button from './Button.svelte';

test('button click increments counter', async () => {
  render(Button, { label: 'Click me' });

  const button = screen.getByRole('button');
  await fireEvent.click(button);

  expect(button).toHaveTextContent('Clicked: 1');
});
```

## 开发命令

```bash
# 开发服务器
bun run dev

# 构建生产版本
bun run build

# 预览生产构建
bun run preview

# 类型检查
bun run check

# 代码检查
bun run lint

# 测试
bun test
```

## 最佳实践

### 组件设计
- 保持组件小而专注
- 使用 TypeScript 确保类型安全
- 实现适当的 props 验证
- 使用组合而非继承
- 使组件可重用和可组合

### 性能优化
- 使用动态导入进行代码拆分
- 对图像和组件实现懒加载
- 预加载关键路由和数据
- 监控包大小
- 适当使用 SSR/SSG
- 实现适当的缓存策略

### 可访问性（a11y）
- 使用语义化 HTML 元素
- 在需要时实现适当的 ARIA 属性
- 确保键盘导航工作正常
- 正确管理焦点
- 确保颜色对比度符合标准（WCAG AA/AAA）
- 使用屏幕阅读器测试

### 安全性
- 清理用户输入
- 实现 CSRF 保护
- 使用安全的 HTTP 头
- 在客户端和服务器端验证数据
- 实现适当的身份验证/授权
- 避免在客户端代码中暴露敏感数据

### 样式指南
- 使用 Tailwind CSS（shadcn-svelte 自带）
- 通过 shadcn-svelte 主题维护一致的设计系统
- 保持组件样式的作用域
- 使用 CSS 变量实现主题化
- 实现暗黑模式支持
- 确保响应式设计（移动优先方法）
