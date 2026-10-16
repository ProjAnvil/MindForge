#!/bin/bash
# Tests for inject-style-rules.sh
# Usage: bash test-inject-style-rules.sh

set -u
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-style-rules.sh"
PY=/Users/yuhaochen/.workbuddy/binaries/python/versions/3.13.12/bin/python3
PASS=0
FAIL=0

check() {
    local name="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "PASS: $name"
        PASS=$((PASS+1))
    else
        echo "FAIL: $name"
        echo "  expected: $expected"
        echo "  actual:   $actual"
        FAIL=$((FAIL+1))
    fi
}

# validate <name> <marker-content|none> <payload> <expected_event> <expect_zh:yes/no> <expect_en:yes/no> [args]
validate() {
    local name="$1" marker="$2" payload="$3" expected_event="$4" expect_zh="$5" expect_en="$6" hook_args="${7:-}"
    local tmp out result
    tmp="$(mktemp -d)"
    cp "$(dirname "$HOOK")/inject-style-rules.sh" "$tmp/"
    cp "$(dirname "$HOOK")/style-rules-zh.md" "$tmp/"
    cp "$(dirname "$HOOK")/style-rules-en.md" "$tmp/"
    [ "$marker" != "none" ] && printf '%s' "$marker" > "$tmp/style-rules.lang"
    out="$(printf '%s' "$payload" | bash "$tmp/inject-style-rules.sh" $hook_args)"
    result="$("$PY" -c '
import json, sys
obj = json.loads(sys.argv[1])
hso = obj["hookSpecificOutput"]
ctx = hso["additionalContext"]
assert hso["hookEventName"] == sys.argv[2], "event mismatch"
has_zh = "受控写作规范" in ctx
has_en = "ASD-STE100" in ctx
assert has_zh == (sys.argv[3] == "yes"), "zh presence mismatch"
assert has_en == (sys.argv[4] == "yes"), "en presence mismatch"
if has_en:
    assert "Disconnect the power." in ctx, "quote escaping broke content"
assert len(ctx) < 10000, "over char limit"
print("ok")
' "$out" "$expected_event" "$expect_zh" "$expect_en" 2>&1)"
    check "$name" "ok" "$result"
    rm -rf "$tmp"
}

# --- zh-cn mode: Chinese + English ---

validate "zh-cn marker, UserPromptSubmit" "zh-cn" \
    '{"session_id":"abc","hook_event_name":"UserPromptSubmit","prompt":"hi"}' \
    "UserPromptSubmit" "yes" "yes"

validate "zh-cn marker, SubagentStart" "zh-cn" \
    '{"hook_event_name":"SubagentStart","agent_type":"general-purpose"}' \
    "SubagentStart" "yes" "yes"

validate "zh-cn marker, SessionStart" "zh-cn" \
    '{"hook_event_name":"SessionStart","source":"startup"}' \
    "SessionStart" "yes" "yes"

# --- en mode: English only ---

validate "en marker, UserPromptSubmit (English only)" "en" \
    '{"hook_event_name":"UserPromptSubmit","prompt":"hi"}' \
    "UserPromptSubmit" "no" "yes"

validate "en marker, SubagentStart (English only)" "en" \
    '{"hook_event_name":"SubagentStart","agent_type":"general-purpose"}' \
    "SubagentStart" "no" "yes"

# --- marker edge cases ---

validate "missing marker defaults to en" "none" \
    '{"hook_event_name":"UserPromptSubmit"}' \
    "UserPromptSubmit" "no" "yes"

validate "unknown marker defaults to en" "fr" \
    '{"hook_event_name":"UserPromptSubmit"}' \
    "UserPromptSubmit" "no" "yes"

validate "marker with whitespace/newline" "zh-cn
" \
    '{"hook_event_name":"UserPromptSubmit"}' \
    "UserPromptSubmit" "yes" "yes"

# --- robustness ---

validate "empty stdin falls back to default event" "en" "" "UserPromptSubmit" "no" "yes"

# Missing rules files fail open with empty output
MISSING="$(mktemp -d)"
cp "$HOOK" "$MISSING/inject-style-rules.sh"
out="$(printf '{}' | bash "$MISSING/inject-style-rules.sh")"
check "missing rules file -> empty output, exit 0" "" "$out"
rm -rf "$MISSING"

MISSING_ZH="$(mktemp -d)"
cp "$HOOK" "$MISSING_ZH/inject-style-rules.sh"
cp "$(dirname "$HOOK")/style-rules-en.md" "$MISSING_ZH/"
printf 'zh-cn' > "$MISSING_ZH/style-rules.lang"
out="$(printf '{}' | bash "$MISSING_ZH/inject-style-rules.sh")"
check "zh mode with missing zh file -> empty output" "" "$out"
rm -rf "$MISSING_ZH"

# Plain-text stdout JSON contains no raw newlines (single JSON object rule)
out="$(printf '{"hook_event_name":"UserPromptSubmit"}' | bash "$HOOK")"
lines="$(printf '%s' "$out" | wc -l | tr -d ' ')"
check "single-line JSON output (repo dir, no marker -> en)" "0" "$lines"

# --- argument overrides marker ---

validate "arg zh-cn overrides en marker" "en" \
    '{"hook_event_name":"UserPromptSubmit"}' \
    "UserPromptSubmit" "yes" "yes" "zh-cn"

validate "arg en overrides zh-cn marker" "zh-cn" \
    '{"hook_event_name":"UserPromptSubmit"}' \
    "UserPromptSubmit" "no" "yes" "en"

echo ""
echo "Results: $PASS passed, $FAIL failed"
exit "$FAIL"
