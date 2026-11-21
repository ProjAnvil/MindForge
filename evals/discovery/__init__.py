"""MindForge L1 skill discovery suites built on Smelt 0.7.0."""

from __future__ import annotations

from pathlib import Path

from smelt import skill_catalog

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_ROOTS = {
    "en": PROJECT_ROOT / "skills" / "en",
    "zh-cn": PROJECT_ROOT / "skills" / "zh-cn",
}
DISTRACTOR_ROOTS = {
    "en": Path(__file__).resolve().parent / "distractors" / "en",
    "zh-cn": Path(__file__).resolve().parent / "distractors" / "zh-cn",
}
K = 5


def build_catalog(lang: str):
    """Build the fixed candidate pool for one language."""
    return skill_catalog(SKILL_ROOTS[lang], distractors=DISTRACTOR_ROOTS[lang], k=K)
