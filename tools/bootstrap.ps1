# Native Windows preflight; no Python catalog code runs until a version passes.
$ErrorActionPreference='Stop'
$catalogArguments=@($args)
function Test-CatalogInterpreter([string]$Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { return 12 }
    if ($Path -match '\\Microsoft\\WindowsApps\\') { return 12 }
    try {
        $probe=New-Object System.Diagnostics.Process
        $probe.StartInfo.FileName=$Path
        $probe.StartInfo.Arguments='-c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 11)"'
        $probe.StartInfo.UseShellExecute=$false
        $probe.StartInfo.CreateNoWindow=$true
        $probe.StartInfo.RedirectStandardOutput=$true
        $probe.StartInfo.RedirectStandardError=$true
        [void]$probe.Start()
        if (!$probe.WaitForExit(20000)) { $probe.Kill(); return 12 }
        $result=$probe.ExitCode
        if ($result -eq 0 -or $result -eq 11) { return $result }
        return 12
    } catch { return 12 } finally { if ($probe) { $probe.Dispose() } }
}
function Show-CatalogInstall {
    [Console]::Error.WriteLine('Windows: https://www.python.org/downloads/windows/')
    [Console]::Error.WriteLine('Install Python 3.10+ and enable its PATH option, then open this startup file again.')
}
function Finish-Catalog([int]$Code) {
    if ($Code -ne 0 -and !$env:CI -and !$env:KREA2_CATALOG_NO_PAUSE -and ![Console]::IsInputRedirected -and ![Console]::IsOutputRedirected) {
        [Console]::Error.WriteLine('Press Enter to close this window.')
        [void][Console]::ReadLine()
    }
    exit $Code
}
$selected=$null
if ($env:KREA2_CATALOG_PYTHON) {
    $result=Test-CatalogInterpreter $env:KREA2_CATALOG_PYTHON
    if ($result -eq 11) {
        [Console]::Error.WriteLine('[PYTHON_OLD] The specified Python is older than 3.10.')
        Show-CatalogInstall
        Finish-Catalog 11
    } elseif ($result -ne 0) {
        [Console]::Error.WriteLine('[PYTHON_PATH] KREA2_CATALOG_PYTHON cannot run. Correct or unset its executable path.')
        Finish-Catalog 12
    }
    $selected=$env:KREA2_CATALOG_PYTHON
} else {
    $candidates=New-Object 'System.Collections.Generic.List[string]'
    foreach ($folder in ($env:PATH -split ';')) {
        if ($folder) { foreach ($name in @('python.exe','python3.exe','python3.12.exe','python3.11.exe','python3.10.exe')) { $candidates.Add((Join-Path $folder.Trim('"') $name)) } }
    }
    $py=Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($line in (& $py.Source -0p 2>$null)) {
            if ($line -match '^\s*-\S+\s+\*?\s*(.+\.exe)\s*$') { $candidates.Add($Matches[1].Trim()) }
        }
    }
    $seenOld=$false
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        $result=Test-CatalogInterpreter $candidate
        if ($result -eq 0) { $selected=$candidate; break }
        if ($result -eq 11) { $seenOld=$true }
    }
    if (!$selected) {
        if ($seenOld) {
            [Console]::Error.WriteLine('[PYTHON_OLD] Only Python versions older than 3.10 were found.')
            $code=11
        } else {
            [Console]::Error.WriteLine('[PYTHON_MISSING] No runnable Python 3.10+ was found on PATH or in the Python launcher.')
            $code=10
        }
        Show-CatalogInstall
        Finish-Catalog $code
    }
}
& $selected (Join-Path $PSScriptRoot 'launch_catalog.py') @catalogArguments
Finish-Catalog $LASTEXITCODE
