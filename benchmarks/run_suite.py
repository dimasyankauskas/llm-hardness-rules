#!/usr/bin/env python3
"""Run reproducible benchmark suites for llm-hardness-rules."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from analyzers import ANALYZERS
from scaffolds import SETUP_BUILDERS


ROOT = Path(__file__).resolve().parent.parent
SUITES_DIR = Path(__file__).resolve().parent / "suites"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
SURFACE_FILES = {"gemini": "GEMINI.md", "codex": "AGENTS.md"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, help="Suite name or path")
    parser.add_argument("--agent", choices=["gemini", "codex"], required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--model", default=None)
    parser.add_argument("--scenario", action="append", default=[])
    return parser.parse_args()


def resolve_suite(suite_arg: str) -> tuple[str, list[dict]]:
    suite_path = Path(suite_arg)
    if not suite_path.exists():
        suite_path = SUITES_DIR / f"{suite_arg}.json"
    scenarios = json.loads(suite_path.read_text())
    return suite_path.stem, scenarios


def detect_agent_version(agent: str) -> str | None:
    command = [agent, "--version"]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return None
    output = result.stdout.strip() or result.stderr.strip()
    return output or None


def agent_command(agent: str, prompt: str, work_dir: Path, timeout: int, allow_tools: bool, model: str | None) -> tuple[list[str], dict]:
    env = os.environ.copy()
    if agent == "gemini":
        cmd = ["gemini", "-p", prompt, "--output-format", "text"]
        if allow_tools:
            cmd.append("--yolo")
        if model:
            cmd.extend(["-m", model])
        return cmd, {"env": env, "cwd": work_dir, "timeout": timeout, "capture_output": True, "text": True}

    output_file = work_dir / "codex-last-message.txt"
    cmd = [
        "codex",
        "exec",
        prompt,
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ephemeral",
        "-C",
        str(work_dir),
        "-o",
        str(output_file),
    ]
    if allow_tools:
        cmd.append("--full-auto")
    else:
        cmd.extend(["--sandbox", "read-only"])
    if model:
        cmd.extend(["-m", model])
    return cmd, {"env": env, "cwd": work_dir, "timeout": timeout, "capture_output": True, "text": True}


def prepare_workspace(agent: str, variant: str, scenario: dict) -> Path:
    work_dir = Path(tempfile.mkdtemp(prefix=f"{agent}-{variant}-"))
    setup_name = scenario.get("setup")
    if setup_name:
        SETUP_BUILDERS[setup_name](work_dir)

    if agent == "gemini":
        target = work_dir / "GEMINI.md"
        if variant == "hardness":
            shutil.copy(ROOT / "GEMINI.md", target)
        else:
            target.write_text("")
    elif variant == "hardness":
        shutil.copy(ROOT / "AGENTS.md", work_dir / "AGENTS.md")

    return work_dir


def run_once(agent: str, variant: str, scenario: dict, run_index: int, timeout: int, model: str | None, result_root: Path) -> dict:
    work_dir = prepare_workspace(agent, variant, scenario)
    prompt = scenario["prompt"]
    cmd, kwargs = agent_command(agent, prompt, work_dir, timeout, scenario.get("allow_tools", False), model)
    raw_dir = result_root / "raw" / scenario["id"] / variant
    raw_dir.mkdir(parents=True, exist_ok=True)
    timed_out = False
    try:
        completed = subprocess.run(cmd, **kwargs)
        exit_code = completed.returncode
        output = completed.stdout.strip() or completed.stderr.strip()
        if agent == "codex":
            output_file = work_dir / "codex-last-message.txt"
            if output_file.exists():
                output = output_file.read_text().strip() or output
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        output = f"[TIMEOUT after {timeout}s]\n{exc}"

    analysis = ANALYZERS[scenario["analysis"]](output, work_dir)
    run_data = {
        "scenario": scenario["id"],
        "variant": variant,
        "run_index": run_index,
        "prompt": prompt,
        "agent": agent,
        "allow_tools": scenario.get("allow_tools", False),
        "instruction_surface": SURFACE_FILES[agent] if variant == "hardness" else "(baseline)",
        "command": cmd,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "analysis": analysis,
    }
    (raw_dir / f"run-{run_index}.txt").write_text(output + "\n")
    shutil.rmtree(work_dir, ignore_errors=True)
    return run_data


def build_summary(suite_name: str, agent: str, runs: list[dict], output_dir: Path) -> None:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for run in runs:
        grouped[(run["scenario"], run["variant"])].append(run)

    lines = [
        f"# Benchmark Summary — {suite_name}",
        "",
        f"- Agent: `{agent}`",
        f"- Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "| Scenario | Variant | Pass rate | Timeouts |",
        "|---|---:|---:|---:|",
    ]

    for (scenario, variant), items in sorted(grouped.items()):
        pass_count = sum(1 for item in items if item["analysis"].get("passed"))
        timeout_count = sum(1 for item in items if item["timed_out"])
        lines.append(f"| {scenario} | {variant} | {pass_count}/{len(items)} | {timeout_count}/{len(items)} |")

    (output_dir / "summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    suite_name, scenarios = resolve_suite(args.suite)
    if args.scenario:
        wanted = set(args.scenario)
        scenarios = [scenario for scenario in scenarios if scenario["id"] in wanted]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = RESULTS_DIR / f"{suite_name}-{args.agent}-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "suite": suite_name,
        "agent": args.agent,
        "agent_version": detect_agent_version(args.agent),
        "surface_file": SURFACE_FILES[args.agent],
        "runs_per_scenario": args.runs,
        "timeout_seconds": args.timeout,
        "model": args.model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_ids": [scenario["id"] for scenario in scenarios],
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    run_results: list[dict] = []
    for scenario in scenarios:
        for variant in ("baseline", "hardness"):
            for run_index in range(1, args.runs + 1):
                print(f"{scenario['id']} [{variant}] run {run_index}/{args.runs}")
                run_results.append(
                    run_once(args.agent, variant, scenario, run_index, args.timeout, args.model, output_dir)
                )

    (output_dir / "runs.json").write_text(json.dumps(run_results, indent=2) + "\n")
    build_summary(suite_name, args.agent, run_results, output_dir)
    print(f"Wrote results to {output_dir}")


if __name__ == "__main__":
    main()
