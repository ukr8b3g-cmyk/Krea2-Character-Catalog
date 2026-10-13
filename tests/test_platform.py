from pathlib import Path
import importlib.util
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'review'))
import runtime_support as platform


class PlatformTests(unittest.TestCase):
    def test_desktop_folder_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'image with spaces.png';path.touch()
            with patch.object(platform.sys,'platform','win32'), patch.object(platform.shutil,'which',return_value='explorer.exe'):
                self.assertEqual(platform.folder_command(path),['explorer.exe','/select,',str(path.resolve())])
            with patch.object(platform.sys,'platform','darwin'), patch.object(platform.shutil,'which',return_value='/usr/bin/open'):
                self.assertEqual(platform.folder_command(path),['/usr/bin/open','-R',str(path.resolve())])
            with patch.object(platform.sys,'platform','linux'), patch.object(platform.shutil,'which',return_value='/usr/bin/xdg-open'), patch.dict(os.environ,{'DISPLAY':':0'}):
                self.assertEqual(platform.folder_command(path),['/usr/bin/xdg-open',str(path.parent.resolve())])
            with patch.object(platform.sys,'platform','linux'), patch.dict(os.environ,{},clear=True):
                self.assertIsNone(platform.folder_command(path))

    def test_lock_refuses_second_owner_and_releases(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'service.lock'
            with platform.CatalogLock(path,timeout=0):
                with self.assertRaises(TimeoutError):
                    with platform.CatalogLock(path,timeout=0):
                        pass
            with platform.CatalogLock(path,timeout=0):
                pass

    def test_no_command_is_run_without_desktop_support(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'image.png';path.touch()
            with patch.object(platform,'folder_command',return_value=None),patch.object(platform.subprocess,'Popen') as opened:
                with self.assertRaises(ValueError):platform.reveal_image(path)
                opened.assert_not_called()

    def test_loopback_service_identity(self):
        sys.path.insert(0,str(ROOT/'tools'))
        import launch_catalog
        for url in ['http://127.0.0.1:8790/','http://127.0.0.1:8790']:
            self.assertTrue(launch_catalog.valid_url(url))
        for url in ['http://example.com:8790/','http://127.0.0.1:8790/editor','http://user:pass@127.0.0.1:8790/','file:///private']:
            self.assertFalse(launch_catalog.valid_url(url))
        self.assertFalse(launch_catalog.same_catalog({'app':'AnotherApp','root':str(ROOT)},ROOT))


if __name__=='__main__':unittest.main()
