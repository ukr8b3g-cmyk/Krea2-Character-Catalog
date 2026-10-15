"""Disposable GUI fixture: fictitious SQLite and PNG files, never user data."""
from pathlib import Path
import argparse,base64,csv,importlib.util,io,json,shutil,sqlite3,sys,threading,time,urllib.request,uuid
from contextlib import closing
from PIL import Image
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--mock-picker',action='store_true');args=parser.parse_args()
code=args.source.resolve();work=args.workspace.resolve();work.mkdir(parents=True,exist_ok=False)
catalog=work/'Catalog 日本語 with spaces';catalog.mkdir()
for folder in ['review','tools','skills']:shutil.copytree(code/folder,catalog/folder)
shutil.copy2(code/'VERSION',catalog/'VERSION')
sys.path[:0]=[str(catalog/'review'),str(code/'tools')]
from server import make_server as catalog_server
from comparison_setup import make_server as setup_server
server=catalog_server(catalog,0);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
base='http://127.0.0.1:'+str(server.server_port)
(catalog/'outputs/review_service.json').write_text(json.dumps({'url':base}))
anima=work/'AnimaDex テスト';thumbs=anima/'data/characters/thumbs';thumbs.mkdir(parents=True)
stream=io.BytesIO();Image.new('RGB',(31,47),(123,78,44)).save(stream,'PNG');raw=stream.getvalue();(thumbs/'Reference.PnG').write_bytes(raw)
with closing(sqlite3.connect(anima/'data/animadex.db')) as db:
 db.execute('CREATE TABLE characters(character TEXT,name TEXT,trigger TEXT,thumbname TEXT)');db.execute('INSERT INTO characters VALUES(?,?,?,?)',('test hero','Test Hero','test hero, test work','Reference.PnG'))
 db.commit()
(catalog/'original_tags').mkdir()
with (catalog/'original_tags/anima_characters.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=['tag','category','count','insert_mode']);writer.writeheader();writer.writerow({'tag':'test hero, test work','category':4,'count':1,'insert_mode':'phrase'})
spec=importlib.util.spec_from_file_location('fixture_review',code/'skills/krea2-animadex-review/scripts/review.py');skill=importlib.util.module_from_spec(spec);spec.loader.exec_module(skill)
skill.api(base,'/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':'Test Hero.PNG','image_base64':base64.b64encode(raw).decode(),'name':'Test Hero','copyright':'Test Work','copy_tags':'test hero, test work'},server.token)
home=work/'AnimaDex-Comparison';(home/'app').mkdir(parents=True)
def chooser(initial,file):return str(catalog if not initial else anima)
setup=setup_server(home,catalog);thread=threading.Thread(target=setup.serve_forever,daemon=True);thread.start()
info={'url':setup.setup.url,'catalog':str(catalog),'animadex':str(anima),'home':str(home),'mock_picker':args.mock_picker}
(work/'ready.json').write_text(json.dumps(info),encoding='utf-8');print(json.dumps(info),flush=True)
try:
 deadline=time.monotonic()+900
 while not (work/'stop').exists() and time.monotonic()<deadline:time.sleep(.25)
finally:
 settings=setup.setup.defaults()
 if settings.get('prepared_path'):
  root=Path(settings['prepared_path'])/'app';saved=json.loads((root/'review-server.json').read_text());url=saved['url']
  try:
   request=urllib.request.Request(url+'api/shutdown',data=b'{}',headers={'Content-Type':'application/json','X-Comparison-Token':saved['token']})
   with urllib.request.urlopen(request,timeout=5) as r:r.read()
  except OSError:pass
 setup.shutdown();thread.join(5);setup.server_close();server.shutdown();worker.join(5);server.server_close()
