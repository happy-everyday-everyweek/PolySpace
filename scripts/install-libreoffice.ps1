$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$msiFile = Join-Path $projectRoot "libreoffice\LibreOffice-25.8.6-Win-x64.msi"
$installDir = Join-Path $projectRoot "libreoffice"

if (-not (Test-Path $msiFile)) {
    Write-Host "Downloading LibreOffice 25.8.6..."
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    Invoke-WebRequest -Uri "https://download.documentfoundation.org/libreoffice/stable/25.8.6/win/x86_64/LibreOffice_25.8.6_Win_x86-64.msi" -OutFile $msiFile
}

if (Test-Path (Join-Path $installDir "program\soffice.exe")) {
    Write-Host "LibreOffice already installed at: $installDir"
    exit 0
}

Write-Host "Installing LibreOffice to: $installDir"
$msiArgs = "/i `"$msiFile`" /qn INSTALLDIR=`"$installDir`" REGISTER_ALL_MSO_TYPES=0 CREATEDESKTOPLINK=0 ADDLOCAL=ALL"
$process = Start-Process msiexec.exe -ArgumentList $msiArgs -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Write-Host "MSI install failed with exit code: $($process.ExitCode)"
    Write-Host "Trying administrative install..."
    $adminArgs = "/a `"$msiFile`" /qn TARGETDIR=`"$installDir`""
    $process2 = Start-Process msiexec.exe -ArgumentList $adminArgs -Wait -PassThru
    if ($process2.ExitCode -ne 0) {
        Write-Host "Administrative install also failed: $($process2.ExitCode)"
        exit 1
    }
}

$soffice = Join-Path $installDir "program\soffice.exe"
if (Test-Path $soffice) {
    Write-Host "LibreOffice installed successfully: $soffice"
    & $soffice --version
} else {
    Write-Host "Warning: soffice.exe not found at expected location"
    Get-ChildItem $installDir -Recurse -Filter "soffice.exe" | ForEach-Object {
        Write-Host "Found: $($_.FullName)"
    }
}
