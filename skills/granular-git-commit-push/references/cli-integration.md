# CLI Integration

Use this reference when the `ggcp` command is available. The skill supplies reasoning; `ggcp` supplies deterministic Git mechanics.

## Preferred Flow

1. Interpret the user's intent and any screenshots or pasted status.
2. Reconstruct visible files only when explicitly requested.
3. Run `ggcp doctor --json`.
4. Run `ggcp inspect --json`.
5. Run `ggcp plan --json` or `ggcp plan --output plan.json`.
6. Review the deterministic plan. Improve Conventional Commit messages when useful.
7. Change grouping only when unavoidable atomicity makes the default one-file plan invalid or misleading.
8. Run `ggcp validate-plan plan.json`.
9. Run `ggcp execute --plan plan.json` only when the user has authorized commits and push.
10. Explain blockers or recovery states from `ggcp recover --json`.

## Plan Editing

Agents may edit semantic `message` fields. Agents may group entries only when separation would be invalid, unusable, or fundamentally misleading. Do not split one file into multiple commits merely because it has multiple hunks.

## Fallback

If `ggcp` is missing, use Git directly and the bundled helper scripts. Preserve the same safety model: inspect staged work, expand untracked directories, detect sensitive paths, use targeted staging, fetch before push, and never force-push automatically.
