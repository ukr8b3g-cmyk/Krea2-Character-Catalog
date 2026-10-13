[CmdletBinding()]
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
try {
    $pythonCandidates = @()
    if ($env:WEBP_THUMBNAIL_PYTHON) { $pythonCandidates += $env:WEBP_THUMBNAIL_PYTHON }
    $pythonCandidates += (Join-Path $env:USERPROFILE 'miniconda3\python.exe')
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source -notlike '*WindowsApps*') { $pythonCandidates += $pythonCommand.Source }
    $thumbnailPython = $null
    foreach ($pythonCandidate in ($pythonCandidates | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $pythonCandidate -PathType Leaf)) { continue }
        try {
            & $pythonCandidate -B -c 'import PIL, tkinter; from PIL import features; assert features.check(''webp'')' 2>$null
            if ($LASTEXITCODE -eq 0) { $thumbnailPython = $pythonCandidate; break }
        } catch { continue }
    }
    if (-not $thumbnailPython) { throw 'Pillow・WebP・Tkに対応したPythonが見つかりません。README.mdを確認してください。' }
    if ($CheckOnly) { Write-Output "READY: $thumbnailPython"; exit 0 }
    $thumbnailPythonw = Join-Path (Split-Path -Parent $thumbnailPython) 'pythonw.exe'
    $thumbnailExecutable = if (Test-Path -LiteralPath $thumbnailPythonw) { $thumbnailPythonw } else { $thumbnailPython }
    $thumbnailScript = Join-Path $PSScriptRoot 'webp_thumbnail_batch.py'
    Start-Process -FilePath $thumbnailExecutable -WindowStyle Normal -ArgumentList @('-B', ('"' + $thumbnailScript + '"'), '--gui') | Out-Null
} catch {
    if ($CheckOnly) { Write-Error $_; exit 1 }
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'WebP Thumbnail Batch') | Out-Null
    exit 1
}
