"""One local catalog launcher for Windows, macOS, and Linux (Python 3.10+)."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'review'))
from runtime_support import CatalogLock, atomic_json, catalog_version, read_json

HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def get_json(url):
    with HTTP.open(url, timeout=2) as response:
        return json.load(response)


def valid_url(url):
    try:
        value = urllib.parse.urlsplit(url)
        return value.scheme == 'http' and value.hostname == '127.0.0.1' and value.port is not None and not value.username and not value.password and value.path in ('', '/') and not value.query and not value.fragment
    except (ValueError, TypeError):
        return False


def same_catalog(info, root):
    try:
        return info.get('app') == 'Krea2CatalogReview' and Path(info['root']).resolve() == root.resolve()
    except (ValueError, KeyError, TypeError, OSError):
        return False


def service(root, port):
    saved = read_json(root / 'outputs/review_service.json')
    urls = [saved.get('url'), f'http://127.0.0.1:{port}/'] if port else [saved.get('url')]
    for url in dict.fromkeys(urls):
        if not valid_url(url):
            continue
        try:
            info = get_json(url.rstrip('/') + '/api/info')
            if same_catalog(info, root):
                return url.rstrip('/'), info
        except (OSError, ValueError):
            pass
    return None


def check_python(path, dependencies=False):
    if not Path(path).is_file():
        return False
    code = 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'
    if dependencies:
        code = "import sys,PIL; from PIL import features; sys.exit(0 if sys.version_info >= (3,10) and 10 <= int(PIL.__version__.split('.')[0]) < 13 and features.check('webp') else 1)"
    try:
        return subprocess.run([str(path), '-c', code], capture_output=True, timeout=20).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def environment_python(folder):
    return folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def resolve_python(root, preferred=None, force_venv=False):
    candidates = [preferred, os.environ.get('KREA2_CATALOG_PYTHON'),
                  read_json(root / 'outputs/python_runtime.json').get('python'),
                  str(environment_python(root / '.venv')), sys.executable,
                  shutil.which('python3'), shutil.which('python')]
    if os.name == 'nt':
        launcher = shutil.which('py')
        if launcher:
            found = subprocess.run([launcher, '-3', '-c', 'import sys; print(sys.executable)'], capture_output=True, text=True)
            if found.returncode == 0:
                candidates.append(found.stdout.strip())
    base = None
    for candidate in dict.fromkeys(p for p in candidates if p):
        if not check_python(candidate):
            continue
        if base is None:
            base = str(Path(candidate).resolve())
        if not force_venv and check_python(candidate, dependencies=True):
            return str(Path(candidate).absolute())
    if base is None:
        raise RuntimeError('Python 3.10+ was not found. Install Python from https://www.python.org/downloads/ and reopen the catalog, or set KREA2_CATALOG_PYTHON to its executable.')
    folder = root / '.venv'
    executable = environment_python(folder)
    if folder.exists() and not executable.is_file():
        folder = root / ('.venv-' + sys.platform)
        executable = environment_python(folder)
    if not executable.is_file():
        print('Preparing a private Python environment...', file=sys.stderr, flush=True)
        result = subprocess.run([base, '-m', 'venv', str(folder)], stdout=sys.stderr, stderr=sys.stderr)
        if result.returncode:
            raise RuntimeError('Could not create a private venv. Check write permissions and that your Python includes venv (on Ubuntu/Debian, install the matching python3-venv package).')
    if not check_python(executable, dependencies=True):
        print('Installing Pillow in the private environment (internet required)...', file=sys.stderr, flush=True)
        result = subprocess.run([str(executable), '-m', 'pip', 'install', '--disable-pip-version-check', '--index-url', 'https://pypi.org/simple', '-r', str(root / 'tools/requirements-editor.txt')], stdout=sys.stderr, stderr=sys.stderr)
        if result.returncode:
            raise RuntimeError('Could not install Pillow. Check internet access or use an existing Python with Pillow and WebP support.')
    if not check_python(executable, dependencies=True):
        raise RuntimeError('The private Python does not support Pillow 10–12 and WebP. Select a compatible Python installation.')
    return str(executable)


def stop_service(root, port):
    current = service(root, port)
    if current is None:
        return {'stopped': True, 'running': False}
    url, info = current
    token = get_json(url + '/api/editor/bootstrap')['token']
    request = urllib.request.Request(url + '/api/shutdown', data=b'{}', method='POST', headers={'Content-Type':'application/json', 'Origin':url, 'X-Review-Token':token})
    with HTTP.open(request, timeout=5) as response:
        json.load(response)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            observed = get_json(url + '/api/info')
            if not same_catalog(observed, root) or observed.get('pid') != info['pid']:
                return {'stopped':True, 'pid':info['pid']}
        except (OSError, ValueError):
            return {'stopped':True, 'pid':info['pid']}
        time.sleep(0.1)
    raise RuntimeError('The catalog did not stop. No unrelated process was terminated.')


def launch(args):
    root = args.root.resolve()
    if not (root / 'review/server.py').is_file() or not (root / 'VERSION').is_file():
        raise RuntimeError('Run the launcher from the fully extracted catalog folder.')
    with CatalogLock(root / 'outputs/launcher.lock', timeout=180):
        if args.stop:
            return stop_service(root, args.port)
        if args.resolve_only:
            return {'python': resolve_python(root, args.python, args.force_venv)}
        current = service(root, args.port)
        reused = current is not None
        if current:
            url, info = current
            if info.get('catalog_version') != catalog_version(root):
                raise RuntimeError('An older service is running for this folder. Stop this catalog with --stop, then reopen it. Your images and saved changes are preserved.')
        else:
            python = resolve_python(root, args.python, args.force_venv)
            atomic_json(root / 'outputs/python_runtime.json', {'python':python, 'platform':sys.platform})
            outputs = root / 'outputs'
            options = {'stdin':subprocess.DEVNULL, 'cwd':str(root), 'close_fds':True}
            if os.name == 'nt':
                options['creationflags'] = subprocess.CREATE_NO_WINDOW
            else:
                options['start_new_session'] = True
            with (outputs / 'review_server.log').open('ab') as out, (outputs / 'review_server.err.log').open('ab') as err:
                child = subprocess.Popen([python,'-B',str(root/'review/server.py'),'--root',str(root),'--port',str(args.port),'--fallback-port'], stdout=out, stderr=err, **options)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                current = service(root, args.port)
                if current:
                    url, info = current
                    break
                if child.poll() is not None:
                    raise RuntimeError('The catalog could not start. See outputs/review_server.err.log for the cause.')
                time.sleep(0.15)
            else:
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=10)
                raise RuntimeError('Startup timed out. See outputs/review_server.err.log.')
        route = '/editor' if args.editor else args.route
        target = url + route
        if not args.no_open:
            if not webbrowser.open(target):
                print('Open this address in your browser: ' + target, file=sys.stderr)
        return {'url':target, 'root':str(root), 'pid':info['pid'], 'reused':reused, 'version':info.get('catalog_version')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--python',help='Preferred Python executable')
    parser.add_argument('--port',type=int,default=8790)
    parser.add_argument('--route',choices=['/','/editor'],default='/')
    parser.add_argument('--editor',action='store_true')
    parser.add_argument('--no-open',action='store_true')
    parser.add_argument('--force-venv',action='store_true')
    parser.add_argument('--resolve-only',action='store_true')
    parser.add_argument('--stop',action='store_true')
    parser.add_argument('--json',action='store_true',help='Print a machine-readable result')
    args = parser.parse_args()
    try:
        if sys.version_info < (3,10):
            raise RuntimeError('Python 3.10+ is required.')
        if not 0 <= args.port <= 65535:
            raise ValueError('Port must be between 0 and 65535.')
        result = launch(args)
        print(json.dumps(result,ensure_ascii=True) if args.json else result.get('url', result.get('python', 'Catalog stopped.')),flush=True)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('Krea2 Catalog: ' + str(error),file=sys.stderr,flush=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
