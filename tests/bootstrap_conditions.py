"""Adversarial checks of the distributed native entrypoints, using disposable fixtures."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys


def command(root, editor=False):
    name='open_editor' if editor else 'open_review'
    if os.name=='nt': return [str(root/(name+'.cmd'))]
    return ['/bin/sh',str(root/(name+('.command' if sys.platform=='darwin' else '.sh')))]


def invoke(root, extra=(), env=None, editor=False, timeout=180):
    return subprocess.run(command(root,editor)+['--no-open','--json',*extra],env=env,cwd=root.parent,
                          capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,shell=os.name=='nt')


def check(root, directory, old_python=None):
    # These files all come from the extracted release ZIP, not the checkout.
    fixture=directory/'Bootstrap cases 空白'
    fixture.mkdir()
    for folder in ('tools','review'): shutil.copytree(root/folder,fixture/folder)
    shutil.copy2(root/'VERSION',fixture/'VERSION')
    for file in root.glob('open_*'): shutil.copy2(file,fixture/file.name)
    empty=directory/'empty PATH';empty.mkdir()
    env={**os.environ,'CI':'true','PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
    env.pop('KREA2_CATALOG_PYTHON',None)
    env.pop('KREA2_CATALOG_NO_PAUSE',None) # CI must suppress waiting without this escape hatch.
    env['PATH']=str(empty)
    checks=[]
    def failure(expected, label, override=None, extra=()):
        result=invoke(fixture,['--resolve-only',*extra],{**env,**(override or {})},timeout=45)
        assert result.returncode==expected,(label,result.returncode,result.stdout,result.stderr)
        assert label in result.stderr,(label,result.stderr)
        assert 'Press Enter' not in result.stderr
        checks.append(label)
    failure(10,'PYTHON_MISSING')
    text=invoke(fixture,['--resolve-only'],env).stderr
    assert 'startup file again' in text
    assert ('downloads/windows' if os.name=='nt' else 'downloads/macos' if sys.platform=='darwin' else 'using/unix') in text
    failure(12,'PYTHON_PATH',{'KREA2_CATALOG_PYTHON':str(directory/'does not exist/python')})
    failure(12,'PYTHON_PATH',{'KREA2_CATALOG_PYTHON':sys.executable},['--python',str(directory/'bad CLI path')])
    if old_python:
        version=subprocess.check_output([old_python,'-c','import sys; print(sys.version_info[:2])'],text=True).strip()
        assert version=='(3, 9)',version
        old_bin=str(Path(old_python).parent)
        failure(11,'PYTHON_OLD',{'PATH':old_bin})
        failure(11,'PYTHON_OLD',{'KREA2_CATALOG_PYTHON':old_python})
        mixed={**env,'PATH':old_bin+os.pathsep+str(Path(sys.executable).parent)}
        result=invoke(fixture,['--resolve-only'],mixed)
        assert result.returncode==0,result.stderr
        compatible=json.loads(result.stdout.splitlines()[-1])['python']
        subprocess.run([compatible,'-c','import sys; assert sys.version_info >= (3,10)'],check=True)
        checks.append('mixed_real_python_39_and_compatible')
        subprocess.run([old_python,'-m','venv','--without-pip',str(fixture/'.venv')],check=True)
        before={p.relative_to(fixture/'.venv').as_posix():p.read_bytes() for p in (fixture/'.venv').rglob('*') if p.is_file()}
    else:
        before={}
        checks.append('real_python_39_scenarios_NOT_RUN')
    # Simulate an incomplete/foreign existing environment; never repair or remove it.
    legacy=fixture/'.catalog-venv';legacy.mkdir();(legacy/'keep.txt').write_text('DO NOT CHANGE')
    valid={**env,'KREA2_CATALOG_PYTHON':sys.executable}
    result=invoke(fixture,['--resolve-only','--force-venv'],valid,timeout=240)
    assert result.returncode==0,result.stderr
    created=Path(json.loads(result.stdout.splitlines()[-1])['python'])
    assert '.catalog-venv-1' in created.parts
    assert (legacy/'keep.txt').read_text()=='DO NOT CHANGE'
    if before:
        assert before=={p.relative_to(fixture/'.venv').as_posix():p.read_bytes() for p in (fixture/'.venv').rglob('*') if p.is_file()}
    checks.append('old_and_incomplete_venvs_preserved_new_private_environment')
    # Dependency capability failures are injected in child Python only, never installed globally.
    injection=directory/'capability fixture';injection.mkdir()
    (injection/'sitecustomize.py').write_text('''import builtins, os, sys
stage=os.environ.get('CATALOG_TEST_STAGE')
original=builtins.__import__
def guarded(name,*args,**kwargs):
    if stage=='venv' and name in ('venv','ensurepip'): raise ModuleNotFoundError('fixture: missing '+name)
    return original(name,*args,**kwargs)
builtins.__import__=guarded
arguments=getattr(sys,'orig_argv',[])
if stage=='network' and '-m' in arguments and 'pip' in arguments:
    sys.stderr.write('Network connection timed out (test fixture)\\n'); sys.stderr.flush(); os._exit(1)
if stage=='webp' and any('features.check' in a for a in arguments): os._exit(1)
if stage=='write':
    import tempfile
    def denied(*args,**kwargs): raise PermissionError('fixture: directory is not writable')
    tempfile.TemporaryFile=denied
''',encoding='utf-8')
    fault={**valid,'PYTHONPATH':str(injection)}
    failure(13,'VENV_MISSING',{**fault,'CATALOG_TEST_STAGE':'venv'},['--force-venv'])
    failure(14,'WRITE_PERMISSION',{**fault,'CATALOG_TEST_STAGE':'write'})
    failure(16,'NETWORK',{**fault,'CATALOG_TEST_STAGE':'network'},['--force-venv'])
    # Use the already-created compatible private venv with no network for a deficient-WebP probe.
    failure(15,'PILLOW_WEBP',{**fault,'CATALOG_TEST_STAGE':'webp'},['--force-venv'])
    return checks
