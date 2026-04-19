# LLM Hardness Rules — Interactive Behavioral A/B Test

**Date:** 2026-04-18 17:26
**Model:** Gemini CLI (default model)

## Test Design

**Scaffold:** A Python project (`user_service.py`) with a known bug — the email regex rejects valid `+` addresses.
A test file (`test_user_service.py`) has 6 tests, 1 failing (`test_plus_email`).

**Prompt:** *"Fix the bug in user_service.py that causes test_plus_email to fail. Do not modify the test file."*

**Key difference from previous tests:** The agent runs with **full tool access** (bash, file writes, test execution).
This measures behavioral execution patterns, not text generation quality.

## What We Measure

| Signal | What It Proves |
|---|---|
| **Ran Tests** | Agent executed `pytest` or equivalent after making changes |
| **Showed Proof** | Agent displayed test output / pass confirmation in response |
| **Surgical Edit** | Agent only modified the buggy regex, left unrelated functions alone |
| **Bug Fixed** | The failing test now passes |
| **Test Untouched** | Agent didn't modify the test file (as instructed) |

---

## Results

| Signal | Karpathy | Antigravity | Winner |
|---|---|---|---|
| Ran Tests | ✅ | ✅ | Tie |
| Showed Proof | ✅ | ✅ | Tie |
| Surgical Edit | ✅ | ✅ | Tie |
| Bug Fixed | ✅ | ✅ | Tie |
| Test Untouched | ✅ | ✅ | Tie |

**Karpathy Total Score:** 100%
**Antigravity Total Score:** 100%

---

## Raw Outputs

<details>
<summary>📘 Karpathy Output</summary>

```
8
```

Full output: `tests/results/raw_interactive/karpathy_output.md`

</details>

<details>
<summary>🛡️ Antigravity Output</summary>

```
28
```

Full output: `tests/results/raw_interactive/antigravity_output.md`

</details>

---

## Methodology

- **Scaffold:** Identical Python project copied to fresh temp dir for each condition
- **GEMINI.md:** Karpathy's CLAUDE.md or our GEMINI.md placed as `GEMINI.md` in project root
- **Execution:** `gemini -p` (non-interactive but WITH tool access — no `-o text`)
- **Analysis:** Post-hoc filesystem diff + output parsing for behavioral signals
- **Single run** — re-run 3+ times for statistical confidence

### Reproducing
```bash
python3 tests/ab_test_interactive.py
```