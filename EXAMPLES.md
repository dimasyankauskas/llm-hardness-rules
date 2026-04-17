# Examples

Real-world examples demonstrating how the Hardness Rules change agent behavior. Each example shows the common failure and the correct approach.

---

## Coding Examples

### Example 1: Over-engineering a Simple Feature

**Prompt:** "Add a retry mechanism to this API call."

#### ❌ Without Hardness Rules

```python
# Agent builds a full retry framework
class RetryConfig:
    def __init__(self, max_retries=3, backoff_factor=1.5, 
                 retry_on=None, circuit_breaker_threshold=5,
                 jitter=True, max_delay=60):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = retry_on or [500, 502, 503, 504]
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.jitter = jitter
        self.max_delay = max_delay

class CircuitBreaker:
    # ... 40 more lines ...

class RetryExecutor:
    # ... 30 more lines ...
```

Agent built a circuit breaker, jitter, and configurable error codes. You asked for a retry.

#### ✅ With Hardness Rules

**Senior Engineer Test fires:** "Would a senior engineer call this overcomplicated?" → Yes.

```python
# Minimum code that solves the problem
async def call_api_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await fetch(url)
        except Exception:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

**Rules that fired:** §2 Simplicity First, Senior Engineer Test.

---

### Example 2: Drive-by Refactoring

**Prompt:** "Add logging to the `process_order` function."

#### ❌ Without Hardness Rules

```diff
- def process_order(order_id, items):
+ def process_order(order_id: str, items: list[OrderItem]) -> ProcessResult:
-     total = 0
-     for item in items:
-         total += item['price'] * item['qty']
+     total = sum(item.price * item.quantity for item in items)
+     logger.info(f"Processing order {order_id}, total: {total}")
-     if total > 1000:
-         apply_discount(total)
+     if total > DISCOUNT_THRESHOLD:
+         total = apply_discount(total)
      return total
```

Agent added types, renamed variables, introduced a constant, changed the list comprehension style, and fixed a potential bug — all while "adding logging." Only one line was the actual request.

#### ✅ With Hardness Rules

```diff
  def process_order(order_id, items):
      total = 0
      for item in items:
          total += item['price'] * item['qty']
+     logger.info(f"Processing order {order_id}, total: {total}")
      if total > 1000:
          apply_discount(total)
      return total
```

One line added. Every changed line traces to the request.

**Rules that fired:** §2 Surgical Changes — "Match existing style. If you notice unrelated issues, mention them — don't fix them."

**Agent's note to user:** *"I noticed `apply_discount(total)` doesn't capture the return value, which may be a bug. Want me to fix it separately?"*

---

### Example 3: Phantom Completion

**Prompt:** "Fix the import error in `utils.ts`."

#### ❌ Without Hardness Rules

Agent responds: *"Done! I changed the import from `@utils/helpers` to `@/utils/helpers`. The path was incorrect."*

No evidence the file was actually saved. No evidence the build passes. The agent *might* have made the correct edit, or it might have hallucinated the fix entirely.

#### ✅ With Hardness Rules

Agent responds:
```
Fixed the import path in utils.ts.

Verification:
- Diff Proof: replaced `@utils/helpers` with `@/utils/helpers` on line 3
- Runtime Proof: `npm run build` exited with code 0
- Filesystem Proof: grep confirms `@/utils/helpers` at utils.ts:3
```

**Rules that fired:** §3 AP-21 Verify-Before-Claim — agent cannot claim "done" without tool-verified evidence.

---

## Non-Coding Examples

### Example 4: Writing a Product Brief

**Prompt:** "Write a product brief for a voice-first idea capture feature targeting busy professionals."

#### ❌ Without Hardness Rules (Karpathy)

**Zero rules fire.** Karpathy's file says "code" in every section. The agent generates:

- A 2,000-word PRD template with 15 sections
- Speculative features: Siri integration, Apple Watch companion, team sharing
- Competitor analysis section (not requested)
- Legal/compliance section (not requested)
- A timeline with 6 sprints (not requested)

The user asked for a product brief. They got a full PRD with scope creep.

#### ✅ With Hardness Rules

**§2 Simplicity First fires:** "Minimum content that solves the problem."
**Senior Engineer Test fires:** "Would a senior PM call this overcomplicated?" → Yes, cut it.

Agent produces:
- 400-word focused brief: problem, persona, solution, success metrics
- Only the features explicitly implied by the prompt (voice capture, offline, auto-organize)
- No speculative sections

**§3 AP-21 Content Proof fires:** Agent confirms the artifact was created and shows file location.

---

### Example 5: Research Task

**Prompt:** "Research the top 5 AI coding assistants. Compare pricing and features for a board deck."

#### ❌ Without Hardness Rules (Karpathy)

**Zero rules fire.** Agent responds from training data:

*"Here are the top 5 AI coding assistants: 1. GitHub Copilot ($10/mo)..."*

- Pricing may be outdated (training data cutoff)
- Team sizes are hallucinated
- No source citations
- No web search performed
- Board gets wrong numbers

#### ✅ With Hardness Rules

**§2 Determinism over Generation fires:** "If it can be verified by a tool — verify it." Agent performs live web searches instead of relying on training data.

**§3 AP-21 Content Proof fires:** Agent must show search results were retrieved and artifact was created.

Agent produces:
- Table with current pricing (verified via web search)
- Source URLs cited for each data point
- "Could not verify team size for X — marked as unconfirmed"
- Formatted for board deck usage

---

### Example 6: Editing Existing Documentation

**Prompt:** "Update the API docs to reflect the new `/v2/orders` endpoint."

#### ❌ Without Hardness Rules

Agent rewrites the entire API docs file:
- Reformats all existing endpoints to a "better" style
- Adds a table of contents (not requested)
- Changes British spelling to American (style drift)
- Reorders sections alphabetically
- Somewhere in there, adds the `/v2/orders` docs

#### ✅ With Hardness Rules

**§2 Surgical Changes fires:** "When editing documents, preserve existing tone, structure, and formatting."

**§4 Zero-Truncation fires:** File is >100 lines — agent uses chunk edit, not whole-file replacement.

**§4 Verification Anchors fires:** Agent verifies existing endpoint docs are still intact after the edit.

Agent adds one new section for `/v2/orders` matching the existing format. Nothing else changes.

---

## Cross-Session Memory Example

### Example 7: Repeated Hallucination

**Session 1:** Agent uses `SwiftUI.NavigationView` (deprecated in iOS 16+). Build fails. Agent fixes it to `NavigationStack`.

**Session 2 (without Hardness Rules):** Agent uses `NavigationView` again. Same failure. Same fix. Repeat forever.

**Session 2 (with Hardness Rules):**
**§3 AP-23 fires** in Session 1: Agent wrote to MEMORY.md:
```
- **[FAILURE-ANCHOR]** Do not use `NavigationView` because it is deprecated in iOS 16+. Correct: `NavigationStack`.
```

Session 2: Agent reads MEMORY.md during planning phase. Uses `NavigationStack` from the start. Zero wasted cycles.

---

**These rules are working if:**
- Diffs contain only what was requested
- Agent shows proof before claiming "done"
- Research tasks cite live sources, not training data
- The agent never makes the same mistake twice
- PRDs are focused, not bloated
- Existing content survives edits intact
