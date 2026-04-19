import sys

with open("tests/ab_test_claude.py", "r") as f:
    code = f.read()

# Replace run_gemini with run_claude
code = code.replace("def run_gemini", "def run_claude")
code = code.replace("run_gemini(", "run_claude(")

# Replace bin locator
old_bin = """# Find gemini binary via nvm
NVM_DIR  = os.path.expanduser("~/.nvm")
NODE_BIN = None
for d in sorted(Path(NVM_DIR, "versions", "node").glob("v*"), reverse=True):
    candidate = d / "bin" / "gemini"
    if candidate.exists():
        NODE_BIN = str(d / "bin")
        break

GEMINI_BIN   = os.path.join(NODE_BIN, "gemini") if NODE_BIN else "gemini"
TIMEOUT_SECS = 240"""

new_bin = """CLAUDE_BIN = "claude"
TIMEOUT_SECS = 240
MODEL_NAME = "glm5.1;cloud\""""
code = code.replace(old_bin, new_bin)

# Remove NODE_BIN references
code = code.replace("    if NODE_BIN:\n        env[\"PATH\"] = NODE_BIN + \":\" + env.get(\"PATH\", \"\")\n", "")
code = code.replace("if NODE_BIN:", "if False:")

# Replace subprocess run logic
old_run = """        result = subprocess.run(
            [GEMINI_BIN, "-p", prompt, "-o", "text"],"""
new_run = """        cmd = [CLAUDE_BIN, "-p", prompt, "--model", MODEL_NAME]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        result = subprocess.run(
            cmd,"""
code = code.replace(old_run, new_run)

# Add system_prompt arg
code = code.replace("def run_claude(prompt: str, work_dir: str, timeout: int = TIMEOUT_SECS) -> str:", "def run_claude(prompt: str, work_dir: str, system_prompt: str = \"\", timeout: int = TIMEOUT_SECS) -> str:")

# Update judge text
code = code.replace("run_claude(s[\"prompt\"], hardness_dir)", "run_claude(s[\"prompt\"], hardness_dir, system_prompt=hardness_rules)")

code = code.replace("GEMINI_BIN", "CLAUDE_BIN")

with open("tests/ab_test_claude.py", "w") as f:
    f.write(code)
