# LLM Hardness Rules

Portable foundation rules for AI coding agents.

This project is intentionally small at the core: simple defaults, proof before completion, and optional stricter profiles when the task really needs them.

> Built first for **Codex**. Other prompt surfaces remain as compatibility outputs, not equal validation targets.

**Author note:** Codex is my primary agent. OpenAI's vision aligns strongly with my own, so this project is built for Codex first.

## Why This Exists

Most agent failures come from a short list of behaviors:

| What happens | What you actually need |
|---|---|
| Builds a framework for a one-line task | Just the one-line task |
| “Fixes” code while also refactoring nearby code | Only the requested edit |
| Claims completion without proof | Evidence you can inspect |
| Repeats the same bad approach | Failure memory |
| Turns a concrete deliverable into a brainstorm | The requested artifact |

The core protocol is meant to fix those behaviors without turning your prompt file into a workflow constitution.

## Core Protocol

The shared core keeps only the rules that travel well across tools:

- **Simplicity First**
- **Surgical Changes**
- **Deliverable-First**
- **AP-21 Verify-Before-Claim**
- **AP-22 Critic-Refiner Loop**
- **AP-23 Failure Memory**
- security constraints
- an explicit “use judgment for trivial tasks” escape hatch

The canonical source lives in [`protocols/core.md`](./protocols/core.md). Public prompt surfaces are rendered from it with:

```bash
python3 scripts/render_surfaces.py
```

## Optional Profiles

The strict workflows live in opt-in profiles instead of the universal base:

| Profile | Use when |
|---|---|
| [`profiles/bugfix.md`](./profiles/bugfix.md) | real bug investigation, flaky tests, regressions |
| [`profiles/research.md`](./profiles/research.md) | PRDs, competitor analysis, roadmaps, freshness-sensitive facts |
| [`profiles/high-assurance.md`](./profiles/high-assurance.md) | shared interfaces, high regression risk, broad edits |

This is the main reset in vNext: the base stays portable, the heavier process becomes optional.

## Installation

### Codex

Project-local install:

```bash
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/AGENTS.md -o AGENTS.md
```

### Compatibility Outputs

Other generated surfaces remain in the repo for compatibility, but Codex is the only release target that currently matters for benchmark claims:

```bash
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/CLAUDE.md -o CLAUDE.md
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/GEMINI.md -o ~/.gemini/GEMINI.md
mkdir -p .cursor/rules
curl -sL https://raw.githubusercontent.com/dimasyankauskas/llm-hardness-rules/main/.cursor/rules/hardness.mdc \
  -o .cursor/rules/hardness.mdc
```

## Evidence and Limitations

This repo is deliberately more conservative about claims now.

### Supported claims

- Codex is the primary install, benchmark, and release target.
- The shared surfaces are rendered from one canonical core source.
- The repo now includes a reproducible benchmark harness in [`benchmarks/`](./benchmarks/README.md) with separate `core_behavior` and `interactive_tool_use` suites.

### Known limitations

- Historical experiments under `tests/` contain mixed outcomes and timeouts. They are useful as lab notes, not the current public proof surface.
- Open-ended build tasks can still stall or over-ask depending on the model and runtime.
- Compatibility outputs for non-Codex tools exist, but they are not the basis for release claims.

## How We Test Codex

Every release claim should come from the Codex benchmark harness, not ad hoc spot checks.

```bash
python3 benchmarks/run_suite.py --suite core_behavior --agent codex --runs 3
python3 benchmarks/run_suite.py --suite interactive_tool_use --agent codex --runs 3
python3 benchmarks/render_report.py \
  --core-dir benchmarks/results/<core-dir> \
  --interactive-dir benchmarks/results/<interactive-dir> \
  --output benchmarks/reports/codex-baseline-vs-hardness.md
```

Each run records prompt, instruction variant, Codex version, timeout setting, raw output, and analyzer results. Timeouts count as failures.

## Current Codex Benchmark Bar

The README should only claim success after this gate is met:

- 7 scenarios total: `over_engineering`, `drive_by_edit`, `phantom_completion`, `multifile_bug`, `additive_feature`, `scoped_prd`, `roadmap_artifact`
- 3 runs per scenario for both baseline and `AGENTS.md`
- hardness pass rate must be greater than or equal to baseline in every scenario
- hardness must have zero timeouts across all 21 hardness runs
- `roadmap_artifact` must also score `3/3` on the hardness side before the report counts as public-release ready

### Current benchmark position

Use the benchmark harness under `benchmarks/` as the current evaluation surface, and treat Codex as the only decision-making runtime for release. A report is ship-ready only if it clears both the relative gate and the absolute `roadmap_artifact` bar.

## Latest Verified Result

The latest accepted Codex benchmark summary should live here:

- [`benchmarks/reports/codex-baseline-vs-hardness.md`](./benchmarks/reports/codex-baseline-vs-hardness.md)

## Customization

The intended layering is:

1. use the small base surface for everyday work
2. add domain-specific repo context locally
3. reach for a strict profile only when the task needs it

This project is not trying to be a universal workflow operating system.

## Credits

- **Andrej Karpathy** — [named the core failure modes](https://x.com/karpathy/status/2015883857489522876): over-engineering, drive-by edits, hidden assumptions, and unverified claims.
- **forrestchang** — [packaged Karpathy's ideas](https://github.com/forrestchang/andrej-karpathy-skills) as a Claude Code plugin.
- **BuildFutures.ai** — extended the idea into AP-21/22/23, non-coding coverage, and multi-tool distribution.

## License

MIT. Use it anywhere. Fork it. Attribution appreciated but not required.
