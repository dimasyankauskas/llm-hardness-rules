# High-Assurance Profile

Use this profile when the cost of regression is high or the user explicitly wants maximum caution.

## Workflow

1. **Scan impact first:** Grep callers, importers, tests, configs, and docs before changing shared behavior.
2. **Prefer staged edits for broad changes:** Draft larger updates separately, validate them, then apply them surgically.
3. **Protect existing behavior:** After editing, verify the directly affected checks and the broader module/package checks.
4. **Report blast radius:** If the change alters public interfaces or shared behavior, summarize the impact in the final response.

## Guardrails

- Treat public-interface changes as higher risk than local edits.
- Use scratchpad-first thinking for large edits or long documents.
- If the fix or feature unexpectedly fans out across multiple areas, pause and re-evaluate before charging through.
