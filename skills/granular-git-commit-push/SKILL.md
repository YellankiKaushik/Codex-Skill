---
name: granular-git-commit-push
description: Safely inspect or reconstruct a Git codebase from screenshots, terminal captures, git status, file trees, repository URLs, or local paths; create many legitimate granular commits where one independent changed file normally becomes one commit; preserve renames, existing history, secrets, staged work, and remote changes; generate or run Windows PowerShell for safe fetch/rebase/push workflows and recover after partial Git failures. Use when the user asks to reconstruct project files from screenshots, split current repository changes into meaningful per-file commits, push many real changes safely, repeat the workflow with "again", or debug a previous granular-commit/push attempt.
---

# Granular Git Commit Push

## Operating contract

Work only from real evidence. Do not create empty commits, edit files merely to create more commits, alter timestamps, discard local work, rebuild history, force-push automatically, or silently stage unrelated files. One independent changed file normally becomes one commit, but preserve logical renames/moves and tightly coupled changes as one unit. Prefer Windows PowerShell unless the user asks for another shell.

## Choose the mode

- Update Mode: default for an existing repository. Preserve history and commit current legitimate changes on top.
- Bootstrap Mode: use only when the user explicitly says the repository/codebase is new. Initialize Git only when `.git` is absent, and preserve remote starter commits.
- Screenshot Reconstruction Mode: use only when the user explicitly asks to create, reconstruct, or update files from screenshots. Read [references/screenshot-reconstruction.md](references/screenshot-reconstruction.md).
- Recovery Mode: use after a previous script, commit, rebase, or push failure. Read [references/recovery.md](references/recovery.md) before acting.

Treat follow-ups such as "again", "do it again", and "same thing" as a request to inspect the current repository state and continue the same workflow, without recreating commits that already exist.

## Establish sources of truth

Before filesystem access, rely on user-supplied screenshots, terminal output, file trees, repository URLs, and paths. During screenshot reconstruction, visible screenshot content is authoritative; never claim collapsed folders, cropped code, or unreadable text was observed. After local filesystem inspection, the filesystem is authoritative for what exists. After Git inspection, Git is authoritative for what changed.

## Build the change inventory

Inspect the repository before planning. Use read-only helpers when useful:

- [scripts/Test-GitEnvironment.ps1](scripts/Test-GitEnvironment.ps1) for repository, branch, origin, operation-in-progress, staged-work, and status checks.
- [scripts/Get-GitInventory.ps1](scripts/Get-GitInventory.ps1) for normalized Git status, branch, and origin data.
- [scripts/Test-SensitivePath.ps1](scripts/Test-SensitivePath.ps1) before staging any new or unexpected path.

Expand untracked directories recursively with Git, for example `git ls-files --others --exclude-standard -- "docs/"`. Respect `.gitignore`. If unrelated staged work exists, stop unless it is explicitly part of the requested plan.

## Build the commit plan

Read [references/commit-planning.md](references/commit-planning.md) for the detailed algorithm. Default to one independent file change per commit. Use Git status, Git diff, path names, and project context to write meaningful Conventional Commit messages. Preserve moves as one commit by staging the old and new paths together; do not split a single move into artificial delete/add commits.

## Execute or generate PowerShell

Read [references/powershell-generation.md](references/powershell-generation.md) when generating or running a full workflow. Use targeted staging only, check `$LASTEXITCODE` after important native commands, stop after meaningful failures, count created commits dynamically, fetch before push, rebase safely when appropriate, and use `git --no-pager log --oneline -20` for final verification.

## Verify before push

Immediately before synchronizing or pushing, run `git status --porcelain=v1 --untracked-files=all`. If unexpected files remain, stop and print the remaining paths. Do not silently ignore, add, or bundle them.

## Synchronize and push

Determine the current branch from Git instead of assuming `main`. Fetch the configured remote, compare local and remote state, rebase onto the upstream branch when appropriate, stop on conflicts, and push only after verification. Never generate or run an automatic force push.

## Recover from partial failure

Preserve already-created commits. Determine whether changes are uncommitted, committed locally but unpushed, already pushed, in a rebase, remote-ahead, local-ahead, or diverged state. Continue only from the remaining real work. If a pager shows `(END)`, tell the user to press `q`, then continue with no-pager commands.

## Load references only as needed

- [references/workflow.md](references/workflow.md): end-to-end mode flow and source-of-truth order.
- [references/screenshot-reconstruction.md](references/screenshot-reconstruction.md): screenshot evidence and file reconstruction rules.
- [references/git-safety.md](references/git-safety.md): staging, secrets, remote, and prohibited-operation safety rules.
- [references/commit-planning.md](references/commit-planning.md): granular commit planning and messages.
- [references/powershell-generation.md](references/powershell-generation.md): paste-ready Windows PowerShell workflow rules.
- [references/recovery.md](references/recovery.md): partial-success and failure recovery procedures.
