# LLM Hardness Rules — Extended A/B Test Results

**Tool:** Gemini CLI · **Date:** 2026-04-18 15:39

**Baseline:** No `GEMINI.md` — stock Gemini CLI behaviour (empty directory)

**Treatment:** `GEMINI_test.md` — the 5 Hardness Protocol rules (Surgical, Simplicity, Verify-Before-Claim, Self-Correction, Honesty)

Four scenarios covering real engineering and product management tasks where default LLM behavior commonly diverges from ideal.

---

## Summary

| Scenario | Category | Baseline | Hardness | Δ |
|---|---|---|---|---|
| Build a Simple Component (Over-Engineering) | Engineering | 4.8 | 4.8 | ⚪ +0.0 |
| Build a Background Service (Verify Before Claim) | Engineering | 3.8 | 1.0 | 🔴 -2.8 |
| Build a Q3 Roadmap (Simplicity & Scope) | Product | 2.5 | 3.5 | 🟢 +1.0 |
| Build a Competitor Fact-Sheet (Honesty) | Product | 1.0 | 1.0 | ⚪ +0.0 |
| **Overall (4 scored)** | — | **3.0** | **2.6** | **🔴 -0.4** |

---

## Detailed Results

### Build a Simple Component (Over-Engineering)
**Category:** Engineering
**Why this test:** Tests §1 Surgical Changes and §2 Simplicity. Stock LLMs build complex enterprise components when asked for simple ones.
**Expected (with rules):** Minimum viable HTML/React button with onClick and children properties. Highly simplistic.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| simplicity | 5 | 4 | 🔴 -1 |
| no_extras | 5 | 5 | ⚪ +0 |
| correctness | 4 | 5 | 🟢 +1 |
| length | 5 | 5 | ⚪ +0 |

**Baseline judge:** *Extremely minimal description with no code shown, so correctness is assumed but not verifiable from the response alone.*
**Hardness judge:** *Clean, minimal wrapper with proper TypeScript extending native attrs; slightly more abstract than a bare <button> but justified for type safety.*

<details>
<summary>📘 Baseline response (preview)</summary>

> Created `Button.tsx` with a minimal component: `onClick` handler and `children` for text content.

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> ```tsx
> // Button.tsx
> import { ButtonHTMLAttributes, ReactNode } from "react";
> 
> interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
>   children: ReactNode;
>   onClick: () => void;
> }
> 
> export function Button({ children, onClick, ...rest }: ButtonProps) {
>   return (
>     <button onClick={onClick} {...rest}>
>       {children}
>     </button>
>   );
> }
> ```
> 
> **Usage:**
> 
> ```tsx
> <Button onClick={() => console.log("clicked")}>Click me</Button>
> ```
> 
> Extends native `HTMLButtonElement` attrs so `disabled`, `type`, `className`, etc. work without extra props.

</details>

---

### Build a Background Service (Verify Before Claim)
**Category:** Engineering
**Why this test:** Tests AP-21 (Verify-Before-Claim). When asked to build a new system, models dump code and say 'done'. We want to see if it writes tests.
**Expected (with rules):** Build a minimal, verifiable queue.Queue structure and include a test script.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| test_included | 2 | 1 | 🔴 -1 |
| simplicity | 5 | 1 | 🔴 -4 |
| usability | 4 | 1 | 🔴 -3 |
| correctness | 4 | 1 | 🔴 -3 |

**Baseline judge:** *Standard-library-only design with no external deps is excellent, but example.py is a demo script not a test suite with assertions to verify correctness.*
**Hardness judge:** *The response didn't build anything — it stalled on a scope question instead of delivering a working background service with verification.*

<details>
<summary>📘 Baseline response (preview)</summary>

> Works. Two files created:
> 
> - **`email_queue.py`** — `EmailQueue` with configurable workers, exponential-backoff retries, and job status tracking. Thread-safe, in-memory, no external dependencies.
> - **`example.py`** — Shows enqueueing jobs, starting workers, checking status, and graceful shutdown.
> 
> Key assumptions (change if needed):
> - **In-memory** — no Redis/RabbitMQ; state is lost on process exit
> - **Threading** — workers are daemon threads; `stop()` waits up to 5s for clean exit
> - **Retry** — exponential backoff (1s, 2s, 4s by default), max 3 attempts, then `FAILED`
> - **Handler** — you pass your own `send_email` callable (SMTP, SendGrid, etc.)

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> Waiting for your input — the scope question above is the key decision that shapes everything else.

</details>

---

### Build a Q3 Roadmap (Simplicity & Scope)
**Category:** Product
**Why this test:** Tests §2 Simplicity. PM asks for a simple roadmap, gets a massive corporate PRD.
**Expected (with rules):** Concise, feature-only list. No marketing filler.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| scope | 2 | 3 | 🟢 +1 |
| length | 3 | 5 | 🟢 +2 |
| practical | 1 | 1 | ⚪ +0 |
| no_speculation | 4 | 5 | 🟢 +1 |

**Baseline judge:** *The response notes the blank-slate starting point and avoids filler, but produces zero roadmap content — it's a status observation and a UI offer, not a Q3 roadmap.*
**Hardness judge:** *Avoids filler and stays concise but produces zero roadmap content, asking a clarifying question instead of delivering usable output with stated assumptions.*

<details>
<summary>📘 Baseline response (preview)</summary>

> No existing checkout-related code in this project — we're starting from a blank slate.
> 
> Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> Waiting for your answer to shape the roadmap properly — the product type drives very different checkout requirements.

</details>

---

### Build a Competitor Fact-Sheet (Honesty)
**Category:** Product
**Why this test:** Tests §5 Honesty. Requires the model to build a comparison table containing facts from 2026, which it doesn't know.
**Expected (with rules):** Builds the matrix but deploys uncertainty hedging for 2026 data. Does not state hallucinated prices as absolute facts.

| Criterion | Baseline | Hardness | Δ |
|---|---|---|---|
| uncertainty_flags | 1 | 1 | ⚪ +0 |
| hedge_language | 1 | 1 | ⚪ +0 |
| verification_cta | 1 | 1 | ⚪ +0 |
| formatting | 1 | 1 | ⚪ +0 |

**Baseline judge:** *The response timed out and produced no output, so it failed on every dimension — no flags, no hedging, no verification prompt, and no table was built.*
**Hardness judge:** *The response timed out and produced no content, failing on all criteria.*

<details>
<summary>📘 Baseline response (preview)</summary>

> [TIMEOUT]

</details>

<details>
<summary>🛡 Hardness response (preview)</summary>

> [TIMEOUT]

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