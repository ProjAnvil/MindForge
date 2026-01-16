---
name: frontend-svelte
description: Professional frontend development skill covering Svelte, SvelteKit, shadcn-svelte, and Bun ecosystem. Use this skill when building modern web applications, creating UI components, implementing state management, handling forms, or working with TypeScript-based frontend architectures. Ideal for projects requiring reactive frameworks, server-side rendering, or type-safe component development.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Frontend Development Skill

Comprehensive skill for modern frontend development with Svelte, SvelteKit, shadcn-svelte, and the Bun ecosystem.

## Technology Stack

### Core Framework: Svelte + SvelteKit

#### Svelte Fundamentals
- **Reactive Framework**: Compile-time framework that converts components into highly efficient imperative code
- **True Reactivity**: Automatic dependency tracking without virtual DOM
- **Small Bundle Size**: Minimal runtime overhead
- **Built-in Animations**: Transition and animation directives
- **Scoped Styles**: Component styles are scoped by default

#### SvelteKit Features
- **Full-Stack Framework**: Server-side rendering (SSR), static site generation (SSG), and client-side rendering (CSR)
- **File-Based Routing**: Routes defined by file system structure
- **API Routes**: Build API endpoints alongside frontend code
- **Form Actions**: Server-side form handling with progressive enhancement
- **Hooks**: Intercept and modify requests/responses
- **Adapters**: Deploy to any platform (Node, Vercel, Netlify, Cloudflare, etc.)

### UI Component Library: shadcn-svelte

#### Overview
- Port of shadcn/ui for Svelte
- Accessible, customizable components built on Radix Svelte (Melt UI)
- Copy-paste component approach (not an npm package)
- Built with Tailwind CSS
- TypeScript support

#### Key Components
- **Forms**: Input, Textarea, Select, Checkbox, Radio, Switch
- **Feedback**: Alert, Toast (Sonner), Dialog, Alert Dialog
- **Navigation**: Button, Dropdown Menu, Tabs, Command Menu
- **Layout**: Card, Separator, Accordion, Collapsible
- **Data Display**: Table, Badge, Avatar, Skeleton
- **Overlays**: Popover, Tooltip, Sheet, Drawer

#### Installation & Usage
```bash
# Initialize shadcn-svelte
bunx shadcn-svelte@latest init

# Add components as needed
bunx shadcn-svelte@latest add button
bunx shadcn-svelte@latest add card
bunx shadcn-svelte@latest add form
```

### Package Manager: Bun

#### Why Bun?
- **Performance**: 25x faster than npm, 4x faster than pnpm
- **All-in-One**: Runtime, bundler, test runner, package manager
- **Drop-in Replacement**: Compatible with npm/Node.js ecosystem
- **Built-in Testing**: Vitest-compatible test runner
- **TypeScript Native**: Native TypeScript support, no compilation needed

#### npm Compatibility
- Reads package.json and package-lock.json/bun.lockb
- Works with most npm packages
- Can run npm scripts via `bun run`
- Falls back to npm when needed for specific packages

## Project Architecture

### Recommended Directory Structure

```
project-root/
├── src/
│   ├── lib/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn-svelte components
│   │   │   │   ├── button/
│   │   │   │   ├── card/
│   │   │   │   └── ...
│   │   │   ├── layout/          # Layout components
│   │   │   │   ├── Header.svelte
│   │   │   │   ├── Footer.svelte
│   │   │   │   └── Sidebar.svelte
│   │   │   └── features/        # Feature-specific components
│   │   │       ├── auth/
│   │   │       ├── dashboard/
│   │   │       └── ...
│   │   ├── stores/              # Svelte stores
│   │   │   ├── user.ts
│   │   │   ├── theme.ts
│   │   │   └── notifications.ts
│   │   ├── utils/               # Utility functions
│   │   │   ├── api.ts
│   │   │   ├── validation.ts
│   │   │   └── formatting.ts
│   │   ├── types/               # TypeScript types
│   │   │   ├── api.ts
│   │   │   └── models.ts
│   │   ├── server/              # Server-side utilities
│   │   │   ├── db.ts
│   │   │   └── auth.ts
│   │   └── config/              # Configuration
│   │       ├── constants.ts
│   │       └── env.ts
│   ├── routes/                  # SvelteKit routes
│   │   ├── +page.svelte         # Home page
│   │   ├── +layout.svelte       # Root layout
│   │   ├── +error.svelte        # Error page
│   │   ├── api/                 # API routes
│   │   │   └── users/
│   │   │       └── +server.ts
│   │   ├── (auth)/              # Route group
│   │   │   ├── login/
│   │   │   └── register/
│   │   └── dashboard/
│   │       ├── +page.svelte
│   │       └── +page.server.ts
│   ├── app.html                 # HTML template
│   ├── app.css                  # Global styles
│   └── hooks.server.ts          # Server hooks
├── static/                      # Static assets
│   ├── images/
│   └── fonts/
├── tests/                       # Tests
│   ├── unit/
│   └── integration/
├── bun.lockb                    # Bun lockfile
├── package.json
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Core Patterns & Best Practices

### 1. Component Development

#### Component Structure Best Practices
```svelte
<script lang="ts">
  // 1. Imports (external, then internal)
  import { onMount, createEventDispatcher } from 'svelte';
  import { fade } from 'svelte/transition';
  import type { User } from '$lib/types';
  import { Button } from '$lib/components/ui/button';

  // 2. Type definitions (if not in separate file)
  interface $$Props {
    user: User;
    variant?: 'default' | 'compact';
  }

  // 3. Props with defaults
  export let user: User;
  export let variant: $$Props['variant'] = 'default';

  // 4. Event dispatcher
  const dispatch = createEventDispatcher<{
    edit: { userId: string };
    delete: { userId: string };
  }>();

  // 5. Local state
  let isEditing = false;
  let formData = { ...user };

  // 6. Reactive declarations
  $: fullName = `${user.firstName} ${user.lastName}`;
  $: hasChanges = JSON.stringify(formData) !== JSON.stringify(user);

  // 7. Functions
  function handleEdit() {
    isEditing = true;
  }

  function handleSave() {
    dispatch('edit', { userId: user.id });
    isEditing = false;
  }

  // 8. Lifecycle hooks
  onMount(() => {
    console.log('Component mounted');

    return () => {
      console.log('Component will unmount');
    };
  });
</script>

<!-- Template with clear hierarchy -->
<div class="user-card" class:compact={variant === 'compact'}>
  {#if isEditing}
    <form on:submit|preventDefault={handleSave}>
      <!-- Edit mode -->
    </form>
  {:else}
    <!-- View mode -->
    <div class="user-info" transition:fade>
      <h3>{fullName}</h3>
      <p>{user.email}</p>
    </div>
    <Button on:click={handleEdit}>Edit</Button>
  {/if}
</div>

<!-- Scoped styles -->
<style lang="postcss">
  .user-card {
    @apply rounded-lg border p-4;

    &.compact {
      @apply p-2;
    }
  }

  .user-info {
    @apply space-y-2;
  }
</style>
```

#### TypeScript Props Pattern
```typescript
// For complex props, use interface
interface $$Props {
  items: Item[];
  selectedId?: string;
  onSelect?: (item: Item) => void;
  class?: string;
}

export let items: $$Props['items'];
export let selectedId: $$Props['selectedId'] = undefined;
export let onSelect: $$Props['onSelect'] = undefined;

// For class prop forwarding
let className: $$Props['class'] = '';
export { className as class };
```

### 2. State Management

#### Svelte Stores

**Writable Store**
```typescript
// stores/user.ts
import { writable } from 'svelte/store';
import type { User } from '$lib/types';

function createUserStore() {
  const { subscribe, set, update } = writable<User | null>(null);

  return {
    subscribe,
    set,
    login: (user: User) => set(user),
    logout: () => set(null),
    updateProfile: (updates: Partial<User>) =>
      update(user => user ? { ...user, ...updates } : null)
  };
}

export const user = createUserStore();
```

**Derived Store**
```typescript
// stores/user.ts (continued)
import { derived } from 'svelte/store';

export const isAuthenticated = derived(
  user,
  $user => $user !== null
);

export const userPermissions = derived(
  user,
  $user => $user?.roles.flatMap(role => role.permissions) ?? []
);
```

**Readable Store (for external data)**
```typescript
import { readable } from 'svelte/store';

export const time = readable(new Date(), (set) => {
  const interval = setInterval(() => {
    set(new Date());
  }, 1000);

  return () => clearInterval(interval);
});
```

**Custom Store with Persistence**
```typescript
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export function persistedStore<T>(key: string, initialValue: T) {
  const stored = browser ? localStorage.getItem(key) : null;
  const initial = stored ? JSON.parse(stored) : initialValue;

  const store = writable<T>(initial);

  if (browser) {
    store.subscribe(value => {
      localStorage.setItem(key, JSON.stringify(value));
    });
  }

  return store;
}

// Usage
export const theme = persistedStore<'light' | 'dark'>('theme', 'light');
```

#### Context API (Component Tree State)
```svelte
<!-- Parent.svelte -->
<script lang="ts">
  import { setContext } from 'svelte';
  import type { Writable } from 'svelte/store';
  import { writable } from 'svelte/store';

  const formData = writable({ name: '', email: '' });
  setContext('form', formData);
</script>

<!-- Child.svelte -->
<script lang="ts">
  import { getContext } from 'svelte';
  import type { Writable } from 'svelte/store';

  const formData = getContext<Writable<FormData>>('form');
</script>

<input bind:value={$formData.name} />
```

### 3. SvelteKit Routing & Data Loading

#### Page Structure
```typescript
// routes/blog/[slug]/+page.ts
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params, fetch, parent }) => {
  // Access parent layout data
  const parentData = await parent();

  // Fetch data
  const response = await fetch(`/api/posts/${params.slug}`);
  const post = await response.json();

  return {
    post,
    meta: {
      title: post.title,
      description: post.excerpt
    }
  };
};
```

```svelte
<!-- routes/blog/[slug]/+page.svelte -->
<script lang="ts">
  import type { PageData } from './$types';

  export let data: PageData;
</script>

<svelte:head>
  <title>{data.meta.title}</title>
  <meta name="description" content={data.meta.description} />
</svelte:head>

<article>
  <h1>{data.post.title}</h1>
  <div>{@html data.post.content}</div>
</article>
```

#### Server-Side Data Loading
```typescript
// routes/dashboard/+page.server.ts
import type { PageServerLoad, Actions } from './$types';
import { error, fail, redirect } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ locals, depends }) => {
  // depends() creates a dependency for invalidation
  depends('app:dashboard');

  if (!locals.user) {
    throw redirect(307, '/login');
  }

  try {
    const stats = await fetchUserStats(locals.user.id);
    return { stats };
  } catch (err) {
    throw error(500, 'Failed to load dashboard data');
  }
};

export const actions: Actions = {
  updateProfile: async ({ request, locals }) => {
    const formData = await request.formData();
    const name = formData.get('name');

    if (!name) {
      return fail(400, { name, missing: true });
    }

    await updateUser(locals.user.id, { name });
    return { success: true };
  }
};
```

#### Form Actions with Progressive Enhancement
```svelte
<script lang="ts">
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';

  export let form: ActionData;

  let loading = false;
</script>

<form
  method="POST"
  action="?/updateProfile"
  use:enhance={() => {
    loading = true;

    return async ({ result, update }) => {
      await update();
      loading = false;

      if (result.type === 'success') {
        // Handle success
      }
    };
  }}
>
  <input
    name="name"
    value={form?.name ?? ''}
    aria-invalid={form?.missing}
  />

  {#if form?.missing}
    <p class="error">Name is required</p>
  {/if}

  <button disabled={loading}>
    {loading ? 'Saving...' : 'Save'}
  </button>
</form>
```

### 4. API Development

#### REST API Endpoints
```typescript
// routes/api/users/+server.ts
import { json, error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url, locals }) => {
  const page = Number(url.searchParams.get('page')) || 1;
  const limit = 20;

  try {
    const users = await db.users.findMany({
      skip: (page - 1) * limit,
      take: limit
    });

    return json({
      users,
      pagination: {
        page,
        limit,
        total: await db.users.count()
      }
    });
  } catch (err) {
    throw error(500, 'Failed to fetch users');
  }
};

export const POST: RequestHandler = async ({ request, locals }) => {
  if (!locals.user?.isAdmin) {
    throw error(403, 'Unauthorized');
  }

  const body = await request.json();

  // Validate
  if (!body.email || !body.name) {
    throw error(400, 'Missing required fields');
  }

  const user = await db.users.create({ data: body });

  return json(user, { status: 201 });
};
```

#### Type-Safe API Client
```typescript
// lib/utils/api.ts
import { error } from '@sveltejs/kit';

export async function apiClient<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    }
  });

  if (!response.ok) {
    throw error(response.status, await response.text());
  }

  return response.json();
}

// Usage
import type { User } from '$lib/types';

const users = await apiClient<User[]>('/api/users');
```

### 5. Form Handling & Validation

#### Using shadcn-svelte Forms
```svelte
<script lang="ts">
  import { z } from 'zod';
  import { superForm } from 'sveltekit-superforms/client';
  import { zodClient } from 'sveltekit-superforms/adapters';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import type { PageData } from './$types';

  export let data: PageData;

  const schema = z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string()
  }).refine(data => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword']
  });

  const { form, errors, enhance, delayed } = superForm(data.form, {
    validators: zodClient(schema),
    resetForm: false,
    onUpdated: ({ form }) => {
      if (form.valid) {
        // Handle success
        toast.success('Registration successful!');
      }
    }
  });
</script>

<form method="POST" use:enhance>
  <div class="space-y-4">
    <div>
      <Label for="email">Email</Label>
      <Input
        id="email"
        type="email"
        name="email"
        bind:value={$form.email}
        aria-invalid={!!$errors.email}
      />
      {#if $errors.email}
        <p class="text-sm text-destructive">{$errors.email}</p>
      {/if}
    </div>

    <div>
      <Label for="password">Password</Label>
      <Input
        id="password"
        type="password"
        name="password"
        bind:value={$form.password}
        aria-invalid={!!$errors.password}
      />
      {#if $errors.password}
        <p class="text-sm text-destructive">{$errors.password}</p>
      {/if}
    </div>

    <div>
      <Label for="confirmPassword">Confirm Password</Label>
      <Input
        id="confirmPassword"
        type="password"
        name="confirmPassword"
        bind:value={$form.confirmPassword}
        aria-invalid={!!$errors.confirmPassword}
      />
      {#if $errors.confirmPassword}
        <p class="text-sm text-destructive">{$errors.confirmPassword}</p>
      {/if}
    </div>

    <Button type="submit" disabled={$delayed}>
      {$delayed ? 'Registering...' : 'Register'}
    </Button>
  </div>
</form>
```

### 6. Styling with Tailwind CSS

#### Configuration
```javascript
// tailwind.config.js
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))'
        },
        // ... more colors
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)'
      }
    }
  },
  plugins: []
};
```

#### Component Styling Patterns
```svelte
<script lang="ts">
  import { cn } from '$lib/utils';

  let className: string = '';
  export { className as class };

  export let variant: 'default' | 'outline' = 'default';
  export let size: 'sm' | 'md' | 'lg' = 'md';
</script>

<button
  class={cn(
    'inline-flex items-center justify-center rounded-md font-medium transition-colors',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    {
      'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
      'border border-input hover:bg-accent': variant === 'outline',
    },
    {
      'h-8 px-3 text-sm': size === 'sm',
      'h-10 px-4': size === 'md',
      'h-12 px-6 text-lg': size === 'lg',
    },
    className
  )}
  {...$$restProps}
>
  <slot />
</button>
```

### 7. Testing

#### Unit Tests with Vitest
```typescript
// Button.test.ts
import { render, screen, fireEvent } from '@testing-library/svelte';
import { expect, test, describe, vi } from 'vitest';
import Button from './Button.svelte';

describe('Button', () => {
  test('renders with text', () => {
    render(Button, { props: { children: 'Click me' } });
    expect(screen.getByRole('button')).toHaveTextContent('Click me');
  });

  test('calls onClick when clicked', async () => {
    const onClick = vi.fn();
    render(Button, { props: { onclick: onClick } });

    await fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  test('is disabled when disabled prop is true', () => {
    render(Button, { props: { disabled: true } });
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

#### Integration Tests
```typescript
// login.test.ts
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { expect, test, vi } from 'vitest';
import LoginPage from './+page.svelte';

test('login flow', async () => {
  const mockFetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ token: 'abc123' })
    })
  );

  global.fetch = mockFetch;

  render(LoginPage);

  await fireEvent.input(screen.getByLabelText('Email'), {
    target: { value: 'user@example.com' }
  });

  await fireEvent.input(screen.getByLabelText('Password'), {
    target: { value: 'password123' }
  });

  await fireEvent.click(screen.getByRole('button', { name: 'Login' }));

  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith('/api/auth/login', expect.any(Object));
  });
});
```

### 8. Performance Optimization

#### Code Splitting
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
  <div>Loading...</div>
{/if}
```

#### Image Optimization
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

#### Preloading Data
```typescript
// routes/+layout.ts
export const preload = () => {
  return {
    // Preload critical data
  };
};
```

### 9. Accessibility Best Practices

```svelte
<script lang="ts">
  import { createDialog } from '@melt-ui/svelte';

  const {
    elements: { trigger, overlay, content, title, description, close },
    states: { open }
  } = createDialog();
</script>

<button use:trigger>Open Dialog</button>

{#if $open}
  <div use:overlay class="fixed inset-0 bg-black/50" />
  <div
    use:content
    role="dialog"
    aria-labelledby="dialog-title"
    aria-describedby="dialog-description"
    class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
  >
    <h2 use:title id="dialog-title">Dialog Title</h2>
    <p use:description id="dialog-description">Dialog description</p>

    <button use:close aria-label="Close dialog">
      <X class="h-4 w-4" />
    </button>
  </div>
{/if}
```

### 10. Deployment

#### Bun Build & Deploy
```bash
# Build for production
bun run build

# Preview production build
bun run preview

# Deploy with adapter (example: Node)
# svelte.config.js should have: adapter: adapter-node()
node build/index.js
```

#### Environment Variables
```typescript
// lib/config/env.ts
import { PUBLIC_API_URL } from '$env/static/public';
import { PRIVATE_API_KEY } from '$env/static/private';

export const config = {
  apiUrl: PUBLIC_API_URL,
  apiKey: PRIVATE_API_KEY // Only available server-side
};
```

## Common Patterns & Solutions

### 1. Dark Mode with shadcn-svelte
```typescript
// stores/theme.ts
import { persistedStore } from '$lib/utils/stores';

export const theme = persistedStore<'light' | 'dark'>('theme', 'light');

export function toggleTheme() {
  theme.update(t => t === 'light' ? 'dark' : 'light');
}

// Apply theme
if (browser) {
  theme.subscribe(value => {
    document.documentElement.classList.toggle('dark', value === 'dark');
  });
}
```

### 2. Toast Notifications
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

### 3. Authentication Flow
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

### 4. Real-time Updates with SSE
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

## Troubleshooting

### Common Issues

1. **Bun compatibility issues**: Some packages may not work with Bun. Use npm/pnpm as fallback
2. **Hydration mismatches**: Ensure SSR and client render the same content
3. **Memory leaks**: Always cleanup in `onDestroy` or return cleanup functions from `onMount`
4. **Type errors with shadcn-svelte**: Ensure `@melt-ui/svelte` types are installed

### Debug Tools

```svelte
<script lang="ts">
  import { dev } from '$app/environment';

  // Only in development
  $: if (dev) {
    console.log('Component state:', { /* ... */ });
  }
</script>
```

## Resources

- **Svelte**: https://svelte.dev/docs
- **SvelteKit**: https://kit.svelte.dev/docs
- **shadcn-svelte**: https://www.shadcn-svelte.com/docs
- **Bun**: https://bun.sh/docs
- **Melt UI**: https://melt-ui.com/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
