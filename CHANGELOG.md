# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **User directory renamed to `~/.claude/MindForge/`** — MindForge is the
  product users install, so the user-facing directory no longer carries the
  internal zh-guard codename. Legacy installs are migrated transparently on
  the first hook run (before the kill-switch check, so disabled installs
  migrate too): the dictionary is copied and the OFF marker is *moved* —
  copying OFF would leave a stale copy that keeps the guard disabled after
  the user removes the new one. The migrated dictionary then goes through
  the normal @sync refresh, keeping user-added terms. The old
  `~/.claude/zh-guard/` directory is never deleted; users can clean it up
  manually. `ZH_GUARD_LEGACY_HOME` is available for testing/overrides.
- **Three-tier dictionary loading** — project-level terms now work like
  cspell's project dictionary. A `mindforge.zh-dict.tsv` placed at the
  project root (checked into the repo, shared with the team) is discovered
  by walking up from the hook's `cwd`, stopping at the first `.git`
  directory so files outside the project root never apply. Precedence:
  bundled → user → project (most specific wins); L1 display order is the
  reverse, so project terms surface first and broad tiers get cut first
  when the cap hits. All three hook execution points (L1 / L2 / file
  guard) merge all three tiers; the long-lived term-dict MCP process has
  no session cwd and keeps two. `tidy-dict` now covers the project tier
  when found from the working directory.
- **`zh_guard_common.py`** — dictionary loading, migration, exemptions and
  anti-loop state extracted from the three hook scripts (each had its own
  copy of the loader; a fourth copy for project-level logic was the
  signal to consolidate). Hooks are now thin fail-open shells; the common
  module has no import side effects. Deployment note: it must live next
  to the hook scripts.
- **File-write guard (new `inspect-file.py`, PreToolUse on Write|Edit|NotebookEdit)** —
  the Stop exit check only sees the assistant message; a model writing stiff
  translationese into README / docs / comments slipped through when the message
  just said "file written". The new hook inspects `tool_input.content` /
  `new_string` before the write lands, denies with rewrite guidance, and shares
  the dictionary, exemptions and fail-open design with the message layer.
  Deliberately narrow scope: .md / .markdown / .txt / .rst only (isolating
  comments inside code from strings/docstrings is not reliable yet); anti-loop
  state is independent from the Stop layer.
- **Sentence-level pattern entries** — dictionary gains a `re:` regex group for
  template phrasing the substring entries cannot catch: 值得注意的是、综上所述、
  需要指出的是、由于…的原因、进行了…（分析/修改/部署）. Backed by
  translationese-detection literature: function-word and syntactic patterns
  separate translated from original Chinese at 90%+ accuracy with cheap
  lexical features, no LLM needed.
- **Prompt-based Stop judge (Claude Code only)** — `hooks/claude-prompt-hooks.json`
  adds a `type: "prompt"` hook on Stop: when the dictionary misses, a small fast
  model judges whether `last_assistant_message` reads as natural Chinese and
  returns `{ok, reason}` (the prompt/agent verdict contract — `decision:"block"`
  silently fails there). The judge stands down when `stop_hook_active` is true to
  prevent chained blocks, and errs to `{ok: true}` when unsure. Cost: one small-
  model call per turn (~1-3 s). Lives in the Claude-only hooks file; zcode and
  Kimi never load it.
- Dictionary: four new translationese entries from live bad cases — 槽位→插槽 / slot,
  槽键→slot 的 key, 键-值关系→key-value, 已初步清楚→大致了解了 (`@sync` bumped to
  0.9.9 so installed dictionaries refresh on the next hook run).
- L1 injection gains a sixth rule against hard-compounded noun-phrase
  translations (slot key→「槽键」-style compounds) and rule 5 now names the
  公文腔 progress phrase 「大致了解了」 explicitly.
- The per-turn injection cap is raised from 30 to 50 entries. With 32+ bundled
  entries the old cap had already cut the 机器腔 group out of the injected
  list; the new entries would never have been visible to the model.

### Notes

- Cost re-measured (estimate backend): full-dictionary injection is now
  851 chars / 533 tokens per turn, dictionary marginal 279 tokens,
  net hook latency unchanged at ~25–30 ms.
- Tests 20 → 25: legacy-home migration (OFF honored before migration, OFF
  follows as a move, user terms survive via @sync), three-tier discovery (project override, .git boundary,
  display order, file-guard pickup), file-guard behaviors (deny/clean/suffix-gate/
  quote-exemption/anti-loop/Edit coverage), sentence-pattern blocking, and
  judge-config guards ($ARGUMENTS, stop_hook_active, ok/reason contract,
  manifest wiring).

## [0.9.7] - 2026-10-20

### Fixed

- **zcode dead hook registrations** — zcode supports only 7 hook events and has no
  SubagentStart/SubagentStop, so the plugin shipped two never-firing registrations
  that zcode flagged as dead config on every startup. Hooks are now split per
  platform: `hooks/hooks.json` keeps only events all platforms support
  (SessionStart / UserPromptSubmit / Stop); the Claude-only subagent events moved
  to `hooks/subagent-hooks.json`, declared via the `hooks` field of
  `.claude-plugin/plugin.json` (merged with auto-discovery, so Claude Code
  behavior is unchanged).
- **L2 Stop contract on zcode** — inspect.py used to emit `continue:false`, which
  on zcode means "allow the stop" and would have silently disabled the exit
  guard. It now detects `ZCODE_PLUGIN_ROOT` and emits zcode's `decision:"block"`
  + reason contract instead. Claude Code output is unchanged.

### Added

- `.zcode-plugin/plugin.json` — a zcode-specific manifest (preferred by zcode
  over the Claude one) without a `hooks` field, so zcode never loads the
  Claude-only subagent hook file; term-dict MCP is declared with
  `${ZCODE_PLUGIN_ROOT}`.
- Two tests in `test_zh_guard.py` (16 → 18 items): a zcode Stop contract test
  (decision:block, no continue:false, clean message passes) and a structure
  guard (hooks/hooks.json may only contain zcode-supported event names;
  subagent-hooks.json must hold exactly the two subagent events; manifests
  must declare/omit the hooks field accordingly).

### Notes

- **Version sync across the marketplace** — the previous push bumped the
  style-rules-zh-cn manifest but missed the marketplace entry (still 0.9.6),
  and the three sibling plugins (mindforge-en, mindforge-zh-cn, style-rules)
  trailed at 0.8.1. All four plugins and their marketplace entries are now
  aligned at 0.9.7.
- Verified against a real zcode install before the fix: the plugin loads, its
  hooks execute (session_start / user_prompt hook phases in the logs), and the
  term-dict MCP server connects via stdio — the only complaints were the two
  dead registrations. `hooks.enabled: true` in `~/.zcode/cli/config.json` is
  required only for user-level hooks, not for plugin hooks.

## [0.9.6] - 2026-10-19

> 说明：本版本号曾被一次发布的草稿占用（内容跑了题，release 与 tag 均已撤回），  
> 现在是用同一个版本号发出的正式内容。

### Added

- **`eval-zh-guard.py`** — cost evaluation of the whole scheme, not of the  
  tidy step: what does installing zh-guard actually cost per turn. Three arms,  
  so the numbers can be attributed:
  - **baseline** (nothing installed) — structurally 0, the zero point;
  - **empty dictionary** (hooks on, zero entries) — the 5 rule lines plus the  
    hook engine;
  - **full dictionary** — the above plus the dictionary's marginal cost.  
    Reports injection chars / tokens / entries, the per-turn marginal token cost  
    of the dictionary itself, accumulated tokens over N turns, end-to-end hook  
    latency with mean/min, and "net" latency with a bare-interpreter baseline  
    subtracted (interpreter startup dominates).
- **Interception cost** is measured separately, because it is the expensive  
  part and none of the above captures it: once a reply is blocked it is thrown  
  away and rewritten (2 × reply tokens) plus the rewrite instruction —  
  ≈364 tokens per block on the sample reply, ≈1092 tokens in a worst-case  
  10-minute window at the loop-protection cap of 3.
- `test_eval_zh_guard.py` (6 functions): baseline is zero and the interpreter  
  baseline is positive; an empty dictionary still costs rule tokens; the  
  dictionary has a measurable marginal cost; verdicts follow the dictionary  
  (empty passes everything, full blocks hits, quote mentions stay exempt);  
  timing splits startup from logic; interception cost arithmetic holds.

### Notes

- Measured locally (estimate tokenizer): injection 0 → 204 → 452 tokens per  
  turn across the three arms; the dictionary itself accounts for 248 of those.  
  Net hook latency is tens of milliseconds; end-to-end ~150 ms is almost all  
  interpreter startup.
- Priority implied by the numbers: reduce how often the model trips a term  
  (rule injection + term-dict MCP lookup) before trimming injection text; the  
  milliseconds are not worth optimising.
- `pip install tiktoken` gives true counts automatically (the tool detects and  
  reports the backend). Offline environments fall back to the documented  
  estimator — tiktoken downloads its BPE table on first use, which a  
  network-blocked sandbox will kill.

### Changed / Fixed

- `tidy-dict.py` parse: rows indented with a leading tab (common when editing  
  by hand) produced a bogus empty first column and were reported as broken  
  entries. Leading empty cells are now dropped.

## [0.9.5] - 2026-10-19

### Added

- **`tidy-dict.py` — dictionary tidy / lint tool.** Keeping a TSV readable by  
  hand was painful; this does it in one command:
  - aligns the three columns (padding before the tab, CJK counted as two  
    columns) while leaving comments and section headers untouched;
  - normalizes BOM / whitespace / line endings;
  - dedupes entries keeping the last occurrence, matching the runtime merge  
    semantics (user wins) and reporting each removal;
  - lints: invalid regex entries, rows missing the target column, duplicate  
    keys. `--check` exits non-zero for real errors (pre-commit friendly);  
    the read-only pass never modifies files; rendering is idempotent.
  - Defaults to both dictionaries (bundled + user); `--path` targets one.
- The bundled dictionary is reorganized into commented sections  
  (ML/evaluation, serving & distributed, robotics, LLM & token, stiff  
  technical metaphors, machine-register wording) and column-aligned.
- **New entries**: 锚定 → 锁定 / 以 X 为基准 (anchor; Chinese engineers do not  
  say it — 锚点 in frontend page anchors stays legitimate, noted),  
  遗留缺口 → 剩下的待办 (remaining gap), 结构性缺陷 → 设计上的问题  
  (structural defect).
- L1 gains rule 5 on register: write like a person — 剩下的待办 / 发现的问题,  
  not machine nouns lifted from English sentence shapes.
- User-added dictionary entries are now shown first in the L1 negative list,  
  so they are not squeezed out by the 30-entry cap.
- Tests: `test_tidy_dict.py` (5 functions, 14 checks) covering parse/dedupe,  
  error reporting, alignment idempotence, exit codes, and the real bundled  
  dictionary staying clean and tidied.

## [0.9.4] - 2026-10-19

### Changed

- **Dictionary rewrites: expected writings now read like real Chinese.**  
  The second column had drifted into machine-generated, literal-for-literal  
  renderings (`下一刀 → 下一个削减项`). Every entry is rewritten to wording  
  a Chinese technical writer would actually produce, and the English gloss  
  / rationale moved out of the target column into the notes column:
  - `幽灵词元/工人/节点/层/网络 → ghost token / ghost worker / ghost node /
    ghost layer / ghost network` (no established rendering → keep English,  
    per style rule #2), with the contextual alternatives in the notes  
    (e.g. 失联节点 for a lost node still counted by the cluster);
  - `下一刀 / 下一道砍 / re:第\s*\d+\s*刀 → 下一处可以精简的部分 /
    第 N 处可以精简的部分` (cut in cost/scope contexts means trim, not knife);
  - `死因 → 崩溃原因`, `钉死 → 敲定`, `令牌化 → token 化`,  
    `健全性检查 → 合理性检查`, `地面真值 → 真值`, and more.  
    Note-column guidance only: translations are suggestions, not literal  
    substitutions — rewrite the sentence.
- **Dictionary typo/json-safe writing rules documented** in the TSV header  
  and README: target column must be (1) wording a real Chinese writer uses,  
  (2) a drop-in replacement with no parentheticals, (3) English kept where  
  no established rendering exists, (4) community terms used when they exist.
- L2 rewrite instructions now say explicitly to rewrite the sentence using  
  the suggested wording rather than doing word-for-word substitution.

### Added

- **L1 injects the expected writing alongside the banned term**  
  (`「A→B」` pairs). Previously rule 4 promised the expected writing in  
  parentheses but only listed the terms — the model saw what to avoid and  
  not what to write. Regex entries are rendered human-readably  
  (`第\s*\d+\s*刀` → `第N刀`). Cap remains 30 entries; beyond that the  
  injection points at `term-dict` MCP's `lookup_term`.
- **Dictionary version sync**: the bundled dictionary carries a  
  `# @sync <version>` marker. Local copies lacking it (older installs) or  
  behind it are refreshed from the bundled one at the next hook run, with  
  user-added entries (keys absent from the bundled file) preserved. Without  
  this, a bad writing shipped to users could never be corrected — a locally  
  copied row shadows every later bundled fix. Users who want full control  
  keep their own keys or use `ZH_GUARD_DICT`.
- Tests: dictionary version sync (5 checks), L1 expected-writing pairs  
  (1 check); user-dictionary test adjusted to the new semantics  
  (user-only additions win; 16 test functions total).

## [0.9.3] - 2026-10-19

### Added

- **term-dict MCP server** (`hooks/term-dict-server.py`): the  
  terminology dictionary is now also queryable on demand via MCP —  
  a pull-mode knowledge layer complementing L1 (push injection) and  
  L2 (external detection). Pure-Python stdio implementation  
  (JSON-RPC 2.0, zero dependencies, system `python3`), registered in  
  the plugin manifest's `mcpServers` (context-mode-proven  
  `${CLAUDE_PLUGIN_ROOT}` pattern), so installing  
  `style-rules-zh-cn@mindforge` provides it with no extra setup.  
  Shares the merged dictionary (bundled + user, `re:` regex entries,  
  install-time migration) and re-reads it on every call.
- **Tools**: `lookup_term(query)` — bidirectional substring lookup  
  across direct-translation terms, expected writings, and notes  
  (case-insensitive); `check_text(text)` — pre-delivery self-check  
  with the same detection semantics as L2 (code/quote exemptions,  
  regex entries); `add_term(term, expected, note)` — appends to the  
  user dictionary (data flywheel; tab/newline sanitized; effective on  
  the next injected turn and immediately queryable).
- **Tests**: end-to-end stdio JSON-RPC suite driving the real server  
  (5 test functions, 21 assertions): handshake, tool listing, lookup  
  cases, check exemptions, flywheel add + immediate query/detect,  
  TSV-injection sanitization, unknown-tool error handling.
- **New dictionary entries**: 钉死 → 敲定/固定 (nail down),  
  范围守卫 → 作用域守卫 (scope guard).
- `setup-claude.sh` links the server file and prints the manual MCP  
  registration command for symlink deployments.

## [0.9.2] - 2026-10-19

### Added

- **Regex dictionary entries**: terms whose first column starts with  
  `re:` are matched as regular expressions, covering variable-number  
  patterns that literal substring matching cannot (e.g. 「第36刀」,  
  「第 128 刀」 → the whole 第N刀 class via `re:第\s*\d+\s*刀`).  
  Invalid regexes are skipped per entry (fail-open). L2 rewrite  
  instructions cite the actually matched text; L1's negative list  
  shows the pattern.
- **New dictionary entries**: 下一刀, 下一道砍 (next-cut  
  mistranslations in cost/scope contexts), and the regex entry above.

## [0.9.1] - 2026-10-19

### Changed

- **zh-guard merged into the style-rules-zh-cn plugin** (`./hooks`):  
  the standalone `zh-guard` plugin is removed; the dictionary  
  (`terminology.tsv`), L1 (`inject.py`), and L2 (`inspect.py`) now live  
  alongside the style-rules hook files, shipped and installed as one  
  plugin. Chinese users install `style-rules-zh-cn@mindforge` once and  
  get both.
- **Install-time dictionary migration** (all three channels):  
  the dictionary is maintained in the repo at `hooks/terminology.tsv`  
  (distribution source). On install it lands at  
  `~/.claude/zh-guard/terminology.tsv` — explicitly copied by  
  `setup-claude.sh`, or lazily on the first hook run for Claude  
  marketplace and Codex marketplace installs. Migration never  
  overwrites an existing user dictionary; at runtime the bundled and  
  user dictionaries merge (user entries win), so plugin updates  
  deliver new entries without losing user flywheel entries.
- `setup-claude.sh` Step 6 links `inject.py`, `inspect.py`, and  
  `terminology.tsv` into `~/.claude/hooks/`, migrates the dictionary,  
  and the settings merge now deduplicates on all three hook commands  
  (inject-style-rules.sh, inject.py, inspect.py).

### Fixed


- Test suite isolation: tests now set `ZH_GUARD_HOME` to a temp dir,
  so runs never touch the real `~/.claude/zh-guard/`.

## [0.9.0] - 2026-10-19

### Added

- **zh-guard plugin** (`./plugins/zh-guard`): Chinese translationese
  defense, ported from the production-verified WorkBuddy implementation
  (spec: zh-guard-spec-v2.0). Three layers, all fail-open:
  - L0 terminology dictionary (`terminology.tsv`, TSV data flywheel):
    24 entries — the original 15 plus ground-truth mistranslations
    (地面真实/地面真相/地面真值 → 真值), 机械胳膊/机器人胳膊 → 机械臂,
    死因 → 失败原因, 病症 → 症状, 引擎盖下 → 底层实现,
    健全性检查 → 合理性检查.
  - L1 `inject.py` (UserPromptSubmit): injects the terminology rules
    and the dictionary negative list every turn.
  - L2 `inspect.py` (Stop + SubagentStop): inspects
    `last_assistant_message`, blocks on dictionary hits with rewrite
    instructions (code blocks and quoted mentions exempted; anti-loop:
    same message once per session, max 3 blocks per 10-minute window).
- **User dictionary override**: entries in
  `~/.claude/zh-guard/terminology.tsv` merge with the plugin defaults
  (user entries win), surviving plugin updates. Kill switch:
  `ZH_GUARD_OFF=1` env or `~/.claude/zh-guard/OFF` file.
- 12-test suite covering injection format, blocking/passing, code and
  quote exemptions, fail-open, anti-loop, kill switch, and user-dict
  merge/override.

## [0.8.1] - 2026-10-16

### Added

- **Agents and skills as installable plugins**: two bundle plugins join
  the marketplace — `mindforge-en` (source `./plugins/mindforge-en`,
  9 agents + 19 skills, English) and `mindforge-zh-cn` (source
  `./plugins/mindforge-zh-cn`, 9 agents + 19 skills, Chinese). Bundles
  are generated from the `agents/<lang>` and `skills/<lang>` sources by
  `make sync-plugins` (evals stripped, shared `skills/scripts/`
  re-attached into the `xcode-management` skill). Plugin agents and
  skills are namespaced (`/mindforge-en:git-guru`,
  `mindforge-en:code-reviewer`) to avoid conflicts. The style-rules
  hook plugins remain separate so installing a bundle never
  double-injects writing rules.
- **README**: "Install as a Plugin" section now covers the bundles and
  namespacing.

### Changed

- All four plugins bumped to 0.8.1
  (`mindforge-en`, `mindforge-zh-cn`, `style-rules`, `style-rules-zh-cn`).

## [0.8.0] - 2026-10-16

### Added

- **Plugin distribution via marketplace manifest**
  (`.claude-plugin/marketplace.json`): the repo now doubles as a plugin
  marketplace, and both Claude Code and Codex read the same manifest
  (verified empirically: `codex plugin marketplace add` discovers the
  plugins). Install paths: `/plugin marketplace add
  ProjAnvil/MindForge` + `/plugin install <name>@mindforge`
  (Claude Code), or `codex plugin marketplace add` + `codex plugin add`
  (Codex). No symlinks or `settings.json` merging required.
- **Language variants as separate plugins**: `style-rules` (source
  `./plugins/style-rules`, English ASD-STE100 only, the default) and
  `style-rules-zh-cn` (source `./hooks`, Chinese + English). The
  injection script's default language changed from `zh-cn` to `en` to
  match the repo-wide default (`setup-claude.sh` defaults to `--lang=en`);
  the zh plugin passes `zh-cn` explicitly via its hook command. Each
  plugin is self-contained; `make sync-plugins` regenerates the
  `style-rules` variant from the `hooks/` single source of truth
  (`style-rules-zh-cn` lives in `hooks/` and needs no sync).
- **Codex adapter** (`.codex-plugin/hooks.json`): context-mode-style
  manifest at the repo root registering `SessionStart` and
  `UserPromptSubmit` hooks via `${PLUGIN_ROOT}` for whole-repo plugin
  installs. Plugin `hooks/hooks.json` commands now use
  `${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT}}` so the same manifest works
  under either harness. Note: end-to-end hook firing inside Codex could
  not be verified (usage limit); installation and discovery are
  verified.
- **README**: new "Install as a Plugin" section covering both
  harnesses and both language variants.

## [0.7.0] - 2026-10-16

### Added

- **Controlled-writing style rules hook** (`hooks/`): the Chinese
  controlled-writing spec and English ASD-STE100 rules are now injected
  into Claude Code context via hooks, covering both the main session and
  subagents. Injection language follows `setup-claude.sh`'s `--lang`
  parameter via a deploy-time marker file (`hooks/style-rules.lang`);
  priority is CLI argument > marker > `zh-cn` default:
  `en` injects the English rules only, `zh-cn` (also the default when
  the marker is missing or unknown) injects Chinese + English.
  `hooks/style-rules-zh.md` and `hooks/style-rules-en.md` are the
  per-language sources of truth; `hooks/inject-style-rules.sh` composes
  them per the marker and emits the
  `hookSpecificOutput.additionalContext` JSON (pure-bash JSON escaping,
  no jq/python dependency, Windows GitBash compatible, fails open when
  rule files are missing); `hooks/settings-hooks.json` holds the hook
  configuration fragment; `hooks/test-inject-style-rules.sh` covers all
  three events, both languages, and edge cases (12 tests).
  `setup-claude.sh` Step 6 links the hook files into `~/.claude/hooks/`,
  writes the language marker, removes the obsolete single-file
  `style-rules.md` link from earlier installs, and idempotently merges
  the hooks config into `~/.claude/settings.json` (python3 merge with
  soft fallback, foreign hook entries preserved). Events:
  `SessionStart` (session start, resume, clear, compact),
  `UserPromptSubmit` (every turn, compaction-resistant), `SubagentStart`
  (all subagent types, injected before the subagent's first prompt).

## [0.6.0] - 2026-10-14

### Added

- **Agent templates upgraded to the evaluation-informed standard**
  (`templates/agent-template-en.md` / `agent-template-zhcn.md`): new agents
  created via `make init-agent` now start from the same structure the 18
  shipped agents were optimized to in v0.5.1 — description guidance
  (specialty + "Use when ..." delegation trigger), Workflow, **Boundaries**
  (must-not-do / greenfield rule / hand-back conditions, marked
  must-fill), **Output Contract** (deliverable shape + final report),
  Error Handling, and a Quality Checklist. The old template's unfilled
  `[Action 1]`-style placeholder blocks were exactly what the v0.5.1 audit
  found fossilized inside agents/en/ios-developer.md; new agents no longer
  inherit that defect.

### Fixed

- **`make init-agent` never substituted the agent name**: the templates'
  `name: your-sub-agent-name` (and the Chinese template, whose sed pattern
  `你的智能体名称` did not occur in the file at all) never matched the
  Makefile's `your-agent-name` substitution — every generated agent kept
  the placeholder name. Both templates now use `your-agent-name` and the
  Makefile applies one substitution for both languages.
- `make init-agent` next-steps guidance now points at the description
  trigger sentence, the Boundaries/Output Contract sections, and the
  `smelt validate` quality check.

## [0.5.1] - 2026-10-14

### Fixed

Quality fixes for all 18 agent definitions, driven by the v0.5.0 evaluation
reports (writing review: boundaries 0.20–0.55, conciseness 0.30–0.70).
Subagent audit + full eval re-run: writing scores rose to 0.80–0.90 and
every agent now grades A (94.0–97.0 overall, previously 3 A + 15 B); lint
stays 100/A; all behavior and routing cases pass.

- **All 18 agents** gained a Boundaries / 边界与交接 section: must-not-do
  scope prohibitions plus explicit hand-back-to-main-agent conditions.
  Wording is greenfield-safe: in an empty workspace, agents proceed with
  stated assumptions instead of stalling on confirmation.
- **code-reviewer (both languages)**: rewritten to remove heavy duplication
  (principles/checklist/anti-patterns merged into one checklist; one
  feedback template); `tools:` no longer grants Edit/Write — the role is
  review-only, and Bash (zh) is restricted to running tests/builds.
- **ios-developer en**: removed unfilled template placeholder blocks; added
  real Error Handling guidance. **zh**: matching 错误处理 section added.
- **frontend-engineer (both)**: framework detection consolidated to one
  section; added hard limits (no backend/deployment) and an output contract.
- **golang/java-backend (both)**: consolidated guidance repeated 3+×;
  restored unique rules lost in consolidation (SOLID/god classes, externalized
  configuration, logging levels); added boundaries + output contracts.
- **java-unit-test / python-test-engineer (both)**: "never modify production
  code" boundary; output contracts made conditional on the workspace having
  a runnable build, so bare workspaces don't burn turns trying.
- **product-manager (both)**: owns the what/why, not the how — explicit
  must-nots (no architecture/implementation decisions) and structured
  deliverable contract (stories/PRD shape, scope in/out).
- **system-architect (both)**: merged duplicated principle/remember sections;
  must-nots (no code implementation, no unapproved changes); ADR/design-doc
  output contract.
- **python-test-engineer (both)**: removed api-design/database-design skill
  claims not present in frontmatter; removed all `~/.claude/docs/...` dead
  references across agents.

## [0.5.0] - 2026-10-14

### Added

- **Agent (subagent) evaluation** — `evals/` upgraded to Smelt v0.6.0, which
  treats Claude Code agent markdown as a first-class document kind, and the
  18 agent files in `agents/{en,zh-cn}` are now under the same evaluation
  pipeline as the skills:
  - **Static lint** (deterministic, CI-safe): `AgentFrontmatterCheck`
    (Claude Code load contract: name/description/tools/model validity,
    unknown-field detection) plus `DelegationCheck` (description routes
    correctly) over every agent file — all 18 score 100/A.
  - **Delegation routing cases** (LLM): a simulated main agent over each
    language's full roster must delegate specialty tasks to the right
    subagent (`delegates_to`), not steal a sibling's specialty
    (`no_delegation_to`, e.g. Python tests ≠ java-unit-test), and keep
    trivial Q&A for itself (`no_delegation`).
  - **Behavior cases** (LLM): every agent runs as a real subagent — body as
    system prompt, `tools:` frontmatter allowlist hard-enforced — with the
    six core Claude Code tools (Read/Grep/Glob/Bash/Edit/Write) backed by
    an isolated case workspace; assertions pin tool-call evidence (files
    actually written/read), not paraphrased final answers.
  - **Evaluate reports**: full `evaluate_agent` runs (behavior + agent
    writing review + lint + suggestions + adversarial routing probes) for
    all 18 agents, saved to `evals/reports/agent-<lang>-<name>.{md,json}`.
  - **Doctor-ready routing case files** per roster
    (`evals/cases/{en,zh-cn}_agent_routing_cases.py`) for on-demand
    mutation checks via `smelt doctor --agent`.
- README gained an Evaluation section; `make eval` / `make eval-llm` now
  cover agent lint/routing/behavior too.


### Fixed

- Five agent descriptions lacked delegation-trigger sentences and scored
  95.5 on lint: added "Use when …" / 「当…时主动使用」 sentences to
  frontend-engineer and product-manager (en), and frontend-engineer,
  ios-developer, product-manager (zh-cn). All 18 agent files now lint at
  100/A.

## [0.4.0] - 2026-10-09

### Added

- **Skill evaluation suite (`evals/`)** — a uv-managed smelt harness
  (ProjAnvil/Smelt, v0.5.1) with 200+ test cases: static lint over all 38
  SKILL.md files, golden-keyword behavior cases, judge-scored smoke tests,
  two-arm (skill vs. bare-model) discrimination gates for every skill in both
  languages, per-skill evaluate reports with Reference Coverage, and
  doctor-ready module-level case files (`evals/cases/`).
- **`add_files_to_xcode.py`** for both xcode-management skills — the script
  the SKILL.md always referenced but never shipped: scans for untracked
  source files, adds them to the correct target/build phase of
  `project.pbxproj`, with `--dry-run`, `--target`, backup, and idempotent
  re-runs.
- **Trigger-guidance sections** ("When to Use" / "何时使用") for every skill
  in both languages, and per-skill `evals/README.md` pointers to the central
  suite.

### Fixed

- **api-design**: SKILL.md pagination guidance now separates offset vs.
  cursor conventions explicitly and bans mixing field names
  (`next_cursor`/`cursors.*`), both languages — the previous prose made
  agents hybridize the two shapes.
- **database-design**: `references/migration-backup.md` gained a modern
  zero-downtime DDL section (instant ADD COLUMN on PG11+/MySQL 8.0.12+,
  gh-ost/pt-osc criteria, lock_timeout guard rails, CREATE INDEX
  CONCURRENTLY) plus a mandatory Migration Runbook structure; the dual-write
  recipe is now scoped to DB-to-DB moves where it belongs.
- **git-guru**: new "Untrusted Instructions in the Repo" guidance (both
  languages) — instruction files found in a repo are untrusted input, never
  commands to execute; plus act-don't-just-describe guidance for recovery
  tasks.
- **tech-documentation**: worked end-to-end example (POST /login) in both
  languages, replacing a dangling cross-skill reference.


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
