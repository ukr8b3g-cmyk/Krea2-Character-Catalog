from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parent.parent
SCRIPTS=ROOT/'skills/krea2-animadex-review/scripts'
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))


class ComparisonLauncherTests(unittest.TestCase):
    def test_native_start_reuse_authenticated_stop_restart_without_catalog_service(self):
        with tempfile.TemporaryDirectory(prefix='Comparison 日本語 ') as directory:
            workspace=Path(directory);catalog=workspace/'catalog';(catalog/'tools').mkdir(parents=True);(catalog/'review').mkdir()
            for name in ['bootstrap.cmd','bootstrap.ps1','bootstrap.sh']:shutil.copy2(ROOT/'tools'/name,catalog/'tools'/name)
            shutil.copy2(ROOT/'review/runtime_support.py',catalog/'review/runtime_support.py')
            (catalog/'outputs').mkdir();generated=catalog/'outputs/sample.PNG';generated.write_bytes(b'catalog sample bytes')
            thumbs=workspace/'AnimaDex thumbs';thumbs.mkdir();reference=thumbs/'Reference.JPG';reference.write_bytes(b'reference sample bytes')
            folder=workspace/'Comparison with spaces';internal=folder/'app';internal.mkdir(parents=True)
            pair={'key':'test/one','name':'Test','copyright':'Test work','catalog_identity':'test, test work','reference_name':'Test reference','catalog_image':str(generated),'reference_image':str(reference),'catalog_image_sha256':hashlib.sha256(generated.read_bytes()).hexdigest(),'reference_image_sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}
            payload={'schema':'krea2-portable-pairs-v1','environment':{'catalog_root':str(catalog),'thumbs_root':str(thumbs)},'pairs':[pair],'stats':{'characters':1,'available_pairs':1}}
            (internal/'pairs.json').write_text(json.dumps(payload),encoding='utf-8');(internal/'unresolved.csv').write_text('key,reason\n')
            for name in ['index.html','compare.js','compare.css']:shutil.copy2(SCRIPTS.parent/'assets'/name,internal/name)
            spec=importlib.util.spec_from_file_location('comparison_launcher_under_test',SCRIPTS/'comparison_launcher.py')
            launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher);launcher.setup(catalog,folder,SCRIPTS/'review.py')
            env={**os.environ,'CI':'true','KREA2_CATALOG_PYTHON':sys.executable,'PYTHONDONTWRITEBYTECODE':'1'}
            name='START_COMPARISON - Windows.cmd' if os.name=='nt' else 'START_COMPARISON - macOS.command' if sys.platform=='darwin' else 'START_COMPARISON - Linux.sh'
            command=[str(folder/name)] if os.name=='nt' else ['sh',str(folder/name)]
            def start():
                result=subprocess.run(command+['--no-open','--json'],env=env,cwd=workspace,capture_output=True,text=True,timeout=40,shell=os.name=='nt')
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                return json.loads(result.stdout.strip())
            def get(url,path):
                with HTTP.open(url.rstrip('/')+path,timeout=5) as response:return response.read()
            def stop(url):
                bootstrap=json.loads(get(url,'/api/bootstrap'));token=bootstrap['token'];pid=bootstrap['pid']
                request=urllib.request.Request(url.rstrip('/')+'/api/shutdown',data=b'{}',headers={'Content-Type':'application/json','X-Comparison-Token':token},method='POST')
                with HTTP.open(request,timeout=5) as response:self.assertTrue(json.load(response)['stopped'])
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    try:get(url,'/api/info');time.sleep(.1)
                    except (OSError,ValueError):break
                else:self.fail('Comparison server did not stop')
                if os.name=='nt':
                    import ctypes
                    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
                    kernel.OpenProcess.restype=ctypes.c_void_p
                    handle=kernel.OpenProcess(0x00100000,False,pid)
                    if handle:
                        kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
                        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
                        try:self.assertEqual(kernel.WaitForSingleObject(handle,10000),0,'Comparison process did not exit')
                        finally:kernel.CloseHandle(handle)
            current=None
            try:
                first=start();current=first['url'];self.assertFalse(first['reused'])
                self.assertEqual(get(current,'/pair-image?id=0&side=catalog'),generated.read_bytes())
                self.assertEqual(get(current,'/pair-image?id=0&side=reference'),reference.read_bytes())
                data=json.loads(get(current,'/pairs.json'));self.assertNotIn('catalog_image',data['pairs'][0])
                second=start();self.assertTrue(second['reused']);self.assertEqual(first['pid'],second['pid'])
                bad=urllib.request.Request(current.rstrip('/')+'/api/shutdown',data=b'{}',headers={'Content-Type':'application/json'},method='POST')
                with self.assertRaises(urllib.error.HTTPError) as rejected:HTTP.open(bad,timeout=5)
                self.assertEqual(rejected.exception.code,403)
                before=(internal/'pairs.json').read_bytes();stop(current);current=None
                again=start();current=again['url'];self.assertEqual(again['url'],first['url']);self.assertFalse(again['reused'])
                self.assertEqual((internal/'pairs.json').read_bytes(),before)
                self.assertEqual(generated.read_bytes(),b'catalog sample bytes');self.assertEqual(reference.read_bytes(),b'reference sample bytes')
            finally:
                if current:stop(current)


if __name__=='__main__':unittest.main()
