param([switch]$NoOpen, [string]$Route='/', [int]$Port=8790, [string]$Python, [switch]$ResolveOnly, [switch]$ForceVenv)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'python_runtime.ps1')
$catalogRoot=Split-Path -Parent $PSScriptRoot
if(!$Route.StartsWith('/')){throw 'ローカル画面のURLを指定してください。'}
function Get-CatalogInfo([string]$CatalogUrl) { try { Invoke-RestMethod -Uri ($CatalogUrl+'/api/info') -TimeoutSec 2 } catch { $null } }
function Quote-CatalogArgument([string]$Value) { '"'+$Value.Replace('"','\"')+'"' }
try {
    if($ResolveOnly) { Resolve-CatalogPython -Root $catalogRoot -PreferredPython $Python -ForceVenv:$ForceVenv; return }
    $catalogUrl='http://127.0.0.1:'+$Port;$catalogInfo=$null
    $catalogServiceFile=Join-Path $catalogRoot 'outputs\review_service.json'
    if(Test-Path -LiteralPath $catalogServiceFile) {
        try { $catalogService=Get-Content -LiteralPath $catalogServiceFile -Raw | ConvertFrom-Json;$catalogUri=[Uri]$catalogService.url
            if($catalogUri.Scheme -eq 'http' -and $catalogUri.Host -eq '127.0.0.1') { $catalogExisting=Get-CatalogInfo $catalogService.url; if($catalogExisting.app -eq 'Krea2CatalogReview' -and $catalogExisting.root -eq $catalogRoot){$catalogInfo=$catalogExisting;$catalogUrl=$catalogService.url.TrimEnd('/')} }
        } catch { }
    }
    if(!$catalogInfo) { $catalogInfo=Get-CatalogInfo $catalogUrl; if($catalogInfo -and ($catalogInfo.app -ne 'Krea2CatalogReview' -or $catalogInfo.root -ne $catalogRoot)) {$catalogInfo=$null} }
    if(!$catalogInfo) {
        $catalogPython=Resolve-CatalogPython -Root $catalogRoot -PreferredPython $Python -ForceVenv:$ForceVenv
        $catalogOutputs=Join-Path $catalogRoot 'outputs';New-Item -ItemType Directory -Path $catalogOutputs -Force | Out-Null
        @{python=$catalogPython} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $catalogOutputs 'python_runtime.json') -Encoding UTF8
        $catalogServer=Join-Path $catalogRoot 'review\server.py';$catalogListener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$Port)
        try {$catalogListener.Start();$catalogListener.Stop()} catch { $catalogListener.Stop();$catalogListener=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0);$catalogListener.Start();$Port=$catalogListener.LocalEndpoint.Port;$catalogListener.Stop() }
        $catalogUrl='http://127.0.0.1:'+$Port
        $catalogArguments=@('-B',(Quote-CatalogArgument $catalogServer),'--root',(Quote-CatalogArgument $catalogRoot),'--port',[string]$Port)
        $catalogProcess=Start-Process -FilePath $catalogPython -ArgumentList $catalogArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $catalogOutputs 'review_server.log') -RedirectStandardError (Join-Path $catalogOutputs 'review_server.err.log')
        for($catalogAttempt=0;$catalogAttempt -lt 60;$catalogAttempt++) { Start-Sleep -Milliseconds 150;$catalogInfo=Get-CatalogInfo $catalogUrl; if($catalogInfo){break}; if($catalogProcess.HasExited){throw 'カタログを起動できません。outputs\review_server.err.logを確認してください。'} }
        if(!$catalogInfo -or $catalogInfo.root -ne $catalogRoot){throw 'カタログの起動を確認できませんでした。'}
    }
    if($catalogInfo.editor_version -ne 1){throw '古いカタログのサービスが動いています。カタログのサービスを終了して、もう一度開いてください。'}
    if(!$NoOpen){Start-Process ($catalogUrl+$Route)}
    Write-Output ($catalogUrl+$Route)
} catch {
    if($NoOpen -or $ResolveOnly){throw}
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show($_.Exception.Message,'Krea2 Catalog Editor') | Out-Null
    exit 1
}
