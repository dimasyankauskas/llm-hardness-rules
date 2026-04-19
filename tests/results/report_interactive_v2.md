# LLM Hardness Rules — A/B Test v2 (Hard Mode)

**Date:** 2026-04-18 17:35
**Model:** Gemini CLI (default, --yolo)

## Test Design

Three scenarios targeting rules that *differ* between Karpathy and Antigravity:

| # | Scenario | Rule Tested | What Makes It Hard |
|---|---|---|---|
| 1 | Multi-file deceptive bug | AP-22 Critic-Refiner | Obvious fix doesn't work; root cause is in a different file |
| 2 | Add feature to working codebase | Anti-Regression | Must not break 9 existing passing tests |
| 3 | Write a PRD (no code) | Non-Coding Coverage | Must stay focused, honest, structured — no bloat |

---

## Multi-File Deceptive Bug

| Signal | Karpathy | Antigravity |
|---|---|---|
| found_root_cause | ✅ | ✅ |
| config_modified | ✅ | ✅ |
| validator_modified | ❌ | ❌ |
| ran_tests | ✅ | ✅ |
| showed_proof | ❌ | ✅ |
| bug_fixed | ✅ | ✅ |


## Additive Feature (Anti-Regression)

| Signal | Karpathy | Antigravity |
|---|---|---|
| feature_added | ✅ | ✅ |
| existing_tests_pass | ✅ | ✅ |
| ran_tests | ✅ | ✅ |
| verified_existing | ❌ | ❌ |
| new_files | [] | [] |


## Product Task (PRD)

| Signal | Karpathy | Antigravity |
|---|---|---|
| word_count | 129 | 107 |
| line_count | 9 | 6 |
| bloat_count | 0 | 0 |
| honesty_count | 0 | 0 |
| has_structure | ❌ | ❌ |
| is_focused | ✅ | ✅ |

---

## Methodology

- `gemini -p <prompt> --yolo` — full tool access, auto-approved
- Fresh temp directory per condition per scenario
- Post-hoc filesystem analysis + output parsing
- Single run — rerun for statistical significance

### Reproducing
```bash
python3 tests/ab_test_interactive_v2.py
```