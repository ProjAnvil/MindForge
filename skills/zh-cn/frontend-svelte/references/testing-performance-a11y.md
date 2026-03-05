### 7. 测试

#### 使用 Vitest 进行单元测试
```typescript
// Button.test.ts
import { render, screen, fireEvent } from '@testing-library/svelte';
import { expect, test, describe, vi } from 'vitest';
import Button from './Button.svelte';

describe('Button', () => {
  test('渲染文本', () => {
    render(Button, { props: { children: '点击我' } });
    expect(screen.getByRole('button')).toHaveTextContent('点击我');
  });

  test('点击时调用 onClick', async () => {
    const onClick = vi.fn();
    render(Button, { props: { onclick: onClick } });

    await fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  test('当 disabled prop 为 true 时被禁用', () => {
    render(Button, { props: { disabled: true } });
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

#### 集成测试
```typescript
// login.test.ts
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { expect, test, vi } from 'vitest';
import LoginPage from './+page.svelte';

test('登录流程', async () => {
  const mockFetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ token: 'abc123' })
    })
  );

  global.fetch = mockFetch;

  render(LoginPage);

  await fireEvent.input(screen.getByLabelText('邮箱'), {
    target: { value: 'user@example.com' }
  });

  await fireEvent.input(screen.getByLabelText('密码'), {
    target: { value: 'password123' }
  });

  await fireEvent.click(screen.getByRole('button', { name: '登录' }));

  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', expect.any(Object));
  });
});
```

### 8. 性能优化

#### 代码分割
```svelte
<script lang="ts">
  import { onMount } from 'svelte';

  let HeavyComponent;

  onMount(async () => {
    const module = await import('./HeavyComponent.svelte');
    HeavyComponent = module.default;
  });
</script>

{#if HeavyComponent}
  <svelte:component this={HeavyComponent} />
{:else}
  <div>加载中...</div>
{/if}
```

#### 图片优化
```svelte
<script lang="ts">
  import { browser } from '$app/environment';

  export let src: string;
  export let alt: string;

  let loaded = false;
  let visible = false;

  function handleIntersection(entries: IntersectionObserverEntry[]) {
    if (entries[0].isIntersecting) {
      visible = true;
    }
  }

  function setupObserver(node: HTMLElement) {
    if (!browser) return;

    const observer = new IntersectionObserver(handleIntersection);
    observer.observe(node);

    return {
      destroy() {
        observer.disconnect();
      }
    };
  }
</script>

<div use:setupObserver class="aspect-video bg-muted">
  {#if visible}
    <img
      {src}
      {alt}
      loading="lazy"
      class:opacity-0={!loaded}
      class:opacity-100={loaded}
      class="transition-opacity duration-300"
      on:load={() => loaded = true}
    />
  {/if}
</div>
```

### 9. 无障碍访问最佳实践

```svelte
<script lang="ts">
  import { createDialog } from '@melt-ui/svelte';

  const {
    elements: { trigger, overlay, content, title, description, close },
    states: { open }
  } = createDialog();
</script>

<button use:trigger>打开对话框</button>

{#if $open}
  <div use:overlay class="fixed inset-0 bg-black/50" />
  <div
    use:content
    role="dialog"
    aria-labelledby="dialog-title"
    aria-describedby="dialog-description"
    class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
  >
    <h2 use:title id="dialog-title">对话框标题</h2>
    <p use:description id="dialog-description">对话框描述</p>

    <button use:close aria-label="关闭对话框">
      <X class="h-4 w-4" />
    </button>
  </div>
{/if}
```
