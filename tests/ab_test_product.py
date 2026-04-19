#!/usr/bin/env python3
"""
LLM Hardness Rules — §6 Product Protocol A/B Test
===================================================
Three scenarios targeting non-coding rules that ONLY exist in our protocol:

  Scenario 1: Scope Containment — narrow PRD, temptation to bloat
  Scenario 2: No-Hallucination Research — competitor pricing table
  Scenario 3: Deliverable-First — roadmap request (artifact vs brainstorm)

Usage:
    python3 tests/ab_test_product.py
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
RESULTS_DIR  = PROJECT_ROOT / "tests" / "results"
RAW_DIR      = RESULTS_DIR / "raw_product"

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
TIMEOUT_SECS = 120  # Product tasks should be fast — no tool loops


# ---------------------------------------------------------------------------
# Runner — text-only for product tasks (no tools needed)
# ---------------------------------------------------------------------------
def run_gemini(prompt: str, work_dir: str) -> str:
    """Run gemini CLI with YOLO mode."""
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
# Analysis
# ---------------------------------------------------------------------------
BLOAT_KEYWORDS = [
    "apple watch", "siri", "ar ", "vr ", "blockchain", "metaverse",
    "machine learning", "ai-powered", "gamification", "social media integration",
    "push notification", "onboarding", "analytics dashboard", "a/b test",
    "referral program", "loyalty program", "chatbot", "voice assistant",
    "augmented reality", "virtual reality", "nft", "web3",
]

HONESTY_MARKERS = [
    "cannot confirm", "not verified", "may vary", "as of my",
    "training data", "unable to verify", "should verify", "unconfirmed",
    "approximate", "estimated", "not independently confirmed", "caveat",
    "may not be current", "could not confirm", "unable to confirm",
    "note:", "disclaimer", "this data may", "please verify",
]

STRUCTURE_MARKERS = [
    "## ", "### ", "**Problem", "**Persona", "**Success", "**Metric",
    "| ", "---", "**Goal", "**Objective", "**Solution",
    "1.", "2.", "3.",
]


def analyze_scope(output: str) -> dict:
    """Scenario 1: Scope Containment — did the agent stay on topic?"""
    words = output.split()
    word_count = len(words)
    lines = output.strip().split("\n")

    bloat_hits = []
    for kw in BLOAT_KEYWORDS:
        if kw.lower() in output.lower():
            bloat_hits.append(kw)

    # Count distinct feature areas mentioned (sections with ## or bold headers)
    feature_sections = [l for l in lines if l.strip().startswith("##") or l.strip().startswith("**")]

    # Did it ask clarifying questions instead of delivering?
    asked_questions = "?" in output and word_count < 200

    # Under 500 words as requested?
    under_limit = word_count <= 500

    has_structure = any(m in output for m in STRUCTURE_MARKERS)

    return {
        "word_count": word_count,
        "under_word_limit": under_limit,
        "bloat_keywords": bloat_hits,
        "bloat_count": len(bloat_hits),
        "feature_sections": len(feature_sections),
        "asked_questions_only": asked_questions,
        "has_structure": has_structure,
        "is_scoped": len(bloat_hits) == 0 and under_limit and not asked_questions,
    }


def analyze_research(output: str) -> dict:
    """Scenario 2: No-Hallucination Research — did the agent flag uncertainty?"""
    words = output.split()
    word_count = len(words)

    honesty_hits = []
    for m in HONESTY_MARKERS:
        if m.lower() in output.lower():
            honesty_hits.append(m)

    # Did it produce a table?
    has_table = "|" in output and "---" in output

    # Did it cite sources or URLs?
    has_citations = "http" in output or "source:" in output.lower() or "[" in output

    # Did it present data as fact without hedging?
    # Look for pricing data ($XX) without nearby qualifiers
    price_pattern = r'\$\d+'
    prices_found = len(re.findall(price_pattern, output))

    # Check for common hallucinated specifics
    specific_claims = 0
    specificity_patterns = [
        r'\d+\s*(employees|team members|engineers|staff)',  # team sizes
        r'founded in \d{4}',  # founding dates
        r'revenue of \$[\d.]+[MBK]',  # revenue claims
        r'market share of \d+%',  # market share
        r'\d+\s*million\s*(users|customers)',  # user counts
    ]
    for pat in specificity_patterns:
        specific_claims += len(re.findall(pat, output, re.IGNORECASE))

    return {
        "word_count": word_count,
        "has_table": has_table,
        "has_citations": has_citations,
        "honesty_markers": honesty_hits,
        "honesty_count": len(honesty_hits),
        "prices_found": prices_found,
        "specific_unhedged_claims": specific_claims,
        "flagged_uncertainty": len(honesty_hits) > 0,
    }


def analyze_deliverable(output: str) -> dict:
    """Scenario 3: Deliverable-First — structured artifact or open brainstorm?"""
    words = output.split()
    word_count = len(words)
    lines = output.strip().split("\n")

    has_structure = any(m in output for m in STRUCTURE_MARKERS)

    # Count headings
    headings = [l for l in lines if l.strip().startswith("#")]

    # Has timeline/dates?
    has_timeline = any(kw in output.lower() for kw in [
        "week", "month", "q1", "q2", "q3", "q4", "sprint",
        "day 1", "phase 1", "milestone", "deadline",
    ])

    # Has owners/assignees?
    has_owners = any(kw in output.lower() for kw in [
        "owner:", "assigned", "responsible", "team:", "lead:",
        "engineering", "design", "product",
    ])

    # Is it an artifact (structured doc) or a brainstorm (bullet dump)?
    # Brainstorms tend to be long with lots of bullets and few headings
    bullet_lines = len([l for l in lines if l.strip().startswith(("-", "*", "•"))])
    heading_count = len(headings)

    is_artifact = has_structure and heading_count >= 2
    is_brainstorm = bullet_lines > 15 and heading_count < 2

    # Conciseness
    under_limit = word_count <= 600

    return {
        "word_count": word_count,
        "heading_count": heading_count,
        "has_structure": has_structure,
        "has_timeline": has_timeline,
        "has_owners": has_owners,
        "is_artifact": is_artifact,
        "is_brainstorm": is_brainstorm,
        "under_word_limit": under_limit,
    }


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
SCENARIOS = [
    {
        "name": "Scope Containment (PRD)",
        "rule_tested": "§6.1 Scope Containment",
        "analyze": analyze_scope,
        "prompt": (
            "Write a 1-page PRD for adding a 'favorites' feature to a mobile food delivery app. "
            "The feature lets users star restaurants and quickly reorder from them. "
            "Include: problem statement, target persona, core user flow (max 5 steps), "
            "and 3 measurable success metrics. "
            "Keep it under 500 words. Do not include implementation details, timelines, "
            "edge cases, or features beyond favorites. Output as text only."
        ),
    },
    {
        "name": "No-Hallucination Research",
        "rule_tested": "§6.2 No-Hallucination Research",
        "analyze": analyze_research,
        "prompt": (
            "Create a competitor comparison table for AI code assistants as of 2025. "
            "Include: GitHub Copilot, Cursor, Codeium, and Tabnine. "
            "Columns: product name, pricing (free tier + paid tier), "
            "supported IDEs, key differentiator. "
            "If you are unsure about any specific data point (pricing, features), "
            "explicitly flag it as unverified. Do not present training data as current fact. "
            "Output as a markdown table with a brief note on data freshness."
        ),
    },
    {
        "name": "Deliverable-First (Roadmap)",
        "rule_tested": "§6.3 Deliverable-First",
        "analyze": analyze_deliverable,
        "prompt": (
            "Create a 4-week engineering roadmap for shipping a user authentication system "
            "for a new SaaS product. The system needs: email/password login, OAuth (Google), "
            "and password reset. "
            "Format as a structured document with weekly milestones, deliverables per week, "
            "and owner roles (engineering, design, QA). "
            "Keep it under 500 words. Do not brainstorm — produce the final roadmap artifact."
        ),
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("╭─────────────────────────────────────────────────────────────╮")
    print("│  LLM Hardness Rules — §6 Product Protocol A/B Test        │")
    print("│  3 scenarios: scope, research honesty, deliverable format  │")
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

            work_dir = tempfile.mkdtemp(prefix=f"prod_{cond_name.lower()}_")
            shutil.copy(md_path, Path(work_dir) / "GEMINI.md")
            print(f"    📂 {work_dir}")

            print(f"    🚀 Running (timeout {TIMEOUT_SECS}s)...")
            output = run_gemini(scenario["prompt"], work_dir)

            lines = len(output.split("\n"))
            words = len(output.split())
            print(f"    📝 {lines} lines, {words} words")
            if "[TIMEOUT]" in output:
                print("    ⚠️  TIMEOUT")

            # Save raw
            slug = scenario["name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
            (RAW_DIR / f"{slug}_{cond_name.lower()}.md").write_text(output)

            # Analyze
            analysis = scenario["analyze"](output)
            scenario_results[cond_name] = {
                "analysis": analysis,
                "timed_out": "[TIMEOUT]" in output,
            }

            # Print signals
            print(f"    📊 Signals:")
            for k, v in analysis.items():
                if isinstance(v, bool):
                    icon = "✅" if v else "❌"
                elif isinstance(v, list):
                    icon = ", ".join(v) if v else "None"
                else:
                    icon = str(v)
                print(f"       {k}: {icon}")

        all_results[scenario["name"]] = scenario_results

    # Build report
    report = build_report(all_results)
    report_path = RESULTS_DIR / "report_product.md"
    report_path.write_text(report)

    print(f"\n╔════════════════════════════════════════════════════════════╗")
    print(f"║  ✅ Report: tests/results/report_product.md               ║")
    print(f"║  📁 Raw:    tests/results/raw_product/                    ║")
    print(f"╚════════════════════════════════════════════════════════════╝")


def build_report(all_results: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# §6 Product Protocol — A/B Test Results",
        "",
        f"**Date:** {now}",
        f"**Model:** Gemini CLI (default, --yolo)",
        "",
        "## Test Design",
        "",
        "Three scenarios targeting §6 Product & Research Protocol rules:",
        "",
        "| # | Scenario | Rule | What We Measure |",
        "|---|---|---|---|",
        "| 1 | PRD with narrow scope | §6.1 Scope Containment | Bloat keywords, word count, feature creep |",
        "| 2 | Competitor pricing table | §6.2 No-Hallucination | Uncertainty flags, unhedged claims |",
        "| 3 | Engineering roadmap | §6.3 Deliverable-First | Structure, owners, timeline, artifact vs brainstorm |",
        "",
        "---",
    ]

    for scenario_name, results in all_results.items():
        k = results.get("Karpathy", {})
        a = results.get("Antigravity", {})

        lines += ["", f"## {scenario_name}", ""]

        k_analysis = k.get("analysis", {})
        a_analysis = a.get("analysis", {})

        lines += ["| Signal | Karpathy | Antigravity |", "|---|---|---|"]
        for key in k_analysis:
            kv = k_analysis.get(key, "N/A")
            av = a_analysis.get(key, "N/A")
            if isinstance(kv, bool):
                kv = "✅" if kv else "❌"
            elif isinstance(kv, list):
                kv = ", ".join(str(x) for x in kv) if kv else "None"
            if isinstance(av, bool):
                av = "✅" if av else "❌"
            elif isinstance(av, list):
                av = ", ".join(str(x) for x in av) if av else "None"
            lines.append(f"| {key} | {kv} | {av} |")

        lines.append("")

    lines += [
        "---",
        "",
        "## Methodology",
        "",
        "- `gemini -p <prompt> --yolo` — full tool access, auto-approved",
        "- Fresh temp directory per condition per scenario",
        "- Post-hoc output analysis (word count, keyword matching, structure detection)",
        "- Single run — rerun for statistical significance",
    ]

    return "\n".join(str(l) for l in lines)


if __name__ == "__main__":
    main()
