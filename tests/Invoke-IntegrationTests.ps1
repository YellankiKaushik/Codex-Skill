[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path Variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SensitiveScript = Join-Path $RepoRoot "skills\granular-git-commit-push\scripts\Test-SensitivePath.ps1"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)] [string] $Repo,
        [Parameter(Mandatory = $true)] [string[]] $Args,
        [switch] $AllowFailure
    )

    Push-Location -LiteralPath $Repo
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $output = & git @Args 2>&1
        $exit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        Pop-Location
    }

    if (-not $AllowFailure -and $exit -ne 0) {
        throw "git $($Args -join ' ') failed in $Repo with exit $exit`n$($output -join [Environment]::NewLine)"
    }

    [pscustomobject]@{
        ExitCode = $exit
        Output = @($output)
    }
}

function Initialize-GitRepo {
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [string] $Branch = "main"
    )

    New-Item -ItemType Directory -Path $Path -Force | Out-Null
    $init = Invoke-Git -Repo $Path -Args @("init", "-b", $Branch) -AllowFailure
    if ($init.ExitCode -ne 0) {
        Invoke-Git -Repo $Path -Args @("init") | Out-Null
        Invoke-Git -Repo $Path -Args @("checkout", "-b", $Branch) | Out-Null
    }
    Invoke-Git -Repo $Path -Args @("config", "core.autocrlf", "false") | Out-Null
    Invoke-Git -Repo $Path -Args @("config", "user.email", "test@example.invalid") | Out-Null
    Invoke-Git -Repo $Path -Args @("config", "user.name", "Integration Test") | Out-Null
}

function Write-TestFile {
    param(
        [Parameter(Mandatory = $true)] [string] $Path,
        [Parameter(Mandatory = $true)] [string] $Content
    )

    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function New-TestRepository {
    param(
        [Parameter(Mandatory = $true)] [string] $Root,
        [string] $Branch = "main"
    )

    $remote = Join-Path $Root "remote.git"
    $repo = Join-Path $Root "repo"
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    Invoke-Git -Repo $Root -Args @("init", "--bare", $remote) | Out-Null
    Initialize-GitRepo -Path $repo -Branch $Branch
    Write-TestFile -Path (Join-Path $repo "README.md") -Content "# Test Repo`n"
    Write-TestFile -Path (Join-Path $repo "src\app.txt") -Content "one`n"
    Write-TestFile -Path (Join-Path $repo "src\keep.txt") -Content "keep`n"
    Invoke-Git -Repo $repo -Args @("add", "--", "README.md", "src/app.txt", "src/keep.txt") | Out-Null
    Invoke-Git -Repo $repo -Args @("commit", "-m", "chore: initial test repository") | Out-Null
    Invoke-Git -Repo $repo -Args @("remote", "add", "origin", $remote) | Out-Null
    Invoke-Git -Repo $repo -Args @("push", "-u", "origin", $Branch) | Out-Null

    [pscustomobject]@{
        Repo = $repo
        Remote = $remote
        Branch = $Branch
    }
}

function Get-ChangedPathFromStatusLine {
    param([string] $Line)
    $raw = $Line.Substring(3)
    if ($raw -match " -> ") {
        return ($raw -split " -> ", 2)[1]
    }
    $raw
}

function Get-ConventionalMessage {
    param(
        [string] $Path,
        [string] $Kind
    )

    $leaf = [System.IO.Path]::GetFileNameWithoutExtension($Path)
    $scope = ($leaf -replace '[^A-Za-z0-9-]', '-').Trim('-').ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($scope)) { $scope = "files" }

    if ($Path -match '(^|/)docs?/|\.md$') { return "docs($scope): update $leaf" }
    if ($Path -match '(^|/)tests?/|\.test\.|\.spec\.') { return "test($scope): update $leaf" }
    if ($Path -match 'package\.json$|\.ya?ml$|\.json$') { return "build($scope): update $leaf" }
    if ($Kind -eq "delete") { return "chore($scope): remove $leaf" }
    if ($Kind -eq "move") { return "refactor($scope): move $leaf" }
    if ($Kind -eq "add") { return "feat($scope): add $leaf" }
    "chore($scope): update $leaf"
}

function Sync-Repository {
    param([string] $Repo)

    $branch = (Invoke-Git -Repo $Repo -Args @("branch", "--show-current")).Output[0]
    Invoke-Git -Repo $Repo -Args @("fetch", "origin") | Out-Null
    $remoteBranch = Invoke-Git -Repo $Repo -Args @("rev-parse", "--verify", "origin/$branch") -AllowFailure
    if ($remoteBranch.ExitCode -eq 0) {
        $rebase = Invoke-Git -Repo $Repo -Args @("rebase", "origin/$branch") -AllowFailure
        if ($rebase.ExitCode -ne 0) {
            return [pscustomobject]@{
                Success = $false
                StopReason = "RebaseConflict"
                Output = $rebase.Output
            }
        }
    }

    $push = Invoke-Git -Repo $Repo -Args @("push", "-u", "origin", $branch) -AllowFailure
    if ($push.ExitCode -ne 0) {
        return [pscustomobject]@{
            Success = $false
            StopReason = "PushFailed"
            Output = $push.Output
        }
    }

    Invoke-Git -Repo $Repo -Args @("--no-pager", "log", "--oneline", "-20") | Out-Null
    [pscustomobject]@{
        Success = $true
        StopReason = ""
        Output = @()
    }
}

function Invoke-GranularWorkflow {
    param(
        [Parameter(Mandatory = $true)] [string] $Repo,
        [switch] $SkipPush
    )

    $created = 0
    $staged = Invoke-Git -Repo $Repo -Args @("diff", "--cached", "--name-status")
    if ($staged.Output.Count -gt 0) {
        return [pscustomobject]@{ Success = $false; StopReason = "UnrelatedStagedWork"; CreatedCommitCount = 0 }
    }

    $status = Invoke-Git -Repo $Repo -Args @("status", "--porcelain=v1", "--untracked-files=all")
    if ($status.Output.Count -eq 0) {
        if (-not $SkipPush) {
            $sync = Sync-Repository -Repo $Repo
            return [pscustomobject]@{ Success = $sync.Success; StopReason = if ($sync.Success) { "NoChanges" } else { $sync.StopReason }; CreatedCommitCount = 0 }
        }
        return [pscustomobject]@{ Success = $true; StopReason = "NoChanges"; CreatedCommitCount = 0 }
    }

    $paths = foreach ($line in $status.Output) { Get-ChangedPathFromStatusLine -Line $line }
    $sensitive = @(& $SensitiveScript -Path $paths | Where-Object { $_.IsSensitive })
    if ($sensitive.Count -gt 0) {
        return [pscustomobject]@{ Success = $false; StopReason = "SensitivePath"; CreatedCommitCount = 0; SensitivePaths = @($sensitive.Path) }
    }

    $entries = foreach ($line in $status.Output) {
        $code = $line.Substring(0, 2)
        $path = Get-ChangedPathFromStatusLine -Line $line
        [pscustomobject]@{
            Code = $code
            Path = $path
            IsDeleted = $code.Contains("D")
            IsUntracked = $code -eq "??"
            Used = $false
        }
    }

    $plans = New-Object System.Collections.Generic.List[object]
    foreach ($deleted in @($entries | Where-Object { $_.IsDeleted })) {
        $deletedLeaf = Split-Path -Leaf $deleted.Path
        $candidate = @($entries | Where-Object { -not $_.Used -and ($_.IsUntracked -or $_.Code.Contains("A")) -and (Split-Path -Leaf $_.Path) -eq $deletedLeaf } | Select-Object -First 1)
        if ($candidate.Count -gt 0) {
            $deleted.Used = $true
            $candidate[0].Used = $true
            $plans.Add([pscustomobject]@{
                Kind = "move"
                Paths = @($deleted.Path, $candidate[0].Path)
                Message = Get-ConventionalMessage -Path $candidate[0].Path -Kind "move"
            }) | Out-Null
        }
    }

    foreach ($entry in @($entries | Where-Object { -not $_.Used })) {
        $kind = if ($entry.IsDeleted) { "delete" } elseif ($entry.IsUntracked -or $entry.Code.Contains("A")) { "add" } else { "modify" }
        $entry.Used = $true
        $plans.Add([pscustomobject]@{
            Kind = $kind
            Paths = @($entry.Path)
            Message = Get-ConventionalMessage -Path $entry.Path -Kind $kind
        }) | Out-Null
    }

    foreach ($plan in $plans) {
        foreach ($path in $plan.Paths) {
            if ($plan.Kind -eq "delete" -or $plan.Kind -eq "move") {
                Invoke-Git -Repo $Repo -Args @("add", "-A", "--", $path) | Out-Null
            }
            else {
                Invoke-Git -Repo $Repo -Args @("add", "--", $path) | Out-Null
            }
        }
        Invoke-Git -Repo $Repo -Args @("commit", "-m", $plan.Message) | Out-Null
        $created++
    }

    $remaining = Invoke-Git -Repo $Repo -Args @("status", "--porcelain=v1", "--untracked-files=all")
    if ($remaining.Output.Count -gt 0) {
        return [pscustomobject]@{ Success = $false; StopReason = "UnexpectedRemaining"; CreatedCommitCount = $created; Remaining = $remaining.Output }
    }

    if (-not $SkipPush) {
        $syncResult = Sync-Repository -Repo $Repo
        if (-not $syncResult.Success) {
            return [pscustomobject]@{ Success = $false; StopReason = $syncResult.StopReason; CreatedCommitCount = $created; Output = $syncResult.Output }
        }
    }

    [pscustomobject]@{ Success = $true; StopReason = ""; CreatedCommitCount = $created }
}

function Get-CommitCount {
    param([string] $Repo)
    [int](Invoke-Git -Repo $Repo -Args @("rev-list", "--count", "HEAD")).Output[0]
}

function Get-CommitsSince {
    param(
        [string] $Repo,
        [string] $BaseRevision
    )
    @((Invoke-Git -Repo $Repo -Args @("rev-list", "--reverse", "$BaseRevision..HEAD")).Output)
}

function Get-CommitNameStatus {
    param(
        [string] $Repo,
        [string] $Revision
    )
    @((Invoke-Git -Repo $Repo -Args @("diff-tree", "--no-commit-id", "--name-status", "-r", "-M", $Revision)).Output)
}

function Assert-True {
    param(
        [bool] $Condition,
        [string] $Message
    )
    if (-not $Condition) { throw $Message }
}

$tests = New-Object System.Collections.Generic.List[object]

function Add-Test {
    param([string] $Name, [scriptblock] $Body)
    $tests.Add([pscustomobject]@{ Name = $Name; Body = $Body }) | Out-Null
}

Add-Test "multiple modified files" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Write-TestFile -Path (Join-Path $fixture.Repo "src\one.txt") -Content "one`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\two.txt") -Content "two`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\three.txt") -Content "three`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 3) "expected 3 commits"
    Assert-True ((Invoke-Git -Repo $fixture.Repo -Args @("status", "--porcelain=v1", "--untracked-files=all")).Output.Count -eq 0) "tree not clean"
}

Add-Test "recursively expanded untracked directory" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $before = (Invoke-Git -Repo $fixture.Repo -Args @("rev-parse", "HEAD")).Output[0]
    Write-TestFile -Path (Join-Path $fixture.Repo "docs\INSTALL.md") -Content "install`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "docs\RELEASE.md") -Content "release`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "docs\STORE.md") -Content "store`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 3) "expected 3 commits"
    $commits = Get-CommitsSince -Repo $fixture.Repo -BaseRevision $before
    Assert-True ($commits.Count -eq 3) "untracked directory files were grouped"
}

Add-Test "rename/move" {
    param($root)
    $fixture = New-TestRepository -Root $root
    New-Item -ItemType Directory -Path (Join-Path $fixture.Repo "docs") -Force | Out-Null
    Move-Item -LiteralPath (Join-Path $fixture.Repo "README.md") -Destination (Join-Path $fixture.Repo "docs\README.md")
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 1) "expected 1 move commit"
    $diff = (Invoke-Git -Repo $fixture.Repo -Args @("diff", "--name-status", "--find-renames", "HEAD~1", "HEAD")).Output -join "`n"
    Assert-True ($diff -match '^R\d+') "expected Git rename detection"
}

Add-Test "deletion" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Remove-Item -LiteralPath (Join-Path $fixture.Repo "src\keep.txt")
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 1) "expected 1 deletion commit"
}

Add-Test "suspicious env file stops" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $before = Get-CommitCount -Repo $fixture.Repo
    Write-TestFile -Path (Join-Path $fixture.Repo ".env.local") -Content "EXAMPLE_VALUE=value`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True (-not $result.Success) "workflow should stop"
    Assert-True ($result.StopReason -eq "SensitivePath") "expected SensitivePath stop"
    Assert-True ((Get-CommitCount -Repo $fixture.Repo) -eq $before) "should not commit"
}

Add-Test "unrelated staged work stops" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $before = Get-CommitCount -Repo $fixture.Repo
    Write-TestFile -Path (Join-Path $fixture.Repo "staged.txt") -Content "staged`n"
    Invoke-Git -Repo $fixture.Repo -Args @("add", "--", "staged.txt") | Out-Null
    Write-TestFile -Path (Join-Path $fixture.Repo "src\app.txt") -Content "changed`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True (-not $result.Success) "workflow should stop"
    Assert-True ($result.StopReason -eq "UnrelatedStagedWork") "expected staged work stop"
    Assert-True ((Get-CommitCount -Repo $fixture.Repo) -eq $before) "should not commit"
}

Add-Test "remote ahead rebase" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $peer = Join-Path $root "peer"
    Invoke-Git -Repo $root -Args @("clone", "--branch", "main", $fixture.Remote, $peer) | Out-Null
    Invoke-Git -Repo $peer -Args @("config", "core.autocrlf", "false") | Out-Null
    Invoke-Git -Repo $peer -Args @("config", "user.email", "peer@example.invalid") | Out-Null
    Invoke-Git -Repo $peer -Args @("config", "user.name", "Peer") | Out-Null
    Write-TestFile -Path (Join-Path $peer "peer.txt") -Content "peer`n"
    Invoke-Git -Repo $peer -Args @("add", "--", "peer.txt") | Out-Null
    Invoke-Git -Repo $peer -Args @("commit", "-m", "chore: add peer file") | Out-Null
    Invoke-Git -Repo $peer -Args @("push", "origin", "main") | Out-Null
    Write-TestFile -Path (Join-Path $fixture.Repo "local.txt") -Content "local`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 1) "expected 1 local commit"
}

Add-Test "rebase conflict stops" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $peer = Join-Path $root "peer"
    Invoke-Git -Repo $root -Args @("clone", "--branch", "main", $fixture.Remote, $peer) | Out-Null
    Invoke-Git -Repo $peer -Args @("config", "core.autocrlf", "false") | Out-Null
    Invoke-Git -Repo $peer -Args @("config", "user.email", "peer@example.invalid") | Out-Null
    Invoke-Git -Repo $peer -Args @("config", "user.name", "Peer") | Out-Null
    Write-TestFile -Path (Join-Path $peer "src\app.txt") -Content "remote conflict`n"
    Invoke-Git -Repo $peer -Args @("add", "--", "src/app.txt") | Out-Null
    Invoke-Git -Repo $peer -Args @("commit", "-m", "chore: remote conflict") | Out-Null
    Invoke-Git -Repo $peer -Args @("push", "origin", "main") | Out-Null
    Write-TestFile -Path (Join-Path $fixture.Repo "src\app.txt") -Content "local conflict`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True (-not $result.Success) "workflow should stop"
    Assert-True ($result.StopReason -eq "RebaseConflict") "expected rebase conflict"
}

Add-Test "push failure recovery does not duplicate commits" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $hooks = Join-Path $fixture.Repo ".git\hooks"
    Write-TestFile -Path (Join-Path $hooks "pre-push") -Content "#!/bin/sh`nexit 1`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\push-fail.txt") -Content "fail once`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True (-not $result.Success) "workflow should fail push"
    Assert-True ($result.StopReason -eq "PushFailed") "expected push failure"
    Assert-True ($result.CreatedCommitCount -eq 1) "expected 1 created commit"
    Remove-Item -LiteralPath (Join-Path $hooks "pre-push")
    $retry = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $retry.Success "retry should push"
    Assert-True ($retry.CreatedCommitCount -eq 0) "retry should not duplicate commits"
}

Add-Test "non-main branch" {
    param($root)
    $fixture = New-TestRepository -Root $root -Branch "feature/work"
    Write-TestFile -Path (Join-Path $fixture.Repo "feature.txt") -Content "feature`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True (((Invoke-Git -Repo $fixture.Repo -Args @("branch", "--show-current")).Output[0]) -eq "feature/work") "wrong branch"
}

Add-Test "pager-safe logs" {
    param($root)
    $script = Get-Content -LiteralPath $PSCommandPath -Raw
    Assert-True ($script -match 'git".*"--no-pager"|--no-pager') "expected no-pager verification"
}

Add-Test "clean repository has no empty commits" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $before = Get-CommitCount -Repo $fixture.Repo
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    $after = Get-CommitCount -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 0) "expected zero commits"
    Assert-True ($before -eq $after) "commit count changed"
}

Add-Test "rename with modification" {
    param($root)
    $fixture = New-TestRepository -Root $root
    $stableContent = (1..20 | ForEach-Object { "stable line $_" }) -join "`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\keep.txt") -Content "$stableContent`n"
    Invoke-Git -Repo $fixture.Repo -Args @("add", "--", "src/keep.txt") | Out-Null
    Invoke-Git -Repo $fixture.Repo -Args @("commit", "-m", "chore: prepare rename fixture") | Out-Null
    Invoke-Git -Repo $fixture.Repo -Args @("push", "origin", "main") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $fixture.Repo "src\moved") -Force | Out-Null
    Move-Item -LiteralPath (Join-Path $fixture.Repo "src\keep.txt") -Destination (Join-Path $fixture.Repo "src\moved\keep.txt")
    Add-Content -LiteralPath (Join-Path $fixture.Repo "src\moved\keep.txt") -Value "modified"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 1) "expected 1 rename/change commit"
    $diff = (Invoke-Git -Repo $fixture.Repo -Args @("diff", "--name-status", "--find-renames", "HEAD~1", "HEAD")).Output -join "`n"
    Assert-True ($diff -match '^R\d+') "expected Git rename detection"
}

Add-Test "screenshot-created files become Git inventory" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Write-TestFile -Path (Join-Path $fixture.Repo "src\from-screenshot-a.txt") -Content "visible a`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\from-screenshot-b.txt") -Content "visible b`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 2) "expected 2 reconstructed-file commits"
}

Add-Test "independent new files stay separate" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Write-TestFile -Path (Join-Path $fixture.Repo "src\one-independent.ts") -Content "export const one = 1;`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\two-independent.ts") -Content "export const two = 2;`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 2) "two independent new files must not be grouped"
}

Add-Test "implementation and test stay separate by default" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Write-TestFile -Path (Join-Path $fixture.Repo "src\lib\logger.ts") -Content "export function log(message: string) { return message; }`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "tests\logger.test.ts") -Content "import { log } from '../src/lib/logger';`nlog('ready');`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 2) "implementation and test were grouped"
}

Add-Test "single modified file is not split" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Write-TestFile -Path (Join-Path $fixture.Repo "src\app.txt") -Content "line one changed`nline two changed`nline three changed`n"
    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 1) "one modified file should not be split across commits"
}

Add-Test "known black-box fixture creates ten file-level commits" {
    param($root)
    $fixture = New-TestRepository -Root $root
    Write-TestFile -Path (Join-Path $fixture.Repo "src\App.tsx") -Content "export function App() { return 'baseline'; }`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\components\Header.tsx") -Content "export function Header() { return 'header'; }`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "docs\INSTALL.md") -Content "# Install`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "docs\RELEASE.md") -Content "# Release`n"
    Invoke-Git -Repo $fixture.Repo -Args @("add", "--", "src/App.tsx", "src/components/Header.tsx", "docs/INSTALL.md", "docs/RELEASE.md") | Out-Null
    Invoke-Git -Repo $fixture.Repo -Args @("commit", "-m", "chore: prepare black-box fixture") | Out-Null
    Invoke-Git -Repo $fixture.Repo -Args @("push", "origin", "main") | Out-Null
    $before = (Invoke-Git -Repo $fixture.Repo -Args @("rev-parse", "HEAD")).Output[0]

    Write-TestFile -Path (Join-Path $fixture.Repo "README.md") -Content "# Test Repo`n`nUpdated README for black-box fixture.`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\App.tsx") -Content "import { createLogger } from './lib/logger';`nexport function App() { return createLogger('app').info('ready'); }`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\components\Header.tsx") -Content "export function Header() { return 'updated header'; }`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "src\lib\logger.ts") -Content ('export function createLogger(scope: string) { return { info: (message: string) => `[${scope}] ${message}` }; }' + "`n")
    Write-TestFile -Path (Join-Path $fixture.Repo "tests\logger.test.ts") -Content "import { createLogger } from '../src/lib/logger';`ncreateLogger('test').info('ready');`n"
    New-Item -ItemType Directory -Path (Join-Path $fixture.Repo "docs\guides") -Force | Out-Null
    Move-Item -LiteralPath (Join-Path $fixture.Repo "docs\INSTALL.md") -Destination (Join-Path $fixture.Repo "docs\guides\INSTALL.md")
    Remove-Item -LiteralPath (Join-Path $fixture.Repo "docs\RELEASE.md")
    Write-TestFile -Path (Join-Path $fixture.Repo "examples\README.md") -Content "# Examples`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "examples\basic.ts") -Content "export const basic = true;`n"
    Write-TestFile -Path (Join-Path $fixture.Repo "examples\advanced.ts") -Content "export const advanced = true;`n"

    $result = Invoke-GranularWorkflow -Repo $fixture.Repo
    Assert-True $result.Success "workflow failed"
    Assert-True ($result.CreatedCommitCount -eq 10) "known fixture must create exactly 10 file-level commits"
    $commits = @(Get-CommitsSince -Repo $fixture.Repo -BaseRevision $before)
    Assert-True ($commits.Count -eq 10) "expected 10 commits after baseline"
    foreach ($commit in $commits) {
        $nameStatus = @(Get-CommitNameStatus -Repo $fixture.Repo -Revision $commit)
        Assert-True ($nameStatus.Count -eq 1) "commit $commit grouped multiple file-level operations: $($nameStatus -join '; ')"
    }
}

$results = New-Object System.Collections.Generic.List[object]

foreach ($test in $tests) {
    $root = Join-Path ([System.IO.Path]::GetTempPath()) ("ggcp-" + [guid]::NewGuid().ToString("N"))
    $resolvedTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    try {
        New-Item -ItemType Directory -Path $root -Force | Out-Null
        & $test.Body $root
        $results.Add([pscustomobject]@{ Name = $test.Name; Passed = $true; Message = "" }) | Out-Null
    }
    catch {
        $results.Add([pscustomobject]@{ Name = $test.Name; Passed = $false; Message = $_.Exception.Message }) | Out-Null
    }
    finally {
        if (Test-Path -LiteralPath $root) {
            $resolvedRoot = [System.IO.Path]::GetFullPath($root)
            if ($resolvedRoot.StartsWith($resolvedTemp, [System.StringComparison]::OrdinalIgnoreCase)) {
                Remove-Item -LiteralPath $root -Recurse -Force
            }
        }
    }
}

$passed = @($results | Where-Object { $_.Passed }).Count
$failed = @($results | Where-Object { -not $_.Passed }).Count
$results | Format-Table -AutoSize

if ($failed -gt 0) {
    throw "$failed integration test(s) failed; $passed passed."
}

[pscustomobject]@{
    Passed = $passed
    Failed = $failed
    Message = "All integration tests passed."
}
