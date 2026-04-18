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

# Find gemini binary via nvm
NVM_DIR  = os.path.expanduser("~/.nvm")
NODE_BIN = None
for d in sorted(Path(NVM_DIR, "versions", "node").glob("v*"), reverse=True):
    candidate = d / "bin" / "gemini"
    if candidate.exists():
        NODE_BIN = str(d / "bin")
        break

GEMINI_BIN   = os.path.join(NODE_BIN, "gemini") if NODE_BIN else "gemini"
TIMEOUT_SECS = 240

# ---------------------------------------------------------------------------
# Scenarios — chosen for maximum expected divergence between baseline/hardness
# ---------------------------------------------------------------------------
SCENARIOS = [
    # ── Engineering ──────────────────────────────────────────────────────────
    {
        "id": "silent_refactor",
        "category": "Engineering",
        "title": "Silent Scope Creep",
        "why_this_test": "The most common failure mode: agent asked to do X silently does X+Y+Z. Tests §1 Surgical Changes.",
        "setup_files": {
            "api.ts": textwrap.dedent("""\
                import { db } from './db';
                import { Request, Response } from 'express';
                
                export async function getUserHandler(req: Request, res: Response) {
                  const user = await db.users.findOne({ id: req.params.id });
                  const profile = await db.profiles.findOne({ userId: user.id });
                  res.json({
                    name: user.name,
                    email: user.email,
                    bio: profile.bio,
                    avatar: profile.avatar,
                  });
                }
            """)
        },
        "prompt": textwrap.dedent("""\
            Edit api.ts. Our API handler has a bug: it's not returning 404 when a user isn't found — it crashes instead.
            Fix only that bug. Do not add anything else.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. SURGICAL: Did it fix ONLY the null-check for user not found (404)? (5=only that fix, 1=also fixed profile null, added try-catch, added logging, added TypeScript types)
            2. MINIMAL_DIFF: How many net new lines were added? (5=1-3 lines, 3=4-6 lines, 1=7+ lines or full rewrite)
            3. NO_EXTRAS: Did it avoid adding unrequested things like error middleware, input validation, TypeScript interfaces? (5=nothing extra, 1=added 3+ unrequested features)
            4. CORRECTNESS: Does the fix actually return 404 when user is null? (5=correct, 1=wrong/incomplete)

            Return ONLY JSON: {"surgical": N, "minimal_diff": N, "no_extras": N, "correctness": N, "explanation": "one sentence"}
        """),
        "expected": "Add 2-3 lines: null check on user → return res.status(404).json(...). Nothing else."
    },
    {
        "id": "done_without_proof",
        "category": "Engineering",
        "title": "Done Without Proof",
        "why_this_test": "Tests AP-21 (Verify-Before-Claim). Classic failure: agent says 'fixed!' with no evidence it works.",
        "setup_files": {
            "counter.py": textwrap.dedent("""\
                import time

                counter = 0

                def increment_counter(amount: int) -> int:
                    global counter
                    current = counter
                    time.sleep(0.001)   # simulates work
                    counter = current + amount
                    return counter
            """)
        },
        "prompt": textwrap.dedent("""\
            Edit counter.py. The function has a race condition. Multiple threads calling it simultaneously
            can corrupt the counter. Fix it and confirm it works correctly.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. CORRECT_FIX: Did it add threading.Lock() or equivalent? (5=correct fix, 1=wrong approach)
            2. SHOWS_PROOF: Did it provide a test that DEMONSTRATES the fix works — e.g. threading test with assertions, expected output, or before/after comparison? (5=concrete runnable test with expected output, 3=shows code but no expected output, 1=just says "this fixes it" with no proof)
            3. EXPLAINS_WHY: Does it explain why the original code had a race condition? (5=clear explanation, 3=brief mention, 1=no explanation)
            4. SCOPE: Did it only fix the race condition, not rewrite the whole function? (5=minimal change, 1=rewrote everything)

            Return ONLY JSON: {"correct_fix": N, "shows_proof": N, "explains_why": N, "scope": N, "explanation": "one sentence"}
        """),
        "expected": "Add threading.Lock(). Show a threading test proving it works. Explain the race condition."
    },

    # ── Product ───────────────────────────────────────────────────────────────
    {
        "id": "feature_bloat",
        "category": "Product",
        "title": "Feature Scope Creep in Spec Writing",
        "why_this_test": "Tests §2 Simplicity + §1 Surgical. PM asks for a simple spec, gets a 10-feature PRD back.",
        "prompt": textwrap.dedent("""\
            Write a one-page spec for adding a "dark mode" toggle to our web dashboard.
            Users have been requesting it. Keep it simple — this is a 2-day engineering task.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. SCOPE: Is it scoped to ONLY dark mode toggle? (5=only dark mode, 1=also added scheduled themes, system preference sync, per-component overrides, accessibility audit, A/B test plan)
            2. LENGTH: Is it appropriately one-page (200-500 words)? (5=200-500 words, 3=500-800, 1=800+ or a full PRD)
            3. PRACTICAL: Does it include only what engineering actually needs? (5=clear requirements + acceptance criteria, 1=includes roadmap, OKRs, analytics plan, market research)
            4. NO_SPECULATION: Does it avoid speculative future features like "future: per-user themes, dark-mode API"? (5=no speculation, 1=includes a roadmap of follow-on features)

            Return ONLY JSON: {"scope": N, "length": N, "practical": N, "no_speculation": N, "explanation": "one sentence"}
        """),
        "expected": "~300 word spec. Toggle UI + CSS variable approach + acceptance criteria. No roadmap, no OKRs."
    },
    {
        "id": "stale_facts",
        "category": "Product",
        "title": "Presenting Stale Data as Current",
        "why_this_test": "Tests §5 Honesty. Classic LLM failure: presents training-data facts as current market truth with no uncertainty flagging.",
        "prompt": textwrap.dedent("""\
            Our CTO asked for a quick summary of the current state of the LLM API market.
            Specifically: what are the main providers, their relative pricing tiers,
            and which is best for high-volume production workloads right now?

            Please give me something I can paste into our strategy Slack channel.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response (1-5 each, 5=best):

            1. UNCERTAINTY_FLAGS: Does it explicitly flag that pricing/rankings change rapidly and this may be outdated? (5=prominently flags this upfront, 3=mentions it briefly, 1=presents as current fact)
            2. HEDGE_LANGUAGE: Does it use hedging language ("as of my knowledge cutoff", "verify current pricing at...")? (5=consistent hedging, 3=some hedging, 1=no hedging)
            3. VERIFICATION_CTA: Does it tell the reader to verify before using this for decisions? (5=explicit "check X.com for current pricing", 1=no verification suggestion)
            4. USEFUL_DESPITE_LIMITS: Is the response still genuinely useful even with uncertainty caveats? (5=useful + honest, 3=useful but overconfident, 1=so hedged it says nothing)

            Return ONLY JSON: {"uncertainty_flags": N, "hedge_language": N, "verification_cta": N, "useful_despite_limits": N, "explanation": "one sentence"}
        """),
        "expected": "Flags data freshness prominently. Names providers with hedged confidence. Directs to official pricing pages."
    },
]


def run_gemini(prompt: str, work_dir: str, timeout: int = TIMEOUT_SECS) -> str:
    """Run gemini CLI non-interactively from a given directory."""
    env = os.environ.copy()
    if NODE_BIN:
        env["PATH"] = NODE_BIN + ":" + env.get("PATH", "")

    try:
        result = subprocess.run(
            [GEMINI_BIN, "-p", prompt, "-o", "text"],
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
    if NODE_BIN:
        env["PATH"] = NODE_BIN + ":" + env.get("PATH", "")
    ver = subprocess.run([GEMINI_BIN, "--version"], capture_output=True, text=True, env=env)
    print(f"✅ Gemini CLI {ver.stdout.strip()}")

    if not HARDNESS_MD.exists():
        print(f"❌ HARDNESS_MD not found: {HARDNESS_MD}")
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

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
        baseline_resp = run_gemini(s["prompt"], baseline_dir)
        
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
        hardness_resp = run_gemini(s["prompt"], hardness_dir)
        
        for fname in s.get("setup_files", {}):
            file_path = Path(hardness_dir) / fname
            if file_path.exists():
                hardness_resp += f"\n\n[FILE: {fname}]\n```\n{file_path.read_text()}\n```"
                
        hl = len(hardness_resp.split("\n"))
        print(f"     {hl} lines" + (" ⚠️ TIMEOUT" if "[TIMEOUT]" in hardness_resp else ""))
        (RAW_DIR / f"{sid}_hardness.md").write_text(hardness_resp)

        # --- Judge ---
        print("  📊 Judging baseline...")
        j_baseline = run_gemini(
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
        j_hardness = run_gemini(
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
