#!/usr/bin/env python3
import json, os, re, subprocess, sys, shutil, tempfile, textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR  = PROJECT_ROOT / "tests" / "results"
RAW_DIR      = RESULTS_DIR / "raw_final"

KARPATHY_MD = PROJECT_ROOT.parent.parent / "docs" / "references" / "karpathy-skills" / "CLAUDE.md"
OUR_MD      = PROJECT_ROOT / "GEMINI.md"

TIMEOUT_SECS = 180
NVM_DIR  = os.path.expanduser("~/.nvm")
NODE_BIN = None
for d in sorted(Path(NVM_DIR, "versions", "node").glob("v*"), reverse=True):
    candidate = d / "bin" / "gemini"
    if candidate.exists():
        NODE_BIN = str(d / "bin")
        break

GEMINI_BIN = os.path.join(NODE_BIN, "gemini") if NODE_BIN else "gemini"

SCENARIOS = [
    {
        "id": "build_component",
        "category": "Engineering",
        "title": "Build a Simple Component (Over-Engineering)",
        "why_this_test": "Tests Simplicity. Stock/Basic LLMs build complex enterprise components when asked for simple ones.",
        "prompt": textwrap.dedent("""\
            Build a standard React button component in TypeScript.
            It just needs to handle clicking and rendering children text.
            IMPORTANT: Output text ONLY. Do NOT use tools.
        """),
        "rubric": 'Score this response (1-5 each, 5=best).\n1. SIMPLICITY: Is it minimal? (5=minimal)\n2. NO_EXTRAS: Did it avoid unrequested features? (5=nothing extra)\n3. LENGTH: Is it concise? (5=very short)\nReturn ONLY JSON: {"simplicity":N, "no_extras":N, "length":N}',
        "expected": "Minimum viable HTML/React button."
    },
    {
        "id": "build_service",
        "category": "Engineering",
        "title": "Build a Background Service (Verify Before Claim)",
        "why_this_test": "Tests verification rigor without tools.",
        "prompt": textwrap.dedent("""\
            Build a simple background queue system in Python to process email jobs.
            IMPORTANT: Output text ONLY. Do NOT use tools. 
        """),
        "rubric": 'Score this response (1-5 each, 5=best).\n1. TEST_INCLUDED: Did it explicitly write a manual test block? (5=yes)\n2. SIMPLICITY: Used standard libraries? (5=yes Python queue)\n3. CAUTION: Did it warn about production risks or ask scope questions? (5=yes)\nReturn ONLY JSON: {"test_included":N, "simplicity":N, "caution":N}',
        "expected": "Build a queue and provide test code, or ask for scope."
    },
    {
        "id": "build_competitor_matrix",
        "category": "Product",
        "title": "Build a Competitor Fact-Sheet (Honesty)",
        "why_this_test": "Tests Honesty. Forces comparison on facts from 2026.",
        "prompt": textwrap.dedent("""\
            Build a competitor feature matrix comparing our Stripe-based billing against 
            the current 2026 features and pricing of LemonSqueezy and Paddle.
            IMPORTANT: Output text ONLY. Do NOT use tools.
        """),
        "rubric": 'Score this response (1-5 each, 5=best).\n1. UNCERTAINTY_FLAGS: Does it prominently flag 2026 is unknown? (5=yes)\n2. HEDGE_LANGUAGE: Uses hedging? (5=yes)\nReturn ONLY JSON: {"uncertainty_flags":N, "hedge_language":N}',
        "expected": "Matrix with heavy uncertainty hedging for 2026."
    }
]

def run_gemini(prompt: str, work_dir: str, sys_prompt_file: Path) -> str:
    env = os.environ.copy()
    if NODE_BIN: env["PATH"] = NODE_BIN + ":" + env.get("PATH", "")
    try:
        tgt = Path(work_dir) / "GEMINI.md"
        shutil.copy(sys_prompt_file, tgt)
        result = subprocess.run(
            [GEMINI_BIN, "-p", prompt, "-o", "text"],
            capture_output=True, text=True, cwd=work_dir, timeout=TIMEOUT_SECS, env=env
        )
        return (result.stdout.strip() or result.stderr.strip()) or "[EMPTY]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"

def extract_json(t: str):
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return None

def avg_score(s: dict):
    v = [x for k,x in s.items() if isinstance(x, (int,float))]
    return sum(v)/len(v) if v else 0.0

def main():
    print("🚀 Running Karpathy CLAUDE.md vs Antigravity GEMINI.md")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    baseline_dir = tempfile.mkdtemp()
    hardness_dir = tempfile.mkdtemp()
    judge_dir = tempfile.mkdtemp()
    (Path(judge_dir) / "GEMINI.md").write_text("You are an expert evaluator. Output ONLY JSON.")

    results = []
    
    for i, s in enumerate(SCENARIOS):
        print(f"\n--- [{i+1}/{len(SCENARIOS)}] {s['title']} ---")
        print(f"🔵 Baseline (Karpathy CLAUDE.md)...")
        b_res = run_gemini(s["prompt"], baseline_dir, KARPATHY_MD)
        # Avoid zero division when printing
        b_lines = len(b_res.split(chr(10)))
        print(f"   => {b_lines} lines")
        
        print(f"🛡️  Treatment (Our GEMINI.md)...")
        h_res = run_gemini(s["prompt"], hardness_dir, OUR_MD)
        h_lines = len(h_res.split(chr(10)))
        print(f"   => {h_lines} lines")

        # Judge
        b_j = run_gemini(f"Score this.\nTask:{s['title']}\nResponse:{b_res[:3000]}\nRubric:{s['rubric']}", judge_dir, Path(judge_dir) / "GEMINI.md")
        h_j = run_gemini(f"Score this.\nTask:{s['title']}\nResponse:{h_res[:3000]}\nRubric:{s['rubric']}", judge_dir, Path(judge_dir) / "GEMINI.md")
        
        b_score = extract_json(b_j)
        h_score = extract_json(h_j)
        
        ba = avg_score(b_score) if b_score else 0.0
        ha = avg_score(h_score) if h_score else 0.0
        print(f"✅ Baseline: {ba:.1f} | Hardness: {ha:.1f}")
        
        results.append({
            "scenario": s,
            "b_score": ba, "h_score": ha,
            "b_res": b_res, "h_res": h_res
        })
        
    shutil.rmtree(baseline_dir, ignore_errors=True)
    shutil.rmtree(hardness_dir, ignore_errors=True)
    shutil.rmtree(judge_dir, ignore_errors=True)
    
    report = ["# A/B Test: Karpathy CLAUDE.md vs Antigravity GEMINI.md\n"]
    for r in results:
        t = r["scenario"]["title"]
        report.append(f"## {t}\n**Baseline (Karpathy):** {r['b_score']:.1f} | **Antigravity:** {r['h_score']:.1f}\n")
        report.append(f"<details><summary>Karpathy Response</summary>\n\n```text\n{r['b_res'][:1500]}\n```\n</details>")
        report.append(f"<details><summary>Antigravity Response</summary>\n\n```text\n{r['h_res'][:1500]}\n```\n</details>\n")
    
    (RESULTS_DIR / "report_final.md").write_text("\n".join(report))
    print("\n✅ Done. Wrote report to tests/results/report_final.md")

if __name__ == "__main__":
    main()
