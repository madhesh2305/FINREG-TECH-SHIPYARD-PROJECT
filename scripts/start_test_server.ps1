# FINREGTECH SHIPYARD — SAFE TEST SERVER LAUNCHER (PowerShell)
# Starts isolated manual test server locked to finregtech_test on 127.0.0.1
[CmdletBinding()]
param(
    [int]$Port = 8000,
    [string]$HostAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
$PythonExe = Join-Path $BackendDir "venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at $PythonExe. Please activate your venv first."
    exit 1
}

Write-Host "Verifying isolated test database and starting test server..." -ForegroundColor Cyan
& $PythonExe (Join-Path $ScriptDir "start_test_server.py") --port $Port --host $HostAddress
