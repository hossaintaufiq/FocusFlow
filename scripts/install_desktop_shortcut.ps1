# Creates Desktop + Start Menu shortcuts for FocusFlow (double-click to launch).
param(
    [bool]$CreateDesktop = $true,
    [bool]$CreateStartMenu = $true
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $ProjectRoot "FocusFlow.vbs"
$Icon = Join-Path $ProjectRoot "assets\icons\focusflow.ico"

if (-not (Test-Path $Launcher)) {
    throw "Launcher not found: $Launcher"
}

if (-not (Test-Path $Icon)) {
    Write-Host "Icon missing - generating..."
    Push-Location $ProjectRoot
    python (Join-Path $PSScriptRoot "generate_icon.py")
    Pop-Location
}

$Wsh = New-Object -ComObject WScript.Shell

function Write-FocusFlowShortcut {
    param([string]$ShortcutPath)
    $sc = $Wsh.CreateShortcut($ShortcutPath)
    $sc.TargetPath = $Launcher
    $sc.WorkingDirectory = $ProjectRoot
    $sc.WindowStyle = 1
    $sc.Description = "FocusFlow Personal Productivity OS"
    if (Test-Path $Icon) {
        $sc.IconLocation = "$Icon,0"
    }
    $sc.Save()
    Write-Host "Created: $ShortcutPath"
}

if ($CreateDesktop) {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    Write-FocusFlowShortcut -ShortcutPath (Join-Path $desktopPath "FocusFlow.lnk")
}

if ($CreateStartMenu) {
    $programsPath = [Environment]::GetFolderPath("Programs")
    $folder = Join-Path $programsPath "FocusFlow"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    Write-FocusFlowShortcut -ShortcutPath (Join-Path $folder "FocusFlow.lnk")
}

Write-Host ""
Write-Host "Done. Double-click FocusFlow on your Desktop to start the app."
