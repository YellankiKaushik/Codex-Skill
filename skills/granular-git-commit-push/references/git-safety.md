# Git Safety

Use this reference before staging, committing, rebasing, or pushing.

## Protected Work

Inspect staged changes with `git diff --cached --name-status` before planning. If unrelated staged work exists, stop and report it. Do not reset the index or mix it into new commits unless the user explicitly says those staged files are part of the plan.

## Targeted Staging

Stage only the intended paths for the current logical unit. Path-scoped `git add -A -- "path"` is acceptable for deletions and renames because it records the tracked path state. Avoid repository-wide staging in generated workflows.

## Sensitive Paths

Stop before committing or pushing unexpected files matching common secret-bearing names, including `.env`, `.env.*`, `credentials.json`, `service-account.json`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `secrets.*`, `private-key.*`, and `firebase-adminsdk*.json`. Respect `.gitignore`. Filename heuristics are a warning, not proof of a secret. Never print secret file contents.

## Remote Safety

Fetch before push. Rebase only when the current state supports a history-preserving rebase. Stop on conflict, divergence that needs judgment, remote mismatch, missing upstream that the user did not authorize, or push failure.

## Prohibited Automation

Do not automatically force-push, hard-reset, clean the repository, remove `.git`, manufacture empty commits, change timestamps, or discard user work. Mention dangerous commands only as things this skill refuses to automate.
