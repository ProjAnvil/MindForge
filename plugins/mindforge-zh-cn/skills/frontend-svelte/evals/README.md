# frontend-svelte 评估用例

本 skill 的行为由 MindForge 中央评估套件（`evals/`，基于 smelt）验证：

- 静态 lint：`evals/tests/test_skill_lint.py`（全技能参数化）
- 行为冒烟（judge 评分）：`evals/tests/test_all_skills_smoke.py`
- 综合评估（行为 + 写作 + lint + Reference Coverage）：`evals/tests/test_evaluate_all.py`

运行方式：在 `evals/` 目录执行 `uv run pytest -k "frontend-svelte"`（行为用例需 SMELT_API_KEY）。
