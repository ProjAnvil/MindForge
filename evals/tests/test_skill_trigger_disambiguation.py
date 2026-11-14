"""Deterministic guards against skill shadowing in the installed listing.

No API key needed. Two surfaces matter:
  * the trigger clause must claim a proper noun no sibling claims;
  * the full listing text must not reuse that noun in a sibling.
arXiv 2605.24050v2 calls the resulting selection failure skill shadowing.
The real model run lives in test_skill_full_library_routing.py.
"""

from __future__ import annotations

import re
from functools import lru_cache

import pytest

from conftest import PROJECT_ROOT, SKILL_ROOTS, skill_description

LANGS = ("en", "zh-cn")

# Latin anchors work in both languages: proper nouns stay untranslated in the
# Chinese descriptions. CJK anchors only apply to zh-cn. Splitting them keeps
# the leak matrix free of vacuous cases.
LATIN_ANCHORS: dict[str, tuple[str, ...]] = {
    "api-design": ("GraphQL", "API versioning", "idempotency", "OpenAPI",
                   "RESTful API", "API documentation"),
    "database-design": ("ER diagram", "normalization", "sharding"),
    "design-pattern": ("GoF", "SOLID", "code smells"),
    "enterprise-java": ("Spring Boot", "microservices"),
    "frontend-react": ("React", "Next.js", "shadcn/ui"),
    "frontend-svelte": ("Svelte", "SvelteKit", ".svelte", "shadcn-svelte"),
    "frontend-vue": ("Vue", "Nuxt", "Pinia", "shadcn-vue"),
    "git-guru": ("interactive rebase", "worktree", "reflog", "bisect"),
    "go-development": ("Fiber", "Cobra", "GORM"),
    "javascript-typescript": ("ES6+", "JavaScript", "TypeScript", "Node.js"),
    "product-management": ("PRD", "MVP", "user story", "competitive analysis"),
    "python-development": ("FastAPI", "Django", "Flask"),
    "session-summary": ("handover document",),
    "swift-development": ("Swift 6", "data race"),
    "swiftui-development": ("SwiftUI", "NavigationStack", "SwiftData"),
    "system-architecture": ("architecture decision record", "distributed systems"),
    "tech-documentation": ("deployment guides", "operations manuals"),
    "testing": ("TDD/BDD", "mocking", "test automation"),
    "xcode-management": ("Xcode", ".pbxproj"),
}

CJK_ANCHORS: dict[str, tuple[str, ...]] = {
    "api-design": ("幂等", "API 版本"),
    "database-design": ("ER 图", "分片"),
    "design-pattern": ("代码异味",),
    "enterprise-java": ("微服务",),
    "git-guru": ("交互式变基", "工作树"),
    "product-management": ("用户故事", "竞品分析"),
    "session-summary": ("交接文档", "会话总结"),
    "swift-development": ("数据竞争",),
    "system-architecture": ("架构决策记录", "分布式系统"),
    "tech-documentation": ("部署指南", "运维手册"),
    "testing": ("Mock 策略", "测试自动化"),
}

# Generic trigger phrases removed during the 2026-11-14 disambiguation pass.
# They describe a whole problem domain rather than one skill, so a request
# containing them can match several skills at once. Add new offenders here.
FORBIDDEN_GENERIC_PHRASES: dict[str, tuple[str, ...]] = {
    "en": (
        "building modern web applications",
        "TypeScript-based frontend architectures",
        "reactive frameworks",
        "type-safe component development",
        "building React/Node.js projects",
        "React, testing frameworks",
        "implementing RESTful APIs with Fiber",
        "writing API documentation",
        "creating architecture design documents",
        "planning data architecture",
    ),
    "zh-cn": (
        "构建现代 Web 应用",
        "基于 TypeScript 的前端架构",
        "响应式框架",
        "类型安全组件开发",
        "构建 React/Node.js 项目",
        "React、测试框架和最佳实践",
        "实现 RESTful API",
        "编写 API 文档",
        "创建架构设计文档",
        "规划数据架构",
    ),
}

TRIGGER_MARKERS = {
    "en": ("Use this skill when", "Use this skill for"),
    "zh-cn": ("使用此技能",),
}
TRIGGER_STOPS = {"en": ("Ideal for",), "zh-cn": ("适合",)}

# Claude Code caps one listing entry at 1536 chars and scales the whole listing
# to ~1% of the context window (200k * 1% ~ 2000 tokens ~ 8000 chars). CJK
# costs more per char, so zh-cn gets a tighter cap. These are ceilings, not a
# regression detector: current en=5987, zh-cn=2268 chars.
MAX_DESCRIPTION_CHARS = 1536
MAX_LISTING_CHARS = {"en": 8000, "zh-cn": 4000}

MANIFESTS = (
    PROJECT_ROOT / ".claude-plugin" / "marketplace.json",
    PROJECT_ROOT / "plugins" / "mindforge-en" / ".claude-plugin" / "plugin.json",
    PROJECT_ROOT / "plugins" / "mindforge-zh-cn" / ".claude-plugin" / "plugin.json",
)

_SKILL_CASES = [(lang, skill) for lang in LANGS for skill in LATIN_ANCHORS]
_ANCHOR_CASES = [
    (lang, skill, anchor)
    for lang in LANGS
    for skill in LATIN_ANCHORS
    for anchor in (
        LATIN_ANCHORS[skill]
        + (CJK_ANCHORS.get(skill, ()) if lang == "zh-cn" else ())
    )
]
_PHRASE_CASES = [
    (lang, phrase)
    for lang in LANGS
    for phrase in FORBIDDEN_GENERIC_PHRASES[lang]
]


def _anchors_for(lang: str, skill: str) -> tuple[str, ...]:
    latin = LATIN_ANCHORS[skill]
    return latin + (CJK_ANCHORS.get(skill, ()) if lang == "zh-cn" else ())


@lru_cache(maxsize=None)
def _disk_skills(lang: str) -> tuple[str, ...]:
    root = SKILL_ROOTS[lang]
    return tuple(sorted(p.name for p in root.iterdir() if (p / "SKILL.md").exists()))


@lru_cache(maxsize=None)
def _description(lang: str, skill: str) -> str:
    return skill_description(SKILL_ROOTS[lang] / skill)


@lru_cache(maxsize=None)
def _all_descriptions(lang: str) -> dict[str, str]:
    return {skill: _description(lang, skill) for skill in _disk_skills(lang)}


def _contains(text: str, anchor: str) -> bool:
    if any("\u4e00" <= char <= "\u9fff" for char in anchor):
        return anchor.lower() in text.lower()
    # Word boundaries stop "React" from matching "reactive" and "Svelte" from
    # matching "SvelteKit". The optional plural keeps "PRD" matching "PRDs".
    pattern = r"(?<!\w)" + re.escape(anchor) + r"s?(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _trigger_clause(description: str, lang: str) -> str:
    start, marker = -1, ""
    for candidate in TRIGGER_MARKERS[lang]:
        pos = description.find(candidate)
        if pos >= 0 and (start < 0 or pos < start):
            start, marker = pos, candidate
    if start < 0:
        return ""
    tail = description[start + len(marker):]
    for stop in TRIGGER_STOPS[lang]:
        tail = tail.split(stop)[0]
    return tail


@pytest.mark.parametrize("lang", LANGS)
def test_anchor_table_matches_disk(lang):
    assert set(LATIN_ANCHORS) == set(_disk_skills(lang)), (
        f"{lang}: anchor table is out of sync with skills/{lang}"
    )


@pytest.mark.parametrize("path", MANIFESTS)
def test_declared_skill_counts_match_disk(path):
    text = path.read_text(encoding="utf-8")
    counts = {int(n) for n in re.findall(r"(\d+)\s+(?:skills|个技能)", text)}
    assert counts, f"{path}: no skill count declared"
    assert counts == {len(_disk_skills("en"))}, (
        f"{path}: declares {counts}, disk has {len(_disk_skills('en'))}"
    )


def test_readme_declares_disk_skill_count():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    count = len(_disk_skills("en"))
    assert f"9 agents + {count} skills" in text


@pytest.mark.parametrize(("lang", "skill"), _SKILL_CASES)
def test_trigger_clause_has_exclusive_anchor(lang, skill):
    clause = _trigger_clause(_description(lang, skill), lang)
    assert clause, f"{lang}/{skill}: no trigger clause found"
    assert any(_contains(clause, anchor) for anchor in _anchors_for(lang, skill)), (
        f"{lang}/{skill}: trigger clause has no exclusive anchor: {clause!r}"
    )


@pytest.mark.parametrize(("lang", "skill", "anchor"), _ANCHOR_CASES)
def test_anchor_does_not_appear_in_sibling_descriptions(lang, skill, anchor):
    for sibling, text in _all_descriptions(lang).items():
        if sibling == skill:
            continue
        assert not _contains(text, anchor), (
            f"{lang}: {skill} anchor {anchor!r} leaks into {sibling}"
        )


@pytest.mark.parametrize(("lang", "phrase"), _PHRASE_CASES)
def test_generic_trigger_phrase_is_gone(lang, phrase):
    hits = [
        skill for skill in _disk_skills(lang)
        if _contains(_trigger_clause(_description(lang, skill), lang), phrase)
    ]
    assert hits == [], f"{lang}: generic phrase {phrase!r} is back in {hits}"


@pytest.mark.parametrize("lang", LANGS)
def test_description_budget(lang):
    descriptions = _all_descriptions(lang)
    for skill, text in descriptions.items():
        assert len(text) <= MAX_DESCRIPTION_CHARS, (
            f"{lang}/{skill}: {len(text)} chars exceeds per-skill cap"
        )
    total = sum(len(text) for text in descriptions.values())
    assert total <= MAX_LISTING_CHARS[lang], (
        f"{lang}: listing is {total} chars, ceiling is {MAX_LISTING_CHARS[lang]}"
    )


@pytest.mark.parametrize("lang", LANGS)
def test_plugin_copies_match_sources(lang):
    plugin_root = PROJECT_ROOT / "plugins" / f"mindforge-{lang}" / "skills"
    source_names = set(_disk_skills(lang))
    copy_names = {p.name for p in plugin_root.iterdir() if (p / "SKILL.md").exists()}
    assert copy_names == source_names, (
        f"{lang}: plugin skills differ; missing={source_names - copy_names}, "
        f"extra={copy_names - source_names}"
    )
    for skill in sorted(source_names):
        source = (SKILL_ROOTS[lang] / skill / "SKILL.md").read_bytes()
        copy = (plugin_root / skill / "SKILL.md").read_bytes()
        assert copy == source, f"{lang}/{skill}: plugin copy is out of sync"
