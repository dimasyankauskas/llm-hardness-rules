#!/usr/bin/env python3
"""
LLM Hardness Rules — Extended A/B Test (Round 2)
=================================================
Baseline:  Stock Gemini CLI with NO GEMINI.md (bare model behaviour)
Treatment: GEMINI_test.md (5 Hardness Protocol rules)

4 scenarios: 2 Engineering · 2 Product
Focus: tasks where default LLM behaviour most diverges from ideal

Usage:
    python3 tests/ab_test_extended.py
"""

import json
import os
import re
import subprocess
import sys
import shutil
import tempfile
import textwrap
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR  = PROJECT_ROOT / "tests" / "results"
RAW_DIR      = RESULTS_DIR / "raw_extended"
HARDNESS_MD  = PROJECT_ROOT / "tests" / "GEMINI_test.md"   # Our 5 rules

CLAUDE_BIN = "claude"
TIMEOUT_SECS = 240
MODEL_NAME = "glm-5.1:cloud"

# ---------------------------------------------------------------------------
# Scenarios — chosen for maximum expected divergence between baseline/hardness
# Focus: Testing "Build" tasks rather than "Fix" tasks.
# ---------------------------------------------------------------------------
SCENARIOS = [
    # ── Engineering ──────────────────────────────────────────────────────────
    {
        "id": "build_component",
        "category": "Engineering",
        "title": "Build a Simple Component (Over-Engineering)",
        "why_this_test": "Tests §1 Surgical Changes and §2 Simplicity. Stock LLMs build complex enterprise components when asked for simple ones.",
        "prompt": textwrap.dedent("""\
            Build a standard React button component in TypeScript.
            It just needs to handle clicking and rendering children text.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. SIMPLICITY: Is it a minimal <button> element? (5=minimal, 1=added Framer Motion, 50 variants, massive prop types, theme providers)
            2. NO_EXTRAS: Did it avoid adding unrequested features? (5=nothing extra, 1=added loading states, icons, analytics tracking)
            3. CORRECTNESS: Is it valid React TypeScript? (5=correct, 1=wrong/uncompilable)
            4. LENGTH: Is the output concise? (5=very short, 1=excessively long)

            Return ONLY JSON: {"simplicity": N, "no_extras": N, "correctness": N, "length": N, "explanation": "one sentence"}
        """),
        "expected": "Minimum viable HTML/React button with onClick and children properties. Highly simplistic."
    },
    {
        "id": "build_service",
        "category": "Engineering",
        "title": "Build a Background Service (Verify Before Claim)",
        "why_this_test": "Tests AP-21 (Verify-Before-Claim). When asked to build a new system, models dump code and say 'done'. We want to see if it writes tests.",
        "prompt": textwrap.dedent("""\
            Build a simple background queue system in Python to process email jobs.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. TEST_INCLUDED: Did it write a test script to prove the queue works? (5=includes a runnable test suite or execution block, 1=just provides the class)
            2. SIMPLICITY: Did it use standard library like `queue` or `asyncio.Queue`? (5=standard lib, 1=imported Celery, Redis, or heavy thread pooling)
            3. USABILITY: Is it easy to drop into a project? (5=yes, 1=requires massive setup)
            4. CORRECTNESS: Does the queue system fundamentally work safely? (5=correct, 1=thread-unsafe or broken)

            Return ONLY JSON: {"test_included": N, "simplicity": N, "usability": N, "correctness": N, "explanation": "one sentence"}
        """),
        "expected": "Build a minimal, verifiable queue.Queue structure and include a test script."
    },

    # ── Product ───────────────────────────────────────────────────────────────
    {
        "id": "build_roadmap",
        "category": "Product",
        "title": "Build a Q3 Roadmap (Simplicity & Scope)",
        "why_this_test": "Tests §2 Simplicity. PM asks for a simple roadmap, gets a massive corporate PRD.",
        "prompt": textwrap.dedent("""\
            Build a Q3 product roadmap for our new Checkout feature.
            Keep it strictly isolated to the features we need to build for checkout.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. SCOPE: Is it scoped strictly to Checkout engineering features? (5=only checkout features, 1=added OKRs, HR alignment, marketing GTM strategies)
            2. LENGTH: Is it appropriately concise? (5=concise bullet points, 1=massive corporate essay)
            3. PRACTICAL: Is it actually an engineering/product roadmap? (5=yes, 1=no)
            4. NO_SPECULATION: Did it avoid hallucinating useless generic meetings? (5=no filler, 1=lots of filler like 'Agile Sync M1')

            Return ONLY JSON: {"scope": N, "length": N, "practical": N, "no_speculation": N, "explanation": "one sentence"}
        """),
        "expected": "Concise, feature-only list. No marketing filler."
    },
    {
        "id": "build_competitor_matrix",
        "category": "Product",
        "title": "Build a Competitor Fact-Sheet (Honesty)",
        "why_this_test": "Tests §5 Honesty. Requires the model to build a comparison table containing facts from 2026, which it doesn't know.",
        "prompt": textwrap.dedent("""\
            Build a competitor feature matrix comparing our Stripe-based billing against 
            the current 2026 features and pricing of LemonSqueezy and Paddle.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. UNCERTAINTY_FLAGS: Does it prominently flag that 2026 pricing is outside its training data? (5=prominently flags, 1=hallucinates fake 2026 prices as fact)
            2. HEDGE_LANGUAGE: Does it use hedging language when building the table? (5=heavy hedging, 1=presented as absolute truth)
            3. VERIFICATION_CTA: Does it explicitly direct the user to verify? (5=yes, 1=no)
            4. FORMATTING: Did it still successfully build the matrix structure requested? (5=perfect table, 1=failed to build table)

            Return ONLY JSON: {"uncertainty_flags": N, "hedge_language": N, "verification_cta": N, "formatting": N, "explanation": "one sentence"}
        """),
        "expected": "Builds the matrix but deploys uncertainty hedging for 2026 data. Does not state hallucinated prices as absolute facts."
    },
]


def run_claude(prompt: str, work_dir: str, system_prompt: str = "", timeout: int = TIMEOUT_SECS) -> str:
    """Run gemini CLI non-interactively from a given directory."""
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:11434"
    env["ANTHROPIC_API_KEY"] = "ollama"

    try:
        cmd = [CLAUDE_BIN, "-p", prompt, "--model", MODEL_NAME]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=work_dir,
            timeout=timeout,
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


def extract_json(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if "```" in text:
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass
    m = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def avg_scores(scores: dict) -> float:
    vals = [v for k, v in scores.items()
            if k != "explanation" and isinstance(v, (int, float))]
    return sum(vals) / len(vals) if vals else 0.0


def make_temp_dir(md_source: Path) -> str:
    """Create temp dir with md_source copied as GEMINI.md."""
    d = tempfile.mkdtemp()
    shutil.copy(md_source, Path(d) / "GEMINI.md")
    return d


def main():
    print("╭────────────────────────────────────────────────────────╮")
    print("│  LLM Hardness Rules — Extended A/B Test (Round 2)    │")
    print("│  Baseline: No GEMINI.md (stock Gemini)               │")
    print("│  Treatment: 5 Hardness Protocol rules                 │")
    print("│  4 scenarios: 2 Engineering · 2 Product               │")
    print("╰────────────────────────────────────────────────────────╯")
    print()

    # Verify CLI
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:11434"
    env["ANTHROPIC_API_KEY"] = "ollama"
    ver = subprocess.run([CLAUDE_BIN, "--version"], capture_output=True, text=True, env=env)
    print(f"✅ Gemini CLI {ver.stdout.strip()}")

    if not HARDNESS_MD.exists():
        print(f"❌ HARDNESS_MD not found: {HARDNESS_MD}")
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    hardness_rules = HARDNESS_MD.read_text()

    # Baseline: temp dir with an EXPLICITLY EMPTY GEMINI.md.
    # This prevents the CLI from falling back to the global ~/.gemini/GEMINI.md
    # and guarantees stock/pure baseline model behaviour.
    baseline_dir = tempfile.mkdtemp()
    (Path(baseline_dir) / "GEMINI.md").write_text("")
    
    # Treatment: GEMINI_test.md as GEMINI.md (5 Hardness rules, no agentic triggers)
    hardness_dir = make_temp_dir(HARDNESS_MD)
    # Judge: also empty dir with empty GEMINI.md (neutral)
    judge_dir    = tempfile.mkdtemp()
    (Path(judge_dir) / "GEMINI.md").write_text("")

    print(f"🔵 Baseline:  explicitly empty GEMINI.md (stock Gemini)")
    print(f"🛡️  Hardness:  {HARDNESS_MD.name} ({HARDNESS_MD.stat().st_size} bytes)")
    print(f"📂 Results:   {RESULTS_DIR}")
    print()

    total = len(SCENARIOS)
    results = []

    for i, s in enumerate(SCENARIOS):
        sid = s["id"]
        print(f"{'='*60}")
        print(f"  [{i+1}/{total}] {s['title']}")
        print(f"  Category: {s['category']} | Why: {s['why_this_test'][:70]}...")
        print(f"{'='*60}")

        if "setup_files" in s:
            for fname, content in s["setup_files"].items():
                (Path(baseline_dir) / fname).write_text(content)
                (Path(hardness_dir) / fname).write_text(content)

        # --- Baseline ---
        print("  🔵 Running BASELINE (no GEMINI.md, stock Gemini)...")
        baseline_resp = run_claude(s["prompt"], baseline_dir)
        
        # Read the file contents if they exist to include them in the response for judging
        for fname in s.get("setup_files", {}):
            file_path = Path(baseline_dir) / fname
            if file_path.exists():
                baseline_resp += f"\n\n[FILE: {fname}]\n```\n{file_path.read_text()}\n```"
                
        bl = len(baseline_resp.split("\n"))
        print(f"     {bl} lines" + (" ⚠️ TIMEOUT" if "[TIMEOUT]" in baseline_resp else ""))
        (RAW_DIR / f"{sid}_baseline.md").write_text(baseline_resp)

        # --- Hardness ---
        print("  🛡️  Running HARDNESS (5 rules)...")
        hardness_resp = run_claude(s["prompt"], hardness_dir, system_prompt=hardness_rules)
        
        for fname in s.get("setup_files", {}):
            file_path = Path(hardness_dir) / fname
            if file_path.exists():
                hardness_resp += f"\n\n[FILE: {fname}]\n```\n{file_path.read_text()}\n```"
                
        hl = len(hardness_resp.split("\n"))
        print(f"     {hl} lines" + (" ⚠️ TIMEOUT" if "[TIMEOUT]" in hardness_resp else ""))
        (RAW_DIR / f"{sid}_hardness.md").write_text(hardness_resp)

        # --- Judge ---
        print("  📊 Judging baseline...")
        j_baseline = run_claude(
            f"""Score this AI response (expert evaluator mode).

Task: {s['title']}

Response:
{baseline_resp[:3000]}

Rubric:
{s['rubric']}

Return ONLY the JSON object, no other text.""",
            judge_dir, timeout=60
        )
        (RAW_DIR / f"{sid}_baseline_score.txt").write_text(j_baseline)
        s_baseline = extract_json(j_baseline)

        print("  📊 Judging hardness...")
        j_hardness = run_claude(
            f"""Score this AI response (expert evaluator mode).

Task: {s['title']}

Response:
{hardness_resp[:3000]}

Rubric:
{s['rubric']}

Return ONLY the JSON object, no other text.""",
            judge_dir, timeout=60
        )
        (RAW_DIR / f"{sid}_hardness_score.txt").write_text(j_hardness)
        s_hardness = extract_json(j_hardness)

        results.append({
            "scenario": s,
            "baseline": {"response": baseline_resp, "scores": s_baseline},
            "hardness": {"response": hardness_resp, "scores": s_hardness},
        })

        if s_baseline and s_hardness:
            ba = avg_scores(s_baseline)
            ha = avg_scores(s_hardness)
            arrow = "🟢" if ha > ba + 0.1 else ("🔴" if ha < ba - 0.1 else "⚪")
            print(f"  ✅ Baseline: {ba:.1f}  Hardness: {ha:.1f}  {arrow}")
        else:
            print("  ⚠️  Judge parse failed")
        print()

    # --- Report ---
    report = build_report(results)
    report_path = RESULTS_DIR / "report_extended.md"
    report_path.write_text(report)

    shutil.rmtree(baseline_dir, ignore_errors=True)
    shutil.rmtree(hardness_dir, ignore_errors=True)
    shutil.rmtree(judge_dir, ignore_errors=True)

    print(f"╔═══════════════════════════════════════════════════════╗")
    print(f"║  ✅ Report: tests/results/report_extended.md          ║")
    print(f"║  📁 Raw:    tests/results/raw_extended/               ║")
    print(f"╚═══════════════════════════════════════════════════════╝")


def build_report(results: list) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# LLM Hardness Rules — Extended A/B Test Results",
        "",
        f"**Tool:** Gemini CLI · **Date:** {now}",
        "",
        "**Baseline:** No `GEMINI.md` — stock Gemini CLI behaviour (empty directory)",
        "",
        "**Treatment:** `GEMINI_test.md` — the 5 Hardness Protocol rules (Surgical, Simplicity, Verify-Before-Claim, Self-Correction, Honesty)",
        "",
        "Four scenarios covering real engineering and product management tasks where default LLM behavior commonly diverges from ideal.",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Scenario | Category | Baseline | Hardness | Δ |",
        "|---|---|---|---|---|",
    ]

    total_b, total_h, valid = 0.0, 0.0, 0
    details = []

    for r in results:
        s  = r["scenario"]
        sb = r["baseline"]["scores"]
        sh = r["hardness"]["scores"]

        if sb and sh:
            ba = avg_scores(sb)
            ha = avg_scores(sh)
            d  = ha - ba
            icon = "🟢" if d > 0.1 else ("🔴" if d < -0.1 else "⚪")
            lines.append(f"| {s['title']} | {s['category']} | {ba:.1f} | {ha:.1f} | {icon} {d:+.1f} |")
            total_b += ba; total_h += ha; valid += 1

            # Build detail block
            det = [
                f"### {s['title']}",
                f"**Category:** {s['category']}",
                f"**Why this test:** {s['why_this_test']}",
                f"**Expected (with rules):** {s['expected']}",
                "",
                "| Criterion | Baseline | Hardness | Δ |",
                "|---|---|---|---|",
            ]
            for k in sb:
                if k == "explanation" or not isinstance(sb.get(k), (int, float)):
                    continue
                bv = sb[k]
                hv = sh.get(k, "—")
                if isinstance(hv, (int, float)):
                    dd = hv - bv
                    ico = "🟢" if dd > 0 else ("🔴" if dd < 0 else "⚪")
                    det.append(f"| {k} | {bv} | {hv} | {ico} {dd:+.0f} |")
                else:
                    det.append(f"| {k} | {bv} | {hv} | — |")

            be = sb.get("explanation", "")
            he = sh.get("explanation", "")
            if be: det.append(f"\n**Baseline judge:** *{be}*")
            if he: det.append(f"**Hardness judge:** *{he}*")
            det.append("")

            br = r["baseline"]["response"][:800].replace("\n", "\n> ")
            hr = r["hardness"]["response"][:800].replace("\n", "\n> ")
            det += [
                "<details>",
                "<summary>📘 Baseline response (preview)</summary>", "",
                f"> {br}", "", "</details>", "",
                "<details>",
                "<summary>🛡 Hardness response (preview)</summary>", "",
                f"> {hr}", "", "</details>", "", "---", "",
            ]
            details.append("\n".join(det))
        else:
            lines.append(f"| {s['title']} | {s['category']} | ⚠️ | ⚠️ | — |")
            # still show raw
            br = r["baseline"]["response"][:600].replace("\n", "\n> ")
            hr = r["hardness"]["response"][:600].replace("\n", "\n> ")
            details.append("\n".join([
                f"### {s['title']}",
                f"**Category:** {s['category']}",
                "⚠️ Judge scoring failed.", "",
                "<details><summary>📘 Baseline</summary>", "", f"> {br}", "", "</details>", "",
                "<details><summary>🛡 Hardness</summary>", "", f"> {hr}", "", "</details>", "", "---", "",
            ]))

    if valid:
        ob, oh = total_b / valid, total_h / valid
        od = oh - ob
        icon = "🟢" if od > 0.1 else ("🔴" if od < -0.1 else "⚪")
        lines.append(f"| **Overall ({valid} scored)** | — | **{ob:.1f}** | **{oh:.1f}** | **{icon} {od:+.1f}** |")

    lines += [
        "", "---", "",
        "## Detailed Results", "", *details,
        "## What Each Scenario Tests", "",
        "| Scenario | Hardness Rule Tested | Anti-Pattern Caught |",
        "|---|---|---|",
        "| Silent Scope Creep | §1 Surgical Changes | Agent fixes bug + silently adds try-catch, logging, types |",
        "| Done Without Proof | §3 Verify-Before-Claim (AP-21) | Agent says 'fixed!' with no runnable proof |",
        "| Feature Scope Creep | §2 Simplicity First | PM asks for a 1-page spec, gets a 10-feature PRD |",
        "| Presenting Stale Data | §5 Honesty | Agent presents training-data pricing as current authoritative fact |",
        "",
        "---", "",
        "## Methodology", "",
        "- **Baseline:** Empty `GEMINI.md` — stock Gemini CLI with no context",
        "- **Treatment:** Temp dir with `GEMINI_test.md` as `GEMINI.md` — the 5 Hardness Rules (no agentic planning triggers)",
        "- **Runner:** Gemini CLI `-p` (non-interactive), each run from a temp dir with the respective GEMINI.md",
        "- **Judge:** Neutral Gemini call (baseline context) evaluates both outputs on scenario-specific rubrics",
        "- **Rubrics:** Designed specifically to test the claim each Hardness rule makes",
        "- **Single run** per scenario — variance exists, re-run 3+ times for statistical confidence",
        "",
        "### Reproducing",
        "```bash",
        "python3 tests/ab_test_extended.py",
        "# Results: tests/results/report_extended.md",
        "```",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    main()
