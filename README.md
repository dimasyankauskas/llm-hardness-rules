# LLM Hardness Rules

Behavioral contracts that force AI agents to finish what they start. Not guidelines. Enforcement.

We'd been grinding on this problem for months before anyone else named it. Agents over-engineering single-line fixes into Strategy patterns. Making drive-by edits nobody asked for. Silently breaking features they'd shipped two hours earlier. We ran an [agent optimization lab](https://github.com/AIMasterMinds/Antigravity_Expert) for roughly 4 months — about 6 production projects, thousands of agent sessions — trying to figure out why LLM agents degrade under pressure and what structural fixes actually stick.

Then [Karpathy posted](https://x.com/karpathy/status/2015883857489522876) about the exact same failure modes. Same diagnosis, arrived at independently. He nailed the problems. We'd already built the treatment.

The gap between his rules and ours? He wrote advice. We wrote contracts — enforcement gates that don't soften when context windows get crowded, cross-session memory that stops the agent from re-learning the same lesson every Monday, and coverage for the roughly 50% of knowledge work that isn't code. His CLAUDE.md goes quiet when you ask for a product brief. Ours doesn't.

> Works with **Claude Code** · **Google Antigravity** · **Cursor** · any LLM IDE that reads system prompts

## The problem

Every AI coding assistant makes the same five mistakes. Over and over and over.

| What happens | What you wanted |
|---|---|
| Builds a Strategy pattern for a one-liner | Just the one-liner |
| Changes your quote style while fixing a bug | Only the bug fix |
| Says "Done! I added the import." Never verified. | Proof it compiled |
| Hallucinates the same deprecated API every session | Memory. Any memory at all. |
| Goes silent when you ask for a product brief | Same rigor, any task |

Karpathy's guidelines handle the first two. Solid diagnosis. But that's where they stop. These rules handle all five — coding and non-coding, first session and fiftieth.

## Why contracts beat suggestions

Here's the difference in one example:

```
Karpathy:  "Define success criteria. Loop until verified."
Hardness:  "You are FORBIDDEN from claiming done until you provide
            Runtime Proof, Filesystem Proof, Diff Proof, or Content Proof.
            Verbal assertions without tool evidence are a Tier 1 defect."
```

One is advice. The other is a structural constraint.

Advice degrades under pressure. Long sessions, complex multi-file edits, context window crowding — the agent quietly drops the good habits first. We've watched it happen. Constraints don't degrade because they aren't optional. The agent can't mark the task complete without showing receipts.

We've been running these rules across 6 production projects for about 4 months. The difference isn't subtle — it's the difference between "I think I fixed it" and a green test suite screenshot in the chat.

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

**AP-21 — Verify-Before-Claim.** The agent can't say "done" without tool-verified evidence. Build output, file content check, search results — something you can see. "I added the import" without proof isn't a style issue. It's a defect. We treat it like one.

**AP-22 — Critic-Refiner Loop.** When something breaks, the agent self-corrects up to three times before escalating. Each attempt has to target a different root cause. No more "the build failed, what should I do?" on the first error. That's not collaboration — that's learned helplessness.

**AP-23 — Failure Memory.** When a pattern fails twice in the same session, the agent writes it to persistent storage. Next session reads it. The mistake doesn't repeat. Sounds almost too simple? It transforms everything. Before AP-23, we'd watch the same deprecated API call come back every single Monday morning. Now it doesn't.

## How we tested this

We ran four scenarios head-to-head — Karpathy's CLAUDE.md against our rules. Two coding tasks, two non-coding. Same prompts, same codebase context, same model. Here's what happened.

### Coding: fix a race condition

Both rule sets produced reasonable behavioral guidance. The code fix was roughly equivalent. The gap? Verification. Karpathy's agent said "Fixed it" and moved on. Ours ran the test, displayed the exit code, confirmed zero regressions in adjacent modules. Same fix. Completely different confidence level for the developer reading the output.

### Coding: add dark mode toggle

Karpathy's agent added the toggle — but also reorganized the settings page layout and renamed a variable it thought was unclear. Three files touched, one requested. Classic drive-by. Our agent added the toggle. One file. Nothing else. Done.

### Non-coding: write a product brief

This is where it gets uncomfortable. Karpathy's file mentions "code" in nearly every section. When there's no code involved, zero rules activate. The agent generated a 2,000-word PRD template with Siri integration, an Apple Watch companion app, and a compliance section nobody asked for. Textbook over-engineering — but for documents instead of code.

Our agent produced a focused 400-word brief: problem, persona, solution, success metrics. The Senior Engineer Test (§2) caught the bloat before it shipped. Would a senior engineer call this overcomplicated? Yes. Cut it.

### Non-coding: research competitors for a board deck

Karpathy's agent responded entirely from training data. Stale pricing, hallucinated team sizes, no citations. Our agent ran live web searches — the Determinism rule (§2) forces tool verification over generation — cited every source, and flagged two data points it couldn't independently confirm.

### Results

| Scenario | Karpathy | Hardness |
|---|---|---|
| Fix race condition | 3/5 | 5/5 |
| Add dark mode | 3/5 | 5/5 |
| Write product brief | 1/5 | 4/5 |
| Research competitors | 1/5 | 5/5 |
| **Average** | **2.0** | **4.75** |

The coding gap is enforcement — both rule sets know the right behavior, but only one actually forces it. The non-coding gap is existence. Karpathy's rules don't fire when there's no code involved. Ours do.

## Installation

### Claude Code

Drop it in your project root:

```bash
curl -sL https://raw.githubusercontent.com/AIMasterMinds/llm-hardness-rules/main/CLAUDE.md -o CLAUDE.md
```

Or install as a plugin:

```bash
claude plugin add AIMasterMinds/llm-hardness-rules
```

### Google Antigravity

Global install — covers every project you open:

```bash
curl -sL https://raw.githubusercontent.com/AIMasterMinds/llm-hardness-rules/main/GEMINI.md -o ~/.gemini/GEMINI.md
```

Or install as a skill:

```bash
mkdir -p ~/.gemini/antigravity/skills/hardness-protocol
curl -sL https://raw.githubusercontent.com/AIMasterMinds/llm-hardness-rules/main/skills/hardness-protocol/SKILL.md \
  -o ~/.gemini/antigravity/skills/hardness-protocol/SKILL.md
```

### Cursor

```bash
mkdir -p .cursor/rules
curl -sL https://raw.githubusercontent.com/AIMasterMinds/llm-hardness-rules/main/.cursor/rules/hardness.mdc \
  -o .cursor/rules/hardness.mdc
```

### Anything else

Copy the contents of `CLAUDE.md` or `GEMINI.md` into your system prompt. The rules are platform-agnostic — just text.

## Customization

These are the foundation layer. Stack your project-specific context on top:

- **Claude Code:** Append to `CLAUDE.md` below the base rules
- **Antigravity:** Create a project-level `GEMINI.md` with domain context
- **Cursor:** Add more `.mdc` files in `.cursor/rules/`

The base handles universal behavior. Your project file handles identity, tech stack, domain expertise. We run this exact split across all of our production repos — one global contract, one project-specific context file per codebase.

## Credits

- **Andrej Karpathy** — [identified the core failure modes](https://x.com/karpathy/status/2015883857489522876): over-engineering, drive-by edits, hidden assumptions, agents that don't verify. The diagnosis was right. His tweet is what finally gave this problem a public name.
- **forrestchang** — [packaged them](https://github.com/forrestchang/andrej-karpathy-skills) as a Claude Code plugin. Smart distribution.
- **BuildFutures.ai** — Discovered the same failure modes independently through months of agent optimization in the [Antigravity Expert lab](https://github.com/AIMasterMinds/Antigravity_Expert). Added enforcement architecture (AP-21/22/23), non-coding task coverage, cross-session failure memory, and multi-platform support. He identified the disease. We built the treatment.

## License

MIT. Use it anywhere. Fork it. Attribution appreciated but not required.
