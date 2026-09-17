# PowerShell Generation

Use this reference when producing or executing a paste-ready workflow. Windows PowerShell is the primary target.

## Required Shape

Start with a concise count of planned logical commits, then provide one complete PowerShell block. Keep post-script instructions limited to critical notes.

## Required Checks

Generated PowerShell should validate Git exists, validate the repository root, detect the current branch, inspect `origin`, inspect staged changes, inventory all real changes, expand untracked directories, protect suspicious paths, and stop after meaningful failures.

Include this compatibility setting when native command non-zero handling could interfere with expected Git probes:

```powershell
if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}
```

## Staging and Commits

Use targeted staging for each logical unit. Check `$LASTEXITCODE` after important Git commands. Derive the number of commits from before/after revisions or a run counter, not from a hard-coded claim.

## Synchronization

Fetch before pushing. Rebase onto the corresponding remote branch when appropriate. Stop on conflict and do not push. Refuse to push if unexpected files remain after the commit plan.

## Verification

Use:

```powershell
git status
git rev-list --count HEAD
git --no-pager log --oneline -20
```

Always use `--no-pager` for log verification so the user does not land in `(END)`.

## Shell Rules

Do not use Bash syntax in PowerShell examples. Quote paths with `-- "path"` for Git pathspecs. Prefer arrays for file lists. Avoid repository-wide staging when targeted staging is available.
