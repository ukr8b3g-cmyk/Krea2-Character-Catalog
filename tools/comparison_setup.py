"""Local comparison setup screen; shares pairing code with the optional skill."""
from pathlib import Path
import argparse, importlib.util, json, os, secrets, socket, subprocess, sys, tempfile, threading, time, urllib.parse, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import TCPServer
from catalog_layout import app_root, catalog_home

ROOT=Path(__file__).resolve().parent.parent
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def read(path,default=None):
    try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except FileNotFoundError:return default

def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temporary,path)

def list_folders(initial='',file=False):
    path=Path(initial).expanduser() if initial else Path.home()
    path=path.resolve()
    while not path.exists() and path.parent!=path:path=path.parent
    if path.is_file():path=path.parent
    if not path.is_dir():raise ValueError('Folder unavailable. Choose another location. / フォルダーを確認できません。別の場所を選択してください。')
    roots=[{'name':'Home','path':str(Path.home())}]
    if os.name=='nt':
        import ctypes
        mask=ctypes.windll.kernel32.GetLogicalDrives()
        roots += [{'name':chr(65+i)+':','path':chr(65+i)+':/'} for i in range(26) if mask & (1<<i)]
    else:roots.append({'name':'/','path':'/'})
    entries=[]
    with os.scandir(path) as children:
        for child in children:
            try:
                directory=child.is_dir()
                if directory or file and child.is_file():entries.append({'name':child.name,'path':str(Path(child.path).resolve()),'directory':directory})
            except OSError:continue
    entries.sort(key=lambda r:(not r['directory'],r['name'].casefold()))
    return {'path':str(path),'parent':str(path.parent),'roots':roots,'entries':entries}

class Setup:
    def __init__(self,home,catalog):
        self.home=Path(home).resolve();self.catalog=Path(catalog).resolve();self.url='';self.lock=threading.Lock()
        scripts=ROOT/'skills/krea2-animadex-review/scripts';sys.path.insert(0,str(scripts))
        spec=importlib.util.spec_from_file_location('comparison_setup_review',scripts/'review.py');self.review=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.review)
        self.settings=self.home/'app/setup-settings.json'
    def defaults(self):
        return read(self.settings,{}) or {'catalog_root':str(self.catalog),'animadex_root':'','copyright':'','output':str(self.catalog.parent/'Krea2-AnimaDex-Review')}
    def environment(self,data):
        if not isinstance(data,dict):raise ValueError('Invalid settings.')
        config={key:data.get(key,'') for key in ('catalog_root','animadex_root','animadex_db','thumbs_root')}
        if not config['catalog_root']:raise ValueError('Select the Krea2 catalog folder. / カタログを選択してください。')
        if not config['animadex_root']:raise ValueError('Select the AnimaDex folder. / AnimaDexを選択してください。')
        with tempfile.TemporaryDirectory(prefix='Krea2 setup ') as temp:
            path=Path(temp)/'settings.json';atomic(path,config)
            return self.review.environment(path)
    def check(self,data):
        env=self.environment(data)
        payload,_=self.review.collect(env,data.get('copyright',''))
        listing=self.review.api(env['catalog_url'],'/api/list')
        return {'stats':payload['stats'],'works':sorted({r.get('copyright','') for r in listing['entries'] if r.get('kind','character')=='character'}),'database':env['animadex_db'],'thumbnails':env['thumbs_root']}
    def create(self,data):
        with self.lock:
            env=self.environment(data);env['setup_url']=self.url
            output=Path(data.get('output') or str(self.catalog.parent/'Krea2-AnimaDex-Review')).expanduser().resolve()
            # A new workspace preserves all previous browser drafts and verdict exports.
            if output.exists():
                output=output.with_name(output.name+'-'+time.strftime('%Y%m%d-%H%M%S'))
            stats=self.review.prepare(env,output,data.get('copyright',''))
            from comparison_launcher import open_comparison
            opened=open_comparison(output,no_open=True)
            saved={key:data.get(key,'') for key in ('catalog_root','animadex_root','animadex_db','thumbs_root','copyright')}
            saved.update({'output':str(output),'prepared_path':str(output)})
            atomic(self.settings,saved)
            return {**opened,'stats':stats}
    def start_catalog(self,data):
        root=app_root(Path(data.get('catalog_root','')))
        result=subprocess.run([sys.executable,'-B',str(root/'tools/launch_catalog.py'),'--root',str(root),'--no-open','--json'],capture_output=True,text=True,timeout=100)
        if result.returncode:raise ValueError(result.stderr.strip() or 'Could not start catalog.')
        return json.loads(result.stdout.strip().splitlines()[-1])

def make_server(home,catalog,port=0):
    setup=Setup(home,catalog);token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,value,status=200):
            raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
        def host_ok(self):return self.headers.get('Host')=='127.0.0.1:'+str(self.server.server_port)
        def do_GET(self):
            if not self.host_ok():self.send_error(403);return
            route=urllib.parse.urlsplit(self.path).path
            if route=='/api/info':self.send({'app':'Krea2ComparisonSetup','home':str(setup.home),'pid':os.getpid()});return
            if route=='/api/bootstrap':self.send({'token':token,'settings':setup.defaults()});return
            name={'/':'comparison_setup.html','/comparison_setup.js':'comparison_setup.js','/comparison_setup.css':'comparison_setup.css'}.get(route)
            if not name:self.send_error(404);return
            raw=(ROOT/'review'/name).read_bytes();self.send_response(200);self.send_header('Content-Type',('text/html' if name.endswith('.html') else 'text/javascript' if name.endswith('.js') else 'text/css')+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            origin='http://127.0.0.1:'+str(self.server.server_port)
            if not self.host_ok() or self.headers.get('Origin',origin)!=origin or not secrets.compare_digest(self.headers.get('X-Setup-Token',''),token):self.send_error(403);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if self.headers.get('Content-Type','').split(';')[0]!='application/json' or not 0<length<65536:raise ValueError('Invalid request.')
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):raise ValueError('Invalid settings.')
                if self.path=='/api/folders':
                    if data.get('field') not in {'catalog_root','animadex_root','animadex_db','thumbs_root','output'}:raise ValueError('Invalid field.')
                    self.send(list_folders(str(data.get('initial','')),data['field']=='animadex_db'));return
                if self.path=='/api/check':self.send(setup.check(data));return
                if self.path=='/api/create':self.send(setup.create(data));return
                if self.path=='/api/start-catalog':self.send(setup.start_catalog(data));return
                if self.path=='/api/shutdown':
                    self.send({'stopped':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
                self.send_error(404)
            except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
                message=str(error)
                if isinstance(error,PermissionError):message='Cannot write here. Choose a writable folder. / 書き込めるフォルダーを選択してください。'
                self.send({'error':message},400)
    class Server(ThreadingHTTPServer):
        allow_reuse_address=os.name!='nt'
        def server_bind(self):
            if os.name=='nt':self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            TCPServer.server_bind(self);self.server_name='localhost';self.server_port=self.server_address[1]
    server=Server(('127.0.0.1',port),Handler);server.setup=setup;setup.url='http://127.0.0.1:'+str(server.server_port)+'/'
    return server

def open_setup(home,catalog,no_open=False,settings=False):
    home=Path(home).resolve();runtime=home/'app';runtime.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(ROOT/'review'))
    from runtime_support import CatalogLock
    with CatalogLock(runtime/'setup-launcher.lock',timeout=15):
        saved=read(runtime/'setup-service.json',{});info=None
        if saved:
            parsed=urllib.parse.urlsplit(saved.get('url',''))
            if parsed.scheme!='http' or parsed.hostname!='127.0.0.1' or parsed.username or parsed.password:raise ValueError('Invalid saved setup URL.')
            try:
                with HTTP.open(saved['url']+'api/info',timeout=2) as response:info=json.load(response)
            except OSError:pass
            if info and (info.get('app')!='Krea2ComparisonSetup' or Path(info.get('home','')).resolve()!=home):raise ValueError('Another application owns this setup port. Nothing was stopped.')
        if not info:
            options={'stdin':subprocess.DEVNULL,'cwd':str(ROOT),'close_fds':True}
            if os.name=='nt':options['creationflags']=subprocess.CREATE_NO_WINDOW
            else:options['start_new_session']=True
            with (runtime/'setup.log').open('ab') as out,(runtime/'setup.err.log').open('ab') as err:
                child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--serve','--home',str(home),'--catalog-root',str(catalog),'--port',str(saved.get('port',0))],stdout=out,stderr=err,**options)
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                latest=read(runtime/'setup-service.json',{})
                if latest:
                    try:
                        with HTTP.open(latest['url']+'api/info',timeout=1) as response:info=json.load(response)
                        if info.get('app')=='Krea2ComparisonSetup' and Path(info.get('home','')).resolve()==home:saved=latest;break
                    except OSError:pass
                if child.poll() is not None:raise ValueError('Setup could not start. See app/setup.err.log in the comparison folder.')
                time.sleep(.1)
            else:
                child.terminate();child.wait(timeout=10);raise ValueError('Setup startup timed out.')
        target=saved['url']
        configured=read(runtime/'setup-settings.json',{})
        if configured.get('prepared_path') and not settings:
            sys.path.insert(0,str(ROOT/'skills/krea2-animadex-review/scripts'))
            from comparison_launcher import open_comparison
            target=open_comparison(configured['prepared_path'],no_open=True)['url']
        if not no_open:webbrowser.open(target)
        return {'url':target,'setup_url':saved['url'],'pid':info['pid']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--home',type=Path,required=True);parser.add_argument('--catalog-root',type=Path,default=catalog_home(ROOT));parser.add_argument('--serve',action='store_true');parser.add_argument('--settings',action='store_true');parser.add_argument('--port',type=int,default=0);parser.add_argument('--no-open',action='store_true');parser.add_argument('--json',action='store_true');args=parser.parse_args()
    if args.serve:
        with make_server(args.home,args.catalog_root,args.port) as server:
            atomic(args.home/'app/setup-service.json',{'url':server.setup.url,'port':server.server_port,'pid':os.getpid()});server.serve_forever()
    else:print(json.dumps(open_setup(args.home,args.catalog_root,args.no_open,args.settings)),flush=True)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,TimeoutError) as error:print('Comparison setup: '+str(error),file=sys.stderr);raise SystemExit(1)
