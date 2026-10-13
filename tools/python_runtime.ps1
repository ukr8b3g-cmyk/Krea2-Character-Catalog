$script:catalogRuntimeTools = $PSScriptRoot
function Test-CatalogPython {
    param([string]$Path, [switch]$Dependencies)
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $catalogCheck = 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'
    if ($Dependencies) { $catalogCheck = "import sys, PIL; from PIL import features; sys.exit(0 if sys.version_info >= (3,10) and 10 <= int(PIL.__version__.split('.')[0]) < 13 and features.check('webp') else 1)" }
    try { $catalogResult = & $Path -c $catalogCheck 2>$null; return $LASTEXITCODE -eq 0 } catch { return $false }
}
function Resolve-CatalogPython {
    param([string]$Root, [string]$PreferredPython, [switch]$ForceVenv)
    $catalogCandidates = [Collections.Generic.List[string]]::new()
    if ($PreferredPython) { $catalogCandidates.Add($PreferredPython) }
    if ($env:KREA2_CATALOG_PYTHON) { $catalogCandidates.Add($env:KREA2_CATALOG_PYTHON) }
    $catalogConfig = Join-Path $Root 'outputs\python_runtime.json'
    if (Test-Path -LiteralPath $catalogConfig) { try { $catalogSaved = Get-Content -LiteralPath $catalogConfig -Raw | ConvertFrom-Json; if($catalogSaved.python){$catalogCandidates.Add($catalogSaved.python)} } catch { } }
    $catalogCandidates.Add((Join-Path $Root '.venv\Scripts\python.exe'))
    $catalogCommand = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($catalogCommand) { try { $catalogDetected = & $catalogCommand.Source -3 -c 'import sys; print(sys.executable)' 2>$null; if($LASTEXITCODE -eq 0 -and $catalogDetected){$catalogCandidates.Add([string]$catalogDetected)} } catch { } }
    $catalogCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($catalogCommand -and $catalogCommand.Source -notlike '*\WindowsApps\*') { $catalogCandidates.Add($catalogCommand.Source) }
    if($env:LOCALAPPDATA) { $catalogInstallRoot = Join-Path $env:LOCALAPPDATA 'Programs\Python'; if(Test-Path -LiteralPath $catalogInstallRoot) { Get-ChildItem -LiteralPath $catalogInstallRoot -Directory | ForEach-Object { $catalogCandidates.Add((Join-Path $_.FullName 'python.exe')) } } }
    foreach($catalogHomeName in @('miniconda3','anaconda3')) { if($env:USERPROFILE){$catalogCandidates.Add((Join-Path (Join-Path $env:USERPROFILE $catalogHomeName) 'python.exe'))} }
    $catalogBase = $null
    foreach($catalogCandidate in ($catalogCandidates | Select-Object -Unique)) { if(Test-CatalogPython -Path $catalogCandidate) { if(!$catalogBase){$catalogBase=$catalogCandidate}; if(!$ForceVenv -and (Test-CatalogPython -Path $catalogCandidate -Dependencies)) { return $catalogCandidate } } }
    if(!$catalogBase) {
        Add-Type -AssemblyName System.Windows.Forms
        [Windows.Forms.MessageBox]::Show('Python 3.10以上が見つかりません。既存のpython.exeを選んでください。Python本体がない場合は、公式のPythonを導入してから開いてください。','Krea2 Catalog Editor') | Out-Null
        $catalogPicker=[Windows.Forms.OpenFileDialog]::new();$catalogPicker.Title='利用するPythonを選択';$catalogPicker.Filter='Python (python.exe)|python.exe';$catalogPicker.CheckFileExists=$true
        if($catalogPicker.ShowDialog() -ne [Windows.Forms.DialogResult]::OK){throw 'Pythonの選択を取り消しました。カタログは変更していません。'}
        $catalogBase=$catalogPicker.FileName
        if(!(Test-CatalogPython -Path $catalogBase)){throw 'Python 3.10以上のpython.exeを選んでください。'}
        if(!$ForceVenv -and (Test-CatalogPython -Path $catalogBase -Dependencies)){return $catalogBase}
    }
    $catalogEnvironment=Join-Path $Root '.venv';$catalogEnvironmentPython=Join-Path $catalogEnvironment 'Scripts\python.exe'
    if(!(Test-Path -LiteralPath $catalogEnvironmentPython -PathType Leaf)) { & $catalogBase -m venv $catalogEnvironment; if($LASTEXITCODE -ne 0){throw '専用venvを作成できませんでした。フォルダーへの書き込み権限を確認してください。'} }
    if(!(Test-CatalogPython -Path $catalogEnvironmentPython -Dependencies)) { $catalogRequirements=Join-Path $script:catalogRuntimeTools 'requirements-editor.txt'; & $catalogEnvironmentPython -m pip install --disable-pip-version-check --index-url https://pypi.org/simple -r $catalogRequirements | Out-Host; if($LASTEXITCODE -ne 0){throw '画像読み込み用Pillowを専用venvへ導入できませんでした。インターネット接続を確認するか、Pillowのある既存Pythonを指定してください。'} }
    if(!(Test-CatalogPython -Path $catalogEnvironmentPython -Dependencies)){throw '専用venvの画像読み込みを確認できませんでした。'}
    return $catalogEnvironmentPython
}
