# LLM Hardness Rules

Behavioral contracts that force AI agents to finish what they start. Not guidelines. Enforcement.

We'd been grinding on this for months inside an [agent optimization lab](https://github.com/dimasyankauskas/Antigravity_Expert) — roughly 6 production projects, thousands of agent sessions — trying to figure out why LLM agents degrade under pressure and what structural fixes actually hold. Then [Karpathy posted](https://x.com/karpathy/status/2015883857489522876) about the exact same failure modes. Same diagnosis, arrived at independently. He identified the problems. We'd already been building the fix.

> Works with **Claude Code** · **Google Antigravity** · **Cursor** · any LLM IDE that reads system prompts

## The problem

Every AI coding assistant makes the same five mistakes. Over and over.

| What happens | What you wanted |
|---|---|
| Builds a Strategy pattern for a one-liner | Just the one-liner |
| Changes your quote style while fixing a bug | Only the bug fix |
| Says "Done! I added the import." Never verified. | Proof it compiled |
| Hallucinates the same deprecated API every session | Memory. Any memory at all. |
| Goes silent when you ask for a product brief | Same rigor, any task |

Karpathy's guidelines handle the first two well. But rows 3 through 5? Nothing fires. These rules cover all five.

## Why contracts beat suggestions

Here's the difference in one example:

```
Karpathy:  "Define success criteria. Loop until verified."
Hardness:  "You are FORBIDDEN from claiming done until you provide
            Runtime Proof, Filesystem Proof, Diff Proof, or Content Proof.
            Verbal assertions without tool evidence are a Tier 1 defect."
```

One is advice. The other is a structural constraint. Advice degrades under pressure — long sessions, complex multi-file edits, the agent quietly drops good habits first. We've watched it happen across hundreds of sessions. Constraints don't degrade because they aren't optional. The agent can't mark the task complete without showing receipts.

## What's inside

49 lines. Six sections. That's the whole thing.

| Section | What it does |
|---|---|
| **§1 Identity** | Sets tone — technical for code, precise for writing |
| **§2 Philosophy** | Simplicity First, Surgical Changes, the Senior Engineer Test |
| **§3 Hardness Protocol** | Three non-negotiable verification gates |
| **§4 Anti-Regression** | Stops new work from silently wiping old work |
| **§5 Security** | Zero-trust, least privilege, no key leaks |
| **§6 Operational** | Skill routing, memory hygiene, path safety |

### The three gates

**AP-21 — Verify-Before-Claim.** The agent can't say "done" without tool-verified evidence. Build output, file content check, search results — something you can see. "I added the import" without proof isn't a style issue. It's a defect.

**AP-22 — Critic-Refiner Loop.** When something breaks, the agent self-corrects up to three times before escalating. Each attempt targets a different root cause. No more "the build failed, what should I do?" on the first error.

**AP-23 — Failure Memory.** When a pattern fails twice in the same session, the agent writes it to persistent storage. Next session reads it. The mistake doesn't repeat. Before AP-23, we'd watch the same deprecated API call resurface every Monday morning. That stopped.

## How we tested this

Four scenarios head-to-head — Karpathy's CLAUDE.md against our rules. Two coding tasks, two non-coding. Same prompts, same codebase context, same model.

### Coding: fix a race condition

Both rule sets produced roughly equivalent code fixes. The gap was verification. Karpathy's agent said "Fixed it" and moved on. Ours ran the test, displayed the exit code, confirmed zero regressions in adjacent modules. Same fix — completely different confidence level for the developer reading the output.

### Coding: add dark mode toggle

Karpathy's agent added the toggle but also reorganized the settings page layout and renamed a variable. Three files touched, one requested. Our agent added the toggle. One file. Nothing else.

### Non-coding: write a product brief

This is where it gets uncomfortable. Karpathy's file mentions "code" in nearly every section. When there's no code, zero rules activate. The agent generated a 2,000-word PRD template with Siri integration, an Apple Watch companion app, and a compliance section nobody asked for.

Our agent produced a focused 400-word brief: problem, persona, solution, success metrics. The Senior Engineer Test (§2) caught the bloat. Would a senior engineer call this overcomplicated? Yes. Cut it.

### Non-coding: research competitors for a board deck

Karpathy's agent responded from training data. Stale pricing, hallucinated team sizes, no citations. Our agent ran live web searches — the Determinism rule (§2) forces tool verification over generation — cited every source, and flagged two data points it couldn't independently confirm.

### What we observed

| Capability | Karpathy's Rules | Hardness Rules |
|---|---|---|
| Correct code fix | ✅ Yes | ✅ Yes |
| Verified before claiming done | ❌ No | ✅ Yes |
| Avoided drive-by edits | ❌ No | ✅ Yes |
| Non-coding task quality | — Out of scope | ✅ Covered |
| Cross-session memory | — Not addressed | ✅ AP-23 |

Karpathy's rules produce good coding behavior — the diagnosis was accurate and the guidance is sound. The gaps are verification enforcement and non-coding coverage, which is what these rules add.

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
