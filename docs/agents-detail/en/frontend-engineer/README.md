# Frontend Engineer Agent - Detailed Guide

This document contains comprehensive examples, templates, and best practices for modern frontend development with Svelte and SvelteKit.

## Project Setup

```bash
# Create new SvelteKit project with Bun
bun create svelte@latest my-app
cd my-app
bun install

# Add shadcn-svelte
bunx shadcn-svelte@latest init

# Add components
bunx shadcn-svelte@latest add button
bunx shadcn-svelte@latest add card
```

## Project Structure

```
src/
├── lib/
│   ├── components/     # Reusable components
│   │   ├── ui/        # shadcn-svelte components
│   │   └── custom/    # Custom components
│   ├── stores/        # Svelte stores
│   ├── utils/         # Helper functions
│   ├── types/         # TypeScript types
│   └── server/        # Server-side code
├── routes/            # SvelteKit routes
│   ├── +page.svelte
│   ├── +layout.svelte
│   └── api/          # API routes
└── app.html          # HTML template
```

## Component Structure Template

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import type { ComponentProps } from './types';

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

## Form Handling with shadcn-svelte

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

## Store Management

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

## API Integration

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

## Testing with Vitest

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

## Development Commands

```bash
# Development server
bun run dev

# Build for production
bun run build

# Preview production build
bun run preview

# Type checking
bun run check

# Linting
bun run lint

# Testing
bun test
```

## Best Practices

### Component Design
- Keep components small and focused
- Use TypeScript for type safety
- Implement proper prop validation
- Use composition over inheritance
- Make components reusable and composable

### Performance Optimization
- Use dynamic imports for code splitting
- Implement lazy loading for images and components
- Preload critical routes and data
- Monitor bundle size
- Use SSR/SSG appropriately
- Implement proper caching strategies

### Accessibility (a11y)
- Use semantic HTML elements
- Implement proper ARIA attributes when needed
- Ensure keyboard navigation works
- Manage focus properly
- Ensure color contrast compliance (WCAG AA/AAA)
- Test with screen readers

### Security
- Sanitize user inputs
- Implement CSRF protection
- Use secure HTTP headers
- Validate data on both client and server
- Implement proper authentication/authorization
- Avoid exposing sensitive data in client-side code

### Styling Guidelines
- Use Tailwind CSS (comes with shadcn-svelte)
- Maintain consistent design system via shadcn-svelte theme
- Keep component styles scoped
- Use CSS variables for theming
- Implement dark mode support
- Ensure responsive design (mobile-first approach)
