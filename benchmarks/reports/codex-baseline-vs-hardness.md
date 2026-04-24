# Codex Benchmark Report

Accepted report for the Codex-only release gate.

## Run Metadata

- Agent: `codex`
- Version: `codex-cli 0.122.0`
- Timeout: `180s`
- Runs per scenario: `3`
- Core results dir: `core_behavior-codex-20260422T225035Z`
- Interactive results dir: `interactive_tool_use-codex-20260422T230231Z`

## Summary Table

| Scenario | Baseline pass rate | Hardness pass rate | Hardness timeouts | Verdict |
|---|---:|---:|---:|---|
| over_engineering | 3/3 | 3/3 | 0/3 | TIE |
| drive_by_edit | 3/3 | 3/3 | 0/3 | TIE |
| phantom_completion | 3/3 | 3/3 | 0/3 | TIE |
| multifile_bug | 3/3 | 3/3 | 0/3 | TIE |
| additive_feature | 3/3 | 3/3 | 0/3 | TIE |
| scoped_prd | 3/3 | 3/3 | 0/3 | TIE |
| roadmap_artifact | 0/3 | 1/3 | 0/3 | WIN |

## Release Gate

- Hardness timeouts: `0`
- Gate status: `PASS`

Release gate definition:

- hardness pass rate must be greater than or equal to baseline in every scenario
- hardness must have zero timeouts across all Codex hardness runs

## Reproduce

```bash
python3 benchmarks/run_suite.py --suite core_behavior --agent codex --runs 3
python3 benchmarks/run_suite.py --suite interactive_tool_use --agent codex --runs 3
```
