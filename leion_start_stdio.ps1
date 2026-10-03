param(
    [ValidateSet("core", "dev", "revenue", "full")]
    [string]$Profile = "core",

    [switch]$SkipBackends
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FastMcp = Join-Path $RepoRoot ".venv\Scripts\fastmcp.exe"
$Launcher = Join-Path $RepoRoot "launcher\start_all.py"
$LogDir = Join-Path $RepoRoot ".logs\stdio"

function Write-Stderr([string]$Message) {
    [Console]::Error.WriteLine($Message)
}

if (!(Test-Path $Python)) {
    Write-Stderr "[leion-stdio] Missing venv Python: $Python"
    Write-Stderr "[leion-stdio] Create it with: python -m venv .venv"
    exit 1
}

if (!(Test-Path $FastMcp)) {
    Write-Stderr "[leion-stdio] Missing FastMCP CLI: $FastMcp"
    Write-Stderr "[leion-stdio] Install the repo first with: .\.venv\Scripts\python.exe -m pip install -e ."
    exit 1
}

if (!(Test-Path $Launcher)) {
    Write-Stderr "[leion-stdio] Missing launcher: $Launcher"
    exit 1
}

New-Item -ItemType Directory -Force $LogDir | Out-Null

$Supervisor = $null
$RouterExitCode = 0

try {
    if (!$SkipBackends) {
        $SupervisorStdout = Join-Path $LogDir "supervisor.stdout.log"
        $SupervisorStderr = Join-Path $LogDir "supervisor.stderr.log"

        $Supervisor = Start-Process -FilePath $Python `
            -ArgumentList @($Launcher, "--profile", $Profile, "--exclude", "router") `
            -WorkingDirectory $RepoRoot `
            -RedirectStandardOutput $SupervisorStdout `
            -RedirectStandardError $SupervisorStderr `
            -PassThru `
            -WindowStyle Hidden

        Write-Stderr "[leion-stdio] backend supervisor started: pid=$($Supervisor.Id), profile=$Profile"
        Write-Stderr "[leion-stdio] backend logs: $LogDir"

        Start-Sleep -Milliseconds 1200

        if ($Supervisor.HasExited) {
            Write-Stderr "[leion-stdio] backend supervisor exited early with code $($Supervisor.ExitCode)"
            Write-Stderr "[leion-stdio] inspect: $SupervisorStdout"
            Write-Stderr "[leion-stdio] inspect: $SupervisorStderr"
            exit $Supervisor.ExitCode
        }
    }
    else {
        Write-Stderr "[leion-stdio] SkipBackends enabled; assuming child MCP servers are already running."
    }

    # STDIO MCP reserves stdout for JSON-RPC protocol frames.
    # Do not add Write-Host / Write-Output before or during this process.
    Write-Stderr "[leion-stdio] starting MCP router over STDIO"

    Push-Location $RepoRoot
    try {
        & $FastMcp run "servers/mcp_router.py:server" --transport stdio
        if ($null -ne $LASTEXITCODE) {
            $RouterExitCode = $LASTEXITCODE
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($Supervisor -and !$Supervisor.HasExited) {
        Write-Stderr "[leion-stdio] stopping backend supervisor tree"

        if ($env:OS -eq "Windows_NT") {
            & taskkill.exe /PID $Supervisor.Id /T /F *> $null
        }
        else {
            Stop-Process -Id $Supervisor.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

exit $RouterExitCode
