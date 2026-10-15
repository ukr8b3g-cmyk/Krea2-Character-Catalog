"""Resolve the public catalog folder without exposing its internal layout."""
from pathlib import Path
import os
import sys

START_FILES={
    'win32':'START_HERE - Windows.cmd',
    'darwin':'START_HERE - macOS.command',
    'linux':'START_HERE - Linux.sh',
}


def app_root(folder):
    folder=Path(folder).resolve()
    for candidate in (folder,folder/'app'):
        if (candidate/'review/server.py').is_file():return candidate
    raise ValueError('Choose the extracted Krea2-Character-Catalog folder.')


def catalog_home(folder):
    root=app_root(folder)
    if root.name=='app' and any((root.parent/name).is_file() for name in START_FILES.values()):return root.parent
    return root


def startup_command(folder,editor=False):
    home=catalog_home(folder)
    name=START_FILES.get(sys.platform,START_FILES['linux'])
    if not (home/name).is_file():
        name='open_review.cmd' if os.name=='nt' else 'open_review.command' if sys.platform=='darwin' else 'open_review.sh'
    result=[str(home/name)] if os.name=='nt' else ['/bin/sh',str(home/name)]
    return result+(['--editor'] if editor else [])
