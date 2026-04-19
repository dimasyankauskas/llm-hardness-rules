# LLM Hardness Protocol v5

Behavioral contracts that force AI agents to finish what they start. Not guidelines. Enforcement.

We built these rules because polite suggestions fail in production. We burned thousands of tokens watching agents drift halfway through complex edits, quietly forget requirements, and generate bloated text blobs instead of structured deliverables. Then [Karpathy posted](https://x.com/karpathy/status/2015883857489522876) about the exact same failure modes. Same diagnosis. We'd already been building the fix.

> Works with **Claude Code** · **Google Antigravity** · **Cursor** · any LLM IDE that reads system prompts

## The Reality of AI Coding Assistants

Every AI coding assistant fails on the same five edge cases. Over and over.

| What happens | What you actually need |
|---|---|
| Builds a Strategy pattern for a one-liner | Just the one-liner |
| Formats adjacent code while fixing a bug | Only the bug fix |
| Claims "I added the import" with zero proof | Verified compiler output |
| Hallucinates the same deprecated API every run | Cross-session memory |
| Generates an unstructured brainstorm | A structured product deliverable |

Karpathy's baseline guidelines handle the first two. Rows 3 through 5 are where agentic systems fall apart without structural limits. The Hardness Protocol covers all five.

## Why Contracts Beat Suggestions

Here's the difference in one example:

```
Baseline:  "Define success criteria. Loop until verified."
Hardness:  "You are FORBIDDEN from claiming done until you provide
            Runtime Proof, Filesystem Proof, Diff Proof, or Content Proof.
            Verbal assertions without tool evidence are a Tier 1 defect."
```

One is advice. The other is a structural constraint. Advice degrades under pressure. Make a 10-file refactor request, and the agent drops its good habits by file four. We watched it happen across hundreds of sessions. Constraints don't degrade. The agent can't mark the task complete without showing receipts. That's the whole ballgame.

## What's inside

~60 lines. Six sections. That's the whole thing.

| Section | What it does |
|---|---|
| **§1 Identity** | Sets tone — technical for code, precise for writing |
| **§2 Philosophy** | Simplicity First, Surgical Changes, the Senior Engineer Test |
| **§3 Hardness Protocol** | Three non-negotiable verification gates |
| **§4 Anti-Regression** | Stops new work from silently wiping old work |
| **§5 Security** | Zero-trust, least privilege, no key leaks |
| **§6 Product & Research** | Scope containment, no-hallucination research, deliverable-first |

### The three gates

**AP-21 — Verify-Before-Claim.** The agent can't say "done" without tool-verified evidence. Build output, file content check, search results — something you can see. "I added the import" without proof isn't a style issue. It's a defect.

**AP-22 — Critic-Refiner Loop.** When something breaks, the agent self-corrects up to three times before escalating. Each attempt targets a different root cause. No more "the build failed, what should I do?" on the first error.

**AP-23 — Failure Memory.** When a pattern fails twice in the same session, the agent writes it to persistent storage. Next session reads it. The mistake doesn't repeat. Before AP-23, we'd watch the same deprecated API call resurface every Monday morning. That stopped.

## Empirical Validation

We ran three scenarios designed to exercise rules that differ between the two sets. Same model (Gemini 2.5 Pro), same prompts, identical project scaffolds copied to fresh temp directories per run. Full tool access (`gemini -p --yolo`).

### Scenario 1: The Multi-File Deceptive Bug

A Python project with a failing email validation test. The obvious fix location (`validator.py`) doesn't work — the root cause is a missing `+` character in a config file (`config.py`).

Both agents found the root cause. Both ran the test. *The difference was transparency.*

- **Baseline agent:** Narrative summary — *"I fixed the root cause of the failing test."* No output displayed.
- **Hardness agent:** Structured verification block — *"Runtime Proof: `python3 -m pytest` — 11 passed. Filesystem Proof: `config.py` updated."* 

Same fix. Different confidence level for the developer reading the output. AP-21 forces the agent to categorize its evidence.

### Scenario 2: Zero-Regression Feature Addition

A working inventory system with 9 passing tests. Task: add an `apply_discount()` method and tests without breaking anything.

Both agents added the feature. Both preserved existing tests. The Hardness agent added one extra edge case test (non-existent product) that the baseline skipped. Minor difference — both shipped verifiable code.

### Scenario 3: Product Deliverable Scoping

We ran three product-focused scenarios: writing a scoped PRD, building a competitor pricing matrix, and generating an engineering roadmap. This exposed a massive gap between baseline advice and structural rules.

Under standard advice, LLMs naturally drift into "brainstorming mode" on non-coding tasks. They produce unformatted blobs of text, hallucinate numbers, and ignore constraints. 

By applying §6 Product & Research Protocol (and the Deliverable-First override), the Hardness agent acted like a PM:
- **Scope Containment:** Delivered a 238-word PRD instead of an endless feature dump.
- **Deliverable-First:** Built a fully formatted 5-heading roadmap with timelines and owners. The baseline agent failed completely, outputting a 56-word unformatted snippet.
- **No-Hallucination Research:** Successfully populated fact-based comparison matrices without making up missing data.

### The Scorecard: Hardness vs Baseline (Karpathy)

| Capability | Baseline Rules | Hardness Protocol |
|---|---|---|
| **Code correctness** | ✅ Solved | ✅ Solved |
| **Surgical edits** | ✅ Precise | ✅ Precise |
| **Verification transparently** | ❌ Narrative claim | **✅ Categorized proof (AP-21)** |
| **PRD scope containment** | ✅ Met constraints | ✅ Met constraints |
| **Research artifact delivery** | ❌ Asked questions | **✅ Produced table directly** |
| **Roadmap structure** | ❌ Unformatted text | **✅ 5-heading artifact** |
| **Cross-session memory** | — Not addressed | **✅ Yes (AP-23)** |

Baseline rules are a strong, lean foundation for coding logic. But if you want **auditable tool evidence** and **structured product deliverables** without the agent going into an endless clarification loop, you need structural enforcement. That's what the Hardness Protocol provides.

## Installation

### Claude Code

Drop it in your project root:

```bash
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/CLAUDE.md -o CLAUDE.md
```

Or install as a plugin:

```bash
claude plugin add dimasyankauskas/llm-hardness-rules
```

### Google Antigravity

Global install — covers every project you open:

```bash
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/GEMINI.md -o ~/.gemini/GEMINI.md
```

Or install as a skill:

```bash
mkdir -p ~/.gemini/antigravity/skills/hardness-protocol
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/skills/hardness-protocol/SKILL.md \
  -o ~/.gemini/antigravity/skills/hardness-protocol/SKILL.md
```

### Cursor

```bash
mkdir -p .cursor/rules
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/.cursor/rules/hardness.mdc \
  -o .cursor/rules/hardness.mdc
```

### Anything else

Copy the contents of `CLAUDE.md` or `GEMINI.md` into your system prompt. Platform-agnostic — just text.

## Customization

These are the foundation layer. Stack your project-specific context on top:

- **Claude Code:** Append to `CLAUDE.md` below the base rules
- **Antigravity:** Create a project-level `GEMINI.md` with domain context
- **Cursor:** Add more `.mdc` files in `.cursor/rules/`

One global contract, one project-specific context file per codebase. The base handles behavior. Your file handles identity and domain.

## Credits

- **Andrej Karpathy** — [identified the core failure modes](https://x.com/karpathy/status/2015883857489522876): over-engineering, drive-by edits, hidden assumptions, unverified claims. His tweet gave this problem a public name.
- **forrestchang** — [packaged them](https://github.com/forrestchang/andrej-karpathy-skills) as a Claude Code plugin. Smart distribution.
- **BuildFutures.ai** — Discovered the same failure modes independently through months of work in the [Antigravity Expert lab](https://github.com/dimasyankauskas/Antigravity_Expert). Added enforcement architecture (AP-21/22/23), non-coding coverage, cross-session failure memory, and multi-platform support.

## License

MIT. Use it anywhere. Fork it. Attribution appreciated but not required.
