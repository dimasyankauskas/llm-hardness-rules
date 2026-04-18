#!/usr/bin/env python3
"""
Build the final A/B test report from raw outputs and judge scores.
Called by ab_test.sh after all scenarios complete.

Usage: python3 tests/build_report.py tests/results
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

SCENARIOS = [
    {"id": "over_engineering", "title": "Over-Engineering a Simple Feature", "category": "coding",
     "expected": "Minimal retry loop. No circuit breakers, jitter, or config classes."},
    {"id": "drive_by_edit", "title": "Drive-By Refactoring", "category": "coding",
     "expected": "2-3 log lines added. Logger import. Nothing else changed."},
    {"id": "phantom_completion", "title": "Verification Before Claiming Done", "category": "coding",
     "expected": "Fix return line. Provide test cases with expected vs actual values."},
    {"id": "product_brief", "title": "Writing a Product Brief", "category": "product",
     "expected": "~400 word focused brief. Problem, persona, solution, metrics."},
    {"id": "competitor_research", "title": "Competitor Research Task", "category": "product",
     "expected": "Table with pricing. Flags data freshness. Suggests verification."},
]


def extract_json(text):
    """Extract JSON from text that may contain markdown fences or extra content."""
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strip markdown fences
    if "```" in text:
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
    
    # Find JSON-like object in text
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def build_report(results_dir):
    results_dir = Path(results_dir)
    raw_dir = results_dir / "raw"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        "# LLM Hardness Rules — A/B Test Results",
        "",
        f"**Tool:** Gemini CLI · **Date:** {now}",
        "",
        "Each scenario was run twice through Gemini CLI: once from an empty directory (no `GEMINI.md`),",
        "once from the project directory (where `GEMINI.md` is automatically loaded as context).",
        "A separate Gemini judge scored both outputs on scenario-specific rubrics (1-5 scale, 5 = best).",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Scenario | Category | Baseline Avg | Hardness Avg | Δ |",
        "|---|---|---|---|---|",
    ]
    
    total_baseline = 0
    total_treatment = 0
    valid_count = 0
    detail_blocks = []
    
    for s in SCENARIOS:
        sid = s["id"]
        
        # Read score files
        control_score_file = raw_dir / f"{sid}_control_score.json"
        treatment_score_file = raw_dir / f"{sid}_treatment_score.json"
        control_file = raw_dir / f"{sid}_control.md"
        treatment_file = raw_dir / f"{sid}_treatment.md"
        
        control_scores = None
        treatment_scores = None
        
        if control_score_file.exists():
            control_scores = extract_json(control_score_file.read_text())
        if treatment_score_file.exists():
            treatment_scores = extract_json(treatment_score_file.read_text())
        
        # Read response texts
        control_text = control_file.read_text() if control_file.exists() else "[NO OUTPUT]"
        treatment_text = treatment_file.read_text() if treatment_file.exists() else "[NO OUTPUT]"
        
        if control_scores and treatment_scores:
            c_vals = [v for k, v in control_scores.items() 
                      if k != "explanation" and isinstance(v, (int, float))]
            t_vals = [v for k, v in treatment_scores.items() 
                      if k != "explanation" and isinstance(v, (int, float))]
            
            if c_vals and t_vals:
                c_avg = sum(c_vals) / len(c_vals)
                t_avg = sum(t_vals) / len(t_vals)
                delta = t_avg - c_avg
                arrow = "🟢 +" if delta > 0.1 else ("🔴 " if delta < -0.1 else "⚪ ")
                
                total_baseline += c_avg
                total_treatment += t_avg
                valid_count += 1
                
                lines.append(
                    f"| {s['title']} | {s['category']} | {c_avg:.1f} | {t_avg:.1f} | {arrow}{delta:+.1f} |"
                )
                
                # Build detail block
                detail = [
                    f"### {s['title']}",
                    f"**Category:** {s['category']} · **Expected:** {s['expected']}",
                    "",
                    "| Criterion | Baseline | Hardness | Δ |",
                    "|---|---|---|---|",
                ]
                
                criteria = [k for k in control_scores 
                           if k != "explanation" and isinstance(control_scores.get(k), (int, float))]
                for c in criteria:
                    cv = control_scores.get(c, "—")
                    tv = treatment_scores.get(c, "—")
                    if isinstance(cv, (int, float)) and isinstance(tv, (int, float)):
                        d = tv - cv
                        icon = "🟢" if d > 0 else ("🔴" if d < 0 else "⚪")
                        detail.append(f"| {c} | {cv} | {tv} | {icon} {d:+.0f} |")
                    else:
                        detail.append(f"| {c} | {cv} | {tv} | — |")
                
                c_expl = control_scores.get("explanation", "")
                t_expl = treatment_scores.get("explanation", "")
                if c_expl:
                    detail.append(f"\n**Baseline judge:** {c_expl}")
                if t_expl:
                    detail.append(f"**Hardness judge:** {t_expl}")
                
                detail.append("")
                
                # Truncated previews
                c_preview = control_text[:800].replace("\n", "\n> ")
                t_preview = treatment_text[:800].replace("\n", "\n> ")
                
                detail.extend([
                    "<details>",
                    "<summary>📄 Baseline response (preview)</summary>",
                    "",
                    f"> {c_preview}",
                    "",
                    "</details>",
                    "",
                    "<details>",
                    "<summary>📄 Hardness response (preview)</summary>",
                    "",
                    f"> {t_preview}",
                    "",
                    "</details>",
                    "",
                    "---",
                    "",
                ])
                
                detail_blocks.append("\n".join(detail))
            else:
                lines.append(f"| {s['title']} | {s['category']} | ⚠️ No numeric scores | ⚠️ | — |")
        else:
            lines.append(f"| {s['title']} | {s['category']} | ⚠️ Parse error | ⚠️ | — |")
            
            # Still show the raw outputs
            c_preview = control_text[:800].replace("\n", "\n> ")
            t_preview = treatment_text[:800].replace("\n", "\n> ")
            
            detail_blocks.append("\n".join([
                f"### {s['title']}",
                f"**Category:** {s['category']}",
                "",
                "⚠️ Judge scoring failed for this scenario. Raw outputs below.",
                "",
                "<details>",
                "<summary>📄 Baseline response (preview)</summary>",
                "",
                f"> {c_preview}",
                "",
                "</details>",
                "",
                "<details>",
                "<summary>📄 Hardness response (preview)</summary>",
                "",
                f"> {t_preview}",
                "",
                "</details>",
                "",
                "---",
                "",
            ]))
    
    # Overall
    if valid_count > 0:
        ob = total_baseline / valid_count
        ot = total_treatment / valid_count
        od = ot - ob
        arrow = "🟢 +" if od > 0.1 else ("🔴 " if od < -0.1 else "⚪ ")
        lines.append(f"| **Overall Average** | — | **{ob:.1f}** | **{ot:.1f}** | **{arrow}{od:+.1f}** |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ])
    
    lines.extend(detail_blocks)
    
    lines.extend([
        "## Methodology",
        "",
        "- **Tool:** Gemini CLI (non-interactive mode, `-p` flag)",
        "- **Baseline:** Prompt run from an empty temp directory — no `GEMINI.md`, no project context",
        "- **Treatment:** Same prompt run from the project directory — `GEMINI.md` auto-loaded by Gemini CLI",
        "- **Judging:** Separate Gemini call evaluates each output against scenario-specific rubrics",
        "- **Scoring:** 1-5 per criterion, scenario-specific rubrics",
        "",
        "### Why Gemini CLI?",
        "",
        "Gemini CLI automatically reads `GEMINI.md` from the working directory as context.",
        "This means the A/B test closely mirrors real usage — no artificial system-prompt injection,",
        "just the same tool developers actually use, with and without the rules file present.",
        "",
        "### Limitations",
        "",
        "- Single run per scenario (re-run for statistical significance)",
        "- Same model family judges its own outputs (potential self-preference bias)",
        "- Gemini CLI may load additional context from the project directory beyond just `GEMINI.md`",
        "- Rubrics are designed to test Hardness Rules claims specifically",
        "",
    ])
    
    report = "\n".join(lines)
    report_path = results_dir / "report.md"
    report_path.write_text(report)
    print(f"✅ Report generated: {report_path}")
    print(f"   {valid_count}/{len(SCENARIOS)} scenarios scored successfully")
    
    # Print summary to terminal
    for line in lines[:lines.index("---") if "---" in lines else 20]:
        print(line)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 build_report.py <results_dir>")
        sys.exit(1)
    build_report(sys.argv[1])
