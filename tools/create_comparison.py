"""Set up an independent AnimaDex comparison without installing a Codex skill."""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
from catalog_layout import app_root,catalog_home

ROOT=Path(__file__).resolve().parent.parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog-root',type=Path,default=catalog_home(ROOT))
    parser.add_argument('--animadex-root',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    root=app_root(args.catalog_root)
    if args.animadex_root is None:
        if not sys.stdin.isatty():parser.error('Specify --animadex-root when input is redirected.')
        print('Open the catalog first. This setup reads AnimaDex; it does not change its database.')
        args.animadex_root=Path(input('AnimaDex folder: ').strip().strip('"'))
    default=catalog_home(root).parent/'Krea2-AnimaDex-Comparison'
    if args.output is None:
        if sys.stdin.isatty():
            answer=input('New comparison folder ['+str(default)+']: ').strip().strip('"')
            args.output=Path(answer) if answer else default
        else:args.output=default
    if args.output.exists():raise ValueError('That comparison folder already exists. Open its START_COMPARISON file, or choose a new --output folder. Existing choices were not changed.')
    script=ROOT/'skills/krea2-animadex-review/scripts/review.py'
    spec=importlib.util.spec_from_file_location('manual_comparison',script)
    skill=importlib.util.module_from_spec(spec);spec.loader.exec_module(skill)
    # All setup stays beside the comparison, outside both data sources.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='Krea2 comparison setup ') as directory:
        config=Path(directory)/'config.json'
        config.write_text(json.dumps({'catalog_root':str(catalog_home(root)),'animadex_root':str(args.animadex_root.resolve())}),encoding='utf-8')
        stats=skill.prepare(skill.environment(config),args.output)
    result={'comparison_folder':str(args.output.resolve()),'stats':stats}
    if args.json:print(json.dumps(result),flush=True)
    else:
        print('Comparison ready: '+result['comparison_folder'])
        print('Open START_COMPARISON for your OS in that folder. Next time, use that same file again.')
    return result


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError) as error:
        print('Comparison setup: '+str(error),file=sys.stderr);raise SystemExit(1)
