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

### 🎛️ User-Level Configuration

For personalized behavior across all your projects, you can configure user-level instructions:

```bash
# Copy user-level instructions to your Claude directory
cp user_claude_md/en/CLAUDE.md ~/.claude/CLAUDE.md    # English
cp user_claude_md/zh-cn/CLAUDE.md ~/.claude/CLAUDE.md  # Chinese
```

**What user-level configuration provides:**
- **Global principles**: Default behavior applied across all conversations
- **Language preference**: Set your preferred response language (English or Chinese)
- **Search priority**: Instructions for handling uncertain questions
- **Safety rules**: Confirmation requirements for destructive operations
- **Built-in capability priority**: Guidance on when to use agents/skills vs external tools

**Note:** User-level configuration is optional. If not configured, Claude Code will use its default behavior.

### 🌍 Supported Languages

- **en** - English
- **zh-cn** - Simplified Chinese

## 🤖 Available Agents

- **@java-backend-engineer** - Professional Java backend engineer (Spring Boot, Mumble SDK, MyBatis, Clean Architecture)
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
- **git-guru** - Advanced Git operations and version control mastery

## 📁 Project Structure

```
mindforge/
├── agents/              # Claude Code format Agents (multi-language)
│   ├── en/             # English versions
│   │   ├── java-backend-engineer.md
│   │   ├── java-unit-test.md
│   │   ├── python-test-engineer.md
│   │   ├── system-architect.md
│   │   ├── golang-backend-engineer.md
│   │   └── frontend-engineer.md
│   └── zh-cn/          # Chinese versions
│       ├── java-backend-engineer.md
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
│   │   ├── frontend-development/SKILL.md
│   │   └── git-guru/SKILL.md
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
│       ├── frontend-development/SKILL.md
│       └── git-guru/SKILL.md
├── user_claude_md/      # User-level Claude instructions (multi-language)
│   ├── en/
│   │   └── CLAUDE.md   # English user-level instructions
│   └── zh-cn/
│       └── CLAUDE.md   # Chinese user-level instructions
├── templates/           # Templates for creating new resources
│   ├── agent-template-en.md      # English agent template
│   ├── agent-template-zhcn.md    # Chinese agent template
│   ├── skill-template-en.md      # English skill template
│   └── skill-template-zhcn.md    # Chinese skill template
├── mcp/                 # MCP services collection
│   ├── _template/
│   └── mcp-*/
├── docs/                # Documentation
│   ├── README-zhcn.md   # Chinese README
│   └── agents-detail/   # Detailed agent documentation
│       ├── en/          # English detailed guides
│       │   ├── java-backend-engineer/README.md
│       │   ├── java-unit-test/README.md
│       │   ├── python-test-engineer/README.md
│       │   ├── system-architect/README.md
│       │   ├── golang-backend-engineer/README.md
│       │   └── frontend-engineer/README.md
│       └── zh-cn/       # Chinese detailed guides
│           ├── java-backend-engineer/README.md
│           ├── java-unit-test/README.md
│           ├── python-test-engineer/README.md
│           ├── system-architect/README.md
│           ├── golang-backend-engineer/README.md
│           └── frontend-engineer/README.md
├── Makefile             # Build and resource management
└── setup-claude.sh      # Claude Code setup script (supports --lang parameter)
```

## 🛠️ Usage

### Quick Start

```bash
# Show all available commands
make help
```

### List Resources

```bash
# List all MCP services
make list-mcp

# List all Agents (shows both English and Chinese)
make list-agents

# List all Skills (shows both English and Chinese)
make list-skills
```

### Create Resources from Templates

MindForge provides ready-to-use templates for creating new agents and skills. Templates are available in both English and Chinese.

#### Create a New Agent

```bash
# Create an English agent (default)
make init-agent AGENT=my-agent

# Create a Chinese agent
make init-agent AGENT=my-agent LANG=zh-cn

# Create an English agent (explicit)
make init-agent AGENT=my-agent LANG=en
```

**What you get:**
- A complete agent file with frontmatter (name, description, tools, model, skills)
- Structured sections for role definition, principles, and best practices
- Code templates and quality checklists
- Ready to customize for your specific use case

**After creation:**
1. Edit `agents/{lang}/{agent-name}.md` to customize the agent
2. Update the name, description, and system prompt
3. Specify which tools and skills the agent should use
4. Run `./setup-claude.sh --lang={lang}` to activate

#### Create a New Skill

```bash
# Create an English skill (default)
make init-skill SKILL=my-skill

# Create a Chinese skill
make init-skill SKILL=my-skill LANG=zh-cn

# Create an English skill (explicit)
make init-skill SKILL=my-skill LANG=en
```

**What you get:**
- A complete skill file with frontmatter (name, description, allowed-tools)
- Structured sections for expertise, principles, and best practices
- Code patterns, templates, and troubleshooting guides
- Quality checklists and decision frameworks
- Ready to use across multiple agents

**After creation:**
1. Edit `skills/{lang}/{skill-name}/SKILL.md` to define capabilities
2. Add domain-specific knowledge and best practices
3. Include code templates and common patterns
4. Run `./setup-claude.sh --lang={lang}` to activate

#### Create a New MCP Service

```bash
# Create a new MCP service
make init-mcp SERVICE=mcp-foo
```

**After creation:**
1. Navigate to `mcp/mcp-foo/`
2. Implement your MCP service
3. Add a Makefile with `build`, `test`, and `clean` targets

### Manage Skills in Agents

```bash
# Add a skill to an agent (English)
make add-skill AGENT=my-agent SKILL=testing

# Add a skill to a Chinese agent
make add-skill AGENT=my-agent SKILL=testing LANG=zh-cn
```

This automatically updates the agent's frontmatter to include the specified skill.

### Build and Test

```bash
# Build a single MCP service
make build SERVICE=mcp-foo

# Build all MCP services
make build-all

# Test all MCP services
make test-all

# Clean all MCP service artifacts
make clean-all
```

**Note:** Agents and skills are markdown files and don't require building.

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
