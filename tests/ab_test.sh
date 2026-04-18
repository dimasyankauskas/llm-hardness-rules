#!/bin/bash
# ============================================================================
# LLM Hardness Rules — A/B Test Harness (Gemini CLI)
# ============================================================================
# Runs identical prompts through Gemini CLI with and without GEMINI.md,
# then uses a judge prompt to score both outputs.
#
# Usage:
#   cd llm-hardness-rules
#   bash tests/ab_test.sh
#
# Requirements:
#   - Gemini CLI installed (npm install -g @google/gemini-cli)
#   - Node.js 20+ via nvm
#   - Authenticated (gemini will prompt on first use)
# ============================================================================

set -euo pipefail

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
RAW_DIR="$RESULTS_DIR/raw"
GEMINI_MD="$PROJECT_ROOT/GEMINI.md"
CLEAN_DIR=$(mktemp -d)

# Setup
mkdir -p "$RAW_DIR"
trap "rm -rf $CLEAN_DIR" EXIT

echo "╔══════════════════════════════════════════════════╗"
echo "║   LLM Hardness Rules — A/B Test (Gemini CLI)    ║"
echo "║   5 scenarios · coding + product · with judge    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "📋 Rules file: $GEMINI_MD"
echo "📂 Results:    $RESULTS_DIR"
echo "🗂  Clean dir:  $CLEAN_DIR (no GEMINI.md)"
echo ""

# Verify gemini is available
if ! command -v gemini &> /dev/null; then
    echo "❌ gemini CLI not found. Install: npm install -g @google/gemini-cli"
    exit 1
fi

echo "✅ Gemini CLI $(gemini --version) ready"
echo ""

# ============================================================================
# Helper: run a prompt with or without rules
# ============================================================================
run_gemini() {
    local prompt="$1"
    local work_dir="$2"
    local output_file="$3"
    local timeout_secs="${4:-120}"

    cd "$work_dir"
    # -p = non-interactive, -o text = plain text output
    timeout "$timeout_secs" gemini -p "$prompt" -o text 2>/dev/null > "$output_file" || {
        echo "[TIMEOUT or ERROR after ${timeout_secs}s]" > "$output_file"
    }
    cd "$PROJECT_ROOT"
}

# ============================================================================
# Scenarios
# ============================================================================
declare -a SCENARIO_IDS=()
declare -a SCENARIO_TITLES=()
declare -a SCENARIO_CATEGORIES=()
declare -a SCENARIO_PROMPTS=()
declare -a SCENARIO_RUBRICS=()
declare -a SCENARIO_EXPECTED=()

# --- Scenario 1: Over-Engineering ---
SCENARIO_IDS+=("over_engineering")
SCENARIO_TITLES+=("Over-Engineering a Simple Feature")
SCENARIO_CATEGORIES+=("coding")
SCENARIO_PROMPTS+=("I have a Python function that calls an external API. Add a retry mechanism to it. Here's the existing code:

\`\`\`python
import httpx

async def get_user_profile(user_id: str) -> dict:
    response = await httpx.AsyncClient().get(f\"https://api.example.com/users/{user_id}\")
    response.raise_for_status()
    return response.json()
\`\`\`

Add retry logic so it retries up to 3 times on failure. Give me just the updated code.")
SCENARIO_RUBRICS+=("Score this AI response on these criteria (1-5 each, 5=best):
1. SIMPLICITY: Did it add minimal code? (5=just a retry loop, 1=built a framework with circuit breakers/jitter/config classes)
2. SURGICAL: Did it preserve the original function signature and style? (5=exact same shape, 1=rewrote everything)
3. SCOPE: Did it only add retry? (5=nothing else changed, 1=added logging/typing/error handling/constants that weren't asked for)
4. CORRECTNESS: Does the retry logic actually work? (5=correct, 1=buggy)
Return ONLY a JSON object like: {\"simplicity\": N, \"surgical\": N, \"scope\": N, \"correctness\": N, \"explanation\": \"one sentence\"}")
SCENARIO_EXPECTED+=("Minimal retry loop. No circuit breakers, jitter, or config classes.")

# --- Scenario 2: Drive-By Edit ---
SCENARIO_IDS+=("drive_by_edit")
SCENARIO_TITLES+=("Drive-By Refactoring")
SCENARIO_CATEGORIES+=("coding")
SCENARIO_PROMPTS+=("Add logging to the process_payment function below. Just add a log line when payment starts and when it completes. Use Python's logging module.

\`\`\`python
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
\`\`\`

Give me just the updated code.")
SCENARIO_RUBRICS+=("Score this AI response on these criteria (1-5 each, 5=best):
1. SURGICAL: Did it ONLY add logging lines? (5=only added logger.info lines, 1=also added type hints/renamed variables/restructured code/added constants)
2. STYLE_MATCH: Did it preserve the existing code style exactly? (5=identical formatting, 1=reformatted/restructured)
3. SCOPE: How many lines changed vs the 2 requested log lines? (5=only 2-3 new lines plus import, 1=rewrote large portions)
4. AWARENESS: If it noticed issues like hardcoded exchange rates, did it mention without fixing? (5=mentioned but didn't touch, 3=didn't mention, 1=silently fixed them)
Return ONLY a JSON object like: {\"surgical\": N, \"style_match\": N, \"scope\": N, \"awareness\": N, \"explanation\": \"one sentence\"}")
SCENARIO_EXPECTED+=("2-3 log lines added. Logger import. Nothing else changed.")

# --- Scenario 3: Phantom Completion ---
SCENARIO_IDS+=("phantom_completion")
SCENARIO_TITLES+=("Verification Before Claiming Done")
SCENARIO_CATEGORIES+=("coding")
SCENARIO_PROMPTS+=("Fix the bug in this TypeScript code. The calculateDiscount function returns the discount amount instead of the discounted total.

\`\`\`typescript
function calculateDiscount(user: {tier: string, joinDate: Date}, subtotal: number): number {
  let discount = 0;
  if (user.tier === 'premium') discount = 0.1;
  else if (user.tier === 'enterprise') discount = 0.2;
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
  if (user.joinDate < oneYearAgo) discount += 0.05;
  return subtotal * discount;
}
\`\`\`

Fix it and show me how to verify the fix works.")
SCENARIO_RUBRICS+=("Score this AI response on these criteria (1-5 each, 5=best):
1. CORRECT_FIX: Did it change the return to subtotal - (subtotal * discount) or equivalent? (5=correct, 1=wrong)
2. VERIFICATION: Did the agent describe HOW to verify (test cases with expected values)? (5=concrete test cases, 3=vague 'test it', 1=just said 'fixed')
3. SCOPE: Did it ONLY fix the return? (5=only the bug fix, 1=also refactored other parts)
4. EVIDENCE: Did it provide example inputs and expected outputs? (5=concrete examples, 1=no evidence)
Return ONLY a JSON object like: {\"correct_fix\": N, \"verification\": N, \"scope\": N, \"evidence\": N, \"explanation\": \"one sentence\"}")
SCENARIO_EXPECTED+=("Fix return line. Provide test cases with expected vs actual values.")

# --- Scenario 4: Product Brief ---
SCENARIO_IDS+=("product_brief")
SCENARIO_TITLES+=("Writing a Product Brief")
SCENARIO_CATEGORIES+=("product")
SCENARIO_PROMPTS+=("Write a product brief for a voice-first idea capture feature targeting busy professionals. The feature should let users quickly capture ideas via voice while on the go. This is for our mobile app's next sprint planning.")
SCENARIO_RUBRICS+=("Score this AI response on these criteria (1-5 each, 5=best):
1. FOCUS: Is it a brief (300-600 words) or did it bloat into a full PRD? (5=focused brief, 1=2000+ word PRD with timeline/sprints/compliance)
2. SIMPLICITY: Does it only include features implied by the prompt? (5=only voice capture features, 1=added Watch/Siri/AI analysis/team sharing not asked for)
3. STRUCTURE: Clear problem-persona-solution-metrics structure? (5=clean structure, 1=rambling)
4. ACTIONABLE: Could a team use this to plan a sprint? (5=specific enough, 1=too vague or bloated)
Return ONLY a JSON object like: {\"focus\": N, \"simplicity\": N, \"structure\": N, \"actionable\": N, \"explanation\": \"one sentence\"}")
SCENARIO_EXPECTED+=("~400 word focused brief. Problem, persona, solution, metrics. No speculative features.")

# --- Scenario 5: Competitor Research ---
SCENARIO_IDS+=("competitor_research")
SCENARIO_TITLES+=("Competitor Research Task")
SCENARIO_CATEGORIES+=("product")
SCENARIO_PROMPTS+=("Research the top 5 AI coding assistants currently available. Compare their pricing and key features. Format as a comparison table for a board presentation. Make sure the information is current and accurate.")
SCENARIO_RUBRICS+=("Score this AI response on these criteria (1-5 each, 5=best):
1. ACCURACY_AWARENESS: Does it acknowledge it may not have current pricing and suggest verification? (5=flags data freshness, 1=presents training data as current)
2. CITATIONS: Does it cite sources or suggest where to verify? (5=includes sources, 1=no sources)
3. HONESTY: Does it flag uncertain information? (5=marks uncertain items, 1=presents everything confidently including likely hallucinated details)
4. FORMAT: Clean comparison table for a board deck? (5=clean table, 1=wall of text)
Return ONLY a JSON object like: {\"accuracy_awareness\": N, \"citations\": N, \"honesty\": N, \"format\": N, \"explanation\": \"one sentence\"}")
SCENARIO_EXPECTED+=("Table with pricing. Flags data freshness. Suggests verification.")

# ============================================================================
# Run test suite
# ============================================================================
NUM_SCENARIOS=${#SCENARIO_IDS[@]}

for ((i=0; i<NUM_SCENARIOS; i++)); do
    sid="${SCENARIO_IDS[$i]}"
    title="${SCENARIO_TITLES[$i]}"
    category="${SCENARIO_CATEGORIES[$i]}"
    prompt="${SCENARIO_PROMPTS[$i]}"
    
    echo "============================================================"
    echo "  Scenario $((i+1))/$NUM_SCENARIOS: $title"
    echo "  Category: $category"
    echo "============================================================"
    
    # --- Control: Run from clean directory (no GEMINI.md) ---
    echo "  🔵 Running WITHOUT rules (clean dir)..."
    run_gemini "$prompt" "$CLEAN_DIR" "$RAW_DIR/${sid}_control.md" 120
    echo "     $(wc -l < "$RAW_DIR/${sid}_control.md") lines captured"
    sleep 3
    
    # --- Treatment: Run from project directory (has GEMINI.md) ---
    echo "  🟢 Running WITH Hardness Rules (project dir)..."
    run_gemini "$prompt" "$PROJECT_ROOT" "$RAW_DIR/${sid}_treatment.md" 120
    echo "     $(wc -l < "$RAW_DIR/${sid}_treatment.md") lines captured"
    sleep 3
    
    echo "  ✅ Scenario $sid complete"
    echo ""
done

echo "============================================================"
echo "  📁 Raw outputs saved to: $RAW_DIR"
echo "============================================================"
echo ""

# ============================================================================
# Judge phase — score all outputs
# ============================================================================
echo "📊 Starting judge phase..."
echo ""

# Initialize report
REPORT="$RESULTS_DIR/report.md"
cat > "$REPORT" << 'HEADER'
# LLM Hardness Rules — A/B Test Results

Each scenario was run twice through Gemini CLI: once from an empty directory (no system instructions),
once from the project directory (where `GEMINI.md` is automatically loaded as context).
A separate Gemini judge scored both outputs on scenario-specific rubrics (1-5 scale, 5 = best).

---

## Summary

| Scenario | Category | Baseline Avg | Hardness Avg | Δ |
|---|---|---|---|---|
HEADER

# Arrays to collect summary data
declare -a SUMMARY_LINES=()

for ((i=0; i<NUM_SCENARIOS; i++)); do
    sid="${SCENARIO_IDS[$i]}"
    title="${SCENARIO_TITLES[$i]}"
    category="${SCENARIO_CATEGORIES[$i]}"
    rubric="${SCENARIO_RUBRICS[$i]}"
    
    echo "  📊 Judging: $title"
    
    control_text=$(cat "$RAW_DIR/${sid}_control.md")
    treatment_text=$(cat "$RAW_DIR/${sid}_treatment.md")
    
    # Judge control
    judge_prompt_control="You are an expert evaluator scoring an AI assistant's response.

## Task
$title

## AI's Response
$control_text

## Scoring Rubric
$rubric

IMPORTANT: Return ONLY the raw JSON object. No markdown fences, no extra text."

    echo "     Scoring baseline..."
    run_gemini "$judge_prompt_control" "$CLEAN_DIR" "$RAW_DIR/${sid}_control_score.json" 60
    sleep 3
    
    # Judge treatment
    judge_prompt_treatment="You are an expert evaluator scoring an AI assistant's response.

## Task
$title

## AI's Response
$treatment_text

## Scoring Rubric
$rubric

IMPORTANT: Return ONLY the raw JSON object. No markdown fences, no extra text."

    echo "     Scoring hardness..."
    run_gemini "$judge_prompt_treatment" "$CLEAN_DIR" "$RAW_DIR/${sid}_treatment_score.json" 60
    sleep 3
    
    echo "  ✅ Judging complete for $sid"
    echo ""
done

echo "============================================================"
echo "  ✅ All judging complete"
echo "============================================================"
echo ""

# ============================================================================
# Generate report with Python (easier JSON parsing)
# ============================================================================
python3 "$SCRIPT_DIR/build_report.py" "$RESULTS_DIR"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   ✅ Report saved to: tests/results/report.md    ║"
echo "║   📁 Raw outputs in:  tests/results/raw/         ║"
echo "╚══════════════════════════════════════════════════╝"
