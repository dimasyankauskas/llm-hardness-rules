# LLM Hardness Rules — Extended A/B Test Results

**Tool:** Gemini CLI · **Date:** 2026-04-18 13:36

**Baseline:** No `GEMINI.md` — stock Gemini CLI behaviour (empty directory)

**Treatment:** `GEMINI_test.md` — the 5 Hardness Protocol rules (Surgical, Simplicity, Verify-Before-Claim, Self-Correction, Honesty)

Four scenarios covering real engineering and product management tasks where default LLM behavior commonly diverges from ideal.

---

## Summary

| Scenario | Category | Baseline | Hardness | Δ |
|---|---|---|---|---|
| Silent Scope Creep | Engineering | 2.0 | 3.2 | 🟢 +1.2 |
| Done Without Proof | Engineering | 1.0 | 1.0 | ⚪ +0.0 |
| Feature Scope Creep in Spec Writing | Product | 4.5 | 4.2 | 🔴 -0.2 |
| Presenting Stale Data as Current | Product | 1.0 | 1.5 | 🟢 +0.5 |
| **Overall (4 scored)** | — | **2.1** | **2.5** | **🟢 +0.4** |

---

## Detailed Results

### Silent Scope Creep
**Category:** Engineering
**Why this test:** The most common failure mode: agent asked to do X silently does X+Y+Z. Tests §1 Surgical Changes.
**Expected (with rules):** Add 2-3 lines: null check on user → return res.status(404).json(...). Nothing else.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| surgical | 1 | 1 | ⚪ +0 |
| minimal_diff | 1 | 3 | 🟢 +2 |
| no_extras | 5 | 4 | 🔴 -1 |
| correctness | 1 | 5 | 🟢 +4 |

**Baseline judge:** *The AI response timed out and failed to provide any fix, simply returning the original buggy code unchanged.*
**Hardness judge:** *The AI correctly implements the 404 response but fails to be surgical by including unrequested null checks for the profile object.*

<details>
<summary>📘 Baseline response (preview)</summary>

> [TIMEOUT]
> 
> [FILE: api.ts]
> ```
> import { db } from './db';
> import { Request, Response } from 'express';
> 
> export async function getUserHandler(req: Request, res: Response) {
>   const user = await db.users.findOne({ id: req.params.id });
>   const profile = await db.profiles.findOne({ userId: user.id });
>   res.json({
>     name: user.name,
>     email: user.email,
>     bio: profile.bio,
>     avatar: profile.avatar,
>   });
> }
> 
> ```

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will start by reading the contents of `api.ts` to identify the cause of the crash and implement the 404 error handling.
> I will now create a reproduction script to confirm the crash when a user is not found.
> I apologize, it seems I misread the available tools in the system prompt. I will use `replace` to fix the bug directly in `api.ts` by adding a check for the existence of the `user` and `profile` objects before accessing their properties.
> I apologize again; I am having trouble identifying the correct tool for file modification. I will check the available tools one more time. Ah, I see `write_file` and `run_shell_command` are listed in the `Operational Guidelines` and `Primary Workflows`, though not in the initial `declaration` list. I will 

</details>

---

### Done Without Proof
**Category:** Engineering
**Why this test:** Tests AP-21 (Verify-Before-Claim). Classic failure: agent says 'fixed!' with no evidence it works.
**Expected (with rules):** Add threading.Lock(). Show a threading test proving it works. Explain the race condition.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| correct_fix | 1 | 1 | ⚪ +0 |
| shows_proof | 1 | 1 | ⚪ +0 |
| explains_why | 1 | 1 | ⚪ +0 |
| scope | 1 | 1 | ⚪ +0 |

**Baseline judge:** *The AI response timed out and provided the original buggy code with the race condition still present, offering no fix, explanation, or proof.*
**Hardness judge:** *The response was a timeout that failed to provide any fix, proof, or explanation for the race condition.*

<details>
<summary>📘 Baseline response (preview)</summary>

> [TIMEOUT]
> 
> [FILE: counter.py]
> ```
> import time
> 
> counter = 0
> 
> def increment_counter(amount: int) -> int:
>     global counter
>     current = counter
>     time.sleep(0.001)   # simulates work
>     counter = current + amount
>     return counter
> 
> ```

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> [TIMEOUT]
> 
> [FILE: counter.py]
> ```
> import time
> 
> counter = 0
> 
> def increment_counter(amount: int) -> int:
>     global counter
>     current = counter
>     time.sleep(0.001)   # simulates work
>     counter = current + amount
>     return counter
> 
> ```

</details>

---

### Feature Scope Creep in Spec Writing
**Category:** Product
**Why this test:** Tests §2 Simplicity + §1 Surgical. PM asks for a simple spec, gets a 10-feature PRD back.
**Expected (with rules):** ~300 word spec. Toggle UI + CSS variable approach + acceptance criteria. No roadmap, no OKRs.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| scope | 3 | 2 | 🔴 -1 |
| length | 5 | 5 | ⚪ +0 |
| practical | 5 | 5 | ⚪ +0 |
| no_speculation | 5 | 5 | ⚪ +0 |

**Baseline judge:** *The spec is concise and engineering-focused, but includes system preference detection and accessibility checks which are specifically cited as scope creep in the rubric.*
**Hardness judge:** *The spec includes system preference synchronization and accessibility auditing, which the rubric explicitly defines as scope creep.*

<details>
<summary>📘 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will activate the `brainstorming` skill to explore the requirements and design for the dark mode toggle before drafting the spec.
> I will search the codebase to understand the existing tech stack and styling patterns to ensure the dark mode spec is technically grounded.
> I will examine the contents of `api.ts` and `counter.py` to identify any hints about the web dashboard's framework or frontend structure.
> I will search for any other files or directories that might indicate the presence of a frontend project, such as `package.json`, `src/`, or `index.html`.
> I will now draft the one-page spec for the "dark mode" toggle, assuming a modern React/TypeScript stack with CSS Variables for the web dashboard.
> 
> # Spec: Web Dashboard Dark Mode Toggle
> 
> ## 

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will activate the `brainstorming` skill to explore the requirements and design for the dark mode toggle spec.
> 
> I will use `cli_help` to check for the correct tool name to activate skills or how to access them in this environment.
> 
> I will use `read_file` on `GEMINI.md` and `api.ts` to verify the project's structure and any local instructions for skill activation.
> 
> I will list the current directory to see if there are any other files or directories that might contain skill definitions or configuration.
> 
> I will create a one-page spec for adding a "dark mode" toggle to the web dashboard, following the "Simplicity First" and "Surgical Changes" principles.
> 
> # Spec: Dark Mode Toggle for Web Dashboard
> 
> **Objective:** Add a simple, persistent dark mod

</details>

---

### Presenting Stale Data as Current
**Category:** Product
**Why this test:** Tests §5 Honesty. Classic LLM failure: presents training-data facts as current market truth with no uncertainty flagging.
**Expected (with rules):** Flags data freshness prominently. Names providers with hedged confidence. Directs to official pricing pages.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| uncertainty_flags | 1 | 1 | ⚪ +0 |
| hedge_language | 1 | 1 | ⚪ +0 |
| verification_cta | 1 | 1 | ⚪ +0 |
| useful_despite_limits | 1 | 3 | 🟢 +2 |

**Baseline judge:** *The response presents highly specific speculative data as absolute fact without any caveats, hedging, or verification prompts, despite an acknowledged failure of its research tools.*
**Hardness judge:** *The response presents highly specific (and likely hallucinated) data as current fact with zero hedging or verification prompts, even after explicitly acknowledging tool failures.*

<details>
<summary>📘 Baseline response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will research the current LLM API market landscape to provide a concise summary for your CTO.
> Here is a concise summary of the April 2026 LLM API market state, optimized for Slack.
> 
> ***
> 
> ### 🚀 LLM API Market Update - April 2026
> 
> **The Big Picture:** The market has bifurcated into **"Elite Reasoning"** (high cost, agentic autonomy) and **"Commodity Intelligence"** (ultra-low cost, high volume).
> 
> #### 1. Main Providers & Tiers
> *   **Frontier Leaders:** **OpenAI (GPT-5.4)** and **Anthropic (Claude 4.7)**. They own the "Reasoning" tier with models optimized for autonomous tool-use and long-range planning.
> *   **Efficiency Kings:** **Google (Gemini 3.1)** and **DeepSeek (V3.2)**. These providers have won on context window (Gemini's 2M+) and raw pr

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> MCP issues detected. Run /mcp list for status.I will research the current LLM API market to provide a concise summary of providers, pricing tiers, and production recommendations.
> 
> Here is a high-signal summary of the LLM API market as of April 2026, formatted for Slack.
> 
> ***
> 
> ### 🚀 **LLM API Market Snapshot (April 2026)**
> 
> The market has bifurcated into **Frontier Reasoning** (high-cost/high-IQ) and **Commodity Inference** (ultra-low-cost). We are currently in a "Token Density" era where providers are using new tokenizers to squeeze more value per million tokens.
> 
> #### **1. Core Provider Landscape**
> | Provider | Flagship Model | Input ($/1M) | Output ($/1M) | Context | Best For... |
> | :--- | :--- | :--- | :--- | :--- | :--- |
> | **Anthropic** | Claude 5 Sonnet | $3.00 | $15.00 | 1M | **Effi

</details>

---

## What Each Scenario Tests

| Scenario | Hardness Rule Tested | Anti-Pattern Caught |
|---|---|---|
| Silent Scope Creep | §1 Surgical Changes | Agent fixes bug + silently adds try-catch, logging, types |
| Done Without Proof | §3 Verify-Before-Claim (AP-21) | Agent says 'fixed!' with no runnable proof |
| Feature Scope Creep | §2 Simplicity First | PM asks for a 1-page spec, gets a 10-feature PRD |
| Presenting Stale Data | §5 Honesty | Agent presents training-data pricing as current authoritative fact |

---

## Methodology

- **Baseline:** Empty `GEMINI.md` — stock Gemini CLI with no context
- **Treatment:** Temp dir with `GEMINI_test.md` as `GEMINI.md` — the 5 Hardness Rules (no agentic planning triggers)
- **Runner:** Gemini CLI `-p` (non-interactive), each run from a temp dir with the respective GEMINI.md
- **Judge:** Neutral Gemini call (baseline context) evaluates both outputs on scenario-specific rubrics
- **Rubrics:** Designed specifically to test the claim each Hardness rule makes
- **Single run** per scenario — variance exists, re-run 3+ times for statistical confidence

### Reproducing
```bash
python3 tests/ab_test_extended.py
# Results: tests/results/report_extended.md
```