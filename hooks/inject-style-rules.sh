#!/bin/bash
# MindForge hook: inject controlled-writing style rules into context.
#
# Events: UserPromptSubmit | SessionStart | SubagentStart
# Input:  hook JSON on stdin (hook_event_name is read to echo back)
# Output: single JSON object with hookSpecificOutput.additionalContext
#
# Language is chosen by (highest priority first):
#   1. command-line argument ($1): en | zh-cn (used by plugin variants)
#   2. the marker file style-rules.lang next to this script
#      (written by setup-claude.sh from its --lang parameter)
#   3. default: en
# en    -> inject English rules only
# zh-cn -> inject Chinese + English rules
#
# No external dependencies (no jq/python) so it runs on macOS, Linux,
# and Windows GitBash.

set -u

# Resolve files next to this script.
# Works through symlinks because they are linked alongside.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
RULES_ZH="$SCRIPT_DIR/style-rules-zh.md"
RULES_EN="$SCRIPT_DIR/style-rules-en.md"
LANG_FILE="$SCRIPT_DIR/style-rules.lang"

if [ ! -f "$RULES_EN" ]; then
    # Fail open: no English rules file, inject nothing.
    exit 0
fi

# Choose language: argument > marker > default en.
LANG_CODE="en"
if [ $# -ge 1 ]; then
    case "$1" in
        en|zh-cn) LANG_CODE="$1" ;;
    esac
elif [ -f "$LANG_FILE" ]; then
    MARKER="$(tr -d '[:space:]' < "$LANG_FILE")"
    case "$MARKER" in
        en|zh-cn) LANG_CODE="$MARKER" ;;
    esac
fi

# Compose rules per language.
if [ "$LANG_CODE" = "en" ]; then
    RULES="$(cat "$RULES_EN")"
    PREAMBLE="Follow these controlled writing rules (ASD-STE100) for all output:"
else
    if [ ! -f "$RULES_ZH" ]; then
        # Fail open if the Chinese rules file is missing.
        exit 0
    fi
    RULES="$(cat "$RULES_ZH")

$(cat "$RULES_EN")"
    PREAMBLE="写作时必须遵守以下受控写作规范（中文与英文均适用）："
fi

# Read hook event name from stdin JSON; default to UserPromptSubmit.
INPUT="$(cat)"
EVENT="$(printf '%s' "$INPUT" | sed -n 's/.*"hook_event_name"[: ]*"\([^"]*\)".*/\1/p' | head -n 1)"
[ -z "$EVENT" ] && EVENT="UserPromptSubmit"

# Escape a string for embedding inside a JSON string literal.
escape_json() {
    local s="$1"
    s="${s//\\/\\\\}"      # backslash first
    s="${s//\"/\\\"}"      # double quote
    s="${s//$'\n'/\\n}"    # newline
    s="${s//$'\r'/}"       # carriage return: drop
    s="${s//$'\t'/\\t}"    # tab
    printf '%s' "$s"
}

printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s %s"}}' \
    "$EVENT" "$(escape_json "$PREAMBLE")" "$(escape_json "$RULES")"
