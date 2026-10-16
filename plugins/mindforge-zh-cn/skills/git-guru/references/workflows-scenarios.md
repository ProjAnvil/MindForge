## 高级工作流

### 1. 清晰的功能分支工作流
```bash
# 从 main 创建功能分支
git checkout main
git pull
git checkout -b feature/new-auth

# 进行多次提交
git commit -m "feat: 添加登录表单"
git commit -m "fix: 按钮对齐"
git commit -m "feat: 实现 OAuth"
git commit -m "docs: 更新 README"

# 合并前，使用交互式变基清理
git rebase -i main

# 合并 fixup，按逻辑重新排序，reword 以增加清晰度

# 仅使用快进合并
git checkout main
git merge --ff-only feature/new-auth

# 删除功能分支
git branch -d feature/new-auth
```

### 2. 使用 Worktree 进行紧急修复
```bash
# 在功能分支上工作
git status
# 在 feature/auth 上，未提交的更改

# 出现紧急 bug - 不想 stash 或 commit

# 为 hotfix 创建工作树
git worktree add ../hotfix-123 main
cd ../hotfix-123

# 修复 bug
git commit -m "fix: 严重的生产 bug"

# 推送并部署
git push origin main

# 返回功能工作
cd ../original-project
# 继续功能开发，无中断
```

### 3. 从错误的 Rebase 中恢复
```bash
# 交互式 rebase 出错了
git rebase -i main~10
# 犯了错误，现在历史很混乱

# Reflog 救援
git reflog
# 找到 rebase 之前的状态
# abc1234 HEAD@{5}: commit: rebase 之前的工作状态

git reset --hard HEAD@{5}

# 或使用 reflog 查找特定提交
git reflog | grep "commit"

# 从丢失的状态重建分支
git checkout -b saved-work abc1234
```

### 4. 使用 Bisect 查找回归
```bash
# 在生产中发现 bug
git checkout main

# 开始 bisect
git bisect start
git bisect bad HEAD  # 当前版本有 bug
git bisect good v1.0.0  # 已知的好版本

# Git 检出中间提交
# 测试应用程序
npm test
# bug 存在
git bisect bad

# Git 检出另一个提交
# 测试
npm test
# 没有 bug
git bisect good

# 重复直到找到
# abc1234 是第一个 bad 提交
git show abc1234  # 查看改变了什么

git bisect reset
```

### 5. 在拉取请求中清理提交信息
```bash
# 功能分支有 20 个混乱的提交
git log --oneline
# wip1, 修复拼写错误, wip2, 更多工作, 修复 bug, wip3

# 使用交互式 rebase 清理
git rebase -i main

# 标记提交：
# pick abc1234 初始功能实现
# fixup def5678 修复拼写错误
# fixup ghi9012 更多工作
# squash jkl2345 修复 bug
# squash mno6789 最后的修饰

# 结果：一个清晰、全面的提交
```

## 常见场景

### 场景 1：清理混乱的历史
```bash
# 功能分支有 20 个混乱的提交
git checkout feature-branch

# 交互式 rebase 进行 squash 和重新排序
git rebase -i main

# 大量使用 fixup 进行小修正
# 将相关更改 squash 在一起
# Reword 以增加清晰度

# 强制推送（小心！）
git push --force-with-lease origin feature-branch
```

### 场景 2：同时处理多个功能
```bash
# 为每个功能创建工作树
git worktree add ../feature-a feature/a
git worktree add ../feature-b feature/b
git worktree add ../hotfix-c main

# 同时处理所有三个
# 无需上下文切换，无需 stash

# 完成后：
git checkout main
git merge feature/a
git merge feature/b
git merge hotfix/c

# 清理工作树
git worktree remove ../feature-a
git worktree remove ../feature-b
git worktree remove ../hotfix-c
```

### 场景 3：恢复意外删除的分支
```bash
# 糟糕，删除了错误的分支
git branch -D important-feature

# 在 reflog 中查找
git reflog | grep important-feature

# abc1234 HEAD@{10}: checkout: moving from main to important-feature

# 重建分支
git checkout -b important-feature abc1234

# 验证正确
git log
```

### 场景 4：从 PR 合并特定提交
```bash
# 大型 PR 有 50 个提交，只想要其中 3 个特定提交
git log feature-branch --oneline

# 精选特定提交
git checkout main
git cherry-pick abc123 def456 ghi789

# 或精选提交范围
git cherry-pick main~10..main
```

### 场景 5：推送后撤销提交
```bash
# 推送了有错误的提交
git push origin main
# 糟糕，留下了调试代码

# 创建 revert 提交（安全）
git revert HEAD
git push origin main

# 或强制 revert（危险，谨慎使用）
git reset --hard HEAD~1
git push --force-with-lease origin main
```

## 响应模式

### 当用户需要高级 Git 帮助时

1. **理解目标**：他们想实现什么？
2. **评估安全性**：这是破坏性操作吗？警告他们。
3. **提供步骤**：清晰、有序的命令
4. **解释原因**：每一步的作用
5. **提供替代方案**：可用的更安全选项
6. **备份建议**：在风险操作前始终建议备份或创建分支

### 常见用户场景

#### 清理提交历史
```
理解：功能分支有混乱的提交
推荐：使用 fixup/squash 进行交互式 rebase
步骤：
1. 创建备份分支
2. 交互式 rebase
3. 恰当标记 fixup/squash
4. 使用 --force-with-lease 强制推送
```

#### 恢复丢失的工作
```
理解：意外删除了重要提交/分支
推荐：使用 reflog 查找和恢复
步骤：
1. 检查 reflog
2. 识别丢失的提交
3. reset 或重建分支
4. 验证恢复
```

#### 处理多个功能
```
理解：需要同时处理多个功能
推荐：Git worktree
步骤：
1. 为每个任务创建工作树
2. 独立工作
3. 完成时合并
4. 清理工作树
```

#### 查找 bug 引入
```
理解：这个 bug 何时出现？
推荐：Git bisect
步骤：
1. 标记好和坏提交
2. 让 bisect 缩小范围
3. 识别坏提交
4. 分析更改
```

## 始终遵循的最佳实践

### 安全第一
```bash
# 在破坏性操作前始终创建备份
git branch backup-before-rebase

# 使用 --force-with-lease 而不是 --force
git push --force-with-lease

# 永远不要 rebase 已发布的历史
git rebase main  # 可以
git rebase origin/main  # 如果已推送则危险
```

### 清晰的历史
```bash
# 合并前 squash 相关提交
git rebase -i main

# 编写清晰的提交信息
git commit -m "feat(auth): 添加 OAuth2 登录

实现 GitHub 和 Google 提供商的
OAuth2 身份验证流程。

Closes #123"

# 删除 WIP 提交
git commit --fixup=abc123
git rebase -i --autosquash
```

### 定期维护
```bash
# 定期垃圾回收
git gc

# 清理过时分支
git remote prune origin

# 清理工作树
git worktree prune
```

## 记住

- **Reflog 是你的安全网** - 几乎任何东西都可以恢复
- **交互式 rebase 用于清晰历史** - 但永远不要 rebase 共享分支
- **Worktree 用于并行工作** - 避免 stash 和上下文切换
- **Bisect 用于调试** - 比手动搜索快得多
- **约定式提交** - 清晰、结构化的提交信息
- **Force-with-lease** - 比 force push 更安全
- **破坏性操作前备份** - reset/rebase 前创建分支

资料来源：
- [高级 Git 教程 - 交互式 Rebase、Cherry-picking](https://www.youtube.com/watch?v=qsTthZi23VE)
- [30 个高级 Git 命令可视化](https://nagibaba.medium.com/30-advanced-git-commands-visualised-by-chargraph-beb3ab42f027)
- [Git Worktree 教程](https://www.datacamp.com/tutorial/git-worktree-tutorial)
- [Git Worktree 高级技术](https://medium.com/@sunithvs/git-worktree-advanced-git-techniques-for-10x-developer-productivity-ac3a532ede51)
- [高级 Git 命令：Reflog、Archive、Bisect](https://medium.com/@moamen.ashraf1892001/advanced-git-commands-reflog-archive-bisect-and-beyond-85549ed23115)
- [Git 高级命令教程（中文）](https://friday-go.icu/Tools/Git%25E9%25AB%2598%25E7%25BA%25A7%25E5%2591%25BD%25E4%25BB%25A4%25E6%2595%2599%25E7%25A8%258B)
- [超越基础：10 个高级 Git 命令](https://alphashaban.hashnode.dev/beyond-the-basics-10-advanced-git-commands-for-power-users)
