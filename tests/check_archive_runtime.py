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


def run(archive,report_path,test_venv=False,keep=False):
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
        first=launch(['--port','0']);base=first['url'].rstrip('/')
        assert first['version']=='0.91' and not first['reused'];checks.append('native_entrypoint')
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
        changed=post(base,'/api/editor/edit',{'key':key,'image_sha256':image_hash,'fields':{'name':'Edited 日本語','copyright':'Runtime test','copy_prompt':'test prompt','copy_tags':'test, tags'}},token)
        assert changed['saved'];assert get(base,'/api/editor/record?key='+key)['record']['name']=='Edited 日本語';checks.append('edit_saved')
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
        stop()
        if test_venv:
            result=subprocess.run([sys.executable,'-B',str(launcher),'--resolve-only','--force-venv','--json'],env=env,capture_output=True,text=True,timeout=240)
            assert result.returncode==0,result.stderr
            resolved=json.loads(result.stdout.strip())['python'];assert '.venv' in Path(resolved).parts
            subprocess.run([resolved,'-c',"from PIL import features; assert features.check('webp')"],check=True)
            checks.append('private_venv_and_webp')
        report={'platform':sys.platform,'python':sys.version.split()[0],'checks':checks,'passed':True,'desktop_file_manager_manually_tested':False}
        report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)
    finally:
        try:stop()
        finally:
            if keep:
                temporary._finalizer.detach();print('Test installation: '+str(root))
            else:temporary.cleanup()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--test-venv',action='store_true');args=parser.parse_args()
    run(args.archive,args.report,args.test_venv)
