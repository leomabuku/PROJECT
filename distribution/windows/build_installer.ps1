param([string]$Python = "")

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $Python) {
    $VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    $Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
}

$BuildRoot = Join-Path $RepoRoot "build\windows-installer"
$AppDist = Join-Path $BuildRoot "app-dist"
$ReleaseDir = Join-Path $RepoRoot "dist"
$Version = "0.2.0"
$Compiler = "C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
$LogoIco = Join-Path $RepoRoot "assets\branding\tongalang.ico"
$LogoPng = Join-Path $RepoRoot "assets\branding\tongalang-logo-128.png"

function Assert-ChildPath([string]$Path) {
    $Full = [System.IO.Path]::GetFullPath($Path)
    $Root = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\') + '\'
    if (-not $Full.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify a path outside the repository: $Full"
    }
}

Assert-ChildPath $BuildRoot
Assert-ChildPath $ReleaseDir
if (Test-Path -LiteralPath $BuildRoot) { Remove-Item -LiteralPath $BuildRoot -Recurse -Force }
if (-not (Test-Path -LiteralPath $Compiler)) { throw ".NET Framework C# compiler was not found at $Compiler" }
if (-not (Test-Path -LiteralPath $LogoIco)) { throw "TongaLang icon was not found at $LogoIco" }
if (-not (Test-Path -LiteralPath $LogoPng)) { throw "TongaLang installer logo was not found at $LogoPng" }
New-Item -ItemType Directory -Path $BuildRoot, $AppDist, $ReleaseDir -Force | Out-Null

Push-Location $RepoRoot
try {
    & $Python -m PyInstaller --noconfirm --clean --onedir --windowed `
        --name TongaLang --icon $LogoIco --paths $RepoRoot --collect-submodules ply `
        --add-data "$RepoRoot\assets;assets" `
        --distpath $AppDist --workpath (Join-Path $BuildRoot "app-work") `
        --specpath (Join-Path $BuildRoot "spec") distribution\app_entry.py
    if ($LASTEXITCODE -ne 0) { throw "TongaLang executable build failed." }

    $AppDir = Join-Path $AppDist "TongaLang"
    & $Compiler /nologo /target:winexe /optimize+ `
        "/win32icon:$LogoIco" `
        "/out:$AppDir\TongaLang-Uninstall.exe" `
        /reference:System.dll /reference:System.Core.dll /reference:System.Windows.Forms.dll `
        distribution\windows\Uninstaller.cs
    if ($LASTEXITCODE -ne 0) { throw "TongaLang uninstaller build failed." }

    New-Item -ItemType Directory -Path (Join-Path $AppDir "Documentation") -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $RepoRoot "README.md") -Destination (Join-Path $AppDir "Documentation\README.md")
    Copy-Item -LiteralPath (Join-Path $RepoRoot "docs\INSTALLATION.md") -Destination (Join-Path $AppDir "Documentation\INSTALLATION.md")
    Copy-Item -LiteralPath (Join-Path $RepoRoot "TONGALANG_LANGUAGE_REFERENCE.md") -Destination (Join-Path $AppDir "Documentation\TONGALANG_LANGUAGE_REFERENCE.md")
    Copy-Item -LiteralPath (Join-Path $RepoRoot "examples") -Destination (Join-Path $AppDir "Examples") -Recurse

    $PayloadZip = Join-Path $BuildRoot "TongaLang-payload.zip"
    Compress-Archive -Path (Join-Path $AppDir "*") -DestinationPath $PayloadZip -CompressionLevel Optimal

    $SetupName = "TongaLang-Setup-$Version"
    $ReleaseExe = Join-Path $ReleaseDir "$SetupName.exe"
    & $Compiler /nologo /target:winexe /optimize+ "/out:$ReleaseExe" `
        "/win32icon:$LogoIco" `
        /reference:System.dll /reference:System.Core.dll /reference:System.Drawing.dll `
        /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll `
        /reference:System.Windows.Forms.dll /reference:Microsoft.CSharp.dll `
        "/resource:$PayloadZip,TongaLangPayload" "/resource:$LogoPng,TongaLangLogo" `
        distribution\windows\Installer.cs
    if ($LASTEXITCODE -ne 0) { throw "TongaLang setup build failed." }

    $Hash = (Get-FileHash -LiteralPath $ReleaseExe -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath "$ReleaseExe.sha256" -Value "$Hash  $SetupName.exe" -Encoding ascii
    Write-Host "Built $ReleaseExe"
    Write-Host "SHA256 $Hash"
}
finally {
    Pop-Location
}
