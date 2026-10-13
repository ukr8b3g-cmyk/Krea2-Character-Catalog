from pathlib import Path
import base64
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import uuid
from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'review'))
from catalog_editor import EditorCatalog, inspect_image


def png(api=None, snapshots=None, workflow=None):
    info = PngImagePlugin.PngInfo()
    for key, value in [('prompt', api), ('krea2_catalog_prompts', snapshots), ('workflow', workflow)]:
        if value is not None: info.add_text(key, json.dumps(value))
    stream = io.BytesIO()
    Image.new('RGB', (13, 17), (29, 71, 113)).save(stream, 'PNG', pnginfo=info)
    return stream.getvalue()


def graph(positive='POSITIVE_SENTINEL'):
    # Negative deliberately precedes positive in JSON insertion order.
    return {
        'negative': {'class_type':'CLIPTextEncode', 'inputs':{'text':'NEGATIVE_SENTINEL'}},
        'positive': {'class_type':'CLIPTextEncode', 'inputs':{'text':positive}},
        'sampler': {'class_type':'KSampler', 'inputs':{'positive':['positive',0], 'negative':['negative',0]}},
        'decode': {'class_type':'VAEDecode', 'inputs':{'samples':['sampler',0]}},
        'save': {'class_type':'SaveImage', 'inputs':{'images':['decode',0]}},
    }


class MetadataTests(unittest.TestCase):
    def test_negative_order_does_not_choose_negative(self):
        self.assertEqual(inspect_image(png(graph()))['generation_prompt'], 'POSITIVE_SENTINEL')

    def test_real_node_snapshot_is_read_from_png(self):
        location = ROOT/'comfyui/custom_nodes/ComfyUI-Krea2-Catalog-Tools/nodes.py'
        spec = importlib.util.spec_from_file_location('audit_prompt_node', location)
        nodes = importlib.util.module_from_spec(spec); spec.loader.exec_module(nodes)
        snapshot = {}
        node = nodes.Krea2CatalogPromptFile()
        # Use the actual node's resolved metadata contract, without GPU/ComfyUI.
        result = node.load_record(file_path='', index=0, common_suffix='', output_folder='',
                           manual_prompt='RESOLVED_CATALOG_PROMPT', manual_id='audit',
                           unique_id='catalog', extra_pnginfo=snapshot)
        self.assertEqual(result['result'][0], 'RESOLVED_CATALOG_PROMPT')
        api = graph(['catalog',0])
        api['catalog'] = {'class_type':'Krea2CatalogPromptFile','inputs':{'file_path':'unavailable.csv'}}
        details = inspect_image(png(api, snapshot['krea2_catalog_prompts']))
        self.assertEqual(details['generation_prompt'], 'RESOLVED_CATALOG_PROMPT')

    def test_snapshot_uses_connected_positive_node(self):
        api = graph(['used',0]); api['used'] = {'class_type':'Krea2CatalogPromptFile','inputs':{}}
        stored = {'unused':{'prompt':'UNRELATED'}, 'used':{'prompt':'CONNECTED'}}
        self.assertEqual(inspect_image(png(api,stored))['generation_prompt'], 'CONNECTED')

    def test_unknown_connected_node_and_ambiguous_outputs_stay_blank(self):
        api = graph(['unknown',0]); api['unknown'] = {'class_type':'UnknownNode','inputs':{'text':'GUESS'}}
        self.assertEqual(inspect_image(png(api))['generation_prompt'], '')
        api = graph(); api.update({
            'other':{'class_type':'KSampler','inputs':{'positive':['negative',0]}},
            'other-save':{'class_type':'SaveImage','inputs':{'images':['other',0]}},
        })
        self.assertEqual(inspect_image(png(api))['generation_prompt'], '')

    def test_reusable_and_generation_text_stay_separate(self):
        stored = {'record':{'name':'Example', 'copy_prompt':'REUSABLE', 'generation_prompt':'ACTUAL'}}
        details = inspect_image(png(snapshots=stored))
        self.assertEqual(details['metadata']['copy_prompt'], 'REUSABLE')
        self.assertEqual(details['generation_prompt'], 'ACTUAL')

    def test_bundled_character_and_style_positive_paths(self):
        for path in (ROOT/'comfyui/workflows').glob('*.api.json'):
            with self.subTest(workflow=path.name):
                api = json.loads(path.read_text(encoding='utf-8-sig'))
                snapshots = {}
                for key,node in api.items():
                    if node['class_type'] == 'Krea2CatalogPromptFile':
                        snapshots[key] = {'prompt':'SAVED_'+path.stem}
                    elif node['class_type'] == 'CLIPTextEncode' and isinstance(node['inputs'].get('text'),str):
                        node['inputs']['text'] = 'SAVED_'+path.stem
                self.assertEqual(inspect_image(png(api,snapshots))['generation_prompt'], 'SAVED_'+path.stem)

    def test_removed_auto_explicit_and_legacy_workflows_preserve_image(self):
        raw = png(workflow={'nodes':[{'id':1}]})
        with tempfile.TemporaryDirectory() as directory:
            editor = EditorCatalog(directory)
            for selection, expected in [({},'auto'), ({'workflow':None},'removed'), ({'workflow':{'nodes':[]}},'explicit')]:
                result = editor.add({'operation_id':str(uuid.uuid4()), 'filename':'原画像.PnG',
                                     'image_base64':base64.b64encode(raw).decode(), 'allow_duplicate':True, **selection}, [])
                record = editor.read_items()['items'][-1]
                self.assertTrue(result['saved']); self.assertEqual(record['workflow_mode'], expected)
                self.assertEqual(editor.path(record['files']['image']).read_bytes(),raw)
                self.assertEqual(editor.workflow(record), None if expected=='removed' else selection.get('workflow',{'nodes':[{'id':1}]}))
            legacy = dict(record); legacy.pop('workflow_mode'); legacy['files'] = {'image':record['files']['image']}
            self.assertEqual(editor.workflow(legacy), {'nodes':[{'id':1}]})


if __name__ == '__main__': unittest.main()
