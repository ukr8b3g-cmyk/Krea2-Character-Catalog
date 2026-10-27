"""Portable local-service locking and desktop integration."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
import uuid


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('w', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return {}


def catalog_version(root):
    try:
        return (Path(root) / 'VERSION').read_text(encoding='utf-8-sig').strip()
    except OSError:
        return ''


class CatalogLock:
    """OS releases the lock if its owner exits; never delete a live lock file."""
    def __init__(self, path, timeout=30):
        self.path = Path(path)
        self.timeout = timeout
        self.stream = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open('a+b')
        if self.path.stat().st_size == 0:
            self.stream.write(b'\0')
            self.stream.flush()
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.stream.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    self.stream.close()
                    self.stream = None
                    raise TimeoutError('This catalog is already starting or running. Try again shortly.') from None
                time.sleep(0.1)

    def __exit__(self, *unused):
        if self.stream is not None:
            self.stream.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            finally:
                self.stream.close()
                self.stream = None


def folder_command(path):
    path = Path(path).resolve()
    if sys.platform == 'win32':
        program = shutil.which('explorer.exe')
        return [program, '/select,', str(path)] if program else None
    if sys.platform == 'darwin':
        program = shutil.which('open')
        return [program, '-R', str(path)] if program else None
    if sys.platform.startswith('linux'):
        program = shutil.which('xdg-open')
        desktop = os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
        return [program, str(path.parent)] if program and desktop else None
    return None


def folder_available():
    return folder_command(Path(__file__)) is not None


def reveal_image(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError('Image not found.')
    command = folder_command(path)
    if command is None:
        raise ValueError('Opening folders requires a desktop file manager. You can still open the original image in your browser.')
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {'opened': True}


def catalog_origin(root):
    value=read_json(Path(root)/'outputs/review_origin.json')
    if (not isinstance(value,dict) or value.get('schema_version')!=1
            or type(value.get('port')) is not int or not 1<=value['port']<=65535
            or type(value.get('requested_port')) is not int or not 0<=value['requested_port']<=65535):
        return {}
    return value


def bind_catalog_server(root, requested_port, fallback, factory):
    import errno
    saved=catalog_origin(root)
    ports=[]
    if saved.get('requested_port')==requested_port:ports.append(saved['port'])
    if requested_port not in ports:ports.append(requested_port)
    server=None
    for port in ports:
        try:
            server=factory(root,port)
            break
        except OSError as error:
            occupied=error.errno in (errno.EADDRINUSE,10048) or (os.name=='nt' and getattr(error,'winerror',None)==10013)
            if not fallback or not port or not occupied:raise
    if server is None:server=factory(root,0)
    previous=f"http://127.0.0.1:{saved['port']}/" if saved else None
    current=f'http://127.0.0.1:{server.server_port}/'
    changed=bool(previous and previous!=current)
    try:
        atomic_json(Path(root)/'outputs/review_origin.json',{'schema_version':1,'requested_port':requested_port,
                    'port':server.server_port,'previous_url':previous if changed else saved.get('previous_url')})
    except Exception:
        server.server_close()
        raise
    return server,{'origin_changed':changed,'previous_url':previous if changed else None}
