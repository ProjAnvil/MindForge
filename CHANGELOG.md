# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-12

### Changed

- **Setup Script Naming**: Renamed all internal variables and user-facing text from `AITK` to `MindForge` in `setup-claude.sh` for brand consistency:
  - `AITK_DIR` → `MINDFORGE_DIR`
  - `AITK_AGENTS_DIR` → `MINDFORGE_AGENTS_DIR`
  - `AITK_SKILLS_DIR` → `MINDFORGE_SKILLS_DIR`
  - `AITK_DOCS_SRC_DIR` → `MINDFORGE_DOCS_SRC_DIR`
  - `AITK_USER_CLAUDE_MD_SRC` → `MINDFORGE_USER_CLAUDE_MD_SRC`
  - Banner text updated from "AITK Claude Code Setup" to "MindForge Claude Code Setup"

## [0.3.0] - 2026-03-05

### Changed

- **Progressive Disclosure Architecture**: Restructured all skill files to follow a three-level loading system for improved token efficiency:
  - **Level 1 (Metadata)**: Skill name and description always loaded (~100 words)
  - **Level 2 (SKILL.md body)**: Core concepts and quick reference loaded when skill triggers (<500 lines)
  - **Level 3 (References)**: Detailed patterns, templates, and examples loaded only when needed

### Added

- **References Subdirectories**: Created `references/` folders for 12 skills in both English and Chinese (24 total):
  - `api-design`: OpenAPI templates, GraphQL patterns, pagination & rate limiting, common patterns
  - `database-design`: Sharding strategies, query optimization, migration & backup
  - `design-pattern`: Pattern implementations with code examples
  - `enterprise-java`: Class templates, response patterns
  - `frontend-svelte`: API patterns, forms & styling, testing & performance & a11y, deployment patterns
  - `git-guru`: Advanced features, workflows & scenarios
  - `go-development`: File templates for clean architecture
  - `javascript-typescript`: Express API patterns, React patterns, testing patterns
  - `python-development`: FastAPI patterns, Django patterns, testing patterns
  - `system-architecture`: Architecture templates
  - `tech-documentation`: API docs, architecture docs, deployment docs templates
  - `testing`: Language-specific test patterns (JUnit, pytest, Jest, testify)

### Technical Details

- All SKILL.md files now stay under 500 lines for optimal context loading
- 56 new reference files created (28 English + 28 Chinese)
- Total reduction of ~12,500 lines moved from main skill files to references
- Maintains consistent structure across English (`en`) and Chinese (`zh-cn`) versions

## [0.2.0] - 2026-03-03

### Added

- **Modern Go Guidelines**: Added `modern-go.md` supporting file to `go-development` skill with comprehensive version-specific syntax guidelines from Go 1.0 to Go 1.26+, including:
  - Dynamic Go version detection via shell command
  - Modern alternatives for legacy patterns (slices, maps, cmp packages)
  - Version-specific best practices (omitzero, b.Loop(), t.Context(), wg.Go(), etc.)
  - Before/after code examples for each feature

### Changed

- **Simplified Skill Frontmatter**: Removed `allowed-tools` field from all 38 skill files. Claude Code's permission system handles tool access control appropriately without requiring explicit allowlists in skill definitions.

## [0.1.0] - 2026-01-27

### Initial Release of MindForge

MindForge is a comprehensive AI Toolkit for Claude Code, designed to enhance development workflows with specialized Agents and Skills.

### 🚀 Key Features

*   **Multi-language Support**: Full support for English and Simplified Chinese (zh-cn).
*   **Automated Setup**: `setup-claude.sh` script to seamlessly integrate with Claude Code (`~/.claude/`).
*   **9 Specialized Agents**:
    *   `code-reviewer`: Expert in code quality and architecture.
    *   `frontend-engineer`: React/Vue/Svelte expert.
    *   `golang-backend-engineer`: Go ecosystem expert.
    *   `ios-developer`: Swift 6 & SwiftUI expert.
    *   `java-backend-engineer`: Spring Boot & Enterprise Java expert.
    *   `java-unit-test`: Automated unit test generation.
    *   `product-manager`: Product strategy and documentation.
    *   `python-test-engineer`: Python testing specialist.
    *   `system-architect`: System design and ADRs.
*   **18 Domain-Specific Skills**:
    *   Development: `go-development`, `python-development`, `swift-development`, `swiftui-development`, `enterprise-java`, `api-design`, `database-design`.
    *   Frontend: `frontend-react`, `frontend-vue`, `frontend-svelte`, `frontend-development`.
    *   Workflow: `git-guru`, `xcode-management`, `tech-documentation`, `product-management`.
    *   General: `testing`, `javascript-typescript`.
    *   **New**: `session-summary` for efficient context handover.
*   **MCP Support**: Infrastructure for Model Context Protocol services.

### 🛠 Improvements

*   Fixed symlink logic in `setup-claude.sh` to prevent source directory pollution.
*   Standardized `SKILL.md` and agent configurations.
