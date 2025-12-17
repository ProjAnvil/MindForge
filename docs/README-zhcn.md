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

### 🌍 支持的语言

- **en** - English（英文）
- **zh-cn** - 简体中文

## 🤖 可用的 Agents

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

## 📁 项目结构

```
mindforge/
├── agents/              # Claude Code 格式的 Agents（多语言支持）
│   ├── en/             # 英文版本
│   │   ├── java-unit-test.md
│   │   ├── python-test-engineer.md
│   │   ├── system-architect.md
│   │   ├── golang-backend-engineer.md
│   │   └── frontend-engineer.md
│   └── zh-cn/          # 中文版本
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
│   │   └── frontend-development/SKILL.md
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
│       └── frontend-development/SKILL.md
├── mcp/                 # MCP 服务集合
│   ├── _template/
│   └── mcp-*/
├── setup-claude.sh      # Claude Code 设置脚本（支持 --lang 参数）
└── docs/                # 文档
    └── README-zhcn.md   # 中文 README
```

## 🛠️ 使用方法

### 查看资源

```sh
# 列出所有 MCP 服务
make list-mcp

# 列出所有 Agents
make list-agents

# 列出所有 Skills
make list-skills
```

### 创建资源

```sh
# 创建新的 MCP 服务
make init-mcp SERVICE=mcp-foo

# 创建新的 Agent
make init-agent AGENT=my-agent

# 创建新的 Skill
make init-skill SKILL=my-skill
```

### 为 Agent 添加 Skill

```sh
# 将 skill 添加到 agent
make add-skill AGENT=my-agent SKILL=my-skill
```

### 构建和测试

```sh
# 构建单个 MCP 服务
make build SERVICE=mcp-foo

# 构建单个 Agent
make build AGENT=my-agent

# 构建单个 Skill
make build SKILL=my-skill

# 构建所有资源
make build-all

# 测试所有资源
make test-all

# 清理所有资源
make clean-all
```

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