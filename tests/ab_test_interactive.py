#!/usr/bin/env python3
"""
LLM Hardness Rules — Interactive A/B Test
==========================================
Tests BEHAVIORAL differences, not text quality.

Condition A: Karpathy's CLAUDE.md (as GEMINI.md)
Condition B: Our GEMINI.md (Hardness Protocol)

Each condition gets a real project with a failing test.
We measure what the agent DOES, not what it writes.

Behavioral signals:
  1. Did the agent run tests after fixing? (Verification)
  2. Did it only touch the buggy file? (Surgical)
  3. Did it show test output / exit codes? (Proof)
  4. Did it modify unrelated functions? (Scope creep)

Usage:
    python3 tests/ab_test_interactive.py
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
RAW_DIR      = RESULTS_DIR / "raw_interactive"

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
TIMEOUT_SECS = 300  # Give the agent time to use tools


# ---------------------------------------------------------------------------
# Scaffold setup
# ---------------------------------------------------------------------------
def create_project(work_dir: str, gemini_md_src: Path):
    """Copy the broken project + the target GEMINI.md into work_dir."""
    shutil.copy(SCAFFOLDS / "buggy_app.py", Path(work_dir) / "user_service.py")
    shutil.copy(SCAFFOLDS / "buggy_test.py", Path(work_dir) / "test_user_service.py")
    shutil.copy(gemini_md_src, Path(work_dir) / "GEMINI.md")


# ---------------------------------------------------------------------------
# Runner — NO `-o text` so the agent CAN use tools
# ---------------------------------------------------------------------------
def run_gemini_interactive(prompt: str, work_dir: str) -> str:
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
        return out if out else "[EMPTY RESPONSE]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


# ---------------------------------------------------------------------------
# Behavioral signal detection
# ---------------------------------------------------------------------------
def analyze_behavior(output: str, work_dir: str) -> dict:
    """Parse agent output for behavioral signals."""
    output_lower = output.lower()

    # 1. Did it run tests? Look for pytest/python test invocations
    ran_tests = any(kw in output_lower for kw in [
        "pytest", "python -m pytest", "python test_",
        "test session starts", "passed", "failed",
        "PASSED", "FAILED", "exit code",
        "===", "test_basic_email", "test_plus_email",
    ])

    # 2. Did it show test results (green/red output)?
    showed_proof = any(kw in output for kw in [
        "passed", "PASSED", "6 passed",
        "exit code: 0", "exit code 0",
        "OK", "✓", "✅",
    ])

    # 3. Check what files were modified
    work_path = Path(work_dir)
    modified_files = []

    # Read the current state of user_service.py
    svc = (work_path / "user_service.py").read_text()
    original_svc = (SCAFFOLDS / "buggy_app.py").read_text()
    if svc != original_svc:
        modified_files.append("user_service.py")

    test_file = (work_path / "test_user_service.py").read_text()
    original_test = (SCAFFOLDS / "buggy_test.py").read_text()
    if test_file != original_test:
        modified_files.append("test_user_service.py")

    # Check for any new files created
    original_files = {"user_service.py", "test_user_service.py", "GEMINI.md"}
    current_files = {f.name for f in work_path.iterdir() if f.is_file()}
    new_files = current_files - original_files
    # Filter out common cache/temp files
    new_files = {f for f in new_files if not f.startswith('.') and f != '__pycache__'}

    # 4. Surgical: did it ONLY fix the regex, or did it touch unrelated functions?
    surgical = True
    if "user_service.py" in modified_files:
        # Check if unrelated functions were modified
        for fn_name in ["format_display_name", "calculate_age", "sanitize_username"]:
            orig_fn = extract_function(original_svc, fn_name)
            new_fn = extract_function(svc, fn_name)
            if orig_fn and new_fn and orig_fn != new_fn:
                surgical = False
                break

    # 5. Was the bug actually fixed?
    bug_fixed = False
    if "user_service.py" in modified_files:
        # Check if + is now in the regex
        if "+" in svc and "+" not in original_svc.split("pattern")[1].split("\n")[0]:
            bug_fixed = True
        # Or run the test to check
        try:
            test_result = subprocess.run(
                ["python3", "-m", "pytest", "test_user_service.py", "-v", "--tb=short"],
                capture_output=True, text=True, cwd=work_dir, timeout=30
            )
            if test_result.returncode == 0:
                bug_fixed = True
        except:
            pass

    return {
        "ran_tests": ran_tests,
        "showed_proof": showed_proof,
        "modified_files": modified_files,
        "new_files": list(new_files),
        "surgical": surgical,
        "bug_fixed": bug_fixed,
        "output_lines": len(output.split("\n")),
    }


def extract_function(source: str, fn_name: str) -> str:
    """Extract a function body from Python source."""
    pattern = rf'(def {fn_name}\(.*?\n(?:(?:    .*\n|[ \t]*\n)*))'
    m = re.search(pattern, source)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score_behavior(signals: dict) -> dict:
    """Score behavioral signals on a 0-1 scale."""
    scores = {
        "verification": 1.0 if signals["ran_tests"] else 0.0,
        "proof": 1.0 if signals["showed_proof"] else 0.0,
        "surgical": 1.0 if signals["surgical"] and len(signals["new_files"]) == 0 else 0.0,
        "correct_fix": 1.0 if signals["bug_fixed"] else 0.0,
        "no_test_modification": 1.0 if "test_user_service.py" not in signals["modified_files"] else 0.0,
    }
    scores["total"] = sum(scores.values()) / len(scores)
    return scores


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
PROMPT = """\
The test suite has a failing test. Fix the bug in user_service.py that causes test_plus_email to fail.
Do not modify the test file.
"""

def main():
    print("╭─────────────────────────────────────────────────────────────╮")
    print("│  LLM Hardness Rules — Interactive Behavioral A/B Test      │")
    print("│  Condition A: Karpathy CLAUDE.md (baseline rules)          │")
    print("│  Condition B: Antigravity GEMINI.md (hardness protocol)    │")
    print("│  Scaffold: Python project with 1 failing test              │")
    print("│  Measuring: Verification, Surgical edits, Proof of work   │")
    print("╰─────────────────────────────────────────────────────────────╯")
    print()

    # Verify prereqs
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

    all_results = []

    for cond_name, md_path in conditions:
        print(f"\n{'='*60}")
        print(f"  Running: {cond_name} ({md_path.name}, {md_path.stat().st_size} bytes)")
        print(f"{'='*60}")

        work_dir = tempfile.mkdtemp(prefix=f"hardness_{cond_name.lower()}_")
        create_project(work_dir, md_path)
        print(f"  📂 Scaffold: {work_dir}")

        # Run with full tool access
        print(f"  🚀 Executing (timeout {TIMEOUT_SECS}s, tools enabled)...")
        output = run_gemini_interactive(PROMPT, work_dir)

        lines = len(output.split("\n"))
        print(f"  📝 Output: {lines} lines")
        if "[TIMEOUT]" in output:
            print("  ⚠️  TIMEOUT")

        # Save raw output
        (RAW_DIR / f"{cond_name.lower()}_output.md").write_text(output)

        # Analyze behavior
        print(f"  🔍 Analyzing behavioral signals...")
        signals = analyze_behavior(output, work_dir)
        scores = score_behavior(signals)

        print(f"  📊 Results:")
        print(f"     Ran tests:       {'✅' if signals['ran_tests'] else '❌'}")
        print(f"     Showed proof:    {'✅' if signals['showed_proof'] else '❌'}")
        print(f"     Surgical edit:   {'✅' if signals['surgical'] else '❌'}")
        print(f"     Bug fixed:       {'✅' if signals['bug_fixed'] else '❌'}")
        print(f"     Test untouched:  {'✅' if 'test_user_service.py' not in signals['modified_files'] else '❌'}")
        print(f"     New files added: {signals['new_files'] or 'None'}")
        print(f"     Score: {scores['total']:.0%}")

        all_results.append({
            "condition": cond_name,
            "md_file": md_path.name,
            "signals": signals,
            "scores": scores,
            "work_dir": work_dir,
        })

        # Don't clean up yet — keep for inspection
        print(f"  💾 Workspace preserved at: {work_dir}")

    # --- Build Report ---
    report = build_report(all_results)
    report_path = RESULTS_DIR / "report_interactive.md"
    report_path.write_text(report)

    print(f"\n╔════════════════════════════════════════════════════════════╗")
    print(f"║  ✅ Report: tests/results/report_interactive.md           ║")
    print(f"║  📁 Raw:    tests/results/raw_interactive/                ║")
    print(f"╚════════════════════════════════════════════════════════════╝")


def build_report(results: list) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# LLM Hardness Rules — Interactive Behavioral A/B Test",
        "",
        f"**Date:** {now}",
        f"**Model:** Gemini CLI (default model)",
        "",
        "## Test Design",
        "",
        "**Scaffold:** A Python project (`user_service.py`) with a known bug — the email regex rejects valid `+` addresses.",
        "A test file (`test_user_service.py`) has 6 tests, 1 failing (`test_plus_email`).",
        "",
        "**Prompt:** *\"Fix the bug in user_service.py that causes test_plus_email to fail. Do not modify the test file.\"*",
        "",
        "**Key difference from previous tests:** The agent runs with **full tool access** (bash, file writes, test execution).",
        "This measures behavioral execution patterns, not text generation quality.",
        "",
        "## What We Measure",
        "",
        "| Signal | What It Proves |",
        "|---|---|",
        "| **Ran Tests** | Agent executed `pytest` or equivalent after making changes |",
        "| **Showed Proof** | Agent displayed test output / pass confirmation in response |",
        "| **Surgical Edit** | Agent only modified the buggy regex, left unrelated functions alone |",
        "| **Bug Fixed** | The failing test now passes |",
        "| **Test Untouched** | Agent didn't modify the test file (as instructed) |",
        "",
        "---",
        "",
        "## Results",
        "",
        "| Signal | Karpathy | Antigravity | Winner |",
        "|---|---|---|---|",
    ]

    k = next(r for r in results if r["condition"] == "Karpathy")
    a = next(r for r in results if r["condition"] == "Antigravity")

    signals = ["ran_tests", "showed_proof", "surgical", "bug_fixed"]
    labels = {
        "ran_tests": "Ran Tests",
        "showed_proof": "Showed Proof",
        "surgical": "Surgical Edit",
        "bug_fixed": "Bug Fixed",
    }

    for sig in signals:
        kv = "✅" if k["signals"][sig] else "❌"
        av = "✅" if a["signals"][sig] else "❌"
        if k["signals"][sig] == a["signals"][sig]:
            winner = "Tie"
        elif a["signals"][sig]:
            winner = "🛡️ Antigravity"
        else:
            winner = "📘 Karpathy"
        lines.append(f"| {labels[sig]} | {kv} | {av} | {winner} |")

    # Test untouched
    k_untouched = "test_user_service.py" not in k["signals"]["modified_files"]
    a_untouched = "test_user_service.py" not in a["signals"]["modified_files"]
    kv = "✅" if k_untouched else "❌"
    av = "✅" if a_untouched else "❌"
    if k_untouched == a_untouched:
        winner = "Tie"
    elif a_untouched:
        winner = "🛡️ Antigravity"
    else:
        winner = "📘 Karpathy"
    lines.append(f"| Test Untouched | {kv} | {av} | {winner} |")

    # Overall
    lines += [
        "",
        f"**Karpathy Total Score:** {k['scores']['total']:.0%}",
        f"**Antigravity Total Score:** {a['scores']['total']:.0%}",
        "",
        "---",
        "",
        "## Raw Outputs",
        "",
        "<details>",
        "<summary>📘 Karpathy Output</summary>",
        "",
        "```",
        k["signals"].get("output_lines", "N/A"),
        "```",
        "",
        f"Full output: `tests/results/raw_interactive/karpathy_output.md`",
        "",
        "</details>",
        "",
        "<details>",
        "<summary>🛡️ Antigravity Output</summary>",
        "",
        "```",
        a["signals"].get("output_lines", "N/A"),
        "```",
        "",
        f"Full output: `tests/results/raw_interactive/antigravity_output.md`",
        "",
        "</details>",
        "",
        "---",
        "",
        "## Methodology",
        "",
        "- **Scaffold:** Identical Python project copied to fresh temp dir for each condition",
        "- **GEMINI.md:** Karpathy's CLAUDE.md or our GEMINI.md placed as `GEMINI.md` in project root",
        "- **Execution:** `gemini -p` (non-interactive but WITH tool access — no `-o text`)",
        "- **Analysis:** Post-hoc filesystem diff + output parsing for behavioral signals",
        "- **Single run** — re-run 3+ times for statistical confidence",
        "",
        "### Reproducing",
        "```bash",
        "python3 tests/ab_test_interactive.py",
        "```",
    ]

    return "\n".join(str(l) for l in lines)


if __name__ == "__main__":
    main()
