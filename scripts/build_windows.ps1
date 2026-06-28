$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Sanal ortam bulunamadı: $Python"
}

Set-Location $ProjectRoot

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "TekstilPaketlemePlanlayici" `
    --add-data "sample_data;sample_data" `
    --collect-submodules PySide6 `
    --collect-submodules openpyxl `
    app_launcher.py

Write-Host ""
Write-Host "Paket hazır: $ProjectRoot\dist\TekstilPaketlemePlanlayici\TekstilPaketlemePlanlayici.exe"
