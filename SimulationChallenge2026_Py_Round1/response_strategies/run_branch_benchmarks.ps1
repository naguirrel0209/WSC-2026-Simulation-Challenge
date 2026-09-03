param(
    [Parameter(Mandatory = $true)] [string] $Worktree,
    [Parameter(Mandatory = $true)] [string] $ResultsDirectory,
    [Parameter(Mandatory = $true)] [string] $BranchesCsv
)

$ErrorActionPreference = "Stop"
$branches = $BranchesCsv.Split(",", [System.StringSplitOptions]::RemoveEmptyEntries)

New-Item -ItemType Directory -Force -Path $ResultsDirectory | Out-Null
$progressFile = Join-Path $ResultsDirectory "progress.csv"
"Branch,Status,StartedAt,FinishedAt,ExitCode" | Set-Content -LiteralPath $progressFile -Encoding utf8

foreach ($branch in $branches) {
    $startedAt = Get-Date
    & git -C $Worktree checkout --detach $branch | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo cambiar el worktree a $branch"
    }

    $attFile = Join-Path $Worktree "Output\ATT_By_Statistics_Interval.csv"
    if (Test-Path -LiteralPath $attFile) {
        Remove-Item -LiteralPath $attFile -Force
    }

    $logFile = Join-Path $ResultsDirectory "$branch.log"
    $env:PYTHONPATH = "$Worktree\o2despy"
    Push-Location $Worktree
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & C:\Python313\python.exe -c "from main import run_simulation; run_simulation()" *> $logFile
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorPreference
    Pop-Location
    $finishedAt = Get-Date

    if ($exitCode -eq 0 -and (Test-Path -LiteralPath $attFile)) {
        Copy-Item -LiteralPath $attFile -Destination (Join-Path $ResultsDirectory "$branch`_ATT.csv") -Force
        $status = "completed"
    }
    else {
        $status = "failed"
    }

    '"{0}","{1}","{2:o}","{3:o}",{4}' -f $branch, $status, $startedAt, $finishedAt, $exitCode |
        Add-Content -LiteralPath $progressFile -Encoding utf8
}
