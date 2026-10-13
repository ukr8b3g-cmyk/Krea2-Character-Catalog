"""Build one clean cross-platform ZIP from verified v0.9 data and current source."""
from pathlib import Path, PurePosixPath
import argparse
import csv
import hashlib
import io
import json
import shutil
import stat
import urllib.request
import zipfile

BASE_NAME = 'Krea2-Character-Catalog-v0.9.zip'
BASE_SHA = 'ebd54d7e18894c2bbbfba7561bc5f41fbed02e5334c248bc4448ddf07db00f56'
REJECTED_NAME = 'Krea2-Character-Catalog-Rejected-Workflows-v0.9.zip'
REJECTED_SHA = 'a263144c012fe38de2181b0daf1283d8b93cff8a0aaf978d6b04aa93fabd27ce'
PREFIX = 'Krea2-Character-Catalog/'
DOWNLOAD = 'https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/download/v0.9/'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib,'file_digest') else hashlib.sha256(stream.read()).hexdigest()


def verified_download(name, expected, cache):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / name
    if not path.exists():
        with urllib.request.urlopen(DOWNLOAD + name, timeout=120) as incoming, path.open('wb') as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    if digest(path) != expected:
        raise ValueError('Base release checksum does not match: ' + name)
    return path


def safe_extract(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as source:
        for item in source.infolist():
            relative = PurePosixPath(item.filename)
            if relative.is_absolute() or '..' in relative.parts or not item.filename.startswith(PREFIX) or '\\' in item.filename:
                raise ValueError('Invalid archive path: ' + item.filename)
            target = (destination / Path(*relative.parts)).resolve()
            if not target.is_relative_to(destination):
                raise ValueError('Archive entry escapes its destination.')
            if item.is_dir():
                target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(source.read(item))
                mode = item.external_attr >> 16
                if mode:
                    target.chmod(stat.S_IMODE(mode))


def include_source(path):
    if any(p in ('.git','__pycache__','tests','dist','outputs','original_tags') or p.startswith('.venv') for p in path.parts):
        return False
    if path.name == 'SHA256SUMS.txt' or path.suffix in ('.pyc','.zip','.log'):
        return False
    return path.parts[0] in ('.github','comfyui','docs','lists','review','skills','tools') or len(path.parts) == 1


def build(source, destination, base, rejected):
    source = source.resolve()
    destination = destination.resolve()
    if destination == source or destination.is_relative_to(source) and destination.name != 'dist':
        raise ValueError('Use a separate output folder or the ignored dist folder.')
    if digest(base) != BASE_SHA or digest(rejected) != REJECTED_SHA:
        raise ValueError('The saved v0.9 data has changed.')
    version = (source/'VERSION').read_text(encoding='utf-8-sig').strip()
    if version != '0.91':
        raise ValueError('This build recipe requires version 0.91.')
    entries = {}
    with zipfile.ZipFile(base) as previous:
        if previous.testzip() is not None:
            raise ValueError('The base ZIP is damaged.')
        for item in previous.infolist():
            if item.is_dir():
                continue
            if not item.filename.startswith(PREFIX):
                raise ValueError('Unexpected base folder.')
            entries[item.filename[len(PREFIX):]] = previous.read(item)
    initial_state = json.loads(entries.pop('outputs/review_state.json', b'{}').decode('utf-8-sig'))
    assert not any(initial_state.get(key) for key in ('hidden','favorites','similarity','undo')), 'Do not distribute personal state.'
    for path in source.rglob('*'):
        relative = path.relative_to(source)
        if path.is_file() and include_source(relative):
            entries[relative.as_posix()] = path.read_bytes()
    forbidden = ('__pycache__','.venv','review_service.json','python_runtime.json','review_state.json','user_catalog.json','user_catalog_edits.json')
    for name in entries:
        if any(part in forbidden or part.startswith('.venv') for part in PurePosixPath(name).parts) or name.endswith(('.log','.lock','.pyc')):
            raise ValueError('Private runtime file in archive: ' + name)
        if name.endswith(('.command','.sh')):
            entries[name] = entries[name].replace(b'\r\n',b'\n')
        if name.endswith('.cmd'):
            entries[name] = entries[name].replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    images = [name for name in entries if name.lower().endswith(('.webp','.png','.jpg','.jpeg'))]
    assert len(images) == 3919, len(images)
    for name,count in [('character-pass',3809),('character-fail',13122),('style-pass',110),('style-fail',375)]:
        assert len(list(csv.DictReader(io.StringIO(entries['lists/'+name+'.csv'].decode('utf-8-sig'))))) == count
    destination.mkdir(parents=True,exist_ok=True)
    archive = destination / ('Krea2-Character-Catalog-v'+version+'.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as output:
        for name,data in sorted(entries.items()):
            entry = zipfile.ZipInfo(PREFIX+name,date_time=(2026,10,13,0,0,0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | (0o755 if name.endswith(('.command','.sh')) else 0o644)) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(entry,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        with zipfile.ZipFile(base) as old:
            assert all(check.read(PREFIX+name) == old.read(PREFIX+name) for name in images)
    rejected_output = destination / ('Krea2-Character-Catalog-Rejected-Workflows-v'+version+'.zip')
    shutil.copyfile(rejected,rejected_output)
    sums = ''.join(digest(p)+'  '+p.name+'\n' for p in (archive,rejected_output))
    (destination/'SHA256SUMS.txt').write_text(sums,encoding='ascii',newline='\n')
    report = {'version':version,'files':len(entries),'images':len(images),'all_images_unchanged':True,'catalog_sha256':digest(archive),'catalog_bytes':archive.stat().st_size,'rejected_sha256':digest(rejected_output)}
    (destination/'build-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--dest',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    args = parser.parse_args()
    build(args.source,args.dest,verified_download(BASE_NAME,BASE_SHA,args.cache),verified_download(REJECTED_NAME,REJECTED_SHA,args.cache))
