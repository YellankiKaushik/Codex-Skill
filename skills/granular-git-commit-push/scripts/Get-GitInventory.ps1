[CmdletBinding()]
param(
    [string] $RepoPath = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-GitLines {
    param([string[]] $Arguments)
    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    @($output)
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git executable was not found on PATH."
}

Push-Location -LiteralPath $RepoPath
try {
    $root = (Invoke-GitLines @("rev-parse", "--show-toplevel"))[0]
    $branchLines = Invoke-GitLines @("branch", "--show-current")
    $branch = if ($branchLines.Count -gt 0) { [string]$branchLines[0] } else { "" }
    $originOutput = & git remote get-url origin 2>$null
    $origin = if ($LASTEXITCODE -eq 0) { [string]$originOutput } else { $null }
    $statusLines = Invoke-GitLines @("status", "--porcelain=v1", "--untracked-files=all")

    foreach ($line in $statusLines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $indexStatus = $line.Substring(0, 1)
        $workTreeStatus = $line.Substring(1, 1)
        $rawPath = $line.Substring(3)
        $oldPath = $null
        $path = $rawPath

        if ($rawPath -match " -> ") {
            $parts = $rawPath -split " -> ", 2
            $oldPath = $parts[0]
            $path = $parts[1]
        }

        [pscustomobject]@{
            RepositoryRoot = $root
            Branch = $branch
            OriginUrl = $origin
            IndexStatus = $indexStatus
            WorkTreeStatus = $workTreeStatus
            StatusCode = "$indexStatus$workTreeStatus"
            Path = $path
            OldPath = $oldPath
            IsUntracked = $indexStatus -eq "?" -and $workTreeStatus -eq "?"
            IsStaged = $indexStatus -ne " " -and $indexStatus -ne "?"
            IsUnstaged = $workTreeStatus -ne " " -and $workTreeStatus -ne "?"
        }
    }
}
finally {
    Pop-Location
}
