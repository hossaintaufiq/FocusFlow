# Creates Desktop + Start Menu shortcuts for FocusFlow (safe for taskbar pinning).
param(
    [bool]$CreateDesktop = $true,
    [bool]$CreateStartMenu = $true,
    [bool]$CreateProjectShortcut = $true
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $ProjectRoot "FocusFlow.exe"
$VbsLauncher = Join-Path $ProjectRoot "FocusFlow.vbs"
$Icon = Join-Path $ProjectRoot "assets\icons\focusflow.ico"

if (-not (Test-Path $Icon)) {
    Write-Host "Icon missing - generating..."
    Push-Location $ProjectRoot
    python (Join-Path $PSScriptRoot "generate_icon.py")
    Pop-Location
}

function Resolve-Pythonw {
    param([string]$Root)
    $venv = Join-Path $Root ".venv\Scripts\pythonw.exe"
    if (Test-Path $venv) { return $venv }
    $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

$Wsh = New-Object -ComObject WScript.Shell

function Write-FocusFlowShortcut {
    param([string]$ShortcutPath)
    $sc = $Wsh.CreateShortcut($ShortcutPath)

    if (Test-Path $Exe) {
        $sc.TargetPath = $Exe
        $sc.Arguments = ""
    } elseif (Test-Path $VbsLauncher) {
        $sc.TargetPath = "wscript.exe"
        $sc.Arguments = "`"$VbsLauncher`""
    } else {
        throw "No launcher found. Run from project folder or build FocusFlow.exe"
    }

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

if ($CreateProjectShortcut) {
    Write-FocusFlowShortcut -ShortcutPath (Join-Path $ProjectRoot "FocusFlow (Pin to taskbar).lnk")
}

Write-Host ""
Write-Host "Done."
if (Test-Path $Exe) {
    Write-Host "Shortcut uses FocusFlow.exe - safe to pin to taskbar."
} else {
    Write-Host "Tip: run scripts\build_exe.ps1 for a .exe that pins reliably on the taskbar."
}
Write-Host "Right-click Desktop FocusFlow -> Pin to taskbar"
Write-Host "Do NOT pin FocusFlow.pyw directly."
