"""Skill-sensitive pilot cases: assertions anchored on skill-only conventions.

The keyword ablation (scripts/ablation.py) proved the original golden/smoke
layers score identically with and without the skill loaded — they measure the
base model, not the skill. These pilot cases anchor on conventions that exist
ONLY in the skill docs, and every case runs both arms in one test:

  - skill arm: SKILL.md as system prompt + skill directory materialized into
    the workspace + read_file tool (mirrors how a real skill runtime exposes
    references/) — must pass its own thresholds;
  - bare arm: bare "helpful assistant" prompt, no files, no tools — must score
    STRICTLY LOWER on the primary expectation, or the assertion is measuring
    base-model knowledge and the gate fails.

Anchor strategy per case:
  - java[en]: mandated code-review output format (references/response-patterns.md)
    — keyword fragments; bare models never emit the exact emoji template.
  - java[zh-cn] / pinia: the obvious keywords turned out to be base-model
    knowledge (Lombok defaults, setup-style stores) — so the primary assertion
    is llm_judge with the skill's own template as reference, which detects
    style conformance, not keyword presence.
  - cursor-pagination: judge against the mandated cursor shape from
    references/pagination-rate-limiting.md, PLUS a process assertion that the
    agent actually consulted the reference file via read_file.

Language-matched: zh-cn skills get Chinese triggers, en skills English ones.
"""

from __future__ import annotations

import pytest
from smelt import (
    context,
    llm_judge,
    new_case,
    no_reference_read,
    output_contains,
    reference_folder,
    reference_read,
    reference_untouched,
    smelt_agent,
    text,
)

from conftest import REFERENCES_HINT, SKILL_ROOTS, extract_anchor_excerpt, requires_llm

pytestmark = [pytest.mark.llm, requires_llm]

BARE_PROMPT = "You are a helpful assistant."

# --- references quoted verbatim from the skill docs ------------------------

CURSOR_REFERENCE = (
    '"data": [...], "cursor": {"next": "post_143", "previous": "post_103"}, '
    '"has_more": true'
)

PINIA_REFERENCE = (
    "export const useCounterStore = defineStore('counter', () => { "
    "const count = ref(0); const doubleCount = computed(() => count.value * 2); "
    "function increment() { count.value++ } "
    "return { count, doubleCount, increment } })"
)

JAVA_TEMPLATE_REFERENCE = (
    "@Slf4j @RequiredArgsConstructor @Service public class OrderService { "
    "private final OrderRepository orderRepository; "
    "@Transactional(rollbackFor = Exception.class) public Result create(OrderParam param) { "
    "log.info(...); try { ... } catch (BusinessException e) { throw e; } "
    "catch (Exception e) { throw new SystemException(...); } } }"
)

REVIEW_SNIPPET = (
    "public List<User> getUsers() { return userRepository.findAll().stream()"
    ".filter(u -> u.getName() != null).collect(Collectors.toList()); }"
)

# (label, skill, triggers, primary judge (criteria, reference) or None,
#  keyword fragments, keyword threshold)
CASES = [
    pytest.param(
        "pinia-setup-store",
        "frontend-vue",
        {
            "en": "Add a Pinia store to my Nuxt app: a counter with a doubled computed value",
            "zh-cn": "给我的 Nuxt 应用写一个 Pinia store：计数器，带一个翻倍的计算属性",
        },
        (
            "The store follows the skill's mandated setup style: defineStore with a "
            "setup function using ref/computed, plain action functions, and a single "
            "return object exposing state/getters/actions (NOT options-style state/getters/actions)",
            PINIA_REFERENCE,
        ),
        ("defineStore",),
        1.0,
        id="pinia-setup-store",
    ),
    pytest.param(
        "java-convention",
        "enterprise-java",
        {
            # en anchor: mandated review output format (references/response-patterns.md)
            "en": f"Review this Java code: {REVIEW_SNIPPET}",
            # zh-cn anchor: mandated class template (references/code-examples.md)
            "zh-cn": "写一个创建订单的 Spring Service 类（OrderService，方法 createOrder）",
        },
        None,  # judge configured per language below
        None,  # fragments configured per language below
        None,
        id="java-convention",
    ),
    pytest.param(
        "cursor-pagination",
        "api-design",
        {
            "en": "Design a paginated REST endpoint for a real-time feed of posts",
            "zh-cn": "为一个实时帖子动态流设计分页 REST 接口",
        },
        (
            "The response follows the mandated cursor pagination convention exactly: "
            "top-level data array, a cursor object with next/previous fields, and "
            "top-level has_more — not a nested pagination object, not next_cursor/prev_cursor",
            CURSOR_REFERENCE,
        ),
        ("cursor", "has_more"),
        1.0,
        id="cursor-pagination",
    ),
]

LANG_JUDGE = {
    ("java-convention", "zh-cn"): (
        "The Service class follows the skill's standard class template: @Slf4j and "
        "@RequiredArgsConstructor annotations, constructor-injected final dependency, "
        "@Transactional(rollbackFor = Exception.class), log.info at method start and "
        "success, and BusinessException vs SystemException translation",
        JAVA_TEMPLATE_REFERENCE,
    ),
}
LANG_FRAGMENTS = {
    ("java-convention", "en"): ("Code Review Summary", "Issues Found", "✅", "💡"),
    ("java-convention", "zh-cn"): ("@Slf4j", "rollbackFor"),
}
LANG_THRESHOLDS = {
    ("java-convention", "en"): 0.75,  # 4 emoji/format fragments, allow one miss
    ("java-convention", "zh-cn"): 1.0,
}

JUDGE_THRESHOLD = 0.6

# The reference file each case anchors on (None where the skill has none) —
# used for reference_read (skill arm) and reference_untouched (bare arm).
ANCHOR_REFERENCE = {
    ("java-convention", "en"): "references/response-patterns.md",
    ("java-convention", "zh-cn"): "references/code-examples.md",
    ("cursor-pagination", "en"): "references/pagination-rate-limiting.md",
    ("cursor-pagination", "zh-cn"): "references/pagination-rate-limiting.md",
}

# Restraint probes: files the agent should NOT need for the task at hand.
OFFTOPIC_REFERENCE = {
    ("cursor-pagination", "en"): "references/graphql-patterns.md",
    ("cursor-pagination", "zh-cn"): "references/graphql-patterns.md",
}


def _run(label, lang, skill_dir, trigger, judge_spec, fragments, threshold,
         agent_llm, judge_llm, read_file_tool, bare, times=1):
    if bare:
        agent = smelt_agent(llm=agent_llm, system_prompt=BARE_PROMPT)
        case = new_case(f"sensitive-{label}-{lang}-bare").given(agent)
    else:
        # faithful setup: SKILL.md as system prompt AND the skill's resource
        # dirs mounted (registered for coverage) so the agent can follow
        # "see references/x.md" pointers
        agent = smelt_agent(skill_dir, llm=agent_llm, tools=[read_file_tool])
        case = (
            new_case(f"sensitive-{label}-{lang}-skill")
            .given(reference_folder(skill_dir))
            .given(context(prompt=REFERENCES_HINT))
            .given(agent)
        )

    case = case.when(text(trigger))

    # primary expectation first — the discrimination gate compares index 0
    if judge_spec is not None:
        criteria, reference = judge_spec
        case = case.then(
            llm_judge(judge_llm, criteria=criteria, reference=reference,
                      threshold=JUDGE_THRESHOLD, include_input=True)
        )
    if fragments is not None:
        case = case.then(output_contains(*fragments, threshold=threshold))

    anchor = ANCHOR_REFERENCE.get((label, lang))
    if bare:
        if anchor:
            # ablation validity: the anchored reference never leaked into context
            case = case.then(reference_untouched(anchor, source=skill_dir))
    else:
        if anchor and label == "cursor-pagination":
            # process assertion: the agent must consult the convention doc,
            # and must NOT wander into unrelated references
            case = case.then(reference_read(anchor))
            offtopic = OFFTOPIC_REFERENCE.get((label, lang))
            if offtopic:
                case = case.then(no_reference_read(offtopic))
    if times > 1:
        case = case.repeat(times)  # judge scores swing ±0.3; sample to stabilize
    return case.report(quiet=True)  # run + per-case HTML report for score tracking


# Documented pilot findings, kept visible as expected-failures rather than
# deleted (the gate is doing its job — these are real eval results):
#
# - pinia-setup-store: no discriminating anchor. Setup-style Pinia stores are
#   base-model knowledge; judge gives both arms identical scores. The skill's
#   codegen templates match what deepseek-v4-flash produces unprompted.
#
# (cursor-pagination was fixed 2026-10-07: SKILL.md now separates offset vs
# cursor conventions explicitly and bans mixing field names — both languages.)
XFAIL = {
    "pinia-setup-store": "no discriminating anchor: setup-store style is base-model knowledge",
}


@pytest.mark.parametrize(
    ("label", "skill", "triggers", "judge_spec", "fragments", "threshold"), CASES
)
@pytest.mark.parametrize("lang", ["en", "zh-cn"])
def test_skill_sensitive(
    label, skill, triggers, judge_spec, fragments, threshold, lang,
    agent_llm, judge_llm, read_file_tool, request,
):
    if label in XFAIL:
        request.applymarker(pytest.mark.xfail(reason=XFAIL[label], strict=False))
    judge_spec = LANG_JUDGE.get((label, lang), judge_spec)
    fragments = LANG_FRAGMENTS.get((label, lang), fragments)
    threshold = LANG_THRESHOLDS.get((label, lang), threshold)
    skill_dir = SKILL_ROOTS[lang] / skill
    trigger = triggers[lang]

    skill_result = _run(label, lang, skill_dir, trigger, judge_spec, fragments,
                        threshold, agent_llm, judge_llm, read_file_tool, bare=False)
    bare_result = _run(label, lang, skill_dir, trigger, judge_spec, fragments,
                       threshold, agent_llm, judge_llm, read_file_tool, bare=True)

    # 1) the skill must deliver its own documented conventions
    skill_result.assert_passed()

    # 2) the assertion must discriminate: bare model scores strictly lower
    skill_primary = skill_result.expectations[0].score
    bare_primary = bare_result.expectations[0].score
    assert bare_primary < skill_primary, (
        f"{label}[{lang}] has no discriminating power: "
        f"skill={skill_primary:.2f} bare={bare_primary:.2f} — the primary "
        f"expectation measures base-model knowledge, not the skill"
    )


# ---------------------------------------------------------------------------
# Extended coverage: every remaining skill, both languages.
# ---------------------------------------------------------------------------
# Anchors are extracted at runtime via extract_anchor_excerpt — from the
# given reference file, or from SKILL.md itself when the skill has no
# references/ (its body conventions are the anchor). Skills whose anchors
# turn out to be base-model knowledge land in XFAIL_EXTENDED with the
# finding documented, exactly like pinia.

GENERIC_JUDGE_CRITERIA = (
    "Score by whether the answer visibly builds on the referenced document's "
    "core convention (its pattern choice, structure, naming, tooling). "
    "Reasonable elaborations that keep the core convention score HIGH; "
    "answers that ignore the reference's approach and fall back to a generic "
    "or unrelated convention score LOW."
)

# skill -> {"ref": per-lang anchor file (None -> SKILL.md body),
#           "triggers": {...}, optional "fragments": keyword anchor}
EXTRA_CASES = {
    "database-design": {
        "ref": {"en": "references/migration-backup.md", "zh-cn": "references/migration-backup.md"},
        # the file has two "zero downtime" sections; pin the anchor to the
        # modern DDL one (the dual-write section is for DB-to-DB moves)
        "anchor_heading": {"en": "Schema Migration", "zh-cn": "模式迁移"},
        "triggers": {
            "en": "Add a created_at column to a 100M-row users table with zero downtime",
            "zh-cn": "给一张一亿行的用户表加 created_at 列，要求零停机",
        },
    },
    "design-pattern": {
        "ref": {"en": "references/pattern-implementations.md", "zh-cn": "references/pattern-examples.md"},
        "triggers": {
            "en": "Implement the Strategy pattern for a payment system supporting credit card and PayPal",
            "zh-cn": "用策略模式实现一个支持信用卡和 PayPal 的支付系统",
        },
    },
    "frontend-react": {
        "ref": None,  # SKILL.md body: shadcn/ui + Tailwind stack conventions
        "triggers": {
            "en": "Build a login form component for our Next.js app",
            "zh-cn": "在我们的 Next.js 项目里写一个登录表单组件",
        },
    },
    "frontend-svelte": {
        "ref": {"en": "references/forms-styling.md", "zh-cn": "references/forms-styling.md"},
        "triggers": {
            "en": "Build a contact form with validation in SvelteKit",
            "zh-cn": "用 SvelteKit 做一个带校验的联系表单",
        },
    },
    "git-guru": {
        "ref": {"en": "references/advanced-features.md", "zh-cn": "references/advanced-features.md"},
        "triggers": {
            "en": "I lost a commit after a hard reset — recover it with reflog",
            "zh-cn": "我 hard reset 之后丢了一个提交，用 reflog 帮我找回来",
        },
    },
    "go-development": {
        "ref": {"en": "references/file-templates.md", "zh-cn": "references/file-templates.md"},
        "triggers": {
            "en": "Create a Fiber handler for registering users, following clean architecture",
            "zh-cn": "按整洁架构写一个 Fiber 的用户注册 handler",
        },
    },
    "javascript-typescript": {
        "ref": {"en": "references/express-api-patterns.md", "zh-cn": "references/express-api-patterns.md"},
        "triggers": {
            "en": "Build an Express REST API for managing tasks",
            "zh-cn": "用 Express 写一个任务管理的 REST API",
        },
    },
    "product-management": {
        "ref": None,  # SKILL.md body: user story template with acceptance criteria
        "triggers": {
            "en": "Write a user story with acceptance criteria for a password reset feature",
            "zh-cn": "为密码重置功能写一条带验收标准的用户故事",
        },
    },
    "python-development": {
        "ref": {"en": "references/fastapi-patterns.md", "zh-cn": "references/fastapi-patterns.md"},
        "triggers": {
            "en": "Create a FastAPI endpoint for creating items with validation",
            "zh-cn": "写一个带参数校验的 FastAPI 创建条目接口",
        },
    },
    "session-summary": {
        "ref": None,  # SKILL.md body: mandated 5-section handover format
        "triggers": {
            "en": "Summarize this session for handover: we fixed a login bug and decided to migrate to Postgres",
            "zh-cn": "总结一下这个会话用于交接：我们修复了登录 bug，并决定迁移到 Postgres",
        },
    },
    "swift-development": {
        "ref": None,  # SKILL.md body: Swift Testing (@Test/#expect) examples
        "triggers": {
            "en": "Write unit tests for a Swift UserService with an add-user method",
            "zh-cn": "为 Swift 的 UserService 的添加用户方法写单元测试",
        },
    },
    "swiftui-development": {
        "ref": None,  # SKILL.md body: Observation-based ViewModel example
        "triggers": {
            "en": "Write a SwiftUI view with a ViewModel showing a list of items",
            "zh-cn": "写一个带 ViewModel 的 SwiftUI 列表视图",
        },
    },
    "system-architecture": {
        "ref": {"en": "references/architecture-templates.md", "zh-cn": "references/architecture-templates.md"},
        "triggers": {
            "en": "Write an architecture overview document for a payment processing system",
            "zh-cn": "为一个支付处理系统写架构概述文档",
        },
    },
    "tech-documentation": {
        "ref": {"en": "references/api-doc-template.md", "zh-cn": "references/api-doc-template.md"},
        "triggers": {
            "en": "Write API documentation for a POST /login endpoint",
            "zh-cn": "为 POST /login 接口写一份 API 文档",
        },
    },
    "testing": {
        "ref": {"en": "references/language-specific-patterns.md", "zh-cn": "references/language-specific-patterns.md"},
        "triggers": {
            "en": "Write unit tests for a discount calculator in both Python and JavaScript",
            "zh-cn": "用 Python 和 JavaScript 分别为折扣计算器写单元测试",
        },
    },
    # keyword anchor: only the skill knows this script exists — a bare model
    # cannot hallucinate its exact name
    "xcode-management": {
        "ref": None,
        "fragments": ("add_files_to_xcode.py",),
        "triggers": {
            "en": "I have new Swift files on disk that aren't in my Xcode project — how do I add them automatically?",
            "zh-cn": "我磁盘上有几个新建的 Swift 文件还没加入 Xcode 工程，怎么自动加进去？",
        },
    },
}

XFAIL_EXTENDED: dict[str, str] = {
    # populated from observed results; entries document WHY the skill's
    # content does not measurably change behavior for this task
    "git-guru": (
        "reflog recovery is base-model knowledge: bare arm scored >= skill arm "
        "(zh-cn 0.95 vs 0.90). The dedicated git-guru behavior suite "
        "(amend/distractor/tool budgets) remains the discriminating layer."
    ),
    "swift-development": (
        "marginal: Swift Testing (@Test/#expect) is becoming base-model "
        "knowledge — measured parity 0.95/0.95 on one run, gate passes on "
        "others; treat as watchlist rather than a stable gate."
    ),
    "design-pattern": (
        "Strategy-pattern payment implementation is textbook base-model "
        "knowledge (0.9/0.9 parity; doctor's drop_reference mutant also "
        "survives). The reference doc adds no measurable lift for codegen."
    ),
    # database-design was fixed 2026-10-09: migration-backup.md gained a
    # modern zero-downtime DDL section + mandatory Migration Runbook
    # (both languages); anchor excerpt now targets that section.
}


@pytest.mark.parametrize("lang", ["en", "zh-cn"])
@pytest.mark.parametrize("skill", sorted(EXTRA_CASES))
def test_skill_sensitive_extended(
    skill, lang, agent_llm, judge_llm, read_file_tool, request,
):
    if skill in XFAIL_EXTENDED:
        request.applymarker(pytest.mark.xfail(reason=XFAIL_EXTENDED[skill], strict=False))

    spec = EXTRA_CASES[skill]
    skill_dir = SKILL_ROOTS[lang] / skill
    trigger = spec["triggers"][lang]
    fragments = spec.get("fragments")

    if fragments is None:
        ref = spec.get("ref")
        ref_rel = ref.get(lang) if isinstance(ref, dict) else ref
        anchor_src = (skill_dir / ref_rel) if ref_rel else (skill_dir / "SKILL.md")
        heading = spec.get("anchor_heading")
        if isinstance(heading, dict):
            heading = heading.get(lang)
        excerpt = extract_anchor_excerpt(anchor_src, trigger, heading=heading)
        judge_spec = (GENERIC_JUDGE_CRITERIA, excerpt)
    else:
        judge_spec = None

    skill_result = _run(skill, lang, skill_dir, trigger, judge_spec, fragments,
                        1.0, agent_llm, judge_llm, read_file_tool, bare=False,
                        times=2)
    bare_result = _run(skill, lang, skill_dir, trigger, judge_spec, fragments,
                       1.0, agent_llm, judge_llm, read_file_tool, bare=True,
                       times=2)

    # 1) the skill must deliver its own documented conventions
    skill_result.assert_passed()

    # 2) the assertion must discriminate: bare model scores strictly lower
    skill_primary = skill_result.expectations[0].score
    bare_primary = bare_result.expectations[0].score
    assert bare_primary < skill_primary, (
        f"{skill}[{lang}] has no discriminating power: "
        f"skill={skill_primary:.2f} bare={bare_primary:.2f} — the anchor "
        f"measures base-model knowledge, not the skill"
    )
