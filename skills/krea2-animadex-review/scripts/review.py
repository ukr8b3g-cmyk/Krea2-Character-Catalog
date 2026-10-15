"""Portable optional character comparison. Standard-library only; no generation."""
from pathlib import Path
import argparse,collections,csv,datetime,hashlib,json,os,shutil,socket,sqlite3,sys,urllib.parse,urllib.request,secrets,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from socketserver import TCPServer

def review_root(folder):
    folder=Path(folder).resolve()
    return folder/'app' if (folder/'app/pairs.json').is_file() else folder

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def norm(value):return ' '.join(value.casefold().split())
def pair(tags):
    parts=tags.split(',');return tuple(norm(v.strip()) for v in parts[:2]) if len(parts)>=2 and all(v.strip() for v in parts[:2]) else None
def api(url,path,body=None,token=''):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.username or parsed.password:raise ValueError('Only loopback HTTP catalog URLs are supported.')
    headers={'Accept':'application/json'}
    if body is not None:headers.update({'Content-Type':'application/json','X-Review-Token':token})
    request=urllib.request.Request(url.rstrip('/')+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)
def environment(config_path):
    config_path=Path(config_path).resolve();data=read(config_path)
    def location(name,default=None):
        value=data.get(name) or default
        if not value:raise ValueError('Set '+name+' in your private config.')
        path=Path(value).expanduser();return (path if path.is_absolute() else config_path.parent/path).resolve()
    root=location('catalog_root');anima=location('animadex_root')
    if not (root/'review/server.py').is_file() and (root/'app/review/server.py').is_file():root=root/'app'
    if not (root/'review/server.py').is_file() or not anima.is_dir():raise ValueError('Catalog or AnimaDex folder does not exist.')
    url=data.get('catalog_url')
    if not url:
        service=root/'outputs/review_service.json'
        if not service.is_file():raise ValueError('Open this catalog with its normal launcher, or configure its current URL.')
        url=read(service)['url']
    info=api(url,'/api/info')
    if info.get('app')!='Krea2CatalogReview' or Path(info['root']).resolve()!=root:raise ValueError('The URL belongs to a different catalog.')
    if data.get('animadex_db'):db=location('animadex_db')
    else:
        candidates=[p for p in [anima/'animadex-data/animadex.db',anima/'animadex.db',anima/'data/animadex.db'] if p.is_file()]
        if len(candidates)!=1:raise ValueError('Set animadex_db explicitly; no unique database was found.')
        db=candidates[0].resolve()
    thumbs=location('thumbs_root',str(db.parent/'characters/thumbs'));source=location('source_csv',str(root/'original_tags/anima_characters.csv'))
    if not db.is_file() or not thumbs.is_dir() or not source.is_file():raise ValueError('Database, thumbnails or source CSV is missing.')
    return {'catalog_root':str(root),'animadex_root':str(anima),'catalog_url':url.rstrip('/'),'animadex_db':str(db),'thumbs_root':str(thumbs),'source_csv':str(source)}
def database(env):
    conn=sqlite3.connect(Path(env['animadex_db']).as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
    try:
        columns={r[1] for r in conn.execute('PRAGMA table_info(characters)')}
        if not {'character','name','trigger','thumbname'}<=columns:raise ValueError('Unsupported AnimaDex characters schema: inspect and adapt it first.')
        return [dict(r) for r in conn.execute('SELECT character,name,trigger,thumbname FROM characters')]
    finally:conn.close()
def safe_path(root,relative):
    root=Path(root).resolve();path=(root/relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():raise ValueError('Missing or out-of-root image.')
    return path
def collect(env,copyright=''):
    index=collections.defaultdict(list)
    for r in database(env):index[norm(r['trigger'] or '')].append(r)
    with Path(env['source_csv']).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if 'tag' not in (reader.fieldnames or []):raise ValueError('Source CSV requires the actual tag column.')
        identities={pair(r['tag']) for r in reader};identities.discard(None)
    root=Path(env['catalog_root']);judged={}
    for filename in ['human_decisions.json','user_comparison_decisions.json']:
        path=root/'outputs'/filename
        if path.is_file():
            for r in read(path).get('decisions',[]):
                if r.get('decision') in {'match','mismatch'}:judged[(r['key'],r['catalog_image_sha256'])]=r
    listing=api(env['catalog_url'],'/api/list');pairs=[];unresolved=[];stats=collections.Counter({'characters':0,'already_judged':0,'exact_identity':0,'missing_or_ambiguous_identity':0,'missing_image':0});hashes={}
    def cached_sha(path):
        if path not in hashes:hashes[path]=sha(path)
        return hashes[path]
    for item in listing['entries']:
        if item.get('kind','character')!='character' or (copyright and norm(item['copyright'])!=norm(copyright)):continue
        stats['characters']+=1
        if (item['key'],item['image_sha256']) in judged:stats['already_judged']+=1;continue
        identity=pair(item.get('copy_tags',''));matches=index.get(', '.join(identity),[]) if identity in identities else []
        if len(matches)!=1:
            stats['missing_or_ambiguous_identity']+=1
            unresolved.append({'key':item['key'],'name':item['name'],'copyright':item['copyright'],'identity':','.join(item.get('copy_tags','').split(',')[:2]),'reason':'csv_identity_missing' if identity not in identities else 'reference_ambiguous' if matches else 'reference_missing'})
            continue
        source=matches[0];stats['exact_identity']+=1
        try:generated=safe_path(root/'outputs',item['files']['image']);reference=safe_path(env['thumbs_root'],source['thumbname'] or '')
        except ValueError:
            stats['missing_image']+=1
            unresolved.append({'key':item['key'],'name':item['name'],'copyright':item['copyright'],'identity':','.join(item.get('copy_tags','').split(',')[:2]),'reason':'image_missing'})
            continue
        image_sha=cached_sha(generated)
        if image_sha!=item['image_sha256']:raise ValueError('Catalog image changed; refresh before comparison.')
        pairs.append({'key':item['key'],'name':item['name'],'copyright':item['copyright'],'catalog_identity':','.join(item['copy_tags'].split(',')[:2]),'catalog_image':str(generated),'reference_image':str(reference),'catalog_image_sha256':image_sha,'reference_image_sha256':cached_sha(reference),'reference_slug':source['character'],'reference_name':source['name']})
    for name in ['bootstrap.cmd','bootstrap.ps1','bootstrap.sh']:
        if not (root/'tools'/name).is_file():raise ValueError('Use a complete catalog installation; native startup helpers are missing.')
    stats['available_pairs']=len(pairs)
    return {'schema':'krea2-portable-pairs-v1','environment':env,'pairs':pairs,'stats':dict(stats)},unresolved

def prepare(env,output,copyright=''):
    output=Path(output).resolve();catalog=Path(env['catalog_root']);root=catalog
    if catalog.name=='app' and any((catalog.parent/name).is_file() for name in ['START_HERE - Windows.cmd','START_HERE - macOS.command','START_HERE - Linux.sh']):catalog=catalog.parent
    if output.exists() or any(output.is_relative_to(base) or base.is_relative_to(output) for base in [catalog,Path(env['animadex_root'])]):raise ValueError('Use a new review folder outside both catalogs.')
    payload,unresolved=collect(env,copyright);stats=payload['stats']
    home=output;output=home/'app';output.mkdir(parents=True)
    (output/'pairs.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'settings.json').write_text(json.dumps({key:value for key,value in env.items() if key!='catalog_url'},ensure_ascii=False,indent=2),encoding='utf-8')
    with (output/'unresolved.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['key','name','copyright','identity','reason']);writer.writeheader();writer.writerows(unresolved)
    assets=Path(__file__).resolve().parent.parent/'assets'
    for name in ['index.html','compare.js','compare.css']:shutil.copy2(assets/name,output/name)
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from comparison_launcher import setup
    setup(root,home,Path(__file__).resolve())
    return dict(stats)
def validated_decisions(env,review_dir,decisions,selected_keys=None):
    payload=read(review_root(review_dir)/'pairs.json')
    if Path(payload['environment']['catalog_root']).resolve()!=Path(env['catalog_root']).resolve() or Path(payload['environment']['thumbs_root']).resolve()!=Path(env['thumbs_root']).resolve():raise ValueError('Review belongs to a different environment.')
    source=read(decisions)
    if source.get('schema')!='krea2-portable-human-review-v1' or not isinstance(source.get('decisions'),list):raise ValueError('Invalid decision export.')
    listing=api(env['catalog_url'],'/api/list')
    if listing.get('visibility_mode')!='flags':raise ValueError('This catalog does not support flag-based visibility.')
    records={r['key']:r for r in listing['entries']};pairs={r['key']:r for r in payload['pairs']};chosen={}
    for row in source['decisions']:
        if row.get('selected') is not True or row.get('confirmed') is not True or row.get('decision') in {'hold',None}:continue
        if row.get('decision') not in {'match','mismatch'}:raise ValueError('Unknown decision.')
        key=row.get('key')
        if selected_keys is not None and key not in selected_keys:continue
        p=pairs.get(key);record=records.get(key)
        if not p or not record or record['image_sha256']!=row.get('catalog_image_sha256') or row.get('reference_image_sha256')!=p['reference_image_sha256']:raise ValueError('Decision or catalog no longer matches this pair.')
        generated=safe_path(Path(env['catalog_root'])/'outputs',record['files']['image']);reference=safe_path(env['thumbs_root'],str(Path(p['reference_image']).relative_to(Path(env['thumbs_root']))))
        if sha(generated)!=p['catalog_image_sha256'] or sha(reference)!=p['reference_image_sha256']:raise ValueError('An image changed; compare again before applying.')
        if key in chosen and chosen[key]['decision']!=row['decision']:raise ValueError('Conflicting selected decisions.')
        chosen[key]={**row,'reference_slug':p['reference_slug']}
    return list(chosen.values()),listing
def visibility_plan(rows,listing):
    records={r['key']:r for r in listing['entries']}
    plan={'restore':[],'hide':[],'unchanged':[]}
    for row in rows:
        hidden=bool(records[row['key']]['hidden'])
        route='restore' if hidden and row['decision']=='match' else 'hide' if not hidden and row['decision']=='mismatch' else 'unchanged'
        plan[route].append(row['key'])
    return plan

def write_json(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    try:
        temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)

def apply(env,review_dir,decisions,dry_run=False):
    decision_digest=sha(decisions)
    rows,listing=validated_decisions(env,review_dir,decisions)
    if sha(decisions)!=decision_digest:raise ValueError('Decision export changed during validation; retry the dry run.')
    plan=visibility_plan(rows,listing)
    result={'selected_confirmed':len(rows),'match':sum(r['decision']=='match' for r in rows),'mismatch':sum(r['decision']=='mismatch' for r in rows),'dry_run':dry_run,
            'visibility_changes':len(plan['restore'])+len(plan['hide']),'unchanged':len(plan['unchanged']),'plan':plan}
    if dry_run or not rows:return result
    root=Path(env['catalog_root']);review_dir=review_root(review_dir)
    if review_dir.is_relative_to(root):raise ValueError('Keep snapshots outside the catalog.')
    path=root/'outputs/user_comparison_decisions.json';previous=read(path) if path.exists() else {'schema':'krea2-portable-human-review-v1','decisions':[]}
    if previous.get('schema')!='krea2-portable-human-review-v1' or not isinstance(previous.get('decisions'),list) or any(not isinstance(r,dict) or 'key' not in r for r in previous['decisions']):raise ValueError('Existing comparison decisions are invalid; no visibility changes were applied.')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');snapshot=review_dir/'snapshots'/stamp;snapshot.mkdir(parents=True)
    for name in ['review_state.json','user_comparison_decisions.json']:
        source=root/'outputs'/name
        if source.is_file():shutil.copy2(source,snapshot/name)
    checkpoint={'applied':[],'selected':rows,'result':result,'completed':False}
    checkpoint_path=review_dir/'apply-checkpoint.json'
    write_json(checkpoint_path,checkpoint)
    for route in ['restore','hide']:
        keys=plan[route]
        for start in range(0,len(keys),100):
            if sha(decisions)!=decision_digest:raise ValueError('Decision export changed; inspect the checkpoint before retry.')
            batch=keys[start:start+100]
            current_rows,current_listing=validated_decisions(env,review_dir,decisions,set(batch))
            batch=visibility_plan(current_rows,current_listing)[route]
            if batch:
                api(env['catalog_url'],'/api/'+route,{'keys':batch},current_listing['token'])
                checkpoint['applied']+=batch
                write_json(checkpoint_path,checkpoint)
    if sha(decisions)!=decision_digest:raise ValueError('Decision export changed; inspect the checkpoint before retry.')
    verified_rows,verified_listing=validated_decisions(env,review_dir,decisions)
    now={r['key']:r for r in verified_listing['entries']}
    for row in rows:
        if bool(now[row['key']]['hidden'])!=(row['decision']=='mismatch'):raise ValueError('Visibility verification failed. Inspect the checkpoint before retry.')
    merged={(r['key'],r.get('catalog_image_sha256','')):r for r in previous['decisions']}
    for row in verified_rows:
        identity=(row['key'],row['catalog_image_sha256']);old=merged.get(identity,{})
        unchanged=all(old.get(key)==row.get(key) for key in ['decision','reference_slug','reference_image_sha256','selected','confirmed'])
        merged[identity]={**row,'decided_at':old.get('decided_at') if unchanged and old.get('decided_at') else datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write_json(path,{**previous,'decisions':list(merged.values())})
    checkpoint['completed']=True;write_json(checkpoint_path,checkpoint)
    result['verified']=True;result['snapshot']=str(snapshot);return result
def serve(review_dir,port):
    root=review_root(review_dir);payload=read(root/'pairs.json');pairs=payload['pairs'];env=payload['environment']
    service_path=root/'review-server.json'
    if port==0 and service_path.is_file():
        previous=read(service_path);port=previous.get('port')
        if previous.get('schema')!='krea2-portable-review-server-v1' or not isinstance(port,int) or not 1<=port<=65535:raise ValueError('Invalid saved comparison port. Use an explicit --port after checking the file.')
    if not 0<=port<=65535:raise ValueError('Port must be between 0 and 65535.')
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if urllib.parse.urlsplit('http://'+self.headers.get('Host','')).hostname not in {'127.0.0.1','localhost','::1'}:self.send_error(403);return
            url=urllib.parse.urlsplit(self.path)
            try:
                if url.path in {'/api/info','/api/bootstrap'}:
                    value={'app':'Krea2AnimaDexComparison','review_dir':str(root),'pid':os.getpid()}
                    if url.path=='/api/bootstrap':value.update({'token':info['token'],'setup_url':env.get('setup_url','')})
                    content=json.dumps(value).encode();mime='application/json'
                elif url.path=='/pair-image':
                    q=urllib.parse.parse_qs(url.query);index=int(q['id'][0]);side=q['side'][0]
                    if index<0 or index>=len(pairs) or side not in {'catalog','reference'}:raise ValueError('Invalid pair')
                    item=pairs[index];base=Path(env['catalog_root'])/'outputs' if side=='catalog' else Path(env['thumbs_root']);relative=str(Path(item[side+'_image']).relative_to(base));path=safe_path(base,relative)
                    if sha(path)!=item[side+'_image_sha256']:self.send_error(409,'Image changed');return
                    content=path.read_bytes();mime='image/webp' if path.suffix.lower()=='.webp' else 'image/png' if path.suffix.lower()=='.png' else 'image/jpeg'
                elif url.path=='/pairs.json':
                    content=json.dumps({'pairs':[{k:v for k,v in p.items() if k not in {'catalog_image','reference_image'}} for p in pairs],'stats':payload['stats']},ensure_ascii=False).encode();mime='application/json'
                elif url.path=='/ai_candidates.json':
                    path=root/'ai_candidates.json';content=path.read_bytes() if path.exists() else b'[]';mime='application/json'
                else:
                    name={'/':'index.html','/index.html':'index.html','/compare.js':'compare.js','/compare.css':'compare.css','/unresolved.csv':'unresolved.csv'}.get(url.path)
                    if not name:self.send_error(404);return
                    content=(root/name).read_bytes();mime='text/html' if name.endswith('.html') else 'text/javascript' if name.endswith('.js') else 'text/csv' if name.endswith('.csv') else 'text/css'
                self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8' if not mime.startswith('image/') else mime);self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
            except (ValueError,KeyError,OSError):self.send_error(400)
        def do_POST(self):
            origin='http://127.0.0.1:'+str(self.server.server_port)
            if self.headers.get('Host')!='127.0.0.1:'+str(self.server.server_port) or self.headers.get('Origin',origin)!=origin or not secrets.compare_digest(self.headers.get('X-Comparison-Token',''),info['token']):
                self.send_error(403);return
            if self.path!='/api/shutdown' or self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send_error(400);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<1000:raise ValueError('Invalid request')
                if not isinstance(json.loads(self.rfile.read(length)),dict):raise ValueError('Invalid request')
            except (ValueError,TypeError):self.send_error(400);return
            content=b'{"stopped":true}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
            threading.Thread(target=self.server.shutdown,daemon=True).start()
    class ReviewServer(ThreadingHTTPServer):
        allow_reuse_address=os.name!='nt'
        def server_bind(self):
            if os.name=='nt':self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            TCPServer.server_bind(self)
            self.server_name='localhost';self.server_port=self.server_address[1]
    with ReviewServer(('127.0.0.1',port),Handler) as server:
        info={'schema':'krea2-portable-review-server-v1','url':'http://127.0.0.1:'+str(server.server_port)+'/','port':server.server_port,'pid':os.getpid(),'read_only':True,'review_dir':str(root),'token':secrets.token_urlsafe(24)}
        temporary=service_path.with_suffix('.json.tmp');temporary.write_text(json.dumps(info,indent=2),encoding='utf-8');os.replace(temporary,service_path)
        print(json.dumps(info),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
    for name in ['inspect','prepare','apply']:
        cmd=sub.add_parser(name);cmd.add_argument('--config',type=Path,required=True)
        if name=='prepare':cmd.add_argument('--output',type=Path,required=True);cmd.add_argument('--copyright',default='')
        if name=='apply':cmd.add_argument('--review-dir',type=Path,required=True);cmd.add_argument('--decisions',type=Path,required=True);cmd.add_argument('--dry-run',action='store_true')
    cmd=sub.add_parser('serve');cmd.add_argument('--review-dir',type=Path,required=True);cmd.add_argument('--port',type=int,default=0)
    args=parser.parse_args()
    if args.command=='serve':serve(args.review_dir,args.port);return
    env=environment(args.config)
    if args.command=='inspect':result={**env,'anima_characters':len(database(env)),'catalog_characters':sum(r.get('kind','character')=='character' for r in api(env['catalog_url'],'/api/list')['entries'])}
    elif args.command=='prepare':result=prepare(env,args.output,args.copyright)
    else:result=apply(env,args.review_dir,args.decisions,args.dry_run)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,sqlite3.Error) as error:print(str(error),file=sys.stderr);sys.exit(1)
