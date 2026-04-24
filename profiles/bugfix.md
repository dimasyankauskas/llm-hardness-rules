# Bugfix Profile

Use this profile when the task is a real bug, flaky behavior, failing test, or regression investigation.

## Workflow

1. **Reproduce first:** Run the failing command or capture the failing path before editing.
2. **Read the path, do not guess:** Follow the real code path to the root cause instead of symptom patching.
3. **Write a failing test when practical:** Prefer an automated regression test. If a test is not practical, record the manual repro clearly.
4. **Fix minimally:** Change the smallest amount of code needed to make the failing test or repro pass.
5. **Verify wider safety:** Re-run the direct test, then the relevant package/module test suite, and report the evidence.

## Guardrails

- Do not mix bugfixes with opportunistic refactors.
- If the bug touches shared behavior, summarize the blast radius before changing it.
- If three distinct root-cause hypotheses fail, stop and escalate with the evidence.
