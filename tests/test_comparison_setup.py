from pathlib import Path
import importlib.util,json,sys,tempfile,threading,unittest,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from comparison_setup import make_server,list_folders

class SetupTests(unittest.TestCase):
 def test_folder_navigation_and_cancel_does_not_save_and_api_requires_token(self):
  with tempfile.TemporaryDirectory(prefix='GUI 日本語 ') as temp:
   root=Path(temp);(root/'One folder').mkdir();(root/'Reference.PNG').write_bytes(b'test')
   listing=list_folders(str(root));self.assertEqual([r['name'] for r in listing['entries']],['One folder'])
   self.assertEqual(list_folders(str(root/'new review folder'))['path'],str(root.resolve()))
   self.assertEqual(len(list_folders(str(root),True)['entries']),2)
   home=root/'comparison';server=make_server(home,ROOT);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   url=server.setup.url
   def get(route):
    with urllib.request.urlopen(url+route) as r:return json.load(r)
   def post(route,value,token):
    request=urllib.request.Request(url+route,data=json.dumps(value).encode(),headers={'Content-Type':'application/json','X-Setup-Token':token,'Origin':url.rstrip('/')})
    with urllib.request.urlopen(request) as r:return json.load(r)
   try:
    token=get('api/bootstrap')['token']
    with self.assertRaises(urllib.error.HTTPError) as denied:post('api/folders',{'field':'catalog_root','initial':str(root)},'bad')
    self.assertEqual(denied.exception.code,403)
    self.assertEqual(post('api/folders',{'field':'catalog_root','initial':str(root)},token)['path'],str(root.resolve()))
    self.assertFalse(server.setup.settings.exists())
    with self.assertRaises(urllib.error.HTTPError):post('api/create',{},token)
    self.assertFalse(server.setup.settings.exists())
   finally:server.shutdown();thread.join(5);server.server_close()

if __name__=='__main__':unittest.main()
