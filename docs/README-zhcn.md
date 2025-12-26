# MindForge - AI Toolkit for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](../README.md) | 中文文档

MindForge 是一个综合性的工具集，用于管理 MCP（模型上下文协议）服务、AI Agents 和 Skills，旨在为你的 Claude Code 开发体验增添动力。

## ✨ 功能特性

- **多语言支持**：可选择英文或中文版本的 agents 和 skills
- **丰富的 Agent 集合**：针对 Java、Python、Go、前端和系统架构的专业 agents
- **可复用的 Skills**：可组合和跨 agents 共享的领域专属技能
- **MCP 服务**：可扩展的模型上下文协议服务集合
- **简易设置**：一键安装脚本实现 Claude Code 集成
- **灵活的技术栈**：每个组件都可以使用自己偏好的技术栈

## 🚀 快速开始使用 Claude Code

MindForge 与 Claude Code 无缝集成。运行设置脚本自动配置所有 agents 和 skills：

```bash
# 使用默认语言（英文）
./setup-claude.sh

# 使用中文
./setup-claude.sh --lang=zh-cn

# 使用英文（显式指定）
./setup-claude.sh --lang=en
```

这将创建符号链接到 `~/.claude/` 目录，使 Claude Code 自动加载所有 agents 和 skills。

### 🎛️ 用户级别配置

为了在所有项目中获得个性化的行为，你可以配置用户级别指令：

```bash
# 复制用户级别指令到 Claude 目录
cp user_claude_md/en/CLAUDE.md ~/.claude/CLAUDE.md    # 英文
cp user_claude_md/zh-cn/CLAUDE.md ~/.claude/CLAUDE.md  # 中文
```

**用户级别配置提供：**
- **全局原则**：应用于所有对话的默认行为
- **语言偏好**：设置你偏好的响应语言（中文或英文）
- **搜索优先**：处理不确定问题时的指导
- **安全规则**：破坏性操作的确认要求
- **内置能力优先**：关于何时使用 agents/skills 与外部工具的指导

**注意：** 用户级别配置是可选的。如果未配置，Claude Code 将使用其默认行为。

### 🌍 支持的语言

- **en** - English（英文）
- **zh-cn** - 简体中文

## 🤖 可用的 Agents

- **@java-backend-engineer** - 专业 Java 后端工程师（Spring Boot, MyBatis, Clean Architecture）
- **@java-unit-test** - 专业的 Java 单元测试生成器（JUnit, Mockito, AssertJ）
- **@python-test-engineer** - 专业的 Python 测试工程师（pytest, unittest, pytest-asyncio）
- **@system-architect** - 系统架构设计专家（架构模式、技术选型、ADR 文档）
- **@golang-backend-engineer** - Go 后端开发专家（Fiber, Cobra, GORM, Clean Architecture）
- **@frontend-engineer** - 前端开发专家（Svelte, SvelteKit, shadcn-svelte, Bun）

## 🎯 可用的 Skills

- **testing** - 通用测试技能（单元、集成、TDD/BDD）
- **enterprise-java** - 企业级 Java 开发（Spring Boot, 微服务）
- **go-development** - Go 开发（Fiber, Cobra, GORM）
- **python-development** - Python 开发（FastAPI, Django, Flask, asyncio）
- **javascript-typescript** - JavaScript/TypeScript 开发（Node.js, Express, React）
- **system-architecture** - 系统架构设计
- **api-design** - API 设计（REST, GraphQL, gRPC）
- **database-design** - 数据库设计与优化
- **tech-documentation** - 技术文档编写
- **frontend-development** - 前端开发（Svelte, SvelteKit, shadcn-svelte, Tailwind CSS）
- **git-guru** - 高级 Git 操作和版本控制精通

## 📁 项目结构

```
mindforge/
├── agents/              # Claude Code 格式的 Agents（多语言支持）
│   ├── en/             # 英文版本
│   │   ├── java-backend-engineer.md
│   │   ├── java-unit-test.md
│   │   ├── python-test-engineer.md
│   │   ├── system-architect.md
│   │   ├── golang-backend-engineer.md
│   │   └── frontend-engineer.md
│   └── zh-cn/          # 中文版本
│       ├── java-backend-engineer.md
│       ├── java-unit-test.md
│       ├── python-test-engineer.md
│       ├── system-architect.md
│       ├── golang-backend-engineer.md
│       └── frontend-engineer.md
├── skills/              # Claude Code 格式的 Skills（多语言支持）
│   ├── en/             # 英文版本
│   │   ├── testing/SKILL.md
│   │   ├── enterprise-java/SKILL.md
│   │   ├── go-development/SKILL.md
│   │   ├── python-development/SKILL.md
│   │   ├── javascript-typescript/SKILL.md
│   │   ├── system-architecture/SKILL.md
│   │   ├── api-design/SKILL.md
│   │   ├── database-design/SKILL.md
│   │   ├── tech-documentation/SKILL.md
│   │   ├── frontend-development/SKILL.md
│   │   └── git-guru/SKILL.md
│   └── zh-cn/          # 中文版本
│       ├── testing/SKILL.md
│       ├── enterprise-java/SKILL.md
│       ├── go-development/SKILL.md
│       ├── python-development/SKILL.md
│       ├── javascript-typescript/SKILL.md
│       ├── system-architecture/SKILL.md
│       ├── api-design/SKILL.md
│       ├── database-design/SKILL.md
│       ├── tech-documentation/SKILL.md
│       ├── frontend-development/SKILL.md
│       └── git-guru/SKILL.md
├── user_claude_md/      # 用户级别 Claude 指令（多语言支持）
│   ├── en/
│   │   └── CLAUDE.md   # 英文用户级别指令
│   └── zh-cn/
│       └── CLAUDE.md   # 中文用户级别指令
├── templates/           # 创建新资源的模板
│   ├── agent-template-en.md      # 英文 agent 模板
│   ├── agent-template-zhcn.md    # 中文 agent 模板
│   ├── skill-template-en.md      # 英文 skill 模板
│   └── skill-template-zhcn.md    # 中文 skill 模板
├── mcp/                 # MCP 服务集合
│   ├── _template/
│   └── mcp-*/
├── docs/                # 文档
│   ├── README-zhcn.md   # 中文 README
│   └── agents-detail/   # 详细 agent 文档
│       ├── en/          # 英文详细指南
│       │   ├── java-backend-engineer/README.md
│       │   ├── java-unit-test/README.md
│       │   ├── python-test-engineer/README.md
│       │   ├── system-architect/README.md
│       │   ├── golang-backend-engineer/README.md
│       │   └── frontend-engineer/README.md
│       └── zh-cn/       # 中文详细指南
│           ├── java-backend-engineer/README.md
│           ├── java-unit-test/README.md
│           ├── python-test-engineer/README.md
│           ├── system-architect/README.md
│           ├── golang-backend-engineer/README.md
│           └── frontend-engineer/README.md
├── Makefile             # 构建和资源管理
└── setup-claude.sh      # Claude Code 设置脚本（支持 --lang 参数）
```

## 🛠️ 使用方法

### 快速开始

```bash
# 显示所有可用命令
make help
```

### 列出资源

```bash
# 列出所有 MCP 服务
make list-mcp

# 列出所有 Agents（显示英文和中文）
make list-agents

# 列出所有 Skills（显示英文和中文）
make list-skills
```

### 从模板创建资源

MindForge 提供即用型模板来创建新的 agents 和 skills。模板支持中英文两种语言。

#### 创建新的 Agent

```bash
# 创建英文 agent（默认）
make init-agent AGENT=my-agent

# 创建中文 agent
make init-agent AGENT=my-agent LANG=zh-cn

# 创建英文 agent（显式指定）
make init-agent AGENT=my-agent LANG=en
```

**你将得到:**
- 包含完整 frontmatter 的 agent 文件（name, description, tools, model, skills）
- 结构化的章节：角色定义、核心原则、最佳实践
- 代码模板和质量检查清单
- 可根据具体用途自定义

**创建后的步骤:**
1. 编辑 `agents/{lang}/{agent-name}.md` 自定义 agent
2. 更新名称、描述和系统提示
3. 在 frontmatter 中指定要使用的工具和技能
4. 运行 `./setup-claude.sh --lang={lang}` 激活

#### 创建新的 Skill

```bash
# 创建英文 skill（默认）
make init-skill SKILL=my-skill

# 创建中文 skill
make init-skill SKILL=my-skill LANG=zh-cn

# 创建英文 skill（显式指定）
make init-skill SKILL=my-skill LANG=en
```

**你将得到:**
- 包含完整 frontmatter 的 skill 文件（name, description, allowed-tools）
- 结构化的章节：专业知识、原则、最佳实践
- 代码模式、模板和故障排查指南
- 质量检查清单和决策框架
- 可跨多个 agents 使用

**创建后的步骤:**
1. 编辑 `skills/{lang}/{skill-name}/SKILL.md` 定义能力
2. 添加领域专属知识和最佳实践
3. 包含代码模板和常见模式
4. 运行 `./setup-claude.sh --lang={lang}` 激活

#### 创建新的 MCP 服务

```bash
# 创建新的 MCP 服务
make init-mcp SERVICE=mcp-foo
```

**创建后的步骤:**
1. 进入 `mcp/mcp-foo/` 目录
2. 实现你的 MCP 服务
3. 添加包含 `build`、`test` 和 `clean` 目标的 Makefile

### 管理 Agent 中的 Skills

```bash
# 为英文 agent 添加 skill
make add-skill AGENT=my-agent SKILL=testing

# 为中文 agent 添加 skill
make add-skill AGENT=my-agent SKILL=testing LANG=zh-cn
```

这会自动更新 agent 的 frontmatter 以包含指定的 skill。

### 构建和测试

```bash
# 构建单个 MCP 服务
make build SERVICE=mcp-foo

# 构建所有 MCP 服务
make build-all

# 测试所有 MCP 服务
make test-all

# 清理所有 MCP 服务构建产物
make clean-all
```

**注意:** Agents 和 skills 是 markdown 文件，无需构建。

## 📋 资源约定

每个 MCP 服务、Agent 或 Skill 都应该提供自己的 `Makefile`，至少包含以下目标：

- `build` - 构建资源
- `test` - 测试资源
- `clean` - 清理构建产物

可选目标：

- `fmt` - 格式化代码
- `lint` - 代码检查

每个资源可以使用自己的技术栈（Go/Node/Python/Rust/etc.）

## 🧰 技术栈

- **MCP 服务**：可以使用任何支持 MCP 协议的语言和框架
- **Agents**：AI 代理，用于执行特定任务
- **Skills**：可复用的能力模块，可以被 Agent 引用

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 本仓库
2. 创建你的特性分支（`git checkout -b feature/amazing-feature`）
3. 提交你的更改（`git commit -m 'Add some amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 创建一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件。

## 🙏 致谢

- 为 [Claude Code](https://www.anthropic.com/claude/code) 构建
- 支持 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

## 📞 支持

如果你遇到任何问题或有疑问，请在 GitHub 上[提交 issue](https://github.com/yourusername/mindforge/issues)。

---

由 MindForge 社区用 ❤️ 制作