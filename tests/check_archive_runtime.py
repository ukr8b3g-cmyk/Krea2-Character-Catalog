"""Exercise the same full catalog ZIP on each native OS, outside its source tree."""
from pathlib import Path
import argparse
import base64
import hashlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.parse
import uuid
import zipfile
from bootstrap_conditions import check as check_bootstrap, invoke
from PIL import Image

SOURCE=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(SOURCE/'tools'))
from package_release import safe_extract
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))


def get(base,path):
    with HTTP.open(base+path,timeout=20) as response:return json.load(response)


def post(base,path,payload,token):
    request=urllib.request.Request(base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Origin':base,'X-Review-Token':token})
    with HTTP.open(request,timeout=20) as response:return json.load(response)


def run(archive,report_path,test_venv=False,keep=False,old_python=None,browser_test=False):
    temporary=tempfile.TemporaryDirectory(prefix='Krea2 ZIP test ')
    install=Path(temporary.name)/'Folder with spaces 日本語'
    safe_extract(archive,install)
    root=install/'Krea2-Character-Catalog'
    launcher=root/'tools/launch_catalog.py'
    env={**os.environ,'KREA2_CATALOG_PYTHON':sys.executable,'KREA2_CATALOG_NO_PAUSE':'1','PYTHONDONTWRITEBYTECODE':'1'}
    extension='.cmd' if os.name=='nt' else '.command' if sys.platform=='darwin' else '.sh'
    def command(editor=False):
        entry=str(root/('open_editor' if editor else 'open_review'))+extension
        return [entry] if os.name=='nt' else ['sh',entry]
    def launch(extra=(),editor=False):
        result=subprocess.run(command(editor)+['--no-open','--json',*extra],env=env,cwd=temporary.name,capture_output=True,text=True,timeout=100,shell=os.name=='nt')
        error_log=root/'outputs/review_server.err.log'
        assert result.returncode==0,result.stderr+result.stdout+(error_log.read_text(encoding='utf-8',errors='replace')[-4500:] if error_log.exists() else '')
        return json.loads(result.stdout.strip().splitlines()[-1])
    def stop():
        subprocess.run([sys.executable,'-B',str(launcher),'--stop','--no-open','--json'],env=env,capture_output=True,text=True,check=True,timeout=30)
        deadline=time.monotonic()+10
        while (root/'outputs/review_service.json').exists() and time.monotonic()<deadline:time.sleep(.1)
        assert not (root/'outputs/review_service.json').exists()
    checks=[]
    try:
        if test_venv:
            checks.extend(check_bootstrap(root,Path(temporary.name),old_python))
        first=launch(['--port','0']);base=first['url'].rstrip('/')
        assert first['version']==(root/'VERSION').read_text().strip() and not first['reused'];checks.append('native_entrypoint')
        info=get(base,'/api/info');assert Path(info['root']).resolve()==root.resolve()
        listing=get(base,'/api/list');assert len(listing['entries'])==3919
        assert len([e for e in listing['entries'] if e['kind']=='style'])==110
        assert all(not e['hidden'] for e in listing['entries']);checks.append('complete_catalog_3919')
        second=launch(['--port','0'],editor=True);assert second['pid']==first['pid'] and second['reused'] and second['url'].endswith('/editor');checks.append('editor_and_service_reuse')
        duplicate=subprocess.run([sys.executable,'-B',str(root/'review/server.py'),'--root',str(root),'--port','0'],env=env,capture_output=True,text=True,timeout=20)
        assert duplicate.returncode!=0 and get(base,'/api/info')['pid']==first['pid'];checks.append('server_duplicate_refused')
        image=io.BytesIO();Image.new('RGB',(31,47),(19,38,57)).save(image,format='WEBP',lossless=True)
        raw=image.getvalue();image_hash=hashlib.sha256(raw).hexdigest()
        token=get(base,'/api/editor/bootstrap')['token']
        saved=post(base,'/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':'blank fields.webp','image_base64':base64.b64encode(raw).decode()},token)
        assert saved['saved'];key=saved['key'];record=get(base,'/api/editor/record?key='+key)['record']
        assert record['name']=='blank fields' and record['copy_prompt']=='' and record['copy_tags']==''
        assert (root/'outputs'/record['files']['image']).read_bytes()==raw;checks.append('blank_field_webp_registration')
        for fmt,filename,color in [('PNG','日本語 空白.PnG',(73,22,81)),('JPEG','MiXeD 名前.JpEg',(44,65,21))]:
            stream=io.BytesIO();Image.new('RGB',(29,39),color).save(stream,format=fmt)
            original=stream.getvalue()
            added=post(base,'/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':filename,'image_base64':base64.b64encode(original).decode()},token)
            r=get(base,'/api/editor/record?'+urllib.parse.urlencode({'key':added['key']}))['record']
            assert r['source_filename']==filename and r['name']==Path(filename).stem
            assert (root/'outputs'/r['files']['image']).read_bytes()==original
        checks.append('png_jpeg_webp_original_bytes_and_mixed_case_filenames')
        changed=post(base,'/api/editor/edit',{'key':key,'image_sha256':image_hash,'fields':{'name':'Edited 日本語','copyright':'Runtime test','copy_prompt':'test prompt','copy_tags':'test, tags'}},token)
        assert changed['saved'];assert get(base,'/api/editor/record?key='+key)['record']['name']=='Edited 日本語';checks.append('edit_saved')
        check_write_failure(root,base,token,key,image_hash)
        checks.append('write_failure_protects_saved_data')
        if browser_test:
            check_browser(base,root,Path(temporary.name));checks.extend(['chromium_list_search_add_edit_save_reload','chromium_heading_version_and_language'])
        post(base,'/api/hide',{'keys':[key]},token)
        post(base,'/api/favorite',{'key':key,'enabled':True},token)
        stop();checks.append('clean_shutdown')
        occupied=socket.socket();occupied.bind(('127.0.0.1',0));occupied.listen();port=occupied.getsockname()[1]
        try:
            restarted=launch(['--port',str(port)])
            assert urllib.parse.urlsplit(restarted['url']).port!=port;checks.append('occupied_port_fallback')
        finally:occupied.close()
        base=restarted['url'].rstrip('/');listing=get(base,'/api/list')
        edited=next(e for e in listing['entries'] if e['key']==key)
        assert edited['name']=='Edited 日本語' and edited['hidden'] and edited['favorite'];checks.append('state_survives_restart')
        if browser_test:
            assert any(e['name']=='CI Browser saved' for e in listing['entries'])
            checks.append('browser_saved_entry_survives_backend_restart')
            check_stop_browser(base,root)
            checks.append('chromium_stop_server_labels_tooltips_shutdown_tab_and_saved_data')
            reopened=launch(['--port','0']);base=reopened['url'].rstrip('/')
            edited=next(e for e in get(base,'/api/list')['entries'] if e['key']==key)
            assert edited['name']=='Edited 日本語' and edited['hidden'] and edited['favorite']
            checks.append('native_reopen_after_stop_button_preserves_state')
        stop()
        if test_venv:
            result=invoke(root,['--resolve-only','--force-venv'],env,timeout=240)
            assert result.returncode==0,result.stderr
            resolved=json.loads(result.stdout.strip())['python'];assert '.catalog-venv' in Path(resolved).parts
            subprocess.run([resolved,'-c',"from PIL import features; assert features.check('webp')"],check=True)
            checks.append('private_venv_and_webp')
        report={'platform':sys.platform,'python':sys.version.split()[0],'checks':checks,'passed':True,'desktop_file_manager_manually_tested':False,'animadex_integration_tested':False}
        report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)
    except Exception as error:
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps({'platform':sys.platform,'passed':False,'checks':checks,'error':str(error)},indent=2),encoding='utf-8')
        raise
    finally:
        try:stop()
        finally:
            if keep:
                temporary._finalizer.detach();print('Test installation: '+str(root))
            else:temporary.cleanup()


def check_write_failure(root,base,token,key,digest):
    target=root/'outputs/user_catalog_edits.json';before=target.read_bytes()
    catalog=root/'outputs/user_catalog.json';before_catalog=catalog.read_bytes()
    operation=uuid.uuid4()
    if os.name=='nt':
        import ctypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
        kernel.CreateFileW.restype=ctypes.c_void_p
        handles=[kernel.CreateFileW(str(f),0x80000000,1,None,3,0,None) for f in (target,catalog)]
        assert all(h not in (None,ctypes.c_void_p(-1).value) for h in handles)
    else:
        mode=target.parent.stat().st_mode;target.parent.chmod(0o500)
    try:
        try:
            post(base,'/api/editor/edit',{'key':key,'image_sha256':digest,'fields':{'name':'MUST NOT SAVE'}},token)
            raise AssertionError('Write failure must not report success')
        except urllib.error.HTTPError as error:
            assert error.code>=400 and 'WRITE_PERMISSION' in error.read().decode()
        stream=io.BytesIO();Image.new('RGB',(53,33),(77,9,43)).save(stream,format='PNG')
        try:
            post(base,'/api/editor/add',{'operation_id':str(operation),'filename':'failed.PNG','image_base64':base64.b64encode(stream.getvalue()).decode()},token)
            raise AssertionError('Failed registration must not report success')
        except urllib.error.HTTPError as error:
            assert error.code>=400 and 'WRITE_PERMISSION' in error.read().decode()
        assert target.read_bytes()==before
        assert catalog.read_bytes()==before_catalog
        assert not (root/'outputs/user_items'/operation.hex).exists()
        assert get(base,'/api/editor/record?key='+key)['record']['name']=='Edited 日本語'
        if os.name!='nt':
            result=invoke(root,['--resolve-only'],{**os.environ,'CI':'true','KREA2_CATALOG_PYTHON':sys.executable})
            assert result.returncode==14 and 'WRITE_PERMISSION' in result.stderr,result.stderr
    finally:
        if os.name=='nt':
            kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            for handle in handles:kernel.CloseHandle(handle)
        else:target.parent.chmod(mode)
    assert not list(target.parent.glob('*.tmp'))


def check_stop_browser(base,root):
    from playwright.sync_api import sync_playwright,expect
    protected=[root/'outputs'/name for name in ['review_state.json','user_catalog.json','user_catalog_edits.json']]
    protected += [p for p in (root/'outputs/user_items').rglob('*') if p.is_file()]
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.exists()}
    with sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            page=browser.new_page();page.goto(base)
            page.locator('#language').select_option('en')
            stop_button=page.get_by_role('button',name='Stop server',exact=True)
            expect(stop_button).to_be_enabled(timeout=30000)
            expect(stop_button).to_have_attribute('title',"Stop this catalog's background process. The browser tab stays open.")
            page.locator('#language').select_option('ja')
            stop_button=page.get_by_role('button',name='サーバー停止',exact=True)
            expect(stop_button).to_have_attribute('title','このカタログのバックグラウンド処理を停止します。ブラウザーの画面は閉じません。')
            stop_button.click()
            expect(page.get_by_role('button',name='サーバー停止済み',exact=True)).to_be_disabled()
            expect(page.locator('#connection')).to_contain_text('サーバーを停止しました')
            assert not page.is_closed() and page.url.rstrip('/')==base
            deadline=time.monotonic()+10
            while (root/'outputs/review_service.json').exists() and time.monotonic()<deadline:time.sleep(.1)
            assert not (root/'outputs/review_service.json').exists()
            with socket.socket() as sock:assert sock.connect_ex(('127.0.0.1',urllib.parse.urlsplit(base).port))!=0
            assert all(path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==digest for path,digest in before.items())
        finally:browser.close()


def check_browser(base,root,directory):
    # CI-only disposable headless Chromium, distinct from a user's desktop/browser.
    from playwright.sync_api import sync_playwright, expect
    image=directory/'UI 架空.PNG';Image.new('RGB',(23,27),(77,81,65)).save(image)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page()
        page.goto(base)
        expect(page.locator('#grid .card').first).to_be_visible(timeout=30000)
        version='v'+(root/'VERSION').read_text().strip()
        expect(page.locator('h1')).to_contain_text(version)
        page.locator('#language').select_option('ja')
        expect(page.locator('h1')).to_contain_text(version)
        page.locator('#language').select_option('en')
        expect(page.locator('h1')).to_contain_text(version)
        page.locator('#search').fill('akari (pokemon)')
        expect(page.locator('#grid .card')).to_have_count(1)
        page.reload();expect(page.locator('#search')).to_have_value('akari (pokemon)')
        page.goto(base+'/editor')
        page.locator('#file').set_input_files(str(image))
        page.locator('#name').fill('CI Browser 日本語')
        page.locator('#register').click()
        expect(page.locator('#status')).to_contain_text('Saved to the catalog.',timeout=20000)
        page.goto(base)
        page.locator('#search').fill('CI Browser 日本語')
        expect(page.locator('#grid .card')).to_have_count(1)
        page.locator('#grid .card img').click()
        page.locator('#detail-edit').click()
        page.locator('#edit-name').fill('CI Browser saved')
        page.locator('#panel-edit-save').click()
        expect(page.locator('#detail-name')).to_have_text('CI Browser saved')
        page.reload();page.locator('#search').fill('CI Browser saved')
        expect(page.locator('#grid .card')).to_have_count(1)
        browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--test-venv',action='store_true');parser.add_argument('--old-python');parser.add_argument('--browser-test',action='store_true');args=parser.parse_args()
    run(args.archive,args.report,args.test_venv,old_python=args.old_python,browser_test=args.browser_test)
