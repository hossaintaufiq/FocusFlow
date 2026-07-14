# Build a lean FocusFlow.exe (no collect-all; much faster).
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python -m pip install pyinstaller --quiet

$icon = Join-Path $ProjectRoot "assets\icons\focusflow.ico"
if (-not (Test-Path $icon)) {
    python (Join-Path $PSScriptRoot "generate_icon.py")
}

Write-Host "Building FocusFlow.exe..."
python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onefile `
    --name FocusFlow `
    --icon $icon `
    --paths $ProjectRoot `
    --hidden-import PySide6.QtCore `
    --hidden-import PySide6.QtGui `
    --hidden-import PySide6.QtWidgets `
    --hidden-import matplotlib.backends.backend_qtagg `
    --exclude-module torch `
    --exclude-module pandas `
    --exclude-module scipy `
    --exclude-module IPython `
    --exclude-module notebook `
    --exclude-module jupyter `
    (Join-Path $ProjectRoot "main.py")

$built = Join-Path $ProjectRoot "dist\FocusFlow.exe"
$target = Join-Path $ProjectRoot "FocusFlow.exe"
if (-not (Test-Path $built)) {
    throw "Build failed - dist\FocusFlow.exe not found"
}

Copy-Item $built $target -Force
Write-Host "Built: $target"
Write-Host "Now run: powershell -File scripts\install_desktop_shortcut.ps1"
