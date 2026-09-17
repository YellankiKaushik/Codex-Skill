[CmdletBinding()]
param(
    [string] $PluginRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($PluginRoot)) {
    $PluginRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
}
else {
    $PluginRoot = (Resolve-Path $PluginRoot).Path
}

$failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([string] $Message)
    $script:failures.Add($Message) | Out-Null
}

function Test-JsonFile {
    param([string] $Path)
    try {
        Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json | Out-Null
    }
    catch {
        Add-Failure "Invalid JSON: $Path - $($_.Exception.Message)"
    }
}

function Test-YamlLikeFile {
    param([string] $Path)
    $text = Get-Content -LiteralPath $Path -Raw
    $unfinishedPattern = '\[' + 'TO' + 'DO:|' + 'TO' + 'DO placeholder|Briefly describe'
    if ($text -match $unfinishedPattern) {
        Add-Failure "Unfinished placeholder found in $Path"
    }
    if ($Path.EndsWith("SKILL.md")) {
        if ($text -notmatch '(?s)^---\s*\r?\nname:\s*granular-git-commit-push\r?\ndescription:\s*.+?\r?\n---') {
            Add-Failure "SKILL.md frontmatter is missing required name/description."
        }
        if ($text -match '(?m)^(metadata|version|author):') {
            Add-Failure "SKILL.md frontmatter includes unsupported extra fields."
        }
    }
}

$required = @(
    "plugin.json",
    ".codex-plugin/plugin.json",
    "skills/granular-git-commit-push/SKILL.md",
    "skills/granular-git-commit-push/agents/openai.yaml",
    "skills/granular-git-commit-push/references/workflow.md",
    "skills/granular-git-commit-push/references/screenshot-reconstruction.md",
    "skills/granular-git-commit-push/references/git-safety.md",
    "skills/granular-git-commit-push/references/commit-planning.md",
    "skills/granular-git-commit-push/references/powershell-generation.md",
    "skills/granular-git-commit-push/references/recovery.md",
    "skills/granular-git-commit-push/scripts/Get-GitInventory.ps1",
    "skills/granular-git-commit-push/scripts/Test-GitEnvironment.ps1",
    "skills/granular-git-commit-push/scripts/Test-SensitivePath.ps1",
    "tests/Invoke-IntegrationTests.ps1",
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    ".gitignore"
)

foreach ($relative in $required) {
    $path = Join-Path $PluginRoot $relative
    if (-not (Test-Path -LiteralPath $path)) {
        Add-Failure "Missing required file: $relative"
    }
}

foreach ($json in @("plugin.json", ".codex-plugin/plugin.json")) {
    $path = Join-Path $PluginRoot $json
    if (Test-Path -LiteralPath $path) { Test-JsonFile $path }
}

foreach ($yamlLike in @("skills/granular-git-commit-push/SKILL.md", "skills/granular-git-commit-push/agents/openai.yaml")) {
    $path = Join-Path $PluginRoot $yamlLike
    if (Test-Path -LiteralPath $path) { Test-YamlLikeFile $path }
}

$skillText = Get-Content -LiteralPath (Join-Path $PluginRoot "skills/granular-git-commit-push/SKILL.md") -Raw
$links = [regex]::Matches($skillText, '\]\((references/[^)]+|scripts/[^)]+)\)')
foreach ($link in $links) {
    $target = Join-Path (Join-Path $PluginRoot "skills/granular-git-commit-push") $link.Groups[1].Value
    if (-not (Test-Path -LiteralPath $target)) {
        Add-Failure "Broken SKILL.md reference: $($link.Groups[1].Value)"
    }
}

$scriptFiles = Get-ChildItem -LiteralPath (Join-Path $PluginRoot "skills/granular-git-commit-push/scripts") -Filter "*.ps1" -File
foreach ($script in $scriptFiles) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile($script.FullName, [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        Add-Failure "PowerShell parse error in $($script.FullName): $($errors[0].Message)"
    }
}

$executableText = ($scriptFiles | Where-Object { $_.Name -ne "Test-Skill.ps1" } | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }) -join "`n"
$dangerousExecutablePatterns = @(
    'push\s+--force',
    'push\s+--force-with-lease',
    'reset\s+--hard',
    'clean\s+-fd',
    'Remove-Item.+\.git',
    'rm\s+-rf\s+\.git',
    'commit\s+--allow-empty',
    'GIT_AUTHOR_DATE',
    'GIT_COMMITTER_DATE'
)
foreach ($pattern in $dangerousExecutablePatterns) {
    if ($executableText -imatch $pattern) {
        Add-Failure "Dangerous executable pattern found: $pattern"
    }
}

$allText = (Get-ChildItem -LiteralPath $PluginRoot -Recurse -File -Force | Where-Object { $_.FullName -notmatch '\\\.git\\' -and $_.Name -ne "Test-Skill.ps1" } | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }) -join "`n"
$unfinishedMarkerPattern = '\[' + 'TO' + 'DO:|' + 'TO' + 'DO place' + 'holder|Lorem ' + 'ipsum'
if ($allText -match $unfinishedMarkerPattern) {
    Add-Failure "Unfinished placeholder text remains."
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    throw "$($failures.Count) skill validation failure(s)."
}

[pscustomobject]@{
    Passed = $true
    CheckedFiles = $required.Count
    Message = "Skill/plugin validation passed."
}
