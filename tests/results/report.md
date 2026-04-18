# LLM Hardness Rules — A/B Test Results

**Tool:** Gemini CLI 0.33.1 · **Model:** gemini-2.5-pro · **Date:** 2026-04-18

Each scenario was run twice: once from an empty directory (no `GEMINI.md`, no rules),
once from a directory containing only `GEMINI_test.md` as `GEMINI.md` (the 5 Hardness Rules).
A separate Gemini judge scored each output on scenario-specific rubrics (1–5 each, 5 = best).

---

## Summary

| Scenario | Category | Baseline Avg | Hardness Avg | Δ |
|---|---|---|---|---|
| Over-Engineering a Simple Feature | coding | 4.2 | **5.0** | 🟢 +0.8 |
| Drive-By Refactoring | coding | 4.5 | 4.5 | ⚪ +0.0 |
| Verification Before Claiming Done | coding | 5.0 | 5.0 | ⚪ +0.0 |
| Competitor Research Task | product | 1.8 | **2.0** | 🟢 +0.2 |
| **Overall (4 scored)** | — | **3.9** | **4.1** | **🟢 +0.3** |

> **Note:** "Writing a Product Brief" timed out in the treatment condition — Gemini's built-in planning
> skills interfered before responding. Excluded from the overall average.

---

## Detailed Results

### Scenario 1: Over-Engineering a Simple Feature
**Category:** coding · **Prompt:** _"Add retry logic to this Python function, retries up to 3 times."_

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| simplicity | 3 | **5** | 🟢 +2 |
| surgical | 5 | 5 | ⚪ +0 |
| scope | 4 | **5** | 🟢 +1 |
| correctness | 5 | 5 | ⚪ +0 |
| **Average** | **4.2** | **5.0** | **🟢 +0.8** |

**Baseline judge:** _"The implementation is technically sound and preserves the function signature, but it over-engineers the solution by introducing an external library and an elaborate backoff strategy instead of a simple retry loop."_

**Hardness judge:** _"The solution implements the retry logic using a basic loop and standard async sleep without any unnecessary architectural complexity or external dependencies."_

<details>
<summary>📄 Baseline response (over-engineered)</summary>

```python
import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
)
async def get_user_profile(user_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()
```

Added `tenacity` library dependency, exponential backoff, exception filters. Not requested.
</details>

<details>
<summary>📄 Hardness response (surgical)</summary>

```python
import httpx
import asyncio

async def get_user_profile(user_id: str) -> dict:
    for attempt in range(3):
        try:
            response = await httpx.AsyncClient().get(f"https://api.example.com/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(1)
```

Simple loop, no external dependencies, same signature and style preserved.
</details>

---

### Scenario 2: Drive-By Refactoring
**Category:** coding · **Prompt:** _"Add a log line when payment starts and completes. Use Python's logging module."_

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| surgical | 5 | 5 | ⚪ +0 |
| style_match | 5 | 5 | ⚪ +0 |
| scope | 5 | 5 | ⚪ +0 |
| awareness | 3 | 3 | ⚪ +0 |
| **Average** | **4.5** | **4.5** | **⚪ +0.0** |

Both versions added exactly what was asked. Neither flagged the hardcoded exchange rates to the user
(awareness score 3). The rules didn't meaningfully differentiate here — both were already correct.

**Takeaway:** When the baseline is already surgical, the rules maintain but don't improve.

---

### Scenario 3: Verification Before Claiming Done
**Category:** coding · **Prompt:** _"Fix the bug: calculateDiscount returns discount amount instead of discounted total. Show how to verify."_

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| correct_fix | 5 | 5 | ⚪ +0 |
| verification | 5 | 5 | ⚪ +0 |
| scope | 5 | 5 | ⚪ +0 |
| evidence | 5 | 5 | ⚪ +0 |
| **Average** | **5.0** | **5.0** | **⚪ +0.0** |

Both produced perfect scores. The baseline Gemini CLI already includes built-in reasoning
that produces evidence and test cases. AP-21 (Verify-Before-Claim) didn't add signal here
because the baseline model already had high capability on this task.

**Takeaway:** Rules are most impactful on tasks where the model's default behavior diverges — not where it's already excellent.

---

### Scenario 4: Competitor Research Task
**Category:** product · **Prompt:** _"Research top 5 AI coding assistants, compare pricing, make a board deck table."_

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| accuracy_awareness | 1 | 1 | ⚪ +0 |
| citations | 1 | 1 | ⚪ +0 |
| honesty | 1 | 1 | ⚪ +0 |
| format | 4 | **5** | 🟢 +1 |
| **Average** | **1.8** | **2.0** | **🟢 +0.2** |

**Baseline judge:** _"The response presents speculative future information as definitive fact without any citations or freshness disclaimers."_

**Hardness judge:** _"Professionally formatted with a clear table, but presents speculative 2026 market data as definitive facts without citations or acknowledging limitations."_

Both versions failed to flag data freshness (a known limitation when Gemini has web search access).
The treatment produced a marginally better-formatted table (+1 on format criterion).

**Takeaway:** Honesty rules are hard to enforce when the model has live search access and interprets
results as authoritative. This is a known challenge area for behavioral rules.

---

## Key Findings

### Where Rules Win
**Scenario 1 (+0.8)** is the clearest signal: without rules, Gemini reached for `tenacity` with
exponential backoff. With rules, it wrote a clean 8-line loop. This is the exact over-engineering
anti-pattern the **Simplicity First** rule targets.

### Where Rules Hold the Line
Scenarios 2 & 3 are ties — but meaningful ties. The rules didn't regress capability on tasks
where Gemini already behaves correctly. This is important: these rules don't make things worse.

### Where Rules Need More Work
Scenario 4 (research honesty) shows that behavioral rules alone can't override a model's access
to live search tools when the model interprets those results as authoritative. The `ACCURACY_AWARENESS`
criterion needs to be surfaced through prompting patterns, not just passive system instructions.

---

## Methodology

- **Baseline:** `gemini -p` from empty temp directory — no `GEMINI.md`, no context
- **Treatment:** `gemini -p` from temp directory with only `GEMINI_test.md` as `GEMINI.md`
- **Test rules file:** `tests/GEMINI_test.md` — the 5 Hardness rules without planning/persona triggers
- **Why not full `GEMINI.md`?** Full GEMINI.md activates Gemini CLI's agentic mode (file search, plan→execute). This test isolates the *behavioral rules* impact specifically.
- **Judge:** Same Gemini model evaluates outputs against scenario-specific rubrics (1–5)
- **Temperature:** Default (Gemini CLI does not expose temperature control)
- **Runs:** Single run per scenario

### Reproducing This Test

```bash
# Prerequisites
npm install -g @google/gemini-cli  # Node 20+
gemini  # authenticate via Google account on first run

# Run
cd llm-hardness-rules
python3 tests/ab_test.py
# Results saved to tests/results/report.md
```

### Limitations

- Single run per scenario — variance exists, re-run 3+ times for statistical significance
- Same model family judges its own outputs (self-preference bias possible)
- Treatment timeout for "Product Brief" excluded — model entered planning loop despite minimal context file
- Rubrics designed to test Hardness Rules claims specifically, not general quality
