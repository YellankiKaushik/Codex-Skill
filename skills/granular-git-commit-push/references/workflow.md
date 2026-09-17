# Workflow

Use this reference for an end-to-end run after the skill has been selected.

## Modes

Update Mode is the default. Work inside the existing repository, preserve all history, and commit only the current legitimate changes.

Bootstrap Mode applies only when the user explicitly says the repository is new or initial. If `.git` is absent, initialize it locally. If a remote already has starter commits such as README, LICENSE, or `.gitignore`, fetch and integrate them instead of replacing them.

Screenshot Reconstruction Mode applies only when the user explicitly asks to reconstruct or update files from screenshots. Complete reconstruction first, inspect the filesystem, then let Git determine the changed files.

Recovery Mode applies when a previous attempt partially succeeded or failed. Inspect the current state before taking action; never recreate commits that already exist.

## Source Order

Before local access, use screenshots, pasted terminal output, file trees, URLs, and paths as the only evidence. During reconstruction, visible screenshot content outranks guesses. After filesystem inspection, actual files outrank screenshots. After Git inspection, Git status and diffs are authoritative for the change set.

## Standard Flow

1. Confirm the repository path and inspect whether `.git` exists.
2. Run read-only inventory: status, branch, remote, staged diff, unstaged diff, untracked files, and operation-in-progress state.
3. If reconstructing from screenshots, write only visible or safely inferable content, then repeat inventory.
4. Expand untracked directories into real files with Git.
5. Stop for suspicious paths, unrelated staged work, merge/rebase/cherry-pick states, missing branch, missing Git, or remote mismatch.
6. Build a logical commit plan from Git inventory.
7. Stage targeted paths only for each logical unit.
8. Commit with Conventional Commit messages derived from path, diff, and purpose.
9. Verify no unexpected changes remain.
10. Fetch, rebase when appropriate, push, and verify with no-pager logs.

## Stop Conditions

Stop before committing or pushing when evidence is incomplete, a substantial existing file would be overwritten from only partial screenshot data, suspicious secret-like files are present, staged work is unrelated, a rebase or merge conflict exists, a remote has unexpected history, or any post-plan files remain.
