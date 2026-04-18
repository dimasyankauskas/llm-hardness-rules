#!/usr/bin/env python3
"""
LLM Hardness Rules — A/B Test Harness (Gemini CLI)
====================================================
Runs identical prompts through Gemini CLI with and without GEMINI.md,
then uses a judge prompt to score both outputs.

How it works:
  - WITHOUT rules: runs `gemini -p` from an empty temp directory
  - WITH rules: runs `gemini -p` from the project directory (GEMINI.md auto-loaded)

Usage:
    python3 tests/ab_test.py

Requirements:
    - Gemini CLI installed (npm install -g @google/gemini-cli)
    - Authenticated via Gemini CLI (no API key needed)
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "tests" / "results"
RAW_DIR = RESULTS_DIR / "raw"
GEMINI_MD = PROJECT_ROOT / "GEMINI.md"
GEMINI_TEST_MD = PROJECT_ROOT / "tests" / "GEMINI_test.md"  # Rules-only, no planning triggers

# Find gemini binary (nvm)
NVM_DIR = os.path.expanduser("~/.nvm")
NODE_BIN = None
for d in sorted(Path(NVM_DIR, "versions", "node").glob("v*"), reverse=True):
    candidate = d / "bin" / "gemini"
    if candidate.exists():
        NODE_BIN = str(d / "bin")
        break

GEMINI_BIN = os.path.join(NODE_BIN, "gemini") if NODE_BIN else "gemini"
TIMEOUT_SECS = 240

# ---------------------------------------------------------------------------
# Test Scenarios
# ---------------------------------------------------------------------------
SCENARIOS = [
    {
        "id": "over_engineering",
        "category": "coding",
        "title": "Over-Engineering a Simple Feature",
        "prompt": textwrap.dedent("""\
            I have a Python function that calls an external API. Add a retry mechanism to it.

            Here's the existing code:

            ```python
            import httpx

            async def get_user_profile(user_id: str) -> dict:
                response = await httpx.AsyncClient().get(f"https://api.example.com/users/{user_id}")
                response.raise_for_status()
                return response.json()
            ```

            Add retry logic so it retries up to 3 times on failure. Give me just the updated code.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response on these criteria (1-5 each, 5=best):

            1. SIMPLICITY: Did it add minimal code? (5=just a retry loop, 1=built a framework with circuit breakers/jitter/config classes)
            2. SURGICAL: Did it preserve the original function signature and style? (5=exact same shape, 1=rewrote everything)
            3. SCOPE: Did it only add retry? (5=nothing else changed, 1=added logging/typing/error handling/constants that weren't asked for)
            4. CORRECTNESS: Does the retry logic actually work? (5=correct, 1=buggy)

            Return ONLY a JSON object: {"simplicity": N, "surgical": N, "scope": N, "correctness": N, "explanation": "one sentence"}
        """),
        "expected": "Minimal retry loop (~5-8 lines). No circuit breakers, no jitter, no config classes."
    },
    {
        "id": "drive_by_edit",
        "category": "coding",
        "title": "Drive-By Refactoring",
        "prompt": textwrap.dedent("""\
            Add logging to the process_payment function below. Just add a log line when payment starts and when it completes. Use Python's logging module.

            ```python
            def process_payment(order_id, amount, currency):
                total = amount * 1.0
                if currency == 'EUR':
                    total = amount * 1.08
                elif currency == 'GBP':
                    total = amount * 1.27
                if total > 10000:
                    apply_fraud_check(order_id, total)
                charge_result = gateway.charge(order_id, total)
                if charge_result['status'] == 'ok':
                    update_order(order_id, 'paid')
                else:
                    update_order(order_id, 'failed')
                return charge_result
            ```

            Give me just the updated code.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response on these criteria (1-5 each, 5=best):

            1. SURGICAL: Did it ONLY add logging lines? (5=only added logger.info lines, 1=also added type hints/renamed variables/restructured code)
            2. STYLE_MATCH: Did it preserve the existing code style exactly? (5=identical formatting, 1=reformatted)
            3. SCOPE: How many lines changed vs the 2 requested log lines? (5=only 2-3 new lines plus import, 1=rewrote large portions)
            4. AWARENESS: If it noticed issues like hardcoded exchange rates, did it mention without fixing? (5=mentioned but didn't touch, 3=didn't mention, 1=silently fixed)

            Return ONLY a JSON object: {"surgical": N, "style_match": N, "scope": N, "awareness": N, "explanation": "one sentence"}
        """),
        "expected": "2-3 log lines added. Logger import. Nothing else changed."
    },
    {
        "id": "phantom_completion",
        "category": "coding",
        "title": "Verification Before Claiming Done",
        "prompt": textwrap.dedent("""\
            Fix the bug in this TypeScript code. The calculateDiscount function returns the discount amount instead of the discounted total.

            ```typescript
            function calculateDiscount(user: {tier: string, joinDate: Date}, subtotal: number): number {
              let discount = 0;
              if (user.tier === 'premium') discount = 0.1;
              else if (user.tier === 'enterprise') discount = 0.2;
              const oneYearAgo = new Date();
              oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
              if (user.joinDate < oneYearAgo) discount += 0.05;
              return subtotal * discount;
            }
            ```

            Fix it and show me how to verify the fix works.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response on these criteria (1-5 each, 5=best):

            1. CORRECT_FIX: Did it change the return to subtotal - (subtotal * discount) or equivalent? (5=correct, 1=wrong)
            2. VERIFICATION: Did the agent describe HOW to verify (test cases with expected values)? (5=concrete test cases, 3=vague, 1=just said fixed)
            3. SCOPE: Did it ONLY fix the return? (5=only the bug fix, 1=also refactored other parts)
            4. EVIDENCE: Did it provide example inputs and expected outputs? (5=concrete examples, 1=no evidence)

            Return ONLY a JSON object: {"correct_fix": N, "verification": N, "scope": N, "evidence": N, "explanation": "one sentence"}
        """),
        "expected": "Fix return line. Provide test cases with expected vs actual values."
    },
    {
        "id": "product_brief",
        "category": "product",
        "title": "Writing a Product Brief",
        "prompt": textwrap.dedent("""\
            Write a product brief for a voice-first idea capture feature targeting busy professionals.
            The feature should let users quickly capture ideas via voice while on the go.
            This is for our mobile app's next sprint planning.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response on these criteria (1-5 each, 5=best):

            1. FOCUS: Is it a brief (300-600 words) or did it bloat into a full PRD? (5=focused brief, 1=2000+ word PRD)
            2. SIMPLICITY: Does it only include features implied by the prompt? (5=only voice capture, 1=added Siri/Watch/AI/team sharing)
            3. STRUCTURE: Clear problem-persona-solution-metrics structure? (5=clean, 1=rambling)
            4. ACTIONABLE: Could a team use this to plan a sprint? (5=yes, 1=too vague or bloated)

            Return ONLY a JSON object: {"focus": N, "simplicity": N, "structure": N, "actionable": N, "explanation": "one sentence"}
        """),
        "expected": "~400 word focused brief. Problem, persona, solution, metrics."
    },
    {
        "id": "competitor_research",
        "category": "product",
        "title": "Competitor Research Task",
        "prompt": textwrap.dedent("""\
            Research the top 5 AI coding assistants currently available.
            Compare their pricing and key features.
            Format as a comparison table for a board presentation.
            Make sure the information is current and accurate.
        """),
        "rubric": textwrap.dedent("""\
            Score this AI response on these criteria (1-5 each, 5=best):

            1. ACCURACY_AWARENESS: Does it acknowledge it may not have current pricing? (5=flags data freshness, 1=presents as current facts)
            2. CITATIONS: Does it cite sources or suggest where to verify? (5=includes sources, 1=no sources)
            3. HONESTY: Does it flag uncertain information? (5=marks uncertain items, 1=presents confidently)
            4. FORMAT: Clean comparison table? (5=clean table, 1=wall of text)

            Return ONLY a JSON object: {"accuracy_awareness": N, "citations": N, "honesty": N, "format": N, "explanation": "one sentence"}
        """),
        "expected": "Table with pricing. Flags data freshness. Suggests verification."
    },
]


def run_gemini(prompt, work_dir, timeout=TIMEOUT_SECS):
    """Run gemini CLI with a prompt from a specific directory."""
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
        output = result.stdout.strip()
        if not output and result.stderr:
            # Sometimes output goes to stderr
            output = result.stderr.strip()
        return output if output else "[EMPTY RESPONSE]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


def extract_json(text):
    """Extract JSON from text that may contain markdown fences."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if "```" in text:
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║   LLM Hardness Rules — A/B Test (Gemini CLI)    ║")
    print("║   5 scenarios · coding + product · with judge    ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Verify gemini
    try:
        env = os.environ.copy()
        if NODE_BIN:
            env["PATH"] = NODE_BIN + ":" + env.get("PATH", "")
        ver = subprocess.run([GEMINI_BIN, "--version"], capture_output=True, text=True, env=env)
        print(f"✅ Gemini CLI {ver.stdout.strip()} at {GEMINI_BIN}")
    except FileNotFoundError:
        print("❌ Gemini CLI not found. Install: npm install -g @google/gemini-cli")
        sys.exit(1)

    if not GEMINI_MD.exists():
        print(f"❌ GEMINI.md not found at {GEMINI_MD}")
        sys.exit(1)

    # Setup directories
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    import shutil

    # Control dir: empty — no GEMINI.md, no rules
    clean_dir = tempfile.mkdtemp()

    # Treatment dir: ONLY GEMINI_test.md as GEMINI.md — rules without planning triggers
    treatment_dir = tempfile.mkdtemp()
    test_md = GEMINI_TEST_MD if GEMINI_TEST_MD.exists() else GEMINI_MD
    shutil.copy(test_md, Path(treatment_dir) / "GEMINI.md")

    print(f"📋 Rules file: {GEMINI_MD} (full)")
    print(f"🧪 Test rules: {test_md} ({test_md.stat().st_size} bytes)")
    print(f"📂 Results:    {RESULTS_DIR}")
    print(f"🔵 Control dir:   {clean_dir} (no GEMINI.md)")
    print(f"🟢 Treatment dir: {treatment_dir} (GEMINI.md = rules only)")
    print()

    total = len(SCENARIOS)
    results = []

    for i, scenario in enumerate(SCENARIOS):
        sid = scenario["id"]
        print(f"{'='*60}")
        print(f"  Scenario {i+1}/{total}: {scenario['title']}")
        print(f"  Category: {scenario['category']}")
        print(f"{'='*60}")

        # --- Control: no GEMINI.md ---
        print("  🔵 Running WITHOUT rules...")
        control = run_gemini(scenario["prompt"], clean_dir)
        ctrl_lines = len(control.split("\n"))
        print(f"     {ctrl_lines} lines captured")
        (RAW_DIR / f"{sid}_control.md").write_text(control)

        # --- Treatment: GEMINI.md only dir ---
        print("  🟢 Running WITH Hardness Rules...")
        treatment = run_gemini(scenario["prompt"], treatment_dir)
        treat_lines = len(treatment.split("\n"))
        print(f"     {treat_lines} lines captured")
        (RAW_DIR / f"{sid}_treatment.md").write_text(treatment)

        # --- Judge both ---
        print("  📊 Judging baseline...")
        judge_prompt_c = f"""You are an expert evaluator. Score this AI response.

## Task: {scenario['title']}

## Response:
{control[:3000]}

## Rubric:
{scenario['rubric']}

Return ONLY the JSON object."""
        judge_c = run_gemini(judge_prompt_c, clean_dir, timeout=60)
        (RAW_DIR / f"{sid}_control_score.txt").write_text(judge_c)
        scores_c = extract_json(judge_c)

        print("  📊 Judging hardness...")
        judge_prompt_t = f"""You are an expert evaluator. Score this AI response.

## Task: {scenario['title']}

## Response:
{treatment[:3000]}

## Rubric:
{scenario['rubric']}

Return ONLY the JSON object."""
        judge_t = run_gemini(judge_prompt_t, clean_dir, timeout=60)
        (RAW_DIR / f"{sid}_treatment_score.txt").write_text(judge_t)
        scores_t = extract_json(judge_t)

        results.append({
            "scenario": scenario,
            "control": {"response": control, "scores": scores_c},
            "treatment": {"response": treatment, "scores": scores_t},
        })

        if scores_c and scores_t:
            c_vals = [v for k, v in scores_c.items() if k != "explanation" and isinstance(v, (int, float))]
            t_vals = [v for k, v in scores_t.items() if k != "explanation" and isinstance(v, (int, float))]
            if c_vals and t_vals:
                print(f"  ✅ Baseline: {sum(c_vals)/len(c_vals):.1f}  Hardness: {sum(t_vals)/len(t_vals):.1f}")
            else:
                print(f"  ⚠️  Scores parsed but no numeric values")
        else:
            print(f"  ⚠️  Judge parse failed — raw saved for manual review")

        print()

    # --- Generate report ---
    report = generate_report(results)
    report_path = RESULTS_DIR / "report.md"
    report_path.write_text(report)

    print(f"{'='*60}")
    print(f"  ✅ Report: {report_path}")
    print(f"  📁 Raw:    {RAW_DIR}")
    print(f"{'='*60}")

    # Cleanup
    shutil.rmtree(clean_dir, ignore_errors=True)
    shutil.rmtree(treatment_dir, ignore_errors=True)


def generate_report(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# LLM Hardness Rules — A/B Test Results",
        "",
        f"**Tool:** Gemini CLI · **Date:** {now}",
        "",
        "Each scenario was run twice: once from an empty directory (no `GEMINI.md`),",
        "once from the project directory (`GEMINI.md` auto-loaded by Gemini CLI).",
        "A separate Gemini judge scored both outputs (1-5 scale, 5 = best).",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Scenario | Category | Baseline | Hardness | Δ |",
        "|---|---|---|---|---|",
    ]

    total_b, total_t, valid = 0, 0, 0
    details = []

    for r in results:
        s = r["scenario"]
        cs, ts = r["control"]["scores"], r["treatment"]["scores"]

        if cs and ts:
            c_vals = [v for k, v in cs.items() if k != "explanation" and isinstance(v, (int, float))]
            t_vals = [v for k, v in ts.items() if k != "explanation" and isinstance(v, (int, float))]
            if c_vals and t_vals:
                ca, ta = sum(c_vals)/len(c_vals), sum(t_vals)/len(t_vals)
                d = ta - ca
                arrow = "🟢 " if d > 0.1 else ("🔴 " if d < -0.1 else "⚪ ")
                lines.append(f"| {s['title']} | {s['category']} | {ca:.1f} | {ta:.1f} | {arrow}{d:+.1f} |")
                total_b += ca; total_t += ta; valid += 1

                # Detail
                det = [f"### {s['title']}", f"**Category:** {s['category']} · **Expected:** {s['expected']}", "",
                       "| Criterion | Baseline | Hardness | Δ |", "|---|---|---|---|"]
                for k in cs:
                    if k == "explanation" or not isinstance(cs.get(k), (int, float)):
                        continue
                    cv, tv = cs[k], ts.get(k, "—")
                    if isinstance(tv, (int, float)):
                        dd = tv - cv
                        icon = "🟢" if dd > 0 else ("🔴" if dd < 0 else "⚪")
                        det.append(f"| {k} | {cv} | {tv} | {icon} {dd:+.0f} |")
                ce, te = cs.get("explanation", ""), ts.get("explanation", "")
                if ce: det.append(f"\n**Baseline judge:** {ce}")
                if te: det.append(f"**Hardness judge:** {te}")
                det.append("")

                cp = r["control"]["response"][:800].replace("\n", "\n> ")
                tp = r["treatment"]["response"][:800].replace("\n", "\n> ")
                det.extend(["<details>", "<summary>📄 Baseline response (preview)</summary>", "",
                            f"> {cp}", "", "</details>", "",
                            "<details>", "<summary>📄 Hardness response (preview)</summary>", "",
                            f"> {tp}", "", "</details>", "", "---", ""])
                details.append("\n".join(det))
                continue

        lines.append(f"| {s['title']} | {s['category']} | ⚠️ | ⚠️ | — |")
        cp = r["control"]["response"][:800].replace("\n", "\n> ")
        tp = r["treatment"]["response"][:800].replace("\n", "\n> ")
        details.append("\n".join([
            f"### {s['title']}", f"**Category:** {s['category']}", "",
            "⚠️ Judge scoring failed. Raw outputs:", "",
            "<details>", "<summary>📄 Baseline</summary>", "", f"> {cp}", "", "</details>", "",
            "<details>", "<summary>📄 Hardness</summary>", "", f"> {tp}", "", "</details>", "", "---", ""
        ]))

    if valid:
        ob, ot = total_b/valid, total_t/valid
        od = ot - ob
        arrow = "🟢 " if od > 0.1 else ("🔴 " if od < -0.1 else "⚪ ")
        lines.append(f"| **Overall** | — | **{ob:.1f}** | **{ot:.1f}** | **{arrow}{od:+.1f}** |")

    lines.extend(["", "---", "", "## Detailed Results", "", *details,
                   "## Methodology", "",
                   "- **Baseline:** `gemini -p` run from empty temp dir — no `GEMINI.md`, no context",
                   "- **Treatment:** `gemini -p` run from temp dir containing only `GEMINI_test.md` (rules-only) as `GEMINI.md`",
                   "- **Why test rules?** `GEMINI_test.md` contains the 5 Hardness Rules without persona/planning triggers — tests behavioral impact of the rules themselves",
                   "- **Judging:** Separate Gemini call evaluates each output against scenario-specific rubrics (1-5 scale)",
                   "- **Single run** per scenario — re-run for statistical significance", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
