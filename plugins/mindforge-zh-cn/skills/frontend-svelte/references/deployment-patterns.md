### 10. 部署

#### Bun 构建和部署
```bash
# 生产构建
bun run build

# 预览生产构建
bun run preview

# 使用适配器部署（示例：Node）
# svelte.config.js 应该有：adapter: adapter-node()
node build/index.js
```

#### 环境变量
```typescript
// lib/config/env.ts
import { PUBLIC_API_URL } from '$env/static/public';
import { PRIVATE_API_KEY } from '$env/static/private';

export const config = {
  apiUrl: PUBLIC_API_URL,
  apiKey: PRIVATE_API_KEY // 仅服务器端可用
};
```

## 常见模式和解决方案

### 1. 使用 shadcn-svelte 的深色模式
```typescript
// stores/theme.ts
import { persistedStore } from '$lib/utils/stores';

export const theme = persistedStore<'light' | 'dark'>('theme', 'light');

export function toggleTheme() {
  theme.update(t => t === 'light' ? 'dark' : 'light');
}

// 应用主题
if (browser) {
  theme.subscribe(value => {
    document.documentElement.classList.toggle('dark', value === 'dark');
  });
}
```

### 2. Toast 通知
```typescript
// lib/components/ui/sonner.ts
import { toast as sonnerToast } from 'svelte-sonner';

export const toast = {
  success: (message: string, options?) =>
    sonnerToast.success(message, options),
  error: (message: string, options?) =>
    sonnerToast.error(message, options),
  info: (message: string, options?) =>
    sonnerToast.info(message, options),
};
```

### 3. 认证流程
```typescript
// hooks.server.ts
import type { Handle } from '@sveltejs/kit';
import { sequence } from '@sveltejs/kit/hooks';

const authHandler: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get('auth_token');

  if (token) {
    try {
      const user = await verifyToken(token);
      event.locals.user = user;
    } catch {
      event.cookies.delete('auth_token');
    }
  }

  return resolve(event);
};

export const handle = sequence(authHandler);
```

### 4. 使用 SSE 的实时更新
```typescript
// routes/api/events/+server.ts
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
  const stream = new ReadableStream({
    start(controller) {
      const interval = setInterval(() => {
        const data = `data: ${JSON.stringify({ time: Date.now() })}\n\n`;
        controller.enqueue(new TextEncoder().encode(data));
      }, 1000);

      return () => clearInterval(interval);
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
};
```

## 故障排查

### 常见问题

1. **Bun 兼容性问题**：某些包可能不适用于 Bun。使用 npm/pnpm 作为回退
2. **水合不匹配**：确保 SSR 和客户端渲染相同的内容
3. **内存泄漏**：始终在 `onDestroy` 中清理或从 `onMount` 返回清理函数
4. **shadcn-svelte 的类型错误**：确保已安装 `@melt-ui/svelte` 类型

### 调试工具

```svelte
<script lang="ts">
  import { dev } from '$app/environment';

  // 仅在开发环境
  $: if (dev) {
    console.log('组件状态:', { /* ... */ });
  }
</script>
```

## 资源

- **Svelte**：https://svelte.dev/docs
- **SvelteKit**：https://kit.svelte.dev/docs
- **shadcn-svelte**：https://www.shadcn-svelte.com/docs
- **Bun**：https://bun.sh/docs
- **Melt UI**：https://melt-ui.com/docs
- **Tailwind CSS**：https://tailwindcss.com/docs
