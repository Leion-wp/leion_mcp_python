param(
    [ValidateSet("core", "dev", "revenue", "full")]
    [string]$Profile = "full",
    [switch]$List,
    [switch]$NoRestart,
    [string[]]$Exclude = @()
)

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
    Write-Warning "Leion virtual environment not found; using Python from PATH. Create it with python -m venv .venv, then run .\.venv\Scripts\python.exe -m pip install -e ."
}

$Launcher = Join-Path $PSScriptRoot "launcher\start_all.py"
$ArgsList = @($Launcher, "--profile", $Profile)
if ($List) { $ArgsList += "--list" }
if ($NoRestart) { $ArgsList += "--no-restart" }
foreach ($ServerName in $Exclude) {
    if (-not [string]::IsNullOrWhiteSpace($ServerName)) {
        $ArgsList += "--exclude"
        $ArgsList += $ServerName
    }
}

& $Python @ArgsList
exit $LASTEXITCODE
