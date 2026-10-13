"""Reusable WebP thumbnail batch tool. Originals are always read-only."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading

from PIL import Image, ImageOps, features

EXTENSIONS = {'.webp', '.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
INDEX_NAME = '.webp-thumbnail-index.json'
VERSION = 1


def validate_options(source, output, width, quality, workers):
    source, output = Path(source).expanduser().resolve(), Path(output).expanduser().resolve()
    if not source.is_dir():
        raise ValueError('入力フォルダが見つかりません。')
    if source == output or source.is_relative_to(output):
        raise ValueError('出力先は入力フォルダと別にしてください。入力の親フォルダも使えません。')
    if output.exists() and not output.is_dir():
        raise ValueError('出力先に同名のファイルがあります。')
    if not 1 <= width <= 8192:
        raise ValueError('保存幅は1〜8192pxで指定してください。')
    if not 1 <= quality <= 100:
        raise ValueError('品質は1〜100で指定してください。')
    if not 1 <= workers <= 16:
        raise ValueError('同時処理は1〜16枚で指定してください。')
    if not features.check('webp'):
        raise ValueError('このPython環境はWebP保存に対応していません。')
    return source, output


def collect_images(source, output, recursive):
    images = []
    for directory, dirs, files in os.walk(source, followlinks=False):
        parent = Path(directory)
        # Never read generated thumbnails, directory links, or junctions recursively.
        dirs[:] = sorted(d for d in dirs if not (parent / d).is_symlink()
                         and not (parent / d).is_junction()
                         and not (parent / d).resolve().is_relative_to(output)) if recursive else []
        for name in sorted(files):
            path = parent / name
            if path.suffix.lower() in EXTENSIONS and not path.is_symlink():
                images.append(path)
    return images


def load_index(output, source):
    path = output / INDEX_NAME
    if not path.exists():
        return {'version': VERSION, 'input_root': str(source), 'records': {}}
    try:
        index = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise ValueError(f'処理記録を読めません。別の出力フォルダを選んでください: {path}') from error
    if (not isinstance(index, dict) or index.get('version') != VERSION
            or index.get('input_root') != str(source) or not isinstance(index.get('records'), dict)):
        raise ValueError('この出力先は別の入力フォルダまたは別の形式の処理記録を使っています。')
    return index


def file_signature(path):
    stat = path.stat()
    return [stat.st_mtime_ns, stat.st_size]


def output_path(output, relative):
    # Keep the original extension in the name so a.png and a.webp cannot collide.
    return output / relative.parent / (relative.name + '.thumb.webp')


def is_current(record, source_signature, target, settings):
    return (isinstance(record, dict) and record.get('source') == source_signature
            and record.get('settings') == settings and target.is_file()
            and record.get('output') == file_signature(target))


@contextmanager
def output_lock(output):
    output.mkdir(parents=True, exist_ok=True)
    with (output / '.webp-thumbnail.lock').open('a+b') as lock:
        lock.seek(0, 2)
        if lock.tell() == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('同じ出力先で別の処理が動いています。終了後に実行してください。') from error
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == 'nt':
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def save_json_atomic(path, value):
    descriptor, temporary = tempfile.mkstemp(prefix='.index-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def process_one(path, source, output, settings, cached, force, dry_run):
    relative = path.relative_to(source)
    key = relative.as_posix()
    target = output_path(output, relative)
    temporary = None
    try:
        if not target.parent.resolve().is_relative_to(output):
            raise ValueError('出力フォルダ外を指すリンクがあるため保存しません。')
        before = file_signature(path)
        record = cached.get(key)
        if not force and is_current(record, before, target, settings):
            return {'file': key, 'status': 'skipped'}
        if target.exists() and not isinstance(record, dict):
            raise ValueError('同名の未管理ファイルがあるため上書きしません。')
        if dry_run:
            return {'file': key, 'status': 'planned'}
        with Image.open(path) as original:
            if getattr(original, 'n_frames', 1) != 1:
                raise ValueError('複数フレームの画像は対象外です。')
            original.load()
            image = ImageOps.exif_transpose(original)
            alpha = image.mode in {'RGBA', 'LA'} or 'transparency' in image.info
            profile = image.info.get('icc_profile') if image.mode in {'RGB', 'RGBA'} else None
            thumbnail = image.convert('RGBA' if alpha else 'RGB')
            if thumbnail.width > settings['width']:
                height = max(1, round(thumbnail.height * settings['width'] / thumbnail.width))
                thumbnail = thumbnail.resize((settings['width'], height), Image.Resampling.LANCZOS)
            thumbnail.info.clear()
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary = tempfile.mkstemp(prefix='.thumbnail-', suffix='.tmp', dir=target.parent)
            os.close(descriptor)
            thumbnail.save(temporary, format='WEBP', quality=settings['quality'], method=2,
                           exif=b'', xmp=b'', icc_profile=profile or b'')
            size = list(thumbnail.size)
        if file_signature(path) != before:
            raise ValueError('処理中に元画像が更新されました。次回もう一度実行してください。')
        os.replace(temporary, target)
        temporary = None
        return {'file': key, 'status': 'converted', 'size': size,
                'source_bytes': before[1], 'thumbnail_bytes': target.stat().st_size,
                '_record': {'source': before, 'settings': settings, 'output': file_signature(target), 'size': size}}
    except Exception as error:
        return {'file': key, 'status': 'error', 'message': str(error)}
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def run_batch(source, output, width=240, quality=80, workers=2, recursive=True,
              force=False, dry_run=False, on_progress=None):
    source, output = validate_options(source, output, width, quality, workers)
    settings = {'width': width, 'quality': quality, 'method': 2, 'version': VERSION}

    def execute():
        index = load_index(output, source)
        images = collect_images(source, output, recursive)
        report = {'input': str(source), 'output': str(output), 'width': width, 'quality': quality,
                  'dry_run': dry_run, 'total': len(images), 'converted': 0, 'skipped': 0,
                  'planned': 0, 'errors': [], 'source_bytes': 0, 'thumbnail_bytes': 0}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = pool.map(lambda path: process_one(path, source, output, settings,
                                                       index['records'], force, dry_run), images)
            for completed, result in enumerate(results, 1):
                status = result['status']
                if status == 'error':
                    report['errors'].append(result)
                else:
                    report[status] += 1
                if status == 'converted':
                    index['records'][result['file']] = result.pop('_record')
                    report['source_bytes'] += result['source_bytes']
                    report['thumbnail_bytes'] += result['thumbnail_bytes']
                    # Retain completed work if a later image fails or the process is interrupted.
                    save_json_atomic(output / INDEX_NAME, index)
                if on_progress:
                    on_progress(completed, len(images), result)
        return report

    if dry_run:
        return execute()
    with output_lock(output):
        return execute()


class ThumbnailApp:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
        self.root, self.messages = root, queue.Queue()
        self.dialogs, self.alerts = filedialog, messagebox
        root.title('WebP Thumbnail Batch')
        root.geometry('650x460')
        root.minsize(560, 420)
        self.source, self.output = tk.StringVar(), tk.StringVar()
        self.width, self.quality, self.workers = tk.IntVar(value=240), tk.IntVar(value=80), tk.IntVar(value=2)
        self.recursive, self.force = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
        self.status = tk.StringVar(value='入力・出力フォルダを選んでから実行してください。')
        body = ttk.Frame(root, padding=18)
        body.pack(fill='both', expand=True)
        body.columnconfigure(1, weight=1)
        ttk.Label(body, text='WebP サムネイル一括作成', font=('Yu Gothic UI', 15, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 8))
        ttk.Label(body, text='元画像を残して、別フォルダに小さなWebPを保存します。').grid(row=1, column=0, columnspan=3, sticky='w', pady=(0, 16))
        for row, label, variable, command in [(2, '入力フォルダ', self.source, self.choose_source), (3, '出力フォルダ', self.output, self.choose_output)]:
            ttk.Label(body, text=label).grid(row=row, column=0, sticky='w', padx=(0, 10))
            ttk.Entry(body, textvariable=variable).grid(row=row, column=1, sticky='ew', pady=6)
            ttk.Button(body, text='選択…', command=command).grid(row=row, column=2, padx=(8, 0))
        options = ttk.Frame(body)
        options.grid(row=4, column=0, columnspan=3, sticky='w', pady=14)
        for col, label, variable, low, high in [(0, '保存幅 px', self.width, 1, 8192), (2, '品質', self.quality, 1, 100), (4, '同時処理', self.workers, 1, 16)]:
            ttk.Label(options, text=label).grid(row=0, column=col, padx=(0, 6))
            ttk.Spinbox(options, from_=low, to=high, textvariable=variable, width=6).grid(row=0, column=col+1, padx=(0, 18))
        ttk.Checkbutton(body, text='サブフォルダも処理する', variable=self.recursive).grid(row=5, column=0, columnspan=3, sticky='w')
        ttk.Checkbutton(body, text='処理済みサムネイルも作り直す', variable=self.force).grid(row=6, column=0, columnspan=3, sticky='w', pady=(4, 12))
        buttons = ttk.Frame(body)
        buttons.grid(row=7, column=0, columnspan=3, sticky='w')
        self.preview = ttk.Button(buttons, text='対象数を確認', command=lambda: self.start(True))
        self.preview.pack(side='left', padx=(0, 10))
        self.run = ttk.Button(buttons, text='一括変換', command=lambda: self.start(False))
        self.run.pack(side='left')
        self.progress = ttk.Progressbar(body, mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=3, sticky='ew', pady=(14, 8))
        ttk.Label(body, textvariable=self.status, wraplength=590).grid(row=9, column=0, columnspan=3, sticky='w')
        self.busy = False
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def choose_source(self):
        selected = self.dialogs.askdirectory(title='入力フォルダを選択')
        if selected:
            self.source.set(selected)
            if not self.output.get():
                self.output.set(str(Path(selected) / 'thumbnails'))

    def choose_output(self):
        selected = self.dialogs.askdirectory(title='出力フォルダを選択', mustexist=False)
        if selected:
            self.output.set(selected)

    def start(self, dry_run):
        if self.busy:
            return
        try:
            if not self.source.get().strip() or not self.output.get().strip():
                raise ValueError('入力・出力フォルダを選んでください。')
            arguments = dict(source=self.source.get(), output=self.output.get(), width=self.width.get(),
                             quality=self.quality.get(), workers=self.workers.get(), recursive=self.recursive.get(),
                             force=self.force.get(), dry_run=dry_run)
            validate_options(arguments['source'], arguments['output'], arguments['width'], arguments['quality'], arguments['workers'])
        except Exception as error:
            self.alerts.showerror('入力を確認してください', str(error), parent=self.root)
            return
        self.busy = True
        self.preview.state(['disabled'])
        self.run.state(['disabled'])
        self.status.set('対象を確認しています…' if dry_run else '変換しています…')
        self.progress.configure(value=0)

        def work():
            try:
                report = run_batch(**arguments, on_progress=lambda done, total, result: self.messages.put(('progress', done, total)))
                self.messages.put(('done', report))
            except Exception as error:
                self.messages.put(('error', str(error)))

        threading.Thread(target=work, daemon=False).start()

    def poll(self):
        try:
            while True:
                event = self.messages.get_nowait()
                if event[0] == 'progress':
                    self.progress.configure(maximum=max(1, event[2]), value=event[1])
                    self.status.set(f'{event[1]} / {event[2]} 枚')
                else:
                    self.busy = False
                    self.preview.state(['!disabled'])
                    self.run.state(['!disabled'])
                    if event[0] == 'error':
                        self.status.set(event[1])
                        self.alerts.showerror('処理できませんでした', event[1], parent=self.root)
                    else:
                        report = event[1]
                        count = len(report['errors'])
                        self.status.set(f"対象 {report['total']}枚 / 作成 {report['converted']}枚 / 処理済み {report['skipped']}枚 / 変換予定 {report['planned']}枚 / エラー {count}枚")
                        if count:
                            details = '\n'.join(f"{item['file']}: {item['message']}" for item in report['errors'][:8])
                            self.alerts.showwarning('一部の画像を処理できませんでした', details, parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        if self.busy:
            self.status.set('処理が終わってから閉じてください。')
        else:
            self.root.destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description='元画像を変更せず、WebPサムネイルを一括作成します。')
    parser.add_argument('--gui', action='store_true', help='フォルダ選択画面を開く')
    parser.add_argument('--input', type=Path, help='入力フォルダ')
    parser.add_argument('--output', type=Path, help='出力フォルダ')
    parser.add_argument('--width', type=int, default=240, help='保存幅 px（初期値240、縦横比を維持）')
    parser.add_argument('--quality', type=int, default=80, help='WebP品質1〜100（初期値80）')
    parser.add_argument('--workers', type=int, default=2, help='同時処理数（初期値2）')
    parser.add_argument('--no-recursive', action='store_true', help='サブフォルダを処理しない')
    parser.add_argument('--force', action='store_true', help='このツールで作成したサムネイルを再作成')
    parser.add_argument('--dry-run', action='store_true', help='対象数のみ確認。出力ファイルを作らない')
    args = parser.parse_args(argv)
    if args.gui or not (sys.argv[1:] if argv is None else argv):
        import tkinter as tk
        root = tk.Tk()
        ThumbnailApp(root)
        root.mainloop()
        return 0
    if args.input is None or args.output is None:
        parser.error('--input と --output の両方を指定してください。')
    try:
        report = run_batch(args.input, args.output, args.width, args.quality, args.workers,
                           not args.no_recursive, args.force, args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report['errors'] else 0
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
