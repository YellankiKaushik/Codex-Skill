# Recovery

Use this reference after a previous script, commit, rebase, or push failure, or when the user says "again" after a partial run.

## First Inspect

Run `git status`, `git status --porcelain=v1 --untracked-files=all`, `git branch --show-current`, `git remote -v`, and no-pager log/graph commands as needed. Determine what already succeeded before taking action.

## Cases

Changes not yet committed: commit only the remaining legitimate changes.

Commits created locally but not pushed: do not recreate them. Verify the tree, fetch, rebase if appropriate, and push.

Commits already pushed: do not recreate or repush as new commits.

Rebase in progress: inspect status and conflicts. Continue or abort only according to actual state and user intent. Never discard work automatically.

Remote ahead: fetch and rebase safely, stopping on conflicts.

Local ahead: verify there are no unexpected changes, then push.

Diverged history: inspect graph/state and choose a history-preserving reconciliation. Never default to force push.

Push failed after local commits: preserve those commits. Fix the remote, network, hook, authentication, or branch issue; rerun only the synchronization part.

## Pager Trap

If the user is stuck at `(END)`, tell them to press `q`. Continue with `git --no-pager` commands.
