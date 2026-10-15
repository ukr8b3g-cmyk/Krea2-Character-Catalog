from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent


@unittest.skipUnless(os.name=='nt','Windows native startup test')
class WindowsBootstrapTests(unittest.TestCase):
    def test_startup_file_alone_explains_missing_app_without_ci_pause(self):
        with tempfile.TemporaryDirectory(prefix='Catalog missing files ') as directory:
            root=Path(directory);entry=root/'START_HERE - Windows.cmd'
            shutil.copyfile(ROOT/entry.name,entry)
            result=subprocess.run([str(entry)],env={**os.environ,'CI':'true'},cwd=root.parent,shell=True,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertIn('Extract the complete catalog ZIP',result.stderr)

    def test_stale_path_entries_do_not_abort_python_discovery(self):
        with tempfile.TemporaryDirectory(prefix='Catalog bootstrap 日本語 ') as directory:
            root=Path(directory);internal=root/'app';(internal/'tools').mkdir(parents=True)
            for name in ['bootstrap.cmd','bootstrap.ps1']:
                shutil.copyfile(ROOT/'tools'/name,internal/'tools'/name)
            shutil.copyfile(ROOT/'START_HERE - Windows.cmd',root/'START_HERE - Windows.cmd')
            (internal/'tools/launch_catalog.py').write_text('import json,sys; print(json.dumps({"python":sys.executable}))',encoding='utf-8')
            missing_drive=next(letter+':\\missing-python' for letter in 'ZYXWVUTSRQPONMLKJIHGFED' if not Path(letter+':/').exists())
            stale=[missing_drive,str(root/'deleted folder'),'"'+str(root/'quoted missing')+'"']
            env={**os.environ,'CI':'true','PYTHONDONTWRITEBYTECODE':'1'}
            env.pop('KREA2_CATALOG_PYTHON',None)
            for valid in [True,False]:
                with self.subTest(compatible_python_present=valid):
                    env['PATH']=';'.join(stale+([str(Path(sys.executable).parent)] if valid else []))
                    result=subprocess.run([str(root/'START_HERE - Windows.cmd'),'--resolve-only','--json'],env=env,cwd=root.parent,shell=True,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=45)
                    if valid:
                        self.assertEqual(result.returncode,0,result.stderr)
                        selected=json.loads(result.stdout.strip())['python']
                        self.assertEqual(Path(selected).resolve(),Path(sys.executable).resolve())
                    else:
                        self.assertEqual(result.returncode,10,result.stderr)
                        self.assertIn('[PYTHON_MISSING]',result.stderr)
                    self.assertNotIn('Join-Path :',result.stderr)
                    self.assertNotIn('Press Enter',result.stderr)


if __name__=='__main__':unittest.main()
