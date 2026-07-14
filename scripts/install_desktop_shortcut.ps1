# Creates Desktop + Start Menu shortcuts for FocusFlow (double-click to launch).
param(
    [switch]$Desktop = $true,
    [switch]$StartMenu = $true
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $ProjectRoot "FocusFlow.vbs"
$Icon = Join-Path $ProjectRoot "assets\icons\focusflow.ico"

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found: $Launcher"
}

if (-not (Test-Path $Icon)) {
    Write-Host "Icon missing — generating..."
    Push-Location $ProjectRoot
    python (Join-Path $PSScriptRoot "generate_icon.py")
    Pop-Location
}

$Wsh = New-Object -ComObject WScript.Shell

function New-FocusFlowShortcut($Path) {
    $sc = $Wsh.CreateShortcut($Path)
    $sc.TargetPath = $Launcher
    $sc.WorkingDirectory = $ProjectRoot
    $sc.WindowStyle = 1
    $sc.Description = "FocusFlow — Personal Productivity OS"
    if (Test-Path $Icon) {
        $sc.IconLocation = "$Icon,0"
    }
    $sc.Save()
    Write-Host "Created: $Path"
}

if ($Desktop) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    New-FocusFlowShortcut (Join-Path $desktop "FocusFlow.lnk")
}

if ($StartMenu) {
    $programs = [Environment]::GetFolderPath("Programs")
    $folder = Join-Path $programs "FocusFlow"
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    New-FocusFlowShortcut (Join-Path $folder "FocusFlow.lnk")
}

Write-Host ""
Write-Host "Done. Double-click FocusFlow on your Desktop to start the app."
