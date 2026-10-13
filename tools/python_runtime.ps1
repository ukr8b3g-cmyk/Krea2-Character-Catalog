$script:catalogRuntimeTools=$PSScriptRoot
function Invoke-CatalogLauncher {
    param([string[]]$Arguments, [string]$BootstrapPython)
    $catalogScript=Join-Path $script:catalogRuntimeTools 'launch_catalog.py'
    if(!$BootstrapPython){$BootstrapPython=$env:KREA2_CATALOG_PYTHON}
    if($BootstrapPython){ & $BootstrapPython $catalogScript @Arguments }
    elseif(Get-Command py.exe -ErrorAction SilentlyContinue){ & py.exe -3 $catalogScript @Arguments }
    elseif(Get-Command python.exe -ErrorAction SilentlyContinue){ & python.exe $catalogScript @Arguments }
    else {throw 'Python 3.10+ is required. Install Python from https://www.python.org/downloads/.'}
    if($LASTEXITCODE -ne 0){throw 'The catalog launcher failed. See the message above.'}
}
function Resolve-CatalogPython {
    param([string]$Root, [string]$PreferredPython, [switch]$ForceVenv)
    $catalogArguments=@('--root',$Root,'--resolve-only','--json')
    if($PreferredPython){$catalogArguments+=@('--python',$PreferredPython)}
    if($ForceVenv){$catalogArguments+='--force-venv'}
    $catalogResult=Invoke-CatalogLauncher -Arguments $catalogArguments -BootstrapPython $PreferredPython
    return ($catalogResult | ConvertFrom-Json).python
}
