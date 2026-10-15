from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from catalog_layout import app_root,catalog_home,startup_command,START_FILES


class LayoutTests(unittest.TestCase):
    def test_posix_startup_does_not_need_shell_on_path(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);(home/START_FILES['linux']).write_text('# fixture')
            with patch('catalog_layout.catalog_home',return_value=home),patch('catalog_layout.os.name','posix'),patch('catalog_layout.sys.platform','linux'):
                self.assertEqual(startup_command(home)[0],'/bin/sh')

    def test_public_folder_and_internal_folder_resolve_to_same_catalog(self):
        with tempfile.TemporaryDirectory(prefix='Catalog 日本語 ') as directory:
            home=Path(directory);internal=home/'app'
            (internal/'review').mkdir(parents=True);(internal/'review/server.py').write_text('# fixture')
            for name in START_FILES.values():(home/name).write_text('# fixture')
            self.assertEqual(app_root(home),internal)
            self.assertEqual(app_root(internal),internal)
            self.assertEqual(catalog_home(internal),home)
            self.assertIn(str(home/START_FILES[sys.platform]),startup_command(internal))
            self.assertEqual(startup_command(home,editor=True)[-1],'--editor')

    def test_wrong_folder_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'extracted'):app_root(directory)


if __name__=='__main__':unittest.main()
