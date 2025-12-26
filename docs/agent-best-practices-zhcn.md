# Subagent 编写最佳实践

本文档提供编写高质量 Subagent 的指导原则和最佳实践。

## Frontmatter 要求

### name（子代理名称）

- **格式**: 只能使用小写字母和连字符
- **唯一性**: 必须是唯一的标识符
- **示例**:
  - ✅ `code-reviewer`
  - ✅ `test-runner`
  - ✅ `java-backend-engineer`
  - ❌ `Code Reviewer`（包含空格和大写字母）
  - ❌ `代码审查器`（使用中文字符）

### description（描述）

- **格式**: 自然语言描述子代理的用途
- **要求**: 描述**何时应该调用**此子代理
- **关键**: 必须具体且明确，帮助 Claude 识别何时使用
- **示例**:

**❌ 太模糊**:
```yaml
description: 代码审查助手
```

**✅ 具体明确**:
```yaml
description: 专家级代码审查专家。主动审查代码质量、安全性和可维护性。在编写或修改代码后立即使用。
```

### tools（工具列表）

- **格式**: 逗号分隔的工具名称列表
- **可选**: 如果省略，子代理继承主线程的所有工具
- **何时指定**: 需要限制子代理的工具访问权限时
- **示例**:

```yaml
# 只读工具
tools: Read, Grep, Glob

# 完整工具访问
tools: Read, Edit, Write, Bash, Grep, Glob

# 省略 = 继承所有工具（包括 MCP 工具）
```

### model（模型）

- **格式**: 模型别名或 `'inherit'`
- **可选值**:
  - `sonnet` - 平衡性能和成本（推荐）
  - `opus` - 最强推理能力
  - `haiku` - 最快响应速度
  - `'inherit'` - 使用主对话的相同模型
- **省略**: 使用配置的默认子代理模型（通常是 `sonnet`）
- **示例**:

```yaml
# 使用指定模型
model: sonnet

# 与主对话保持一致
model: inherit

# 省略 - 使用默认模型
```

### permissionMode（权限模式）

- **格式**: 权限模式名称
- **可选值**:
  - `default` - 遵循标准权限模型（默认）
  - `acceptEdits` - 自动接受文件编辑
  - `bypassPermissions` - 绕过权限请求
  - `plan` - 计划模式（非执行）
  - `ignore` - 忽略权限
- **示例**:

```yaml
# 标准权限模式
permissionMode: default

# 用于只读操作
permissionMode: bypassPermissions

# 计划模式
permissionMode: plan
```

### skills（技能列表）

- **格式**: 逗号分隔的技能名称列表（必须使用英文名称）
- **用途**: 子代理启动时自动加载的技能
- **示例**:

```yaml
# 加载特定技能
skills: git-guru, testing

# 省略 - 不自动加载任何技能
```

## 描述编写技巧

### 1. 明确触发条件

描述中应该包含明确的触发词和使用场景：

**好的描述示例**:
```yaml
description: |
  调试专家，用于处理错误、测试失败和异常行为。
  在遇到任何问题时主动使用。
```

### 2. 使用动作导向的语言

描述应该说明子代理的**主动性**：

**❌ 被动**:
```yaml
description: 可以帮助运行测试
```

**✅ 主动**:
```yaml
description: 测试运行专家。看到代码更改后主动运行相应的测试。如果测试失败，分析失败并修复。
```

### 3. 包含具体场景

明确列出子代理适用的具体场景：

```yaml
description: |
  Git 提交消息生成器。
  用于编写提交信息、审查暂存的更改、格式化提交历史。
  当用户提到：commit、提交、git diff、暂存区时使用。
```

## 内容组织

### 推荐结构

```markdown
---
name: your-agent
description: 子代理描述
tools: ...
model: ...
---

# 子代理名称

[系统提示 - 可以是多段落]

## 你的角色
[角色描述]

## 核心原则
[原则列表]

## 技术栈
[技术专长]

## 工作流程
[步骤说明]

## 最佳实践
[应该做和不应该做的事]

## 错误处理
[错误处理方法]

## 质量检查清单
[检查项]

## 备注
[重要注意事项]
```

### 编写原则

1. **保持专注**: 一个子代理应该专注于一件事
2. **具体明确**: 提供具体的指令和示例
3. **主动性**: 明确说明何时主动执行任务
4. **约束清晰**: 说明子代理应该遵循的约束

## 子代理类型

### 1. 只读子代理

用于代码探索和分析，不修改文件：

```yaml
---
name: code-analyzer
description: 代码分析专家，用于理解代码结构和模式。只读模式，不修改文件。
tools: Read, Grep, Glob, Bash  # 不包含 Edit, Write
permissionMode: bypassPermissions
model: haiku  # 使用快速模型
---

You are a code analysis expert. When invoked:
1. Use Grep to search for patterns
2. Use Read to examine files
3. Use Bash for read-only commands (ls, git log, git diff)

Focus on understanding code structure and finding patterns.
```

### 2. 主动执行子代理

用于自动执行特定任务：

```yaml
---
name: test-runner
description: 测试运行专家。看到代码更改后主动运行测试并修复失败。
tools: Read, Edit, Write, Bash
model: inherit
---

You are a test automation expert.

When invoked:
1. Run git diff to see recent changes
2. Identify affected tests
3. Run tests immediately
4. If tests fail, analyze and fix them

## When Claude uses you
- Proactively after code changes
- When user mentions tests or testing
- When test failures are detected
```

### 3. 专家审查子代理

用于代码审查和质量检查：

```yaml
---
name: code-reviewer
description: 专家级代码审查专家。主动审查代码质量、安全性和可维护性。编写或修改代码后立即使用。
tools: Read, Grep, Glob, Bash
permissionMode: default
---

You are a senior code reviewer ensuring high standards.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

## Review checklist
- Code is clear and readable
- Functions and variables are well-named
- No duplicated code
- Proper error handling
- No exposed secrets or API keys
- Input validation implemented
- Good test coverage
- Performance considerations addressed

## Provide feedback organized by priority
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider improving)

Include specific examples of how to fix issues.
```

## 模型选择指南

### Sonnet（推荐默认）
- **适用场景**: 大多数任务
- **优势**: 平衡性能和成本
- **推荐用于**:
  - 代码生成和修改
  - 复杂推理任务
  - 多步骤工作流

### Opus
- **适用场景**: 需要最强推理能力
- **优势**: 最强的分析和推理能力
- **推荐用于**:
  - 极其复杂的架构设计
  - 需要深度分析的任务
  - 关键决策

### Haiku
- **适用场景**: 需要快速响应
- **优势** 最低延迟和成本
- **推荐用于**:
  - 只读代码探索
  - 简单的搜索任务
  - 快速查找操作

### Inherit
- **适用场景**: 需要与主对话保持一致
- **优势**: 一致性
- **推荐用于**:
  - 需要与主对话相同模型
  - 连贯的多步骤任务

## 工具权限配置

### 只读工具
```yaml
tools: Read, Grep, Glob, Bash  # Bash 用于只读命令
```

**适用场景**:
- 代码分析
- 文档生成
- 架构审查

### 完整工具
```yaml
tools: Read, Edit, Write, Bash, Grep, Glob
```

**适用场景**:
- 功能开发
- Bug 修复
- 重构任务

### 继承所有工具
```yaml
# 省略 tools 字段
```

**适用场景**:
- 需要访问 MCP 工具
- 不确定需要哪些工具
- 通用型子代理

## 文件位置

### 项目子代理
- **位置**: `.claude/agents/`
- **范围**: 仅在当前项目可用
- **优先级**: 最高（覆盖用户级子代理）
- **版本控制**: 应该提交到 git

```bash
# 创建项目子代理
mkdir -p .claude/agents
echo '---
name: my-agent
description: My project-specific agent
---
' > .claude/agents/my-agent.md
```

### 用户子代理
- **位置**: `~/.claude/agents/`
- **范围**: 所有项目可用
- **优先级**: 较低（被项目级覆盖）
- **版本控制**: 不提交

```bash
# 创建用户子代理
mkdir -p ~/.claude/agents
echo '---
name: my-personal-agent
description: My personal agent
---
' > ~/.claude/agents/my-personal-agent.md
```

## 测试和调试

### 测试 Checklist

- [ ] description 具体且明确（包含触发场景）
- [ ] name 符合命名规范（小写、连字符）
- [ ] YAML frontmatter 语法正确
- [ ] 文件路径正确
- [ ] 包含具体的指令和示例

### 调试技巧

如果 Claude 没有使用你的子代理：

1. **检查 description 是否具体**
   - 是否包含明确的触发词？
   - 是否说明何时主动使用？
   - 是否描述了具体场景？

2. **验证 YAML 语法**
   ```bash
   cat .claude/agents/your-agent.md | head -n 10
   ```
   - 确保有开头和结尾的 `---`
   - 不要使用 Tab，使用空格缩进
   - 特殊字符需要加引号

3. **查看可用子代理**
   ```bash
   # 列出所有子代理
   ls ~/.claude/agents/
   ls .claude/agents/

   # 查看特定子代理
   cat .claude/agents/your-agent.md
   ```

## 示例对比

### 简单子代理

**提交消息助手**:

```yaml
---
name: git-commit-helper
description: 从 git diff 生成清晰的提交消息。编写提交消息或审查暂存的更改时使用。
tools: Bash
model: inherit
---

You are a Git commit message expert.

When invoked:
1. Run git diff to see changes
2. Generate a clear commit message with:
   - Summary under 50 characters
   - Detailed description
   - Affected components

Best practices:
- Use present tense
- Explain what and why, not how
```

### 复杂子代理

**Java 后端工程师**:

```yaml
---
name: java-backend-engineer
description: 专业 Java 后端工程师，使用 Spring Boot、MyBatis 和 Clean Architecture。主动用于构建 Java 应用、实现 RESTful API、编写企业级代码。
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
skills: enterprise-java, testing
---

You are an expert Java backend engineer with 10+ years of experience building enterprise applications.

## Your expertise
- Spring Boot 3.x, Spring MVC, Spring Security
- MyBatis for database operations
- Clean Architecture patterns
- RESTful API design
- Testing with JUnit 5, Mockito

## When invoked
- Building new Java applications
- Implementing RESTful APIs
- Working with Spring Boot
- Writing enterprise-grade code
- Applying Clean Architecture

## Work process
1. Understand requirements
2. Design architecture following Clean Architecture
3. Implement features
4. Write tests
5. Document changes

## Principles
- Follow Clean Architecture principles
- Write testable code
- Use dependency injection
- Implement proper error handling
- Follow Spring best practices

## Quality checklist
Before completing tasks, ensure:
- [ ] Code follows Clean Architecture
- [ ] Tests are written (JUnit + Mockito)
- [ ] Error handling is implemented
- [ ] Code is properly documented
- [ ] Spring best practices are followed
```

## 常见错误

### 错误 1: 描述太模糊

**问题**:
```yaml
description: 帮助编写 Java 代码
```

**修复**:
```yaml
description: |
  专业 Java 后端工程师，使用 Spring Boot、MyBatis 和 Clean Architecture。
  主动用于构建 Java 应用、实现 RESTful API、编写企业级代码。
```

### 错误 2: name 格式错误

**问题**:
```yaml
name: Java Backend Engineer  # ❌ 包含空格和大写字母
```

**修复**:
```yaml
name: java-backend-engineer  # ✅ 只使用小写字母和连字符
```

### 错误 3: skills 使用中文名称

**问题**:
```yaml
skills: git-guru, 测试技能  # ❌ 包含中文
```

**修复**:
```yaml
skills: git-guru, testing  # ✅ 使用英文名称
```

### 错误 4: 缺少主动性

**问题**:
```yaml
description: 可以帮助运行测试
```

**修复**:
```yaml
description: 测试运行专家。看到代码更改后主动运行测试并修复失败。
```

## 最佳实践总结

1. **专注单一职责**: 一个子代理专注于一件事
2. **明确的描述**: 清楚说明何时主动使用
3. **合理的工具配置**: 只授予必要的工具
4. **选择合适的模型**: 根据任务复杂度选择
5. **详细系统提示**: 提供具体的指令和约束
6. **版本控制**: 将项目子代理提交到 git
7. **测试验证**: 创建后测试子代理是否按预期工作

## 参考资源

- [Claude Code Subagents 官方文档](https://code.claude.com/docs/en/sub-agents)
- [MindForge Agent 集合](https://github.com/ProjAnvil/MindForge)

---

**版本**: 1.0.0
**最后更新**: 2025-12
**维护者**: MindForge Team
