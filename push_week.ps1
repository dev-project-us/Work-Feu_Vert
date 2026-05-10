# ──────────────────────────────────────────────────────────────────────────────
# push_week.ps1 — Weekly CSV push wrapper (Windows PowerShell)
#
# Usage (from the repo root in PowerShell):
#   .\push_week.ps1              ← reads from inbox\ by default
#   .\push_week.ps1 C:\exports\this-week
#   .\push_week.ps1 --dry-run   ← preview without committing
#
# First-time setup (allow script execution):
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# ──────────────────────────────────────────────────────────────────────────────

param(
    [string]$InboxPath = "",
    [switch]$DryRun
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Find Python — try venv first, then PATH
$PythonExe = $null
foreach ($candidate in @(".venv\Scripts\python.exe", "venv\Scripts\python.exe")) {
    if (Test-Path $candidate) {
        $PythonExe = $candidate
        break
    }
}
if (-not $PythonExe) { $PythonExe = "python" }

# Build argument list
$PythonArgs = @("scripts\push_week.py")
if ($InboxPath) { $PythonArgs += $InboxPath }
if ($DryRun)    { $PythonArgs += "--dry-run" }

Write-Host "Running: $PythonExe $PythonArgs" -ForegroundColor Cyan
& $PythonExe @PythonArgs
