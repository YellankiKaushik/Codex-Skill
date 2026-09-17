# Contributing

Thank you for helping improve Granular Git Commit Push.

Please keep changes focused and include tests for behavior changes. Core workflows must remain compatible with Windows PowerShell.

Do not add features designed to fabricate GitHub contribution history, manufacture empty commits, alter timestamps, automatically force-push, or automatically delete user work. Git-state bugs should include a clear reproduction using temporary repositories or local bare remotes.

Before opening a contribution, run:

```powershell
.\skills\granular-git-commit-push\scripts\Test-Skill.ps1
.\tests\Invoke-IntegrationTests.ps1
```
