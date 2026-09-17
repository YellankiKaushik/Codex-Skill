# Permanent Universal Prompt

You are helping with a Git repository using the granular-git-commit-push workflow.

First inspect actual Git state. If `ggcp` is installed, prefer:

```text
ggcp doctor --json
ggcp inspect --json
ggcp plan --json
```

Review the deterministic plan. Improve Conventional Commit messages if needed. Do not change grouping unless separating files would make a commit invalid, unusable, or fundamentally misleading. Then run:

```text
ggcp validate-plan plan.json
ggcp execute --plan plan.json
```

If `ggcp` is unavailable, fall back to safe Git inspection:

- `git status --porcelain=v1 --untracked-files=all`
- `git diff --name-status`
- `git diff --cached --name-status`
- `git branch --show-current`
- `git remote -v`

Default to one independent file per commit. Preserve genuine moves as one commit containing old and new paths. Do not group implementation and test files, docs and code, or files from one directory merely because they are related. Do not split one file into multiple commits merely because it contains multiple hunks.

Protect staged work. If unrelated staged changes exist, stop. Protect suspicious secrets such as `.env`, `.env.*`, `credentials.json`, `service-account.json`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `secrets.*`, `private-key.*`, and `firebase-adminsdk*.json`; do not print secret contents.

Use targeted staging only. Never use force push. Never use destructive reset or clean commands. Never create empty commits, manipulate timestamps, or fabricate source changes.

Before pushing, fetch and rebase safely when appropriate. Stop on conflicts. Recover without duplicating commits that already exist.
