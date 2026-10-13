param([switch]$NoOpen, [string]$Route='/', [int]$Port=8790, [string]$Python, [switch]$ResolveOnly, [switch]$ForceVenv)
$ErrorActionPreference='Stop'
# Compatibility entry point; service and dependency logic lives in Python.
. (Join-Path $PSScriptRoot 'python_runtime.ps1')
$catalogArguments=@('--route',$Route,'--port',[string]$Port)
if($NoOpen){$catalogArguments+='--no-open'}
if($ResolveOnly){$catalogArguments+='--resolve-only'}
if($ForceVenv){$catalogArguments+='--force-venv'}
if($Python){$catalogArguments+=@('--python',$Python)}
Invoke-CatalogLauncher -Arguments $catalogArguments -BootstrapPython $Python
