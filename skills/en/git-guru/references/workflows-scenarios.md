# Advanced Git Workflows & Common Scenarios

## Advanced Workflows

### 1. Clean Feature Branch Workflow

```bash
# Create feature branch from main
git checkout main
git pull
git checkout -b feature/new-auth

# Make multiple commits
git commit -m "feat: add login form"
git commit -m "fix: button alignment"
git commit -m "feat: implement OAuth"
git commit -m "docs: update README"

# Before merging, clean up with interactive rebase
git rebase -i main

# Squash fixups, reorder logically, reword for clarity

# Merge with fast-forward only
git checkout main
git merge --ff-only feature/new-auth

# Delete feature branch
git branch -d feature/new-auth
```

### 2. Urgent Fix with Worktree

```bash
# Working on feature branch
git status
# On feature/auth, uncommitted changes

# Urgent bug appears - don't want to stash or commit

# Create worktree for hotfix
git worktree add ../hotfix-123 main
cd ../hotfix-123

# Fix bug
git commit -m "fix: critical production bug"

# Push and deploy
git push origin main

# Return to feature work
cd ../original-project
# Continue feature work, no interruption
```

### 3. Recover from Bad Rebase

```bash
# Interactive rebase went wrong
git rebase -i main~10
# Made mistakes, now history is messy

# Reflog to rescue
git reflog
# Find the state before rebase
# abc1234 HEAD@{5}: commit: Working state before rebase

git reset --hard HEAD@{5}

# Or use reflog to find specific commits
git reflog | grep "commit"

# Recreate branch from lost state
git checkout -b saved-work abc1234
```

### 4. Bisect to Find Regression

```bash
# Bug discovered in production
git checkout main

# Start bisect
git bisect start
git bisect bad HEAD  # Current version has bug
git bisect good v1.0.0  # Known good version

# Git checks out middle commit
# Test the application
npm test
# Bug exists
git bisect bad

# Git checks out another commit
# Test
npm test
# No bug
git bisect good

# Repeat until found
# abc1234 is the first bad commit
git show abc1234  # See what changed

git bisect reset
```

### 5. Commit Message Cleanup in Pull Request

```bash
# Feature branch has many WIP commits
git log --oneline
# wip1, fix typo, wip2, more work, fix bug, wip3

# Use interactive rebase to clean up
git rebase -i main

# Mark commits:
# pick abc1234 Initial feature implementation
# fixup def5678 Fix typo
# fixup ghi9012 More work
# squash jkl2345 Fix bug
# squash mno6789 Final touches

# Result: One clean, comprehensive commit
```

---

## Common Scenarios

### Scenario 1: Clean Up Messy History

```bash
# Feature branch has 20 messy commits
git checkout feature-branch

# Interactive rebase to squash and reorder
git rebase -i main

# Use fixup liberally for minor corrections
# Squash related changes together
# Reword for clarity

# Force push (carefully!)
git push --force-with-lease origin feature-branch
```

### Scenario 2: Work on Multiple Features Simultaneously

```bash
# Create worktrees for each feature
git worktree add ../feature-a feature/a
git worktree add ../feature-b feature/b
git worktree add ../hotfix-c main

# Work on all three simultaneously
# No context switching, no stash needed

# After completion:
git checkout main
git merge feature/a
git merge feature/b
git merge hotfix/c

# Clean up worktrees
git worktree remove ../feature-a
git worktree remove ../feature-b
git worktree remove ../hotfix-c
```

### Scenario 3: Recover Accidentally Deleted Branch

```bash
# Oops, deleted wrong branch
git branch -D important-feature

# Find it in reflog
git reflog | grep important-feature

# abc1234 HEAD@{10}: checkout: moving from main to important-feature

# Recreate branch
git checkout -b important-feature abc1234

# Verify it's correct
git log
```

### Scenario 4: Merge Specific Commits from PR

```bash
# Large PR with 50 commits, only want 3 specific ones
git log feature-branch --oneline

# Cherry-pick specific commits
git checkout main
git cherry-pick abc123 def456 ghi789

# Or cherry-pick range
git cherry-pick main~10..main
```

### Scenario 5: Undo Commit After Push

```bash
# Pushed commit with mistake
git push origin main
# Oops, left debug code in

# Create revert commit (safe)
git revert HEAD
git push origin main

# Or force revert (dangerous, use with caution)
git reset --hard HEAD~1
git push --force-with-lease origin main
```
