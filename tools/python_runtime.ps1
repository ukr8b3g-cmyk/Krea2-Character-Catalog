$script:catalogRuntimeTools=$PSScriptRoot
function Invoke-CatalogLauncher {
    param([string[]]$Arguments, [string]$BootstrapPython)
    $savedCatalogPython=$env:KREA2_CATALOG_PYTHON
    try {
        if($BootstrapPython){$env:KREA2_CATALOG_PYTHON=$BootstrapPython}
        & (Join-Path $script:catalogRuntimeTools 'bootstrap.cmd') @Arguments
    } finally { $env:KREA2_CATALOG_PYTHON=$savedCatalogPython }
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
