"""One-click startup for a prepared, independent comparison workspace."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))


def root_folder(folder):
    folder=Path(folder).resolve()
    if (folder/'pairs.json').is_file():return folder
    if (folder/'app/pairs.json').is_file():return folder/'app'
    raise ValueError('Open the START_COMPARISON file in the prepared comparison folder.')


def setup(catalog,folder,script):
    catalog=Path(catalog);folder=Path(folder);tools=folder/'app/tools';tools.mkdir(parents=True)
    for name in ['bootstrap.cmd','bootstrap.ps1','bootstrap.sh']:
        shutil.copy2(catalog/'tools'/name,tools/name)
    shutil.copy2(catalog/'review/runtime_support.py',tools/'runtime_support.py')
    shutil.copy2(script,folder/'app/review.py')
    shutil.copy2(Path(__file__),folder/'app/comparison_launcher.py')
    (tools/'startup.py').write_text("from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom comparison_launcher import main\nmain(Path(__file__).resolve().parents[1])\n",encoding='utf-8')
    windows='@echo off\r\nsetlocal\r\ntitle Krea2 - AnimaDex Comparison\r\ncall "%~dp0app\\tools\\bootstrap.cmd" %*\r\nexit /b %errorlevel%\r\n'
    (folder/'START_COMPARISON - Windows.cmd').write_bytes(windows.encode('ascii'))
    shell='#!/bin/sh\ncomparison_home=$(CDPATH= cd -- "${0%/*}" && pwd) || exit 1\nexec /bin/sh "$comparison_home/app/tools/bootstrap.sh" "$@"\n'
    for name in ['START_COMPARISON - macOS.command','START_COMPARISON - Linux.sh']:
        path=folder/name;path.write_text(shell,encoding='utf-8',newline='\n');path.chmod(0o755)


def current(root):
    try:saved=json.loads((root/'review-server.json').read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return None
    parsed=urllib.parse.urlsplit(saved.get('url',''))
    if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or parsed.username or parsed.password or parsed.path not in ('','/'):
        raise ValueError('The saved comparison address is invalid. Ask your assistant to repair this comparison setup.')
    try:
        with HTTP.open(saved['url'].rstrip('/')+'/api/info',timeout=2) as response:info=json.load(response)
    except (OSError,ValueError):return None
    if info.get('app')!='Krea2AnimaDexComparison' or Path(info.get('review_dir','')).resolve()!=root:
        raise ValueError('The saved comparison port belongs to another application. No process was stopped.')
    return {**saved,'url':saved['url'].rstrip('/')+'/'}


def open_comparison(folder,no_open=False):
    root=root_folder(folder)
    sys.path.insert(0,str(root/'tools'))
    from runtime_support import CatalogLock
    with CatalogLock(root/'comparison-launcher.lock',timeout=15):
        info=current(root);reused=info is not None
        if info is None:
            options={'cwd':str(root),'stdin':subprocess.DEVNULL,'close_fds':True}
            if os.name=='nt':options['creationflags']=subprocess.CREATE_NO_WINDOW
            else:options['start_new_session']=True
            with (root/'comparison.log').open('ab') as out,(root/'comparison.err.log').open('ab') as err:
                child=subprocess.Popen([sys.executable,'-B',str(root/'review.py'),'serve','--review-dir',str(root),'--port','0'],stdout=out,stderr=err,**options)
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                info=current(root)
                if info is not None:break
                if child.poll() is not None:raise ValueError('Comparison could not start. Keep the whole comparison folder together; ask your assistant to check app/comparison.err.log. A saved port may be in use.')
                time.sleep(.1)
            else:
                child.terminate();child.wait(timeout=10)
                raise ValueError('Comparison startup timed out. Ask your assistant to check the setup.')
        if not no_open:webbrowser.open(info['url'])
        return {'url':info['url'],'pid':info['pid'],'reused':reused,'review_dir':str(root)}


def main(folder):
    import argparse
    parser=argparse.ArgumentParser(description='Open your prepared AnimaDex comparison.')
    parser.add_argument('--no-open',action='store_true');parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    try:
        result=open_comparison(folder,args.no_open)
        print(json.dumps(result) if args.json else result['url'],flush=True)
    except (OSError,ValueError,TimeoutError) as error:
        print('Krea2 comparison: '+str(error),file=sys.stderr,flush=True);raise SystemExit(1)
