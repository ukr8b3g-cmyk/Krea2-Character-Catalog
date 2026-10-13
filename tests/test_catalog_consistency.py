from pathlib import Path
import base64
import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'review'));sys.path.insert(0,str(ROOT/'tools'))
from server import ReviewStore,tag_facets
from build_static_demo import build


class ConsistencyTests(unittest.TestCase):
    def test_facets_do_not_depend_on_identity_prefix(self):
        for tags in ['1girl, red_hair, blue_eyes','Example, Work, 1girl, red_hair, blue_eyes']:
            facets=tag_facets({'name':'Example','copyright':'Work','copy_tags':tags})
            self.assertEqual(facets['gender'],['Female']);self.assertEqual(facets['hairColor'],['red hair'])
            self.assertEqual(facets['eyeColor'],['blue eyes'])

    def test_workflow_export_and_failed_write_preserve_previous_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            store=ReviewStore(directory);stream=io.BytesIO();Image.new('RGB',(9,11)).save(stream,'PNG')
            saved=store.editor.add({'operation_id':str(uuid.uuid4()),'filename':'Example.png',
                  'image_base64':base64.b64encode(stream.getvalue()).decode(),'workflow':{'nodes':[]}},[])
            result=store.export();path=Path(result['file']);rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
            self.assertEqual(len(rows),1);self.assertNotIn('workflow',rows[0]);before=path.read_bytes()
            with patch('server.os.replace',side_effect=PermissionError('test replacement denied')):
                with self.assertRaises(PermissionError):store.export()
            self.assertEqual(path.read_bytes(),before);self.assertEqual(list(store.outputs.glob('*.tmp')),[])

    def test_static_demo_retains_edited_style_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'catalog';shutil.copytree(ROOT/'review',root/'review')
            store=ReviewStore(root);stream=io.BytesIO();Image.new('RGB',(7,9)).save(stream,'PNG')
            saved=store.editor.add({'operation_id':str(uuid.uuid4()),'filename':'style.png','kind':'style',
                  'name':'Original','image_base64':base64.b64encode(stream.getvalue()).decode()},[])
            record=next(r for r in store.list()['entries'] if r['key']==saved['key'])
            store.editor.edit({'image_sha256':record['image_sha256'],'fields':{'name':'Corrected','copy_tags':'corrected tags'}},record)
            listing=store.list();edited=listing['entries'][0]
            listing['style_candidates']=[{'id':edited['id'],'name':'Old artist','copy_tags':'old tags','artist_metadata_revision':'1'}]
            with patch.object(ReviewStore,'list',return_value=listing):build(root,Path(directory)/'demo',assets=ROOT/'review')
            output=json.loads((Path(directory)/'demo/catalog.json').read_text(encoding='utf-8'))['entries'][0]
            self.assertTrue(output['user_edited'])
            for field in ['name','copy_tags','copy_prompt','facets']:self.assertEqual(output[field],edited[field])


if __name__=='__main__':unittest.main()
