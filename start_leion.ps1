param(
    [ValidateSet("core", "dev", "revenue", "full")]
    [string]$Profile = "full",
    [switch]$List,
    [switch]$NoRestart
)

$ArgsList = @("launcher/start_all.py", "--profile", $Profile)
if ($List) { $ArgsList += "--list" }
if ($NoRestart) { $ArgsList += "--no-restart" }

python @ArgsList
exit $LASTEXITCODE
