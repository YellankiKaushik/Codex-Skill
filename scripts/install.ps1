[CmdletBinding()]
param(
    [switch] $Editable,
    [switch] $InstallSkill
)

$ErrorActionPreference = "Stop"

if ($Editable) {
    python -m pip install -e .
} else {
    python -m pip install .
}

ggcp --version
if ($InstallSkill) {
    ggcp install-skill
}
