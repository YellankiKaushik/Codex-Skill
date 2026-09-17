[CmdletBinding()]
param(
    [Parameter(ValueFromPipeline = $true, ValueFromPipelineByPropertyName = $true)]
    [Alias("FullName", "Name")]
    [string[]] $Path
)

begin {
    $patterns = @(
        '(^|[\\/])\.env($|[\\/])',
        '(^|[\\/])\.env\.[^\\/]+$',
        '(^|[\\/])credentials\.json$',
        '(^|[\\/])service-account\.json$',
        '\.pem$',
        '\.key$',
        '(^|[\\/])id_rsa$',
        '(^|[\\/])id_ed25519$',
        '(^|[\\/])secrets\.[^\\/]+$',
        '(^|[\\/])private-key\.[^\\/]+$',
        '(^|[\\/])firebase-adminsdk[^\\/]*\.json$'
    )

    function Test-SensitivePath {
        [CmdletBinding()]
        param(
            [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
            [string] $Candidate
        )

        process {
            $normalized = $Candidate -replace '\\', '/'
            $isSensitive = $false
            $matched = $null

            foreach ($pattern in $patterns) {
                if ($normalized -imatch $pattern) {
                    $isSensitive = $true
                    $matched = $pattern
                    break
                }
            }

            [pscustomobject]@{
                Path = $Candidate
                IsSensitive = $isSensitive
                MatchedPattern = $matched
                Reason = if ($isSensitive) { "Path resembles a common secret-bearing filename. This is a heuristic, not proof." } else { "" }
            }
        }
    }
}

process {
    foreach ($item in $Path) {
        if ($null -ne $item -and $item -ne "") {
            Test-SensitivePath -Candidate $item
        }
    }
}
