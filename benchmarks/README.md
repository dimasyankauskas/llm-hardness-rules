# Benchmarks

Current benchmark harness for `llm-hardness-rules`.

This directory is the supported evaluation surface. The older experiments under `tests/` are kept as historical lab artifacts, not the current source of truth for public claims.

Codex is the primary validated agent. Other prompt surfaces may remain in the repo, but benchmark claims should come from Codex only.

## Suites

- `core_behavior`: over-engineering, drive-by edits, phantom completion
- `interactive_tool_use`: deceptive bugs, additive features, scoped product deliverables

## Example

```bash
python3 benchmarks/run_suite.py --suite core_behavior --agent codex --runs 3
python3 benchmarks/run_suite.py --suite interactive_tool_use --agent codex --runs 3
python3 benchmarks/render_report.py \
  --core-dir benchmarks/results/<core-dir> \
  --interactive-dir benchmarks/results/<interactive-dir> \
  --output benchmarks/reports/codex-baseline-vs-hardness.md
```

Each run writes:

- `metadata.json`
- `runs.json`
- `summary.md`
- raw outputs per scenario and variant

The committed public artifact is the rendered report under `benchmarks/reports/`. Raw run directories under `benchmarks/results/` stay ignored.

Public release rule:

- hardness must beat or tie baseline in every scenario
- hardness must have zero timeouts
- `roadmap_artifact` must score `3/3` on the hardness side before the report counts as public-release ready
