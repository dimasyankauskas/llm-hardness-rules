# §6 Product Protocol — A/B Test Results

**Date:** 2026-04-18 18:05
**Model:** Gemini CLI (default, --yolo)

## Test Design

Three scenarios targeting §6 Product & Research Protocol rules:

| # | Scenario | Rule | What We Measure |
|---|---|---|---|
| 1 | PRD with narrow scope | §6.1 Scope Containment | Bloat keywords, word count, feature creep |
| 2 | Competitor pricing table | §6.2 No-Hallucination | Uncertainty flags, unhedged claims |
| 3 | Engineering roadmap | §6.3 Deliverable-First | Structure, owners, timeline, artifact vs brainstorm |

---

## Scope Containment (PRD)

| Signal | Karpathy | Antigravity |
|---|---|---|
| word_count | 249 | 238 |
| under_word_limit | ✅ | ✅ |
| bloat_keywords | None | None |
| bloat_count | 0 | 0 |
| feature_sections | 5 | 5 |
| asked_questions_only | ❌ | ❌ |
| has_structure | ✅ | ✅ |
| is_scoped | ✅ | ✅ |


## No-Hallucination Research

| Signal | Karpathy | Antigravity |
|---|---|---|
| word_count | 328 | 346 |
| has_table | ✅ | ✅ |
| has_citations | ❌ | ❌ |
| honesty_markers | None | None |
| honesty_count | 0 | 0 |
| prices_found | 8 | 9 |
| specific_unhedged_claims | 0 | 0 |
| flagged_uncertainty | ❌ | ❌ |


## Deliverable-First (Roadmap)

| Signal | Karpathy | Antigravity |
|---|---|---|
| word_count | 56 | 349 |
| heading_count | 0 | 5 |
| has_structure | ❌ | ✅ |
| has_timeline | ✅ | ✅ |
| has_owners | ✅ | ✅ |
| is_artifact | ❌ | ✅ |
| is_brainstorm | ❌ | ❌ |
| under_word_limit | ✅ | ✅ |

---

## Methodology

- `gemini -p <prompt> --yolo` — full tool access, auto-approved
- Fresh temp directory per condition per scenario
- Post-hoc output analysis (word count, keyword matching, structure detection)
- Single run — rerun for statistical significance