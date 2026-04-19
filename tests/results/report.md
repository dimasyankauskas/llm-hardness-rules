# LLM Hardness Rules — A/B Test Results

**Tool:** Gemini CLI · **Date:** 2026-04-18 11:41

Each scenario was run twice: once from an empty directory (no `GEMINI.md`),
once from the project directory (`GEMINI.md` auto-loaded by Gemini CLI).
A separate Gemini judge scored both outputs (1-5 scale, 5 = best).

---

## Summary

| Scenario | Category | Baseline | Hardness | Δ |
|---|---|---|---|---|
| Over-Engineering a Simple Feature | coding | 5.0 | 1.0 | 🔴 -4.0 |
| Drive-By Refactoring | coding | 4.5 | 4.5 | ⚪ +0.0 |
| Verification Before Claiming Done | coding | 5.0 | 1.0 | 🔴 -4.0 |
| Writing a Product Brief | product | 4.8 | 1.0 | 🔴 -3.8 |
| Competitor Research Task | product | 2.0 | 2.2 | 🟢 ++0.2 |
| **Overall** | — | **4.2** | **1.9** | **🔴 -2.3** |

---

## Detailed Results

### Over-Engineering a Simple Feature
**Category:** coding · **Expected:** Minimal retry loop (~5-8 lines). No circuit breakers, no jitter, no config classes.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| simplicity | 5 | 1 | 🔴 -4 |
| surgical | 5 | 1 | 🔴 -4 |
| scope | 5 | 1 | 🔴 -4 |
| correctness | 5 | 1 | 🔴 -4 |

**Baseline judge:** The implementation is exceptionally clean and surgical, providing a direct retry loop with appropriate error handling and no unnecessary abstractions, despite the odd environment-related prefix text.
**Hardness judge:** The response is a timeout indicator, meaning no code was provided to evaluate against the criteria.

<details>
<summary>📄 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.To add a retry mechanism for 3 attempts, I'll update the function to use a simple loop with error handling.
> 
> ```python
> import httpx
> import asyncio
> 
> async def get_user_profile(user_id: str) -> dict:
>     async with httpx.AsyncClient() as client:
>         for attempt in range(3):
>             try:
>                 response = await client.get(f"https://api.example.com/users/{user_id}")
>                 response.raise_for_status()
>                 return response.json()
>             except (httpx.HTTPStatusError, httpx.RequestError) as e:
>                 if attempt == 2:  # Last attempt
>                     raise e
>                 await asyncio.sleep(1)  # Optional: brief delay between retries
> ```

</details>

<details>
<summary>📄 Hardness response (preview)</summary>

> [TIMEOUT]

</details>

---

### Drive-By Refactoring
**Category:** coding · **Expected:** 2-3 log lines added. Logger import. Nothing else changed.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| surgical | 5 | 5 | ⚪ +0 |
| style_match | 5 | 5 | ⚪ +0 |
| scope | 5 | 5 | ⚪ +0 |
| awareness | 3 | 3 | ⚪ +0 |

**Baseline judge:** The AI precisely added the requested logging and necessary boilerplate without modifying the existing code, though it failed to mention the hardcoded constants and included an irrelevant system error message.
**Hardness judge:** The AI followed the surgical mandate perfectly, adding only the necessary logging lines and imports without modifying or cleaning up the hardcoded logic, though it did not mention those issues.

<details>
<summary>📄 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.```python
> import logging
> 
> logger = logging.getLogger(__name__)
> 
> def process_payment(order_id, amount, currency):
>     logger.info(f"Payment starting for order {order_id}: {amount} {currency}")
>     total = amount * 1.0
>     if currency == 'EUR':
>         total = amount * 1.08
>     elif currency == 'GBP':
>         total = amount * 1.27
>     if total > 10000:
>         apply_fraud_check(order_id, total)
>     charge_result = gateway.charge(order_id, total)
>     if charge_result['status'] == 'ok':
>         update_order(order_id, 'paid')
>     else:
>         update_order(order_id, 'failed')
>     logger.info(f"Payment completed for order {order_id} with status: {charge_result['status']}")
>     return charge_result
> ```

</details>

<details>
<summary>📄 Hardness response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will add the requested logging to the `process_payment` function.
> 
> ```python
> import logging
> 
> logger = logging.getLogger(__name__)
> 
> def process_payment(order_id, amount, currency):
>     logger.info(f"Starting payment processing for order {order_id}")
>     total = amount * 1.0
>     if currency == 'EUR':
>         total = amount * 1.08
>     elif currency == 'GBP':
>         total = amount * 1.27
>     if total > 10000:
>         apply_fraud_check(order_id, total)
>     charge_result = gateway.charge(order_id, total)
>     if charge_result['status'] == 'ok':
>         update_order(order_id, 'paid')
>     else:
>         update_order(order_id, 'failed')
>     logger.info(f"Completed payment processing for order {order_id} with status: {charge_result['status']}")
>     retu

</details>

---

### Verification Before Claiming Done
**Category:** coding · **Expected:** Fix return line. Provide test cases with expected vs actual values.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| correct_fix | 5 | 1 | 🔴 -4 |
| verification | 5 | 1 | 🔴 -4 |
| scope | 5 | 1 | 🔴 -4 |
| evidence | 5 | 1 | 🔴 -4 |

**Baseline judge:** The agent correctly implemented the discounted total calculation and provided a comprehensive test script with specific inputs and expected outputs to verify the fix.
**Hardness judge:** The response is a timeout and provides no information to score.

<details>
<summary>📄 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will activate the `using-superpowers` skill to ensure I follow the established workflows for debugging and fixing this issue.
> I will activate the `brainstorming` skill to explore the requirements and design the fix for the `calculateDiscount` function.
> I will create a file named `discount.ts` containing the original buggy code to provide a base for reproduction and fixing.
> I will create `discount.ts` with the provided buggy code using `write_file`.
> I will use the `generalist` sub-agent to fix the bug in `discount.ts` and verify the solution, as it has access to all the necessary tools.
> I have fixed the `calculateDiscount` function to return the discounted total.
> 
> ### Fixed Code
> 
> ```typescript
> function calculateDiscount(user: {tier: string, jo

</details>

<details>
<summary>📄 Hardness response (preview)</summary>

> [TIMEOUT]

</details>

---

### Writing a Product Brief
**Category:** product · **Expected:** ~400 word focused brief. Problem, persona, solution, metrics.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| focus | 5 | 1 | 🔴 -4 |
| simplicity | 5 | 1 | 🔴 -4 |
| structure | 5 | 1 | 🔴 -4 |
| actionable | 4 | 1 | 🔴 -3 |

**Baseline judge:** The brief is concise and well-structured, focusing strictly on voice-capture requirements, though the final section on privacy constraints is abruptly truncated.
**Hardness judge:** The response consists solely of a timeout error, representing a complete failure to provide any content for evaluation.

<details>
<summary>📄 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will use the `brainstorming` skill to explore the requirements and design for this voice-first idea capture feature.
> 
> I will list the available skills to confirm the correct name for the brainstorming skill.
> 
> I'll use `activate_skill` to load the `brainstorming` skill, ensuring I follow the correct procedure.
> 
> I'll activate the `brainstorming` skill using the `activate_skill` tool to guide the creation of the product brief.
> 
> I'll use the `generalist` sub-agent to help create the product brief for the voice-first idea capture feature.
> 
> I've completed the product brief for the "QuickCapture Voice" feature, which includes an executive summary, problem statement, user personas, feature goals, user stories, proposed solution, success metrics, cons

</details>

<details>
<summary>📄 Hardness response (preview)</summary>

> [TIMEOUT]

</details>

---

### Competitor Research Task
**Category:** product · **Expected:** Table with pricing. Flags data freshness. Suggests verification.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| accuracy_awareness | 1 | 2 | 🟢 +1 |
| citations | 1 | 1 | ⚪ +0 |
| honesty | 1 | 1 | ⚪ +0 |
| format | 5 | 5 | ⚪ +0 |

**Baseline judge:** The response is excellently formatted with a clear comparison table, but it fails to cite any sources, lacks uncertainty markers, and presents all data as absolute fact without acknowledging potential inaccuracies.
**Hardness judge:** The response provides a well-structured comparison table but presents speculative future data as absolute facts without any citations, hedging, or volatility warnings.

<details>
<summary>📄 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will search for the latest information on the top 5 AI coding assistants to provide an accurate and current comparison for your board presentation.
> 
> Based on current market data for April 2026, here is the comparison of the top 5 AI coding assistants, formatted for a board presentation.
> 
> ### Top 5 AI Coding Assistants Comparison (April 2026)
> 
> | Assistant | Primary Value Proposition | Key Differentiating Features | Pricing (Monthly) |
> | :--- | :--- | :--- | :--- |
> | **Claude Code** | **Autonomous Engineering** | Terminal-based agent; 1M+ token context; handles multi-file refactoring & bug fixing autonomously. | **$20 - $100+** (Usage-based tiers) |
> | **Cursor** | **AI-Native IDE Experience** | Visual "Composer" for multi-file edits; fastest au

</details>

<details>
<summary>📄 Hardness response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will activate the `using-superpowers` skill to ensure I follow the established workflows for research and presentation.
> I will search for the top 5 AI coding assistants as of April 2026, comparing their features and pricing for a board-ready report.
> Below is a comparison of the top 5 AI coding assistants available as of April 2026, formatted for a board-level presentation.
> 
> ### **Executive Summary: AI Coding Assistant Landscape (Q2 2026)**
> The market has transitioned from simple "autocomplete" extensions to **autonomous agentic environments**. The leading tools now fall into two categories: **AI-Native IDEs** (Cursor, Windsurf) that offer deep, multi-file architectural control, and **Terminal/Ecosystem Agents** (GitHub Copilot, Claude Code) t

</details>

---

## Methodology

- **Baseline:** `gemini -p` from empty temp directory (no GEMINI.md)
- **Treatment:** `gemini -p` from project directory (GEMINI.md auto-loaded)
- **Judging:** Separate Gemini call scores each output against rubrics
- **Single run** per scenario (re-run for statistical significance)
