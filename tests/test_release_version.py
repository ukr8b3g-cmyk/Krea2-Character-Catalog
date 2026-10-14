from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from package_release import checked_version


class VersionTests(unittest.TestCase):
    def test_repository_version_is_consistent(self):
        self.assertEqual(checked_version(ROOT), (ROOT/'VERSION').read_text().strip())

    def test_windows_and_unix_line_endings_produce_clean_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'VERSION.json').write_text(json.dumps({'version':'0.9.4','tag':'v0.9.4'}),encoding='utf-8')
            for ending in [b'\n', b'\r\n']:
                (root/'VERSION').write_bytes(b'0.9.4'+ending)
                self.assertEqual(checked_version(root), '0.9.4')

    def test_version_and_tag_mismatch_block_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'VERSION').write_text('0.9.1\n',encoding='utf-8')
            for data in [{'version':'0.91','tag':'v0.91'}, {'version':'0.9.1','tag':'v0.91'}]:
                (root/'VERSION.json').write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'disagree'): checked_version(root)

    def test_non_semantic_versions_block_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for version in ['0.91', '00.9.2', '../0.9.2', '0.9.2;bad']:
                (root/'VERSION').write_text(version,encoding='utf-8')
                (root/'VERSION.json').write_text(json.dumps({'version':version,'tag':'v'+version}),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'semantic'): checked_version(root)


if __name__ == '__main__': unittest.main()
