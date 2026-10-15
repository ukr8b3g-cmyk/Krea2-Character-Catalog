"""Test the distributed setup launcher and folder-selection UI using fake local data."""
from pathlib import Path
import argparse,json,os,socket,subprocess,sys,tempfile,time,urllib.parse,urllib.request
SOURCE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(SOURCE/'tools'))
from package_release import safe_extract
from playwright.sync_api import sync_playwright,expect
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(url):
    with HTTP.open(url,timeout=10) as r:return json.load(r)
def stop(url,header,token):
    pid=get(url+'api/info')['pid']
    request=urllib.request.Request(url+'api/shutdown',data=b'{}',headers={'Content-Type':'application/json',header:token})
    with HTTP.open(request,timeout=10) as r:assert json.load(r)['stopped']
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        with socket.socket() as probe:
            probe.settimeout(1)
            if probe.connect_ex(('127.0.0.1',urllib.parse.urlsplit(url).port))!=0:break
        time.sleep(.1)
    else:raise AssertionError('Server did not stop listening')
    if os.name=='nt':
        import ctypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.restype=ctypes.c_void_p
        handle=kernel.OpenProcess(0x100000,False,pid)
        if handle:
            kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            try:assert kernel.WaitForSingleObject(handle,10000)==0,'Server process did not exit'
            finally:kernel.CloseHandle(handle)
def run(archive,report):
    checks=[];result={'passed':False,'platform':sys.platform,'synthetic_data_only':True,'checks':checks};fixture=None;setup_url=None;home=None
    try:
        with tempfile.TemporaryDirectory(prefix='Setup ZIP 日本語 ') as temporary:
            work=Path(temporary);safe_extract(archive,work/'release');home=work/'release/Krea2-Character-Catalog';code=home/'app';workspace=work/'fixture'
            env={**os.environ,'CI':'true','KREA2_CATALOG_PYTHON':sys.executable,'KREA2_CATALOG_NO_PAUSE':'1','PYTHONDONTWRITEBYTECODE':'1'}
            with (work/'fixture.log').open('w') as log:
                fixture=subprocess.Popen([sys.executable,'-B',str(SOURCE/'tests/setup_gui_fixture.py'),'--source',str(code),'--workspace',str(workspace)],stdout=log,stderr=log,env=env)
                try:
                    deadline=time.monotonic()+40
                    while not (workspace/'ready.json').exists():
                        if fixture.poll() is not None:raise AssertionError((work/'fixture.log').read_text())
                        if time.monotonic()>deadline:raise AssertionError('Fixture startup timeout')
                        time.sleep(.1)
                    ready=json.loads((workspace/'ready.json').read_text(encoding='utf-8'))
                    name='START_COMPARISON - Windows.cmd' if os.name=='nt' else 'START_COMPARISON - macOS.command' if sys.platform=='darwin' else 'START_COMPARISON - Linux.sh'
                    command=[str(home/'AnimaDex-Comparison'/name)] if os.name=='nt' else ['sh',str(home/'AnimaDex-Comparison'/name)]
                    command+=['--no-open','--json']
                    def launch():
                        r=subprocess.run(command,env=env,cwd=work,capture_output=True,text=True,shell=os.name=='nt',timeout=60);assert r.returncode==0,r.stdout+r.stderr;return json.loads(r.stdout.strip().splitlines()[-1])
                    opened=launch();setup_url=opened['setup_url'];checks.append('native_comparison_setup_launcher')
                    with sync_playwright() as p:
                        browser=p.chromium.launch()
                        try:
                            page=browser.new_page();page.goto(setup_url);page.locator('#language').select_option('ja')
                            page.wait_for_function("document.querySelector('#catalog_root').value.length>0")
                            def choose(field,target):
                                page.locator('[data-pick="'+field+'"]').click();page.wait_for_function("document.querySelector('#picker-path').textContent.length>0")
                                parts=Path(target).resolve().parts;drive=parts[0].replace('\\','/')
                                page.locator('#picker-roots').select_option(drive)
                                page.wait_for_function("value=>document.querySelector('#picker-path').textContent.replaceAll('\\\\','/')===value",arg=drive)
                                for part in parts[1:]:
                                    page.get_by_role('button',name='📁 '+part,exact=True).click()
                                    page.wait_for_function("value=>document.querySelector('#picker-path').textContent.replaceAll('\\\\','/').endsWith('/'+value)",arg=part)
                                page.locator('#picker-use').click()
                            choose('catalog_root',ready['catalog']);choose('animadex_root',ready['animadex']);page.locator('details summary').click();choose('output',str(workspace))
                            checks.append('drive_and_folder_navigation_without_commands_or_json')
                            page.locator('#check').click();expect(page.locator('#save')).to_be_enabled(timeout=30000);expect(page.locator('#result')).to_contain_text('比較可能：1件');checks.append('connection_and_pair_count')
                            page.locator('#save').click();expect(page.locator('#grid .card')).to_have_count(1,timeout=30000)
                            page.wait_for_function("[...document.querySelectorAll('#grid img')].length===2 && [...document.querySelectorAll('#grid img')].every(i=>i.complete&&i.naturalWidth>0)")
                            comparison_url=page.url;checks.append('save_opens_comparison_with_two_decoded_images')
                            page.locator('#comparison-settings').click();expect(page.locator('#animadex_root')).to_have_value(ready['animadex']);checks.append('settings_link_and_persistence')
                            reopened=launch();assert reopened['url']==comparison_url;checks.append('native_reopen_reuses_saved_comparison')
                        finally:browser.close()
                    result['passed']=True
                finally:
                    try:
                        if 'comparison_url' in locals():
                            bootstrap=get(comparison_url+'api/bootstrap');stop(comparison_url,'X-Comparison-Token',bootstrap['token'])
                    finally:
                        try:
                            if setup_url:
                                bootstrap=get(setup_url+'api/bootstrap');stop(setup_url,'X-Setup-Token',bootstrap['token'])
                        finally:
                            if workspace.exists():(workspace/'stop').touch()
                            if fixture:
                                try:fixture.wait(timeout=30)
                                except subprocess.TimeoutExpired:fixture.terminate();fixture.wait(timeout=10)
                    # Native setup workers release their file handles asynchronously after HTTP stop.
                    time.sleep(.5)
            result['test_servers_stopped']=True
    except Exception as error:result['passed']=False;result['error']=str(error);raise
    finally:
        report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args();run(args.archive,args.report)
