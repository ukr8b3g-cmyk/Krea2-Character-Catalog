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
        self.assertEqual(checked_version(ROOT), '0.9.1')

    def test_version_and_tag_mismatch_block_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'VERSION').write_text('0.9.1\n',encoding='utf-8')
            for data in [{'version':'0.91','tag':'v0.91'}, {'version':'0.9.1','tag':'v0.91'}]:
                (root/'VERSION.json').write_text(json.dumps(data),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'disagree'): checked_version(root)


if __name__ == '__main__': unittest.main()
