#!/usr/bin/env python3
"""Render a committed Codex benchmark report from accepted result directories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-dir", required=True)
    parser.add_argument("--interactive-dir", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def load_run_dir(path_str: str) -> tuple[Path, dict, list[dict]]:
    root = Path(path_str)
    metadata = json.loads((root / "metadata.json").read_text())
    runs = json.loads((root / "runs.json").read_text())
    return root, metadata, runs


def summarize_runs(runs: list[dict]) -> dict[str, dict[str, dict[str, int]]]:
    summary: dict[str, dict[str, dict[str, int]]] = {}
    for run in runs:
        scenario = run["scenario"]
        variant = run["variant"]
        bucket = summary.setdefault(scenario, {}).setdefault(
            variant,
            {"runs": 0, "passes": 0, "timeouts": 0},
        )
        bucket["runs"] += 1
        if run["analysis"].get("passed"):
            bucket["passes"] += 1
        if run.get("timed_out"):
            bucket["timeouts"] += 1
    return summary


ABSOLUTE_RELEASE_RULES = {
    "roadmap_artifact": {"hardness_passes": 3, "hardness_timeouts": 0},
}


def scenario_verdict(baseline: dict[str, int], hardness: dict[str, int]) -> str:
    if hardness["passes"] < baseline["passes"]:
        return "FAIL"
    if hardness["timeouts"] > 0:
        return "FAIL"
    if hardness["passes"] > baseline["passes"]:
        return "WIN"
    return "TIE"


def release_bar_status(scenario: str, hardness: dict[str, int]) -> str:
    rule = ABSOLUTE_RELEASE_RULES.get(scenario)
    if not rule:
        return "N/A"
    if hardness["passes"] >= rule["hardness_passes"] and hardness["timeouts"] <= rule["hardness_timeouts"]:
        return "PASS"
    return "FAIL"


def render_report(
    core_root: Path,
    core_meta: dict,
    core_runs: list[dict],
    interactive_root: Path,
    interactive_meta: dict,
    interactive_runs: list[dict],
) -> str:
    all_runs = core_runs + interactive_runs
    summary = summarize_runs(all_runs)

    scenarios = [
        "over_engineering",
        "drive_by_edit",
        "phantom_completion",
        "multifile_bug",
        "additive_feature",
        "scoped_prd",
        "roadmap_artifact",
    ]

    overall_pass = True
    total_hardness_timeouts = 0
    lines = [
        "# Codex Benchmark Report",
        "",
        "Accepted report for the Codex-only release gate.",
        "",
        "## Run Metadata",
        "",
        f"- Agent: `{core_meta['agent']}`",
        f"- Version: `{core_meta.get('agent_version') or 'unknown'}`",
        f"- Timeout: `{core_meta['timeout_seconds']}s`",
        f"- Runs per scenario: `{core_meta['runs_per_scenario']}`",
        f"- Core results dir: `{core_root.name}`",
        f"- Interactive results dir: `{interactive_root.name}`",
        "",
        "## Summary Table",
        "",
        "| Scenario | Baseline pass rate | Hardness pass rate | Hardness timeouts | Relative verdict | Release bar |",
        "|---|---:|---:|---:|---|---|",
    ]

    for scenario in scenarios:
        baseline = summary[scenario]["baseline"]
        hardness = summary[scenario]["hardness"]
        total_hardness_timeouts += hardness["timeouts"]
        verdict = scenario_verdict(baseline, hardness)
        bar_status = release_bar_status(scenario, hardness)
        if verdict == "FAIL":
            overall_pass = False
        if bar_status == "FAIL":
            overall_pass = False
        lines.append(
            f"| {scenario} | {baseline['passes']}/{baseline['runs']} | {hardness['passes']}/{hardness['runs']} | {hardness['timeouts']}/{hardness['runs']} | {verdict} | {bar_status} |"
        )

    if total_hardness_timeouts > 0:
        overall_pass = False

    lines.extend(
        [
            "",
            "## Release Gate",
            "",
            f"- Hardness timeouts: `{total_hardness_timeouts}`",
            f"- Gate status: `{'PASS' if overall_pass else 'FAIL'}`",
            "",
            "Release gate definition:",
            "",
            "- hardness pass rate must be greater than or equal to baseline in every scenario",
            "- hardness must have zero timeouts across all Codex hardness runs",
            "- roadmap_artifact must also score 3/3 on hardness to count as public-release ready",
            "",
            "## Reproduce",
            "",
            "```bash",
            f"python3 benchmarks/run_suite.py --suite core_behavior --agent codex --runs {core_meta['runs_per_scenario']}",
            f"python3 benchmarks/run_suite.py --suite interactive_tool_use --agent codex --runs {interactive_meta['runs_per_scenario']}",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    core_root, core_meta, core_runs = load_run_dir(args.core_dir)
    interactive_root, interactive_meta, interactive_runs = load_run_dir(args.interactive_dir)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_report(
            core_root,
            core_meta,
            core_runs,
            interactive_root,
            interactive_meta,
            interactive_runs,
        )
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
