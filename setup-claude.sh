#!/bin/bash

# Claude Code AITK Setup Script (Multilingual Support)
# This script creates symbolic links from your AITK project to ~/.claude/
# so that Claude Code can automatically discover your agents and skills.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default language
LANG_CODE="en"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --lang=*)
            LANG_CODE="${1#*=}"
            shift
            ;;
        --lang)
            LANG_CODE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --lang=LANG, --lang LANG    Set language (en or zh-cn, default: en)"
            echo "  -h, --help                  Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                  # Use default language (en)"
            echo "  $0 --lang=zh-cn     # Use Chinese"
            echo "  $0 --lang en        # Use English"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate language code
if [[ "$LANG_CODE" != "en" && "$LANG_CODE" != "zh-cn" ]]; then
    echo -e "${RED}Error: Unsupported language '$LANG_CODE'${NC}"
    echo "Supported languages: en, zh-cn"
    exit 1
fi

# Get the absolute path of this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AITK_DIR="$SCRIPT_DIR"

# Source directories (with language)
AITK_AGENTS_DIR="$AITK_DIR/agents/$LANG_CODE"
AITK_SKILLS_DIR="$AITK_DIR/skills/$LANG_CODE"

# Target directories
CLAUDE_DIR="$HOME/.claude"
CLAUDE_AGENTS_DIR="$CLAUDE_DIR/agents"
CLAUDE_SKILLS_DIR="$CLAUDE_DIR/skills"

# Verify source directories exist
if [ ! -d "$AITK_AGENTS_DIR" ]; then
    echo -e "${RED}Error: Agents directory not found: $AITK_AGENTS_DIR${NC}"
    echo "Available languages:"
    ls -d "$AITK_DIR/agents/"*/ 2>/dev/null | xargs -n 1 basename
    exit 1
fi

if [ ! -d "$AITK_SKILLS_DIR" ]; then
    echo -e "${RED}Error: Skills directory not found: $AITK_SKILLS_DIR${NC}"
    echo "Available languages:"
    ls -d "$AITK_DIR/skills/"*/ 2>/dev/null | xargs -n 1 basename
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AITK Claude Code Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Language:${NC} $LANG_CODE"
echo -e "${GREEN}Source:${NC}"
echo "  Agents: $AITK_AGENTS_DIR"
echo "  Skills: $AITK_SKILLS_DIR"
echo -e "${GREEN}Target:${NC} $CLAUDE_DIR/"
echo ""

# Function to create directory if it doesn't exist
create_dir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}Creating directory:${NC} $dir"
        mkdir -p "$dir"
    else
        echo -e "${GREEN}Directory exists:${NC} $dir"
    fi
}

# Function to create or update symlink
create_symlink() {
    local source=$1
    local target=$2
    local name=$3

    if [ -L "$target" ]; then
        # Symlink exists
        local current_target=$(readlink "$target")
        if [ "$current_target" = "$source" ]; then
            echo -e "${GREEN}✓${NC} $name (already linked)"
        else
            echo -e "${YELLOW}⟳${NC} $name (updating link)"
            rm "$target"
            ln -s "$source" "$target"
        fi
    elif [ -e "$target" ]; then
        # File/directory exists but is not a symlink
        echo -e "${RED}✗${NC} $name (conflict: $target exists and is not a symlink)"
        echo -e "${YELLOW}  Please manually remove or backup:${NC} $target"
        return 1
    else
        # Create new symlink
        echo -e "${GREEN}+${NC} $name (creating link)"
        ln -s "$source" "$target"
    fi
}

# Step 1: Create Claude directories
echo -e "\n${BLUE}Step 1: Creating Claude directories${NC}"
create_dir "$CLAUDE_DIR"
create_dir "$CLAUDE_AGENTS_DIR"
create_dir "$CLAUDE_SKILLS_DIR"

# Step 2: Link agents
echo -e "\n${BLUE}Step 2: Linking agents${NC}"

# Auto-discover all agent files
shopt -s nullglob  # Return empty array if no matches
AGENT_FILES=("$AITK_AGENTS_DIR"/*.md)
shopt -u nullglob

if [ ${#AGENT_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}No agent files found in $AITK_AGENTS_DIR${NC}"
else
    for agent_file in "${AGENT_FILES[@]}"; do
        agent_name=$(basename "$agent_file")
        agent_id="${agent_name%.md}"

        target_file="$CLAUDE_AGENTS_DIR/$agent_name"

        create_symlink "$agent_file" "$target_file" "$agent_id"
    done
fi

# Step 3: Link skills
echo -e "\n${BLUE}Step 3: Linking skills${NC}"

# Auto-discover all skill directories
shopt -s nullglob
SKILL_DIRS=("$AITK_SKILLS_DIR"/*/)
shopt -u nullglob

if [ ${#SKILL_DIRS[@]} -eq 0 ]; then
    echo -e "${YELLOW}No skill directories found in $AITK_SKILLS_DIR${NC}"
else
    for skill_dir in "${SKILL_DIRS[@]}"; do
        skill_name=$(basename "$skill_dir")

        target_dir="$CLAUDE_SKILLS_DIR/$skill_name"

        create_symlink "$skill_dir" "$target_dir" "$skill_name"
    done
fi

# Step 4: Verification
echo -e "\n${BLUE}Step 4: Verification${NC}"
echo -e "\n${YELLOW}Agents in ~/.claude/agents/:${NC}"
if [ -d "$CLAUDE_AGENTS_DIR" ]; then
    agent_count=$(ls -lh "$CLAUDE_AGENTS_DIR" 2>/dev/null | grep -E "^l" | wc -l | tr -d ' ')
    if [ "$agent_count" -eq 0 ]; then
        echo -e "${YELLOW}  No agents linked${NC}"
    else
        ls -lh "$CLAUDE_AGENTS_DIR" | grep -E "^l" | awk '{print "  " $9 " -> " $11}'
    fi
else
    echo -e "${RED}  No agents directory${NC}"
fi

echo -e "\n${YELLOW}Skills in ~/.claude/skills/:${NC}"
if [ -d "$CLAUDE_SKILLS_DIR" ]; then
    skill_count=$(ls -lh "$CLAUDE_SKILLS_DIR" 2>/dev/null | grep -E "^l" | wc -l | tr -d ' ')
    if [ "$skill_count" -eq 0 ]; then
        echo -e "${YELLOW}  No skills linked${NC}"
    else
        ls -lh "$CLAUDE_SKILLS_DIR" | grep -E "^l" | awk '{print "  " $9 " -> " $11}'
    fi
else
    echo -e "${RED}  No skills directory${NC}"
fi

# Step 5: Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Language: $LANG_CODE"
echo "  Agents linked: $(ls -lh "$CLAUDE_AGENTS_DIR" 2>/dev/null | grep -E "^l" | wc -l | tr -d ' ')"
echo "  Skills linked: $(ls -lh "$CLAUDE_SKILLS_DIR" 2>/dev/null | grep -E "^l" | wc -l | tr -d ' ')"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Claude Code will now automatically discover these agents and skills"
echo "2. Use agents with: ${BLUE}@agent-name${NC} in Claude Code"
echo "3. Skills are automatically loaded when referenced in agents"
echo ""
echo -e "${YELLOW}Important notes:${NC}"
echo "- Changes to agents/skills in your project are immediately available"
echo "- To switch language, run: ${BLUE}$0 --lang=<lang>${NC}"
echo "- To remove links: ${RED}rm ~/.claude/agents/* ~/.claude/skills/*${NC}"
echo ""
echo -e "${GREEN}Available languages:${NC}"
ls -d "$AITK_DIR/agents/"*/ 2>/dev/null | xargs -n 1 basename | sed 's/^/  - /'
echo ""
echo -e "${GREEN}Documentation:${NC}"
echo "- Project README: $AITK_DIR/README.md"
echo "- Setup guide: $AITK_DIR/CLAUDE_CODE_SETUP.md"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
