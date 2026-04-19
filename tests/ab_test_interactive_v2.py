#!/usr/bin/env python3
"""
LLM Hardness Rules — Interactive A/B Test v2 (Hard Mode)
=========================================================
Three scenarios designed to exercise rules that DIFFER between
Karpathy and Antigravity:

  Scenario 1: Multi-file deceptive bug (AP-22 Critic-Refiner)
  Scenario 2: Additive feature on working codebase (Anti-Regression)
  Scenario 3: Product task — write a PRD (Non-Coding Coverage)

Usage:
    python3 tests/ab_test_interactive_v2.py
"""

import json
import os
import re
import subprocess
import shutil
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLDS    = PROJECT_ROOT / "tests" / "scaffolds"
RESULTS_DIR  = PROJECT_ROOT / "tests" / "results"
RAW_DIR      = RESULTS_DIR / "raw_interactive_v2"

KARPATHY_MD  = PROJECT_ROOT.parent.parent / "docs" / "references" / "karpathy-skills" / "CLAUDE.md"
OUR_MD       = PROJECT_ROOT / "GEMINI.md"

# Find gemini binary via nvm
NVM_DIR  = os.path.expanduser("~/.nvm")
NODE_BIN = None
for d in sorted(Path(NVM_DIR, "versions", "node").glob("v*"), reverse=True):
    candidate = d / "bin" / "gemini"
    if candidate.exists():
        NODE_BIN = str(d / "bin")
        break

GEMINI_BIN   = os.path.join(NODE_BIN, "gemini") if NODE_BIN else "gemini"
TIMEOUT_SECS = 300


# ---------------------------------------------------------------------------
# Scaffold builders
# ---------------------------------------------------------------------------
sys.path.insert(0, str(SCAFFOLDS.parent))

def setup_multifile_bug(work_dir: str, gemini_md: Path):
    """Scenario 1: multi-file deceptive bug."""
    from scaffolds.multifile_bug import CONFIG_PY, VALIDATOR_PY, TEST_VALIDATION_PY
    wd = Path(work_dir)
    (wd / "config.py").write_text(CONFIG_PY)
    (wd / "validator.py").write_text(VALIDATOR_PY)
    (wd / "test_validation.py").write_text(TEST_VALIDATION_PY)
    shutil.copy(gemini_md, wd / "GEMINI.md")


def setup_additive_feature(work_dir: str, gemini_md: Path):
    """Scenario 2: additive feature on working code."""
    from scaffolds.additive_feature import INVENTORY_PY, TEST_INVENTORY_PY
    wd = Path(work_dir)
    (wd / "inventory.py").write_text(INVENTORY_PY)
    (wd / "test_inventory.py").write_text(TEST_INVENTORY_PY)
    shutil.copy(gemini_md, wd / "GEMINI.md")


def setup_product_task(work_dir: str, gemini_md: Path):
    """Scenario 3: product task — no code, just a writing assignment."""
    wd = Path(work_dir)
    shutil.copy(gemini_md, wd / "GEMINI.md")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_gemini(prompt: str, work_dir: str) -> str:
    """Run gemini CLI with YOLO mode — auto-approve all tool calls."""
    env = os.environ.copy()
    if NODE_BIN:
        env["PATH"] = NODE_BIN + ":" + env.get("PATH", "")

    try:
        result = subprocess.run(
            [GEMINI_BIN, "-p", prompt, "--yolo"],
            capture_output=True,
            text=True,
            cwd=work_dir,
            timeout=TIMEOUT_SECS,
            env=env,
        )
        out = result.stdout.strip()
        if not out and result.stderr:
            out = result.stderr.strip()
        return out if out else "[EMPTY]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


# ---------------------------------------------------------------------------
# Analysis functions per scenario
# ---------------------------------------------------------------------------
def analyze_multifile(output: str, work_dir: str) -> dict:
    """Scenario 1: Did the agent find the root cause in config.py?"""
    wd = Path(work_dir)
    output_lower = output.lower()

    # Check if config.py was modified (the real fix location)
    from scaffolds.multifile_bug import CONFIG_PY, VALIDATOR_PY
    config_modified = False
    validator_modified = False
    if (wd / "config.py").exists():
        config_modified = (wd / "config.py").read_text() != CONFIG_PY
    if (wd / "validator.py").exists():
        validator_modified = (wd / "validator.py").read_text() != VALIDATOR_PY

    # Did the agent find the root cause? (+ in allowed_special_chars)
    found_root_cause = False
    if config_modified:
        config_content = (wd / "config.py").read_text()
        if "+" in config_content:
            found_root_cause = True

    # Did it run tests?
    ran_tests = any(kw in output_lower for kw in [
        "pytest", "python -m pytest", "passed", "failed",
        "test session", "test_email_with_plus",
    ])

    # Did it show passing results?
    showed_proof = any(kw in output for kw in [
        "passed", "PASSED", "9 passed", "10 passed",
    ])

    # Did the bug actually get fixed?
    bug_fixed = False
    try:
        r = subprocess.run(
            ["python3", "-m", "pytest", "test_validation.py", "-v", "--tb=short"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        bug_fixed = r.returncode == 0
    except:
        pass

    return {
        "found_root_cause": found_root_cause,
        "config_modified": config_modified,
        "validator_modified": validator_modified,
        "ran_tests": ran_tests,
        "showed_proof": showed_proof,
        "bug_fixed": bug_fixed,
        "output_lines": len(output.split("\n")),
    }


def analyze_additive(output: str, work_dir: str) -> dict:
    """Scenario 2: Did the agent add the feature without breaking existing tests?"""
    wd = Path(work_dir)
    output_lower = output.lower()

    from scaffolds.additive_feature import INVENTORY_PY, TEST_INVENTORY_PY
    inv_modified = (wd / "inventory.py").read_text() != INVENTORY_PY if (wd / "inventory.py").exists() else False

    # Check if discount method was added
    has_discount = False
    if inv_modified:
        content = (wd / "inventory.py").read_text()
        has_discount = "discount" in content.lower()

    # Did existing tests still pass?
    existing_pass = False
    try:
        r = subprocess.run(
            ["python3", "-m", "pytest", "test_inventory.py", "-v", "--tb=short"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        existing_pass = r.returncode == 0
    except:
        pass

    # Did the agent run tests at all?
    ran_tests = any(kw in output_lower for kw in [
        "pytest", "python -m pytest", "passed", "failed", "test session",
    ])

    # Did it verify EXISTING tests still pass (not just new ones)?
    verified_existing = any(kw in output for kw in [
        "test_add_product", "test_remove_product", "test_total_value",
        "test_low_stock", "test_list_by_category",
    ]) or "9 passed" in output or "10 passed" in output

    # Check for new test files
    new_files = set()
    for f in wd.iterdir():
        if f.is_file() and f.name not in {"inventory.py", "test_inventory.py", "GEMINI.md"}:
            if not f.name.startswith('.') and f.name != '__pycache__':
                new_files.add(f.name)

    return {
        "feature_added": has_discount,
        "existing_tests_pass": existing_pass,
        "ran_tests": ran_tests,
        "verified_existing": verified_existing,
        "new_files": list(new_files),
        "output_lines": len(output.split("\n")),
    }


def analyze_product(output: str, work_dir: str) -> dict:
    """Scenario 3: Product task quality — scope containment, honesty, deliverable focus."""
    lines = output.split("\n")
    word_count = len(output.split())

    # Scope containment: does it bloat beyond the ask?
    bloat_keywords = [
        "apple watch", "siri", "ar ", "vr ", "blockchain",
        "machine learning", "ai-powered", "gamification",
        "social media integration", "metaverse",
    ]
    bloat_count = sum(1 for kw in bloat_keywords if kw in output.lower())

    # Honesty: does it flag data uncertainty?
    honesty_markers = [
        "uncertain", "approximate", "estimate", "verify",
        "as of my", "training data", "may vary", "not confirmed",
        "cannot confirm", "should verify", "caveat",
    ]
    honesty_count = sum(1 for m in honesty_markers if m in output.lower())

    # Structure: does it have clear sections?
    has_structure = any(marker in output for marker in [
        "##", "**Problem", "**Persona", "**Success", "**Metric",
        "| ", "---", "Goal", "Objective",
    ])

    # Deliverable focus: is it a focused document or an open brainstorm?
    is_focused = word_count < 800 and bloat_count == 0

    return {
        "word_count": word_count,
        "line_count": len(lines),
        "bloat_count": bloat_count,
        "honesty_count": honesty_count,
        "has_structure": has_structure,
        "is_focused": is_focused,
        "output_lines": len(lines),
    }


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
SCENARIOS = [
    {
        "name": "Multi-File Deceptive Bug",
        "rule_tested": "AP-22 Critic-Refiner Loop",
        "setup": setup_multifile_bug,
        "analyze": analyze_multifile,
        "prompt": (
            "The test_email_with_plus test in test_validation.py is failing. "
            "Find and fix the root cause. Do not modify the test file. "
            "The bug may not be where you first expect."
        ),
    },
    {
        "name": "Additive Feature (Anti-Regression)",
        "rule_tested": "Anti-Regression Harness",
        "setup": setup_additive_feature,
        "analyze": analyze_additive,
        "prompt": (
            "Add a `apply_discount(name: str, percent: float)` method to the Inventory class "
            "that reduces a product's price by the given percentage. "
            "Add a test for it. Make sure all existing tests still pass."
        ),
    },
    {
        "name": "Product Task (PRD)",
        "rule_tested": "Non-Coding Coverage",
        "setup": setup_product_task,
        "analyze": analyze_product,
        "prompt": (
            "Write a 1-page PRD for adding a 'favorites' feature to a mobile food delivery app. "
            "Include: problem statement, target persona, proposed solution, and 3 success metrics. "
            "Keep it under 500 words. Do not include implementation details or timelines. "
            "Output the PRD as text only — do not create any files."
        ),
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("╭─────────────────────────────────────────────────────────────╮")
    print("│  LLM Hardness Rules — Interactive A/B Test v2 (Hard Mode)  │")
    print("│  3 scenarios targeting our UNIQUE rules vs Karpathy        │")
    print("╰─────────────────────────────────────────────────────────────╯")
    print()

    env = os.environ.copy()
    if NODE_BIN:
        env["PATH"] = NODE_BIN + ":" + env.get("PATH", "")
    ver = subprocess.run([GEMINI_BIN, "--version"], capture_output=True, text=True, env=env)
    print(f"✅ Gemini CLI {ver.stdout.strip()}")

    if not KARPATHY_MD.exists():
        print(f"❌ Karpathy CLAUDE.md not found: {KARPATHY_MD}")
        sys.exit(1)
    if not OUR_MD.exists():
        print(f"❌ Our GEMINI.md not found: {OUR_MD}")
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    conditions = [
        ("Karpathy", KARPATHY_MD),
        ("Antigravity", OUR_MD),
    ]

    all_results = {}

    for scenario in SCENARIOS:
        print(f"\n{'━'*60}")
        print(f"  SCENARIO: {scenario['name']}")
        print(f"  Tests: {scenario['rule_tested']}")
        print(f"{'━'*60}")

        scenario_results = {}

        for cond_name, md_path in conditions:
            print(f"\n  ▶ {cond_name} ({md_path.name})")

            work_dir = tempfile.mkdtemp(prefix=f"hard_{cond_name.lower()}_{scenario['name'][:8].lower().replace(' ','_')}_")
            scenario["setup"](work_dir, md_path)
            print(f"    📂 {work_dir}")

            print(f"    🚀 Running (timeout {TIMEOUT_SECS}s, --yolo)...")
            output = run_gemini(scenario["prompt"], work_dir)

            lines = len(output.split("\n"))
            print(f"    📝 {lines} lines")
            if "[TIMEOUT]" in output:
                print("    ⚠️  TIMEOUT")
            if "[EMPTY]" in output:
                print("    ⚠️  EMPTY RESPONSE")

            # Save raw
            slug = scenario["name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
            (RAW_DIR / f"{slug}_{cond_name.lower()}.md").write_text(output)

            # Analyze
            analysis = scenario["analyze"](output, work_dir)
            scenario_results[cond_name] = {
                "analysis": analysis,
                "work_dir": work_dir,
                "timed_out": "[TIMEOUT]" in output,
            }

            # Print key signals
            print(f"    📊 Signals:")
            for k, v in analysis.items():
                if k != "output_lines":
                    icon = "✅" if v and v is not True and isinstance(v, int) and v > 0 else ("✅" if v is True else ("❌" if v is False else f"  {v}"))
                    if isinstance(v, bool):
                        icon = "✅" if v else "❌"
                    elif isinstance(v, int):
                        icon = str(v)
                    elif isinstance(v, list):
                        icon = str(v) if v else "None"
                    print(f"       {k}: {icon}")

        all_results[scenario["name"]] = scenario_results

    # Build report
    report = build_report_v2(all_results)
    report_path = RESULTS_DIR / "report_interactive_v2.md"
    report_path.write_text(report)

    print(f"\n╔════════════════════════════════════════════════════════════╗")
    print(f"║  ✅ Report: tests/results/report_interactive_v2.md        ║")
    print(f"║  📁 Raw:    tests/results/raw_interactive_v2/             ║")
    print(f"╚════════════════════════════════════════════════════════════╝")


def build_report_v2(all_results: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# LLM Hardness Rules — A/B Test v2 (Hard Mode)",
        "",
        f"**Date:** {now}",
        f"**Model:** Gemini CLI (default, --yolo)",
        "",
        "## Test Design",
        "",
        "Three scenarios targeting rules that *differ* between Karpathy and Antigravity:",
        "",
        "| # | Scenario | Rule Tested | What Makes It Hard |",
        "|---|---|---|---|",
        "| 1 | Multi-file deceptive bug | AP-22 Critic-Refiner | Obvious fix doesn't work; root cause is in a different file |",
        "| 2 | Add feature to working codebase | Anti-Regression | Must not break 9 existing passing tests |",
        "| 3 | Write a PRD (no code) | Non-Coding Coverage | Must stay focused, honest, structured — no bloat |",
        "",
        "---",
    ]

    for scenario_name, results in all_results.items():
        k = results.get("Karpathy", {})
        a = results.get("Antigravity", {})

        lines += [
            "",
            f"## {scenario_name}",
            "",
        ]

        if k.get("timed_out") and a.get("timed_out"):
            lines.append("⚠️ Both conditions timed out.")
            continue

        # Build signal comparison table
        k_analysis = k.get("analysis", {})
        a_analysis = a.get("analysis", {})

        lines += ["| Signal | Karpathy | Antigravity |", "|---|---|---|"]
        for key in k_analysis:
            if key == "output_lines":
                continue
            kv = k_analysis.get(key, "N/A")
            av = a_analysis.get(key, "N/A")
            if isinstance(kv, bool):
                kv = "✅" if kv else "❌"
            if isinstance(av, bool):
                av = "✅" if av else "❌"
            lines.append(f"| {key} | {kv} | {av} |")

        lines.append("")

    lines += [
        "---",
        "",
        "## Methodology",
        "",
        "- `gemini -p <prompt> --yolo` — full tool access, auto-approved",
        "- Fresh temp directory per condition per scenario",
        "- Post-hoc filesystem analysis + output parsing",
        "- Single run — rerun for statistical significance",
        "",
        "### Reproducing",
        "```bash",
        "python3 tests/ab_test_interactive_v2.py",
        "```",
    ]

    return "\n".join(str(l) for l in lines)


if __name__ == "__main__":
    main()
