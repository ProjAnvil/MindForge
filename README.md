# MindForge - AI Toolkit for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文文档](docs/README-zhcn.md) | English

MindForge is a comprehensive toolkit for managing MCP (Model Context Protocol) services, AI Agents, and Skills, designed to supercharge your Claude Code development experience.

## ✨ Features

- **Multi-language Support**: Choose between English or Chinese versions of agents and skills
- **Rich Agent Collection**: Specialized agents for Java, Python, Go, Frontend, and System Architecture
- **Reusable Skills**: Domain-specific skills that can be composed and shared across agents
- **MCP Services**: Extensible collection of Model Context Protocol services
- **Easy Setup**: One-command installation script for Claude Code integration
- **Flexible Tech Stack**: Each component can use its own preferred technology stack

## 🚀 Quick Start with Claude Code

MindForge integrates seamlessly with Claude Code. Run the setup script to automatically configure all agents and skills:

```bash
# Use default language (English)
./setup-claude.sh

# Use Chinese
./setup-claude.sh --lang=zh-cn

# Use English (explicit)
./setup-claude.sh --lang=en
```

This creates symbolic links to your `~/.claude/` directory, allowing Claude Code to automatically load all agents and skills.

### 🌍 Supported Languages

- **en** - English
- **zh-cn** - Simplified Chinese

## 🤖 Available Agents

- **@java-unit-test** - Professional Java unit test generator (JUnit, Mockito, AssertJ)
- **@python-test-engineer** - Professional Python testing engineer (pytest, unittest, pytest-asyncio)
- **@system-architect** - System architecture design expert (patterns, tech selection, ADR docs)
- **@golang-backend-engineer** - Go backend development expert (Fiber, Cobra, GORM, Clean Architecture)
- **@frontend-engineer** - Frontend development expert (Svelte, SvelteKit, shadcn-svelte, Bun)

## 🎯 Available Skills

- **testing** - General testing skills (unit, integration, TDD/BDD)
- **enterprise-java** - Enterprise Java development (Spring Boot, microservices)
- **go-development** - Go development (Fiber, Cobra, GORM)
- **python-development** - Python development (FastAPI, Django, Flask, asyncio)
- **javascript-typescript** - JavaScript/TypeScript development (Node.js, Express, React)
- **system-architecture** - System architecture design
- **api-design** - API design (REST, GraphQL, gRPC)
- **database-design** - Database design and optimization
- **tech-documentation** - Technical documentation writing
- **frontend-development** - Frontend development (Svelte, SvelteKit, shadcn-svelte, Tailwind CSS)

## 📁 Project Structure

```
mindforge/
├── agents/              # Claude Code format Agents (multi-language)
│   ├── en/             # English versions
│   │   ├── java-unit-test.md
│   │   ├── python-test-engineer.md
│   │   ├── system-architect.md
│   │   ├── golang-backend-engineer.md
│   │   └── frontend-engineer.md
│   └── zh-cn/          # Chinese versions
│       ├── java-unit-test.md
│       ├── python-test-engineer.md
│       ├── system-architect.md
│       ├── golang-backend-engineer.md
│       └── frontend-engineer.md
├── skills/              # Claude Code format Skills (multi-language)
│   ├── en/             # English versions
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
│   └── zh-cn/          # Chinese versions
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
├── mcp/                 # MCP services collection
│   ├── _template/
│   └── mcp-*/
├── setup-claude.sh      # Claude Code setup script (supports --lang parameter)
└── docs/               # Documentation
    └── README-zhcn.md  # Chinese README
```

## 🛠️ Usage

### List Resources

```bash
# List all MCP services
make list-mcp

# List all Agents
make list-agents

# List all Skills
make list-skills
```

### Create Resources

```bash
# Create a new MCP service
make init-mcp SERVICE=mcp-foo

# Create a new Agent
make init-agent AGENT=my-agent

# Create a new Skill
make init-skill SKILL=my-skill
```

### Add Skills to Agents

```bash
# Add a skill to an agent
make add-skill AGENT=my-agent SKILL=my-skill
```

### Build and Test

```bash
# Build a single MCP service
make build SERVICE=mcp-foo

# Build a single Agent
make build AGENT=my-agent

# Build a single Skill
make build SKILL=my-skill

# Build all resources
make build-all

# Test all resources
make test-all

# Clean all resources
make clean-all
```

## 📋 Resource Conventions

Each MCP service, Agent, or Skill should provide its own `Makefile` with at least the following targets:

- `build` - Build the resource
- `test` - Test the resource
- `clean` - Clean build artifacts

Optional targets:

- `fmt` - Format code
- `lint` - Lint code

Each resource can use its own technology stack (Go/Node/Python/Rust/etc.)

## 🧰 Tech Stack

- **MCP Services**: Any language and framework that supports the MCP protocol
- **Agents**: AI agents for executing specific tasks
- **Skills**: Reusable capability modules that can be referenced by agents

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for [Claude Code](https://www.anthropic.com/claude/code)
- Supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

## 📞 Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/mindforge/issues) on GitHub.

---

Made with ❤️ by the MindForge community
