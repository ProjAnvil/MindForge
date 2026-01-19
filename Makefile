# MindForge Makefile
# Manage MCP services, Agents, and Skills

.PHONY: help list-mcp list-agents list-skills init-mcp init-agent init-skill add-skill build build-all test-all clean-all

# Default target
help:
	@echo "MindForge - AI Toolkit Management"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "  List Resources:"
	@echo "    make list-mcp              List all MCP services"
	@echo "    make list-agents           List all Agents (all languages)"
	@echo "    make list-skills           List all Skills (all languages)"
	@echo ""
	@echo "  Create Resources:"
	@echo "    make init-mcp SERVICE=name           Create a new MCP service"
	@echo "    make init-agent AGENT=name [LANG=en] Create a new Agent (default: en)"
	@echo "    make init-skill SKILL=name [LANG=en] [WITH_SCRIPTS=yes]"
	@echo "                                         Create a new Skill (default: en, no scripts)"
	@echo ""
	@echo "  Manage Resources:"
	@echo "    make add-skill AGENT=name SKILL=skill-name [LANG=en]"
	@echo "                                         Add a skill to an agent"
	@echo ""
	@echo "  Build & Test:"
	@echo "    make build SERVICE=name              Build a single MCP service"
	@echo "    make build AGENT=name                Build a single Agent"
	@echo "    make build SKILL=name                Build a single Skill"
	@echo "    make build-all                       Build all resources"
	@echo "    make test-all                        Test all resources"
	@echo "    make clean-all                       Clean all resources"
	@echo ""
	@echo "Examples:"
	@echo "  make init-agent AGENT=my-agent LANG=en"
	@echo "  make init-agent AGENT=my-agent LANG=zh-cn"
	@echo "  make init-skill SKILL=my-skill"
	@echo "  make init-skill SKILL=my-skill WITH_SCRIPTS=yes"
	@echo "  make add-skill AGENT=my-agent SKILL=testing"

# List all MCP services
list-mcp:
	@echo "Available MCP services:"
	@ls -d mcp/mcp-* 2>/dev/null | xargs -n 1 basename | sed 's/^/  - /' || echo "  No MCP services found"

# List all Agents
list-agents:
	@echo "Available Agents:"
	@echo ""
	@echo "English (en):"
	@ls agents/en/*.md 2>/dev/null | xargs -n 1 basename | sed 's/\.md$$//' | sed 's/^/  - /' || echo "  No agents found"
	@echo ""
	@echo "Chinese (zh-cn):"
	@ls agents/zh-cn/*.md 2>/dev/null | xargs -n 1 basename | sed 's/\.md$$//' | sed 's/^/  - /' || echo "  No agents found"

# List all Skills
list-skills:
	@echo "Available Skills:"
	@echo ""
	@echo "English (en):"
	@ls -d skills/en/*/ 2>/dev/null | xargs -n 1 basename | sed 's/^/  - /' || echo "  No skills found"
	@echo ""
	@echo "Chinese (zh-cn):"
	@ls -d skills/zh-cn/*/ 2>/dev/null | xargs -n 1 basename | sed 's/^/  - /' || echo "  No skills found"

# Create a new MCP service
init-mcp:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE is required"; \
		echo "Usage: make init-mcp SERVICE=mcp-foo"; \
		exit 1; \
	fi
	@if [ -d "mcp/$(SERVICE)" ]; then \
		echo "Error: MCP service already exists: mcp/$(SERVICE)"; \
		exit 1; \
	fi
	@echo "Creating MCP service: $(SERVICE)"
	@mkdir -p mcp/$(SERVICE)
	@cp -r mcp/_template/* mcp/$(SERVICE)/ 2>/dev/null || echo "Note: No template found in mcp/_template"
	@echo "✓ MCP service created: mcp/$(SERVICE)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. cd mcp/$(SERVICE)"
	@echo "  2. Edit files and implement your MCP service"
	@echo "  3. Add a Makefile with build, test, and clean targets"

# Create a new Agent
init-agent:
	@if [ -z "$(AGENT)" ]; then \
		echo "Error: AGENT is required"; \
		echo "Usage: make init-agent AGENT=my-agent [LANG=en]"; \
		exit 1; \
	fi
	$(eval LANG ?= en)
	@if [ "$(LANG)" != "en" ] && [ "$(LANG)" != "zh-cn" ]; then \
		echo "Error: Unsupported language '$(LANG)'"; \
		echo "Supported languages: en, zh-cn"; \
		exit 1; \
	fi
	@mkdir -p agents/$(LANG)
	@if [ -f "agents/$(LANG)/$(AGENT).md" ]; then \
		echo "Error: Agent already exists: agents/$(LANG)/$(AGENT).md"; \
		exit 1; \
	fi
	@echo "Creating Agent: $(AGENT) ($(LANG))"
	@if [ "$(LANG)" = "en" ]; then \
		cp templates/agent-template-en.md agents/$(LANG)/$(AGENT).md; \
		sed -i.bak 's/your-agent-name/$(AGENT)/g' agents/$(LANG)/$(AGENT).md && rm agents/$(LANG)/$(AGENT).md.bak; \
	else \
		cp templates/agent-template-zhcn.md agents/$(LANG)/$(AGENT).md; \
		sed -i.bak 's/你的智能体名称/$(AGENT)/g' agents/$(LANG)/$(AGENT).md && rm agents/$(LANG)/$(AGENT).md.bak; \
	fi
	@echo "✓ Agent created: agents/$(LANG)/$(AGENT).md"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit agents/$(LANG)/$(AGENT).md"
	@echo "  2. Update the agent name, description, and system prompt"
	@echo "  3. Specify tools, model, and skills in the frontmatter"
	@echo "  4. Run ./setup-claude.sh --lang=$(LANG) to activate"

# Create a new Skill
init-skill:
	@if [ -z "$(SKILL)" ]; then \
		echo "Error: SKILL is required"; \
		echo "Usage: make init-skill SKILL=my-skill [LANG=en] [WITH_SCRIPTS=yes]"; \
		exit 1; \
	fi
	$(eval LANG ?= en)
	@if [ "$(LANG)" != "en" ] && [ "$(LANG)" != "zh-cn" ]; then \
		echo "Error: Unsupported language '$(LANG)'"; \
		echo "Supported languages: en, zh-cn"; \
		exit 1; \
	fi
	@mkdir -p skills/$(LANG)/$(SKILL)
	@if [ -f "skills/$(LANG)/$(SKILL)/SKILL.md" ]; then \
		echo "Error: Skill already exists: skills/$(LANG)/$(SKILL)/SKILL.md"; \
		exit 1; \
	fi
	@echo "Creating Skill: $(SKILL) ($(LANG))"
	@if [ "$(LANG)" = "en" ]; then \
		cp templates/skill-template-en.md skills/$(LANG)/$(SKILL)/SKILL.md; \
		sed -i.bak 's/your-skill-name/$(SKILL)/g' skills/$(LANG)/$(SKILL)/SKILL.md && rm skills/$(LANG)/$(SKILL)/SKILL.md.bak; \
	else \
		cp templates/skill-template-zhcn.md skills/$(LANG)/$(SKILL)/SKILL.md; \
		sed -i.bak 's/你的技能名称/$(SKILL)/g' skills/$(LANG)/$(SKILL)/SKILL.md && rm skills/$(LANG)/$(SKILL)/SKILL.md.bak; \
	fi
	@if [ "$(WITH_SCRIPTS)" = "yes" ]; then \
		echo "Creating shared scripts directory..."; \
		mkdir -p skills/scripts/$(SKILL); \
		echo "✓ Scripts directory created: skills/scripts/$(SKILL)"; \
	fi
	@echo "✓ Skill created: skills/$(LANG)/$(SKILL)/SKILL.md"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit skills/$(LANG)/$(SKILL)/SKILL.md"
	@echo "  2. Define the skill's expertise and capabilities"
	@echo "  3. Add best practices and code templates"
	@if [ "$(WITH_SCRIPTS)" = "yes" ]; then \
		echo "  4. Add your scripts to skills/scripts/$(SKILL)/"; \
	fi
	@echo "  4. Run ./setup-claude.sh --lang=$(LANG) to activate"

# Add a skill to an agent
add-skill:
	@if [ -z "$(AGENT)" ] || [ -z "$(SKILL)" ]; then \
		echo "Error: AGENT and SKILL are required"; \
		echo "Usage: make add-skill AGENT=my-agent SKILL=my-skill [LANG=en]"; \
		exit 1; \
	fi
	$(eval LANG ?= en)
	@if [ ! -f "agents/$(LANG)/$(AGENT).md" ]; then \
		echo "Error: Agent not found: agents/$(LANG)/$(AGENT).md"; \
		exit 1; \
	fi
	@if [ ! -d "skills/$(LANG)/$(SKILL)" ]; then \
		echo "Error: Skill not found: skills/$(LANG)/$(SKILL)"; \
		exit 1; \
	fi
	@echo "Adding skill '$(SKILL)' to agent '$(AGENT)' ($(LANG))"
	@if grep -q "^skills:.*$(SKILL)" agents/$(LANG)/$(AGENT).md; then \
		echo "✓ Skill '$(SKILL)' is already in agent '$(AGENT)'"; \
	else \
		sed -i.bak 's/^skills:\(.*\)$$/skills:\1, $(SKILL)/' agents/$(LANG)/$(AGENT).md && rm agents/$(LANG)/$(AGENT).md.bak; \
		echo "✓ Skill '$(SKILL)' added to agent '$(AGENT)'"; \
	fi

# Build a single resource
build:
	@if [ -n "$(SERVICE)" ]; then \
		if [ -d "mcp/$(SERVICE)" ]; then \
			echo "Building MCP service: $(SERVICE)"; \
			cd mcp/$(SERVICE) && make build; \
		else \
			echo "Error: MCP service not found: mcp/$(SERVICE)"; \
			exit 1; \
		fi; \
	elif [ -n "$(AGENT)" ]; then \
		echo "Note: Agents are markdown files and don't require building"; \
	elif [ -n "$(SKILL)" ]; then \
		echo "Note: Skills are markdown files and don't require building"; \
	else \
		echo "Error: Specify SERVICE, AGENT, or SKILL"; \
		echo "Usage: make build SERVICE=name"; \
		exit 1; \
	fi

# Build all resources
build-all:
	@echo "Building all MCP services..."
	@for dir in mcp/mcp-*; do \
		if [ -d "$$dir" ] && [ -f "$$dir/Makefile" ]; then \
			echo "Building $$(basename $$dir)..."; \
			(cd $$dir && make build) || exit 1; \
		fi; \
	done
	@echo "✓ All resources built successfully"

# Test all resources
test-all:
	@echo "Testing all MCP services..."
	@for dir in mcp/mcp-*; do \
		if [ -d "$$dir" ] && [ -f "$$dir/Makefile" ]; then \
			echo "Testing $$(basename $$dir)..."; \
			(cd $$dir && make test) || exit 1; \
		fi; \
	done
	@echo "✓ All tests passed"

# Clean all resources
clean-all:
	@echo "Cleaning all MCP services..."
	@for dir in mcp/mcp-*; do \
		if [ -d "$$dir" ] && [ -f "$$dir/Makefile" ]; then \
			echo "Cleaning $$(basename $$dir)..."; \
			(cd $$dir && make clean) || exit 1; \
		fi; \
	done
	@echo "✓ All resources cleaned"
