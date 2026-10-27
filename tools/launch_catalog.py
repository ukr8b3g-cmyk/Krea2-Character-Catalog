"""One local catalog launcher for Windows, macOS, and Linux (Python 3.10+)."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'review'))
from runtime_support import catalog_origin, CatalogLock, atomic_json, catalog_version, read_json
from catalog_layout import app_root

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
    origin=catalog_origin(root)
    urls=[saved.get('url')]
    if origin:urls.append(f"http://127.0.0.1:{origin['port']}/")
    if port:urls.append(f'http://127.0.0.1:{port}/')
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


class RuntimeIssue(RuntimeError):
    def __init__(self, code, category, message):
        super().__init__('[' + category + '] ' + message)
        self.code = code


def writable(folder):
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=folder):
            pass
    except PermissionError as error:
        raise RuntimeIssue(14, 'WRITE_PERMISSION', 'This folder is not writable: ' + str(folder) + '. Extract the catalog to your own writable folder; existing data was not replaced.') from error


def resolve_python(root, preferred=None, force_venv=False):
    explicit = preferred or os.environ.get('KREA2_CATALOG_PYTHON')
    if explicit:
        if not Path(explicit).is_file():
            raise RuntimeIssue(12, 'PYTHON_PATH', 'The specified Python path is invalid. Correct --python / KREA2_CATALOG_PYTHON, or unset it.')
        try:
            probe = subprocess.run([explicit, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 11)'], capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeIssue(12, 'PYTHON_PATH', 'The specified Python cannot run. Correct or unset its path.') from error
        if probe.returncode == 11:
            raise RuntimeIssue(11, 'PYTHON_OLD', 'The specified Python is older than 3.10. Install a supported version and reopen the startup file.')
        if probe.returncode:
            raise RuntimeIssue(12, 'PYTHON_PATH', 'The specified Python cannot run. Correct or unset its path.')
    candidates = [explicit, read_json(root / 'outputs/python_runtime.json').get('python'),
                  str(environment_python(root / '.venv')), sys.executable,
                  shutil.which('python3'), shutil.which('python')]
    candidates += [str(environment_python(p)) for p in sorted(root.glob('.catalog-venv*')) if p.is_dir()]
    base = None
    for candidate in dict.fromkeys(p for p in candidates if p):
        if not check_python(candidate):
            continue
        if base is None:
            base = str(Path(candidate).absolute())
        if not force_venv and check_python(candidate, dependencies=True):
            return str(Path(candidate).absolute())
    if base is None:
        raise RuntimeIssue(10, 'PYTHON_MISSING', 'Python 3.10+ was not found. Install Python and reopen the startup file. See docs/PLATFORMS.md.')
    supported = subprocess.run([base, '-c', 'import venv, ensurepip'], capture_output=True, text=True)
    if supported.returncode:
        raise RuntimeIssue(13, 'VENV_MISSING', 'This Python lacks venv or ensurepip. Install the matching venv package (e.g. python3-venv on Ubuntu/Debian), or choose another complete Python installation. Existing environments were not changed.')
    writable(root)
    # Never repair or install dependencies into a pre-existing environment.
    folder = root / '.catalog-venv'
    number = 1
    while folder.exists():
        folder = root / ('.catalog-venv-' + str(number))
        number += 1
    print('Preparing a new private Python environment: ' + folder.name, file=sys.stderr, flush=True)
    result = subprocess.run([base, '-m', 'venv', str(folder)], capture_output=True, text=True)
    if result.returncode:
        if 'Permission denied' in result.stderr or 'Access is denied' in result.stderr:
            raise RuntimeIssue(14, 'WRITE_PERMISSION', 'Cannot create the private environment. Extract the catalog to a writable folder.')
        raise RuntimeIssue(13, 'VENV_MISSING', 'Could not create a private venv. Check that the matching venv/ensurepip package is installed. ' + result.stderr[-1200:])
    executable = environment_python(folder)
    print('Installing Pillow in this new environment (internet required)...', file=sys.stderr, flush=True)
    result = subprocess.run([str(executable), '-m', 'pip', 'install', '--disable-pip-version-check', '--retries', '1', '--timeout', '15', '--index-url', 'https://pypi.org/simple', '-r', str(root / 'tools/requirements-editor.txt')], capture_output=True, text=True)
    if result.returncode:
        detail = (result.stdout + result.stderr)[-6000:]
        if any(term in detail.lower() for term in ('connection', 'network', 'proxyerror', 'timed out', 'certificate_verify', 'name resolution', 'sslerror')):
            raise RuntimeIssue(16, 'NETWORK', 'Pillow download failed. Check internet/proxy/certificate settings, then reopen the startup file. Existing Python environments were not changed. ' + detail[-1000:])
        if 'Permission denied' in detail or 'Access is denied' in detail:
            raise RuntimeIssue(14, 'WRITE_PERMISSION', 'The new environment is not writable. Move the catalog to your writable folder.')
        raise RuntimeIssue(17, 'DEPENDENCY_INSTALL', 'Pillow installation failed for a reason other than a detected network failure. Select a Python with Pillow 10–12 and WebP. ' + detail[-1000:])
    if not check_python(executable, dependencies=True):
        raise RuntimeIssue(15, 'PILLOW_WEBP', 'Pillow 10–12 with WebP support is unavailable in the new environment. Choose a compatible Python with WebP support. Existing environments were not changed.')
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
    root = app_root(args.root)
    if not (root / 'review/server.py').is_file() or not (root / 'VERSION').is_file():
        raise RuntimeError('Run the launcher from the fully extracted catalog folder.')
    writable(root / 'outputs')
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
                saved = read_json(root / 'outputs/review_service.json')
                print('Startup diagnostic: ' + json.dumps({'service':saved,'root':str(root),'child_running':child.poll() is None},ensure_ascii=True),file=sys.stderr)
                for name in ('review_server.log','review_server.err.log'):
                    print(name + ': ' + (outputs/name).read_text(encoding='utf-8',errors='replace')[-3000:],file=sys.stderr)
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=10)
                raise RuntimeError('Startup timed out. See outputs/review_server.err.log.')
        route = '/editor' if args.editor else args.route
        origin_info=read_json(root/'outputs/review_service.json')
        if origin_info.get('origin_changed'):
            previous_port=urllib.parse.urlsplit(origin_info['previous_url']).port
            print('Catalog URL changed from '+str(origin_info.get('previous_url'))+' to '+url+'. Browser drafts/settings remain at the previous URL; do not clear its browser data. Close this catalog, free the previous port, then reopen with --port '+str(previous_port)+' to restore that origin.',file=sys.stderr,flush=True)
        target = url + route
        if not args.no_open:
            if not webbrowser.open(target):
                print('Open this address in your browser: ' + target, file=sys.stderr)
        return {'url':target, 'root':str(root), 'pid':info['pid'], 'reused':reused, 'version':info.get('catalog_version'), 'origin_changed':bool(origin_info.get('origin_changed')), 'previous_url':origin_info.get('previous_url')}


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
        if isinstance(error, PermissionError):
            error = RuntimeIssue(14, 'WRITE_PERMISSION', 'Cannot write catalog runtime files. Extract to a writable folder; existing data is preserved.')
        print('Krea2 Catalog: ' + str(error),file=sys.stderr,flush=True)
        return getattr(error, 'code', 1)


if __name__ == '__main__':
    raise SystemExit(main())
