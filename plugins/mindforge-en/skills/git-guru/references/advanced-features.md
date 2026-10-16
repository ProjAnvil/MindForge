# Advanced Git Features: Submodules, Hooks & Maintenance

## 7. Submodules

### Add Submodules

```bash
# Add submodule
git submodule add https://github.com/user/repo.git path/to/submodule

# Initialize and clone submodules
git submodule init
git submodule update

# Clone with submodules
git clone --recursive https://github.com/user/repo.git

# Or after clone
git submodule update --init --recursive
```

### Update Submodules

```bash
# Update to latest commit
cd path/to/submodule
git pull origin main

# Update from main repository
git submodule update --remote

# Update all submodules
git submodule update --recursive

# See submodule status
git submodule status
```

### Remove Submodule

```bash
# Remove submodule properly
git submodule deinit path/to/submodule
git rm path/to/submodule
rm -rf .git/modules/path/to/submodule
```

### Submodule Workflows

```bash
# Track specific branch in submodule
git config -f .gitmodules submodule.path.branch main
git submodule update --remote

# Detach HEAD in submodule
git submodule update --checkout

# Merge submodule updates
git submodule foreach 'git pull origin main'
```

---

## 8. Git Hooks

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run linter
npm run lint
if [ $? -ne 0 ]; then
    echo "Linting failed. Commit aborted."
    exit 1
fi

# Run tests
npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

### Pre-push Hook

```bash
# .git/hooks/pre-push
#!/bin/bash
# Prevent pushing to main
current_branch=$(git symbolic-ref --short HEAD)
if [ "$current_branch" = "main" ]; then
    echo "Direct pushes to main are forbidden!"
    exit 1
fi

# Run full test suite before push
npm run test:full
```

### Commit Message Hook

```bash
# .git/hooks/commit-msg
#!/bin/bash
# Validate commit message format
commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,50}'
if ! grep -qE "$commit_regex" $1; then
    echo "Invalid commit message format."
    echo "Expected: type(scope): subject"
    exit 1
fi
```

### Install Hooks

```bash
# Make hook executable
chmod +x .git/hooks/pre-commit

# Copy hooks from template
cp .githooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit

# Or use core.hooksPath
git config core.hooksPath .githooks
```

---

## 10. Repository Maintenance

### Garbage Collection

```bash
# Basic garbage collection
git gc

# Aggressive garbage collection
git gc --aggressive --prune=now

# Prune loose objects
git prune

# Verify repository integrity
git fsck

# Expire reflog entries
git reflog expire --expire=now --all
git gc --prune=now
```

### Repository Optimization

```bash
# Repack repository
git repack -a -d --depth=250 --window=250

# Remove unreachable objects
git prune --expire now

# Clean up working directory
git clean -f -d

# Dry run first
git clean -n -d
```

### Shallow Clone

```bash
# Clone only latest commit (save space)
git clone --depth 1 https://github.com/user/repo.git

# Clone with specific depth
git clone --depth 5 https://github.com/user/repo.git

# Convert shallow to deep
git fetch --unshallow

# Clone single branch
git clone --single-branch --branch main https://github.com/user/repo.git

# Shallow clone subdirectory
git clone --depth 1 --filter=blob:none --sparse https://github.com/user/repo.git
cd repo
git sparse-checkout set path/to/subdirectory
```

### Partial Clone

```bash
# Clone without blobs
git clone --filter=blob:none https://github.com/user/repo.git

# Fetch blobs as needed
git lfs pull

# Treeless clone
git clone --filter=tree:0 https://github.com/user/repo.git
```
