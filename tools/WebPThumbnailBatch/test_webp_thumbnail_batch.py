import hashlib
from pathlib import Path
import tempfile
import unittest

from PIL import Image
import webp_thumbnail_batch as tool


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.source, self.output = self.base / 'input', self.base / 'output'
        self.source.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def image(self, relative, size=(896, 1184), mode='RGB'):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new(mode, size, (80, 120, 160, 100) if mode == 'RGBA' else (80, 120, 160))
        if path.suffix == '.webp':
            exif = Image.Exif()
            exif[270] = 'test-metadata'
            image.save(path, lossless=True, exif=exif)
        else:
            image.save(path)
        return path

    def test_parallel_conversion_keeps_originals_sizes_alpha_and_names(self):
        files = [self.image('sub/a.webp'), self.image('sub/a.png', mode='RGBA'), self.image('small.png', (60, 80))]
        hashes = {str(path): digest(path) for path in files}
        report = tool.run_batch(self.source, self.output, width=240, workers=2)
        self.assertEqual((report['converted'], report['errors']), (3, []))
        for path in files:
            self.assertEqual(digest(path), hashes[str(path)])
        with Image.open(self.output / 'sub/a.webp.thumb.webp') as image:
            self.assertEqual(image.size, (240, 317))
            self.assertNotIn('exif', image.info)
        with Image.open(self.output / 'sub/a.png.thumb.webp') as image:
            self.assertEqual(image.mode, 'RGBA')
            self.assertLess(image.getpixel((0, 0))[3], 255)
        with Image.open(self.output / 'small.png.thumb.webp') as image:
            self.assertEqual(image.size, (60, 80))

    def test_incremental_rerun_updates_only_changed_inputs_and_settings(self):
        self.image('a.png')
        self.image('b.png')
        tool.run_batch(self.source, self.output)
        first = self.output / 'a.png.thumb.webp'
        saved = first.stat().st_mtime_ns
        report = tool.run_batch(self.source, self.output)
        self.assertEqual((report['converted'], report['skipped']), (0, 2))
        self.assertEqual(first.stat().st_mtime_ns, saved)
        self.image('b.png', (900, 1200))
        report = tool.run_batch(self.source, self.output)
        self.assertEqual((report['converted'], report['skipped']), (1, 1))
        report = tool.run_batch(self.source, self.output, width=200)
        self.assertEqual(report['converted'], 2)
        with Image.open(first) as image:
            self.assertEqual(image.size, (200, 264))

    def test_dry_run_creates_nothing_and_nested_output_is_excluded(self):
        self.image('a.png')
        nested_output = self.source / 'thumbnails'
        report = tool.run_batch(self.source, nested_output, dry_run=True)
        self.assertEqual(report['planned'], 1)
        self.assertFalse(nested_output.exists())
        tool.run_batch(self.source, nested_output)
        report = tool.run_batch(self.source, nested_output)
        self.assertEqual((report['total'], report['skipped']), (1, 1))
        output = self.base / 'non_recursive'
        self.image('sub/b.png')
        self.assertEqual(tool.run_batch(self.source, output, recursive=False)['total'], 1)

    def test_invalid_image_continues_and_unmanaged_output_is_preserved(self):
        self.image('a.png')
        (self.source / 'broken.webp').write_bytes(b'incomplete')
        self.output.mkdir()
        occupied = self.output / 'a.png.thumb.webp'
        occupied.write_bytes(b'keep-existing-file')
        report = tool.run_batch(self.source, self.output, force=True)
        self.assertEqual(len(report['errors']), 2)
        self.assertEqual(occupied.read_bytes(), b'keep-existing-file')
        self.image('b.png')
        report = tool.run_batch(self.source, self.output)
        self.assertEqual(report['converted'], 1)
        self.assertTrue((self.output / tool.INDEX_NAME).exists())

    def test_path_guards_index_ownership_and_concurrent_execution(self):
        for invalid in [self.source, self.base]:
            with self.assertRaises(ValueError):
                tool.run_batch(self.source, invalid)
        with tool.output_lock(self.output):
            with self.assertRaises(ValueError):
                tool.run_batch(self.source, self.output)
        other = self.base / 'other_input'
        other.mkdir()
        self.image('a.png')
        tool.run_batch(self.source, self.output)
        with self.assertRaises(ValueError):
            tool.run_batch(other, self.output)
        (self.output / tool.INDEX_NAME).write_text('{bad-json', encoding='utf-8')
        with self.assertRaises(ValueError):
            tool.run_batch(self.source, self.output)

    def test_exif_orientation_and_multi_frame_rejection(self):
        image = Image.new('RGB', (400, 200), 'red')
        exif = Image.Exif()
        exif[274] = 6
        image.save(self.source / 'rotated.jpg', exif=exif)
        image.save(self.source / 'animated.webp', save_all=True, append_images=[Image.new('RGB', (400, 200), 'blue')], duration=100)
        report = tool.run_batch(self.source, self.output, width=100)
        self.assertEqual((report['converted'], len(report['errors'])), (1, 1))
        with Image.open(self.output / 'rotated.jpg.thumb.webp') as result:
            self.assertEqual(result.size, (100, 200))


if __name__ == '__main__':
    unittest.main()
