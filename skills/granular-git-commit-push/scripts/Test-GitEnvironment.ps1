[CmdletBinding()]
param(
    [string] $RepoPath = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-GitText {
    param([string[]] $Arguments)
    $output = & git @Arguments 2>&1
    [pscustomobject]@{
        Output = @($output)
        ExitCode = $LASTEXITCODE
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git executable was not found on PATH."
}

if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) {
    throw "Repository path does not exist: $RepoPath"
}

Push-Location -LiteralPath $RepoPath
try {
    $root = Invoke-GitText @("rev-parse", "--show-toplevel")
    $isRepo = $root.ExitCode -eq 0
    $branch = Invoke-GitText @("branch", "--show-current")
    $origin = Invoke-GitText @("remote", "get-url", "origin")
    $staged = Invoke-GitText @("diff", "--cached", "--name-status")
    $status = Invoke-GitText @("status", "--porcelain=v1", "--untracked-files=all")

    $gitDirResult = Invoke-GitText @("rev-parse", "--git-dir")
    $gitDir = if ($gitDirResult.ExitCode -eq 0 -and $gitDirResult.Output.Count -gt 0) { [string]$gitDirResult.Output[0] } else { $null }
    $operations = @()
    if ($gitDir) {
        $operationChecks = @{
            RebaseMerge = "rebase-merge"
            RebaseApply = "rebase-apply"
            Merge = "MERGE_HEAD"
            CherryPick = "CHERRY_PICK_HEAD"
        }
        foreach ($name in $operationChecks.Keys) {
            if (Test-Path -LiteralPath (Join-Path $gitDir $operationChecks[$name])) {
                $operations += $name
            }
        }
    }

    [pscustomobject]@{
        RepoPath = (Get-Location).Path
        IsRepository = $isRepo
        RepositoryRoot = if ($isRepo -and $root.Output.Count -gt 0) { [string]$root.Output[0] } else { $null }
        Branch = if ($branch.ExitCode -eq 0 -and $branch.Output.Count -gt 0) { [string]$branch.Output[0] } else { $null }
        OriginUrl = if ($origin.ExitCode -eq 0 -and $origin.Output.Count -gt 0) { [string]$origin.Output[0] } else { $null }
        HasStagedChanges = $staged.ExitCode -eq 0 -and $staged.Output.Count -gt 0
        StagedChanges = @($staged.Output)
        Status = @($status.Output)
        OperationsInProgress = $operations
    }
}
finally {
    Pop-Location
}
