# MindForge - AI Toolkit for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文文档](docs/README-zhcn.md) | English

MindForge is a comprehensive toolkit for managing MCP (Model Context Protocol) services, AI Agents, and Skills, designed to supercharge your Claude Code development experience.

## ✨ Features

- **Multi-language Support**: Choose between English or Chinese versions of agents and skills
- **Rich Agent Collection**: Specialized agents for Java, Python, Go, Frontend, and System Architecture
- **Reusable Skills**: Domain-specific skills that can be composed and shared across agents
- **MCP Services**: Extensible collection of Model Context Protocol services
- **Multi-harness Support**: Claude Code, zcode, and Codex (OpenAI) install the same hooks, dictionary, and rules from one repository
- **zh-guard Translationese Defense**: Controlled-writing rules injected every turn, plus exit checks, a file-write guard, sentence patterns, and an LLM judge that catch stiff machine translation in model output
- **Three-tier Dictionary**: Bundled → user-level (`~/.claude/MindForge/`) → project-level (`mindforge.zh-dict.tsv` in the repo, team-shared)
- **MindForge CLI**: One Go binary (installer / `init dict` / `doctor`) with the whole hook payload embedded
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

**Note:** User-level configuration is optional. If not configured, Claude Code will use its default behavior. Writing-style rules (controlled writing, ASD-STE100) are **not** in this file — the style-rules hook injects them, so keeping them out avoids sending the same rules twice. To use them without the hook, merge `hooks/style-rules-en.md` into the copied file.

### 🌍 Supported Languages

- **en** - English
- **zh-cn** - Simplified Chinese

### 🧩 Install as a Plugin (Claude Code, zcode & Codex)

Agents, skills, and the controlled-writing style rules hook are all distributed as plugins. Claude Code, zcode, and Codex read the same marketplace manifest (`.claude-plugin/marketplace.json`), so one repository serves all harnesses:

```bash
# Claude Code (inside a session)
/plugin marketplace add ProjAnvil/MindForge

# Agents + skills bundles (pick your language)
/plugin install mindforge-en@mindforge             # 9 agents + 19 skills (English)
/plugin install mindforge-zh-cn@mindforge          # 9 agents + 19 skills (Chinese)

# Controlled-writing style rules hook
/plugin install style-rules@mindforge              # English rules (default)
/plugin install style-rules-zh-cn@mindforge        # Chinese + English rules + translationese guard (zh-guard)

# Codex (from your shell)
codex plugin marketplace add ProjAnvil/MindForge
codex plugin add mindforge-zh-cn@mindforge
codex plugin add style-rules-zh-cn@mindforge
```

zcode reads the same marketplace manifest: add `https://github.com/ProjAnvil/MindForge.git` as a plugin marketplace in your zcode client, then install `mindforge-zh-cn@mindforge` and `style-rules-zh-cn@mindforge`. The plugin ships a zcode-specific manifest (`.zcode-plugin/plugin.json`) so no unsupported hook registrations are ever loaded there.

Notes:

- `style-rules-zh-cn` bundles the zh-guard translationese defense (see the next section). On install the dictionary migrates to `~/.claude/MindForge/terminology.tsv` (never overwritten; legacy `~/.claude/zh-guard/` installs are migrated automatically); user entries win and plugin updates still deliver new entries.
- Plugin agents and skills are namespaced, e.g. `/mindforge-en:git-guru` and `mindforge-en:code-reviewer`, so they never conflict with personal or project ones.
- Plugin hooks use `${CLAUDE_PLUGIN_ROOT}` (Claude Code) with a `${PLUGIN_ROOT}` fallback, so no symlinks or `settings.json` merging are required.
- Restart the harness after installing.
- If you modify `hooks/`, `agents/`, or `skills/`, run `make sync-plugins` to refresh the plugin bundles (the `style-rules-zh-cn` plugin lives in `hooks/` and needs no sync).

### 🧠 zh-guard: Translationese Defense

Chinese technical writing by LLMs is full of stiff, literal translations — 病灶实验 for ablation study, 槽键 for slot key, 值得注意的是 template phrases. zh-guard pushes back at five layers, all fail-open (any error lets the text through, never blocking your session):

| Layer | Hook event | What it does |
|---|---|---|
| L1 inject | UserPromptSubmit | Injects controlled-writing rules and a 直译词→expected-writing list every turn |
| L2 exit | Stop / SubagentStop | Scans `last_assistant_message`; on a hit forces a natural-Chinese rewrite |
| File-write guard | PreToolUse (Write\|Edit\|apply_patch) | Denies writes that would land stiff terms into docs (`.md`/`.txt`/…) before they happen |
| Sentence patterns | (dictionary `re:` entries) | Catches template phrasing the word list cannot — 值得注意的是、综上所述、进行了… |
| LLM judge | Stop (Claude Code prompt-type hook) | A small model judges naturalness when the dictionary misses, covering the long tail |

Plus a pull-mode knowledge layer: the `term-dict` MCP server exposes `lookup_term` / `check_text` / `add_term`, so the model can query the dictionary on demand and new bad cases become entries on the spot (a data flywheel).

**Three-tier dictionary** (most specific wins):

1. Bundled — `hooks/terminology.tsv`, shipped with the plugin/CLI;
2. User-level — `~/.claude/MindForge/terminology.tsv`, seeded on install, kept across upgrades;
3. Project-level — `mindforge.zh-dict.tsv` at the project root, committed to the repo and shared with the team. Discovered by walking up from the session's `cwd`, stopping at the first `.git` boundary.

Generate a project dictionary with `mindforge init dict` (or copy the format from `hooks/terminology.tsv`). Entries are `直译词<TAB>期望写法<TAB>说明`; `re:` prefixed entries are regexes. Kill switch: `export ZH_GUARD_OFF=1` or drop an `OFF` file into `~/.claude/MindForge/`. Full details live in [hooks/README.md](hooks/README.md).

### 🔧 MindForge CLI (Go)

The `mindforge` binary is the installer, generator, and doctor — it embeds the whole hook payload (scripts, bundled dictionary, style-rule documents), so a single build carries everything. Install it straight from GitHub:

```bash
# Requires Go 1.24+
go install github.com/ProjAnvil/MindForge/cli/mindforge@latest

# Track the development branch instead:
# go install github.com/ProjAnvil/MindForge/cli/mindforge@main

# Fresh modules can lag in the public proxy/sum DB. If you hit a 404
# right after a release, install once via direct mode:
GOPROXY=direct GOSUMDB=off go install github.com/ProjAnvil/MindForge/cli/mindforge@latest

# Or grab a prebuilt binary from the GitHub releases page, or build from a checkout
git clone https://github.com/ProjAnvil/MindForge.git && cd MindForge && make cli
```

```bash
mindforge install                                        # interactive: pick harnesses + language
mindforge install --platform=claude,zcode,codex --lang=zh-cn --yes   # scripted
mindforge init dict                                      # generate mindforge.zh-dict.tsv here
mindforge doctor                                         # runtimes, registration, dictionary tiers
```

`install` registers the hooks into each harness's own config format (Claude Code `settings.json`, zcode `config.json` with `hooks.enabled=true`, Codex `hooks.json`), idempotently — foreign hook entries survive byte-for-byte. Kimi Code is detected but not yet installable (blocked on an upstream Stop-payload limitation). Platform details in [cli/README.md](cli/README.md).

## 🤖 Available Agents

- **@code-reviewer** - Expert code reviewer (software architecture, design patterns, code quality, SOLID principles)
- **@frontend-engineer** - Modern frontend expert (React, Vue, Svelte, TypeScript)
- **@golang-backend-engineer** - Go backend development expert (Fiber, Cobra, GORM, Clean Architecture)
- **@ios-developer** - Expert iOS Developer (Swift 6, SwiftUI, MVVM, TCA)
- **@java-backend-engineer** - Professional Java backend engineer (Spring Boot, MyBatis, Clean Architecture)
- **@java-unit-test** - Professional Java unit test generator (JUnit, Mockito, AssertJ)
- **@product-manager** - Product management expert (PRD, user stories, competitive analysis)
- **@python-test-engineer** - Professional Python testing engineer (pytest, unittest, pytest-asyncio)
- **@system-architect** - System architecture design expert (patterns, tech selection, ADR docs)

## 🎯 Available Skills

- **api-design** - API design (REST, GraphQL, gRPC)
- **database-design** - Database design and optimization
- **enterprise-java** - Enterprise Java development (Spring Boot, microservices)
- **frontend-react** - React ecosystem (Next.js, Server Components, Tailwind)
- **frontend-svelte** - Svelte ecosystem (SvelteKit, shadcn-svelte)
- **frontend-vue** - Vue ecosystem (Nuxt, Composition API, Pinia)
- **git-guru** - Advanced Git operations and version control mastery
- **go-development** - Go development (Fiber, Cobra, GORM)
- **javascript-typescript** - JavaScript/TypeScript development (Node.js, Express, React)
- **product-management** - Product management and strategy
- **python-development** - Python development (FastAPI, Django, Flask, asyncio)
- **session-summary** - Summarize current session context for seamless handover
- **swift-development** - Core Swift 6+ development (Concurrency, Macros, Testing)
- **swiftui-development** - Modern SwiftUI development (NavigationStack, Observation, SwiftData)
- **system-architecture** - System architecture design
- **tech-documentation** - Technical documentation writing
- **testing** - General testing skills (unit, integration, TDD/BDD)
- **xcode-management** - Xcode project management (automated file addition, project.pbxproj handling)

## 📁 Project Structure

```
mindforge/
├── agents/              # Claude Code format Agents (multi-language)
│   ├── en/             # English versions
│   │   ├── code-reviewer.md
│   │   ├── frontend-engineer.md
│   │   ├── golang-backend-engineer.md
│   │   ├── ios-developer.md
│   │   ├── java-backend-engineer.md
│   │   ├── java-unit-test.md
│   │   ├── product-manager.md
│   │   ├── python-test-engineer.md
│   │   └── system-architect.md
│   └── zh-cn/          # Chinese versions
│       ├── code-reviewer.md
│       ├── frontend-engineer.md
│       ├── golang-backend-engineer.md
│       ├── java-backend-engineer.md
│       ├── java-unit-test.md
│       ├── product-manager.md
│       ├── python-test-engineer.md
│       └── system-architect.md
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
│   │   ├── git-guru/SKILL.md
│   │   └── xcode-management/SKILL.md
│   ├── zh-cn/          # Chinese versions
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
│   │   ├── git-guru/SKILL.md
│   │   └── xcode-management/SKILL.md
│   └── scripts/        # Shared executable scripts for skills
│       └── xcode-management/
│           └── add_files_to_xcode.py  # Automated Xcode file addition
├── user_claude_md/      # User-level Claude instructions (multi-language)
│   ├── en/
│   │   └── CLAUDE.md   # English user-level instructions
│   └── zh-cn/
│       └── CLAUDE.md   # Chinese user-level instructions
├── hooks/               # style-rules-zh-cn plugin: controlled-writing rules + zh-guard
│   ├── hooks/           # hook registrations (shared / Claude-only variants)
│   ├── inject.py / inspect.py / inspect-file.py   # L1 / L2 / file-write guard
│   ├── term-dict-server.py    # zh-guard MCP server (lookup_term/check_text/add_term)
│   ├── zh_guard_common.py    # three-tier dictionary loading (shared library)
│   ├── terminology.tsv       # bundled dictionary (data flywheel)
│   └── .claude-plugin/ / .zcode-plugin/   # per-harness plugin manifests
├── cli/                 # mindforge CLI (Go): install / init dict / doctor
├── plugins/             # generated plugin bundles (mindforge-en/zh-cn, style-rules)
├── go.mod + assets.go   # Go module; embeds the hook payload into the CLI binary
├── templates/           # Templates for creating new resources
│   ├── agent-template-en.md      # English agent template
│   ├── agent-template-zhcn.md    # Chinese agent template
│   ├── skill-template-en.md      # English skill template
│   └── skill-template-zhcn.md    # Chinese skill template
├── mcp/                 # MCP services collection
│   ├── _template/
│   └── mcp-*/
├── evals/               # smelt evaluation suite (skills + agents, uv-managed)
│   ├── tests/           # lint, routing, behavior, evaluate (pytest)
│   ├── cases/           # doctor-ready module-level case files
│   └── reports/         # committed evaluate reports (md + json)
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

## 🧪 Evaluation

The `evals/` directory is a uv-managed [Smelt](https://github.com/ProjAnvil/Smelt) harness
covering both skills and the agent (subagent) definitions, in both languages:

- **Static lint** (deterministic, no API key): every SKILL.md and every agent
  file is linted against Claude Code's loading contract — for agents that
  includes frontmatter validity (name/description/tools/model), and whether
  each description actually routes (delegation triggers).
- **Delegation routing** (LLM): a simulated main agent sees each language's
  roster (names + descriptions) and must delegate specialty tasks to the
  right subagent, refuse to steal a sibling's specialty, and keep trivial
  tasks for itself.
- **Behavior** (LLM): each agent file runs as a real subagent — the markdown
  body is the system prompt and the `tools:` frontmatter allowlist is
  enforced — with the six core Claude Code tools (Read/Grep/Glob/Bash/Edit/
  Write) backed by an isolated case workspace.
- **Evaluate reports**: full per-document evaluations (behavior + writing
  review + lint + suggestions + adversarial routing probes) saved to
  `evals/reports/`.

```bash
make eval        # deterministic evals: lint + plumbing (no API key, CI-safe)
make eval-llm    # full evals incl. behavior/routing/evaluate (needs SMELT_API_KEY)
```

Configuration lives in `evals/.env` (see `evals/.env.template`). Doctor-ready
case files for on-demand mutation checks (run from `evals/`):

```bash
uv run smelt run cases/en_agent_routing_cases.py -v
uv run smelt doctor --agent ../agents/en/code-reviewer.md cases/en_agent_routing_cases.py
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
# Create an English skill (default, no scripts)
make init-skill SKILL=my-skill

# Create a skill with executable scripts
make init-skill SKILL=my-skill WITH_SCRIPTS=yes

# Create a Chinese skill
make init-skill SKILL=my-skill LANG=zh-cn

# Create a Chinese skill with scripts
make init-skill SKILL=my-skill LANG=zh-cn WITH_SCRIPTS=yes
```

**What you get:**
- A complete skill file with frontmatter (name, description, allowed-tools)
- Structured sections for expertise, principles, and best practices
- Code patterns, templates, and troubleshooting guides
- Quality checklists and decision frameworks
- (Optional) A shared `skills/scripts/{skill-name}/` directory for executable scripts
- Ready to use across multiple agents

**After creation:**
1. Edit `skills/{lang}/{skill-name}/SKILL.md` to define capabilities
2. Add domain-specific knowledge and best practices
3. Include code templates and common patterns
4. (Optional) Add executable scripts to `skills/scripts/{skill-name}/`
5. Run `./setup-claude.sh --lang={lang}` to activate

**Scripts Support:**
When `WITH_SCRIPTS=yes` is used, a shared scripts directory is created at `skills/scripts/{skill-name}/`. This allows:
- Multi-language skills to share the same executable scripts
- Scripts referenced via relative path `scripts/` in skill documentation
- Automatic linking/copying of scripts during setup for both Unix/Mac (symlink) and Windows (copy)

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

# Build the mindforge CLI (Go)
make cli

# Vet + test the CLI
make cli-test
```

**Note:** Agents and skills are markdown files and don't require building. The zh-guard hook scripts are tested with `python3 hooks/test_zh_guard.py` (and friends).

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
