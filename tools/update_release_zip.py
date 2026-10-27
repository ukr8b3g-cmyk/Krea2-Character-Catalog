"""Update a verified previous release with 7-Zip, preserving all catalog data."""
from pathlib import Path
import argparse
import hashlib
import json
import posixpath
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.request
from urllib.parse import quote, unquote
import zipfile

from package_release import checked_version, digest, include_source, PREFIX

BASE_TAG = 'v0.9.6'
BASE_NAME = 'Krea2-Character-Catalog-v0.9.6.zip'
BASE_SHA = '9e5850b58a6a412034428af8351ab7323b572039676209659fc15c49ff1ff0a4'
REJECTED_NAME = 'Krea2-Character-Catalog-Rejected-Workflows-v0.9.6.zip'
REJECTED_SHA = 'a263144c012fe38de2181b0daf1283d8b93cff8a0aaf978d6b04aa93fabd27ce'
ROOT_FILES = {'README.md', 'README.ja.md', 'LICENSE', 'NOTICE.md',
              'START_HERE - Windows.cmd', 'START_HERE - macOS.command', 'START_HERE - Linux.sh'}


def public_path(name):
    return name if name in ROOT_FILES else 'app/' + name


def download(name, expected, cache):
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / name
    if not destination.exists():
        url = f'https://github.com/ukr8b3g-cmyk/Krea2-Character-Catalog/releases/download/{BASE_TAG}/{name}'
        with urllib.request.urlopen(url, timeout=120) as incoming, destination.open('wb') as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    if digest(destination) != expected:
        raise ValueError('Previous release checksum mismatch: ' + name)
    return destination


def relocated_markdown(data, name, available):
    target = public_path(name)
    def relocate(match):
        link = match.group(1)
        if '://' in link or link.startswith(('#', '/', 'mailto:')):
            return match.group(0)
        path, sep, fragment = link.partition('#')
        original = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(path)))
        if public_path(original) not in available:
            return match.group(0)
        relative = posixpath.relpath(public_path(original), posixpath.dirname(target) or '.')
        return '](' + quote(relative, safe='/._-') + (sep + fragment if sep else '') + ')'
    return re.sub(r'\]\(([^)]+)\)', relocate, data.decode('utf-8-sig')).encode('utf-8')


def build(source, destination, cache, seven_zip=None):
    source, destination = source.resolve(), destination.resolve()
    if destination == source or (destination.is_relative_to(source) and destination.name != 'dist'):
        raise ValueError('Use a separate destination or the ignored dist folder.')
    version = checked_version(source)
    if tuple(map(int, version.split('.'))) <= (0, 9, 6):
        raise ValueError('Preserve the existing release; use a newer version.')
    seven_zip = seven_zip or shutil.which('7z') or shutil.which('7zz')
    if not seven_zip:
        raise RuntimeError('7-Zip is required; ZIP replacement is never performed by another writer.')
    base, rejected = download(BASE_NAME, BASE_SHA, cache), download(REJECTED_NAME, REJECTED_SHA, cache)
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f'Krea2-Character-Catalog-v{version}.zip'
    if archive.exists():
        raise FileExistsError('Refusing to overwrite an existing candidate: ' + str(archive))
    with zipfile.ZipFile(base) as old, tempfile.TemporaryDirectory(prefix='krea2-7zip-overlay-') as temporary:
        old_names = set(old.namelist())
        if len(old_names) != len(old.infolist()) or old.testzip() is not None:
            raise ValueError('Invalid previous archive.')
        candidates = {}
        for path in source.rglob('*'):
            relative = path.relative_to(source)
            if not path.is_file() or not include_source(relative):
                continue
            name = relative.as_posix()
            if name.startswith(('.github/', '.git')) or (name.startswith('open_') and '/' not in name):
                continue
            candidates[public_path(name)] = (name, path.read_bytes())
        available = {name[len(PREFIX):] for name in old_names} | set(candidates)
        stage = Path(temporary)
        changed = {}
        for target, (name, data) in candidates.items():
            if name.endswith('.md'):
                data = relocated_markdown(data, name, available)
            entry = PREFIX + target
            if entry in old_names and old.read(entry) == data:
                continue
            if target.endswith('.cmd') and entry in old_names and old.read(entry).replace(b'\r\n',b'\n') == data.replace(b'\r\n',b'\n'):
                continue  # Keep existing Windows line endings when content is unchanged.
            output = stage / entry
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
            mode = stat.S_IMODE(old.getinfo(entry).external_attr >> 16) if entry in old_names else 0o644
            output.chmod(mode or 0o644)
            changed[entry] = hashlib.sha256(data).hexdigest()
        if not changed:
            raise ValueError('No replacement files.')
        # User data, original tags, manifests, and images may never enter the overlay.
        assert all('/outputs/' not in name and '/original_tags/' not in name for name in changed)
        shutil.copyfile(base, archive)
        list_file = stage / 'replacement-files.txt'
        list_file.write_text('\n'.join(changed) + '\n', encoding='utf-8')
        subprocess.run([str(seven_zip), 'a', '-tzip', '-mx=9', '-scsUTF-8', str(archive), '@' + str(list_file)], cwd=stage, check=True)
        subprocess.run([str(seven_zip), 't', str(archive)], check=True)
        preserved, images = 0, 0
        with zipfile.ZipFile(archive) as new:
            assert len(new.infolist()) == len(set(new.namelist()))
            assert set(new.namelist()) == old_names | set(changed)
            for entry in old_names | set(changed):
                actual = hashlib.sha256(new.read(entry)).hexdigest()
                if entry in changed:
                    assert actual == changed[entry], entry
                else:
                    assert actual == hashlib.sha256(old.read(entry)).hexdigest(), entry
                    preserved += 1
                    if entry.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        images += 1
    rejected_output = destination / f'Krea2-Character-Catalog-Rejected-Workflows-v{version}.zip'
    if rejected_output.exists():
        raise FileExistsError('Refusing to overwrite: ' + str(rejected_output))
    shutil.copyfile(rejected, rejected_output)
    (destination/'SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in (archive,rejected_output)), encoding='ascii')
    report = {'version': version, 'writer': '7-Zip', 'base_sha256': BASE_SHA, 'files_replaced_or_added': changed,
              'preserved_entries': preserved, 'images_unchanged': images, 'catalog_sha256': digest(archive),
              'catalog_bytes': archive.stat().st_size, 'rejected_sha256': digest(rejected_output)}
    (destination/'build-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--dest', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--7zip', dest='seven_zip')
    args = parser.parse_args()
    build(args.source, args.dest, args.cache, args.seven_zip)
