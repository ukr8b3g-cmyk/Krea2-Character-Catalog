"""Build a read-only GitHub Pages catalog. Never publishes or edits source data."""
from pathlib import Path
import argparse,collections,copy,hashlib,html,json,re,shutil,sys

PUBLIC_FIELDS={'id','key','run_id','kind','name','name_jp','name_cn','copyright','copyright_en','copyright_links','subcategory','category','subject_type','copy_prompt','copy_tags','facets','image_sha256','generated','record_revision','editor_revision','user_edited','rendered_at','seconds','source_style_id','artist_tag','artist_name_candidate','artist_rank','artist_count','rank_basis','artist_metadata_revision','anima_trigger','danbooru_url'}

def build(root,destination,download_url='',assets=None):
    root=root.resolve();destination=destination.resolve()
    assets=(assets or root/'review').resolve()
    if not (root/'review/server.py').is_file() or not (root/'outputs').is_dir():raise ValueError('Choose an existing catalog root.')
    if destination==root or destination.is_relative_to(root) or root.is_relative_to(destination):raise ValueError('Use a separate output folder outside the catalog.')
    if destination.exists():raise ValueError('Output folder already exists. Choose a fresh folder.')
    if download_url and not re.match(r'^https://[^\s]+$',download_url):raise ValueError('Download URL must use https.')
    if 'dataset.catalogMode' not in (assets/'review.js').read_text(encoding='utf-8-sig'):raise ValueError('The catalog frontend must support static demo mode.')
    sys.path.insert(0,str(root/'review'))
    from server import ReviewStore
    store=ReviewStore(root);listing=copy.deepcopy(store.list());entries=[];image_sources={}
    for record in listing['entries']:
        if record.get('hidden') or record.get('deleted') or record.get('generated') is False:continue
        source=store.path(record['files']['image']);digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=record['image_sha256']:raise ValueError('Image changed during demo build: '+record['key'])
        suffix=source.suffix.lower()
        if suffix not in {'.webp','.png','.jpg','.jpeg'}:raise ValueError('Unsupported image format.')
        relative='images/'+digest+suffix;image_sources[relative]=source
        item={k:v for k,v in record.items() if k in PUBLIC_FIELDS};item.update({'demo_image':relative,'hidden':False,'deleted':False,'favorite':False,'similarity':0});entries.append(item)
    style_ids={r.get('source_style_id',r['id']) for r in entries if r['kind']=='style'}
    styles=[{k:v for k,v in r.items() if k in PUBLIC_FIELDS} for r in listing.get('style_candidates',[]) if r.get('id') in style_ids or r.get('source_style_id') in style_ids]
    release_version=(root/'VERSION').read_text(encoding='utf-8-sig').strip() if (root/'VERSION').exists() else 'development'
    catalog={'release_version':release_version,'entries':entries,'style_candidates':styles,'runs':[],'undo_count':0,'visibility_mode':'readonly-demo','hidden_export':False,'version':{'instance':'static-demo','catalog':1,'state':0}}
    payload=json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    # Do not expose backend tokens, absolute paths or personal review state in public JSON.
    if re.search(r'[A-Za-z]:[\\/]',payload.decode('utf-8')):raise ValueError('An absolute filesystem path remains in public metadata. Inspect before publication.')
    source_html=(root/'review/index.html').read_text(encoding='utf-8-sig').replace('<html lang="en"','<html lang="en" data-catalog-mode="demo"',1)
    download=('<a href="'+html.escape(download_url,quote=True)+'" target="_blank" rel="noopener">Download the full ZIP</a>') if download_url else '<span>The downloadable application is being prepared.</span>'
    banner='<aside class="demo-banner"><p><strong>Simplified live demo — v'+html.escape(release_version)+' — not the full application</strong></p><p>This site displays static data without the catalog Python backend. Features and saving differ from the local ZIP application. Public data cannot be deleted, registered, or edited.</p><small>Characters and styles are provisional. Generated results may be inaccurate; please review and correct your downloaded copy.</small>'+download+'</aside>'
    source_html=source_html.replace('</header>','</header>'+banner,1)
    destination.mkdir();(destination/'images').mkdir()
    for relative,source in image_sources.items():
        shutil.copyfile(source,destination/relative)
        assert hashlib.sha256((destination/relative).read_bytes()).hexdigest()==hashlib.sha256(source.read_bytes()).hexdigest()
    for name in ['review.js','review.css']:shutil.copyfile(assets/name,destination/name)
    (destination/'index.html').write_text(source_html,encoding='utf-8');(destination/'catalog.json').write_bytes(payload);(destination/'.nojekyll').write_bytes(b'')
    (destination/'README.md').write_text('# Read-only catalog demo\n\nThis folder is a static GitHub Pages site. It has no Python backend or write/delete API. Upload only after reviewing the images and metadata.\n',encoding='utf-8')
    report={'entries':len(entries),'kinds':dict(collections.Counter(e['kind'] for e in entries)),'unique_images':len(image_sources),'catalog_sha256':hashlib.sha256(payload).hexdigest(),'bytes':sum(p.stat().st_size for p in destination.rglob('*') if p.is_file()),'read_only':True,'published':False}
    print(json.dumps(report,ensure_ascii=False));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent);parser.add_argument('--dest',type=Path,required=True);parser.add_argument('--download-url',default='');parser.add_argument('--assets',type=Path);args=parser.parse_args()
    build(args.root,args.dest,args.download_url,args.assets)
