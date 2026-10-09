# swiftui-development eval cases

This skill's behavior is verified by MindForge's central eval suite (`evals/`, powered by smelt):

- Static lint: `evals/tests/test_skill_lint.py` (parametrized over all skills)
- Behavior smoke (judge-scored): `evals/tests/test_all_skills_smoke.py`
- Golden-keyword behavior: `evals/tests/test_golden_keywords.py`
- Full evaluation (behavior + writing + lint + Reference Coverage): `evals/tests/test_evaluate_all.py`

Run: `cd evals && uv run pytest -k "swiftui-development"` (behavior cases need SMELT_API_KEY).
