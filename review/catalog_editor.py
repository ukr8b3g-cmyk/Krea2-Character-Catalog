"""User additions and guarded edits, layered over the generated catalog."""
import base64
import copy
import csv
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import unicodedata
import uuid
from PIL import Image
from runtime_support import reveal_image

MAX_IMAGE = 64 * 1024 * 1024
FIELDS = ('name', 'copyright', 'copy_prompt', 'copy_tags', 'kind')
FORMATS = {'WEBP': ('webp', 'image/webp'), 'PNG': ('png', 'image/png'), 'JPEG': ('jpg', 'image/jpeg')}

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_json(path, default):
    if not path.exists():
        return copy.deepcopy(default)
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise ValueError('ユーザー登録情報を読み込めません。元のファイルは変更していません。')
    return value

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

def decode_bytes(encoded, limit=MAX_IMAGE):
    if not isinstance(encoded, str) or len(encoded) > (limit + 2) * 4 // 3 + 8:
        raise ValueError('ファイルが大きすぎます。画像は64MB以下を選んでください。')
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise ValueError('ファイルを読み込めませんでした。選び直してください。') from None
    if not data or len(data) > limit:
        raise ValueError('ファイルが空か、許容サイズを超えています。')
    return data

def parsed(value, prefix=None):
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    if isinstance(value, str):
        try: value = value.encode('latin1').decode('utf-8')
        except UnicodeError: pass
        if prefix and value.startswith(prefix):
            value = value[len(prefix):]
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return None
    if not isinstance(value, (dict, list)): return None
    try: json.dumps(value, allow_nan=False)
    except (ValueError, TypeError): return None
    return value

def inspect_image(data):
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in FORMATS:
                raise ValueError('WebP・PNG・JPEGの画像を選んでください。')
            image.load()
            extension, mime = FORMATS[image.format]
            exif, info = image.getexif(), image.info
            stored = parsed(exif.get(315), 'krea2_catalog_prompts:') or {}
            record = stored.get('record', stored) if isinstance(stored, dict) else {}
            if not isinstance(record, dict): record = {}
            workflow = parsed(info.get('workflow')) or parsed(exif.get(305), 'workflow:')
            actual = exif.get(270, '')
            if not isinstance(actual, str): actual = ''
            actual = actual.split('\nSteps:', 1)[0]
            try: actual = actual.encode('latin1').decode('utf-8')
            except (UnicodeError, AttributeError): pass
            api = parsed(info.get('prompt')) or parsed(exif.get(271), 'prompt:')
            if not actual and isinstance(api, dict):
                for node in api.values():
                    text = node.get('inputs', {}).get('text') if isinstance(node, dict) else None
                    if isinstance(text, str): actual = text; break
            metadata = {key:record[key] for key in ('name','copyright','copy_prompt','copy_tags') if isinstance(record.get(key), str)}
            if 'copy_prompt' not in metadata and actual: metadata['copy_prompt'] = actual
            return {'extension':extension,'mime':mime,'width':image.width,'height':image.height,'generation_prompt':actual,
                    'image_sha256':hashlib.sha256(data).hexdigest(),'metadata':metadata,'workflow':workflow}
    except (OSError, Image.DecompressionBombError) as error:
        raise ValueError('画像を読み込めませんでした。壊れていないWebP・PNG・JPEGを選んでください。') from error

def text_fields(payload, filename='image'):
    result = {}
    for field in FIELDS:
        value = payload.get(field, 'character' if field == 'kind' else '')
        if not isinstance(value, str) or len(value) > 100000:
            raise ValueError('入力が長すぎるか、文字列ではありません。')
        result[field] = value
    result['name'] = result['name'].strip() or Path(filename.replace('\\','/').rsplit('/',1)[-1]).stem or 'image'
    result['copyright'] = result['copyright'].strip() or 'Unclassified'
    if result['kind'] not in ('character','style'):
        raise ValueError('キャラクターまたはスタイルを選んでください。')
    return result

class EditorCatalog:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.outputs = self.root/'outputs'
        self.catalog_file = self.outputs/'user_catalog.json'
        self.edits_file = self.outputs/'user_catalog_edits.json'
        self.lock = threading.RLock()
        self.csv_cache = {}

    def path(self, relative):
        path = (self.outputs/relative).resolve()
        if not path.is_relative_to(self.outputs):
            raise ValueError('保存先がカタログの外になっています。')
        return path

    def snapshot(self):
        with self.lock:
            def stamp(path):
                s = path.stat() if path.exists() else None
                return (s.st_mtime_ns, s.st_size) if s else None
            return (stamp(self.catalog_file), stamp(self.edits_file)), self.read_items(), self.read_edits()

    def read_items(self):
        value = load_json(self.catalog_file, {'schema_version':1,'items':[]})
        if not isinstance(value.get('items'), list): raise ValueError('追加情報の形式が違います。')
        return value

    def read_edits(self):
        value = load_json(self.edits_file, {'schema_version':1,'edits':{}})
        if not isinstance(value.get('edits'), dict): raise ValueError('編集情報の形式が違います。')
        return value

    def merge(self, index, present, items, edits, facet_fn):
        for saved in items['items']:
            item = copy.deepcopy(saved)
            uid = item['id']
            if not re.fullmatch('[0-9a-f]{32}', uid): raise ValueError('追加画像のIDが不正です。')
            relative = item['files']['image']
            if relative != f"user_items/{uid}/original.{item['image_format']}": raise ValueError('追加画像の保存場所が不正です。')
            key = 'user/'+uid
            record = {**item,'id':'u'+uid,'key':key,'run_id':'user-added','generated':True,
                      'rendered_at':item['added_at'],'seconds':0,'category':'User','folder':'User',
                      'generation_prompt':item.get('generation_prompt',''),'user_added':True,
                      'record_revision':item.get('updated_at',item['added_at'])}
            index[key] = record; present[key] = self.path(relative).is_file()
        for key, overlay in edits['edits'].items():
            record = index.get(key)
            if record and record['image_sha256'] == overlay.get('image_sha256'):
                record = {**record,**{k:v for k,v in overlay['fields'].items() if k in FIELDS},
                          'user_edited':True,'editor_revision':overlay['updated_at']}
                index[key] = record
        for key, record in list(index.items()):
            if record.get('user_added') or record.get('user_edited'):
                index[key] = {**record,'facets':facet_fn(record)}

    def operation(self, operation_id):
        try: operation_id = uuid.UUID(operation_id).hex
        except (ValueError, TypeError, AttributeError): raise ValueError('登録処理IDが不正です。') from None
        with self.lock:
            for item in self.read_items()['items']:
                if item.get('operation_id') == operation_id:
                    return {'saved':True,'key':'user/'+item['id'],'image_sha256':item['image_sha256']}
        return {'saved':False}

    def add(self, payload, existing):
        try: operation_id = uuid.UUID(payload['operation_id']).hex
        except (KeyError, ValueError, TypeError, AttributeError): raise ValueError('登録処理IDが不正です。') from None
        data = decode_bytes(payload.get('image_base64'))
        details = inspect_image(data)
        filename=payload.get('filename','image')
        if not isinstance(filename,str) or len(filename)>1024: raise ValueError('画像ファイル名が不正です。')
        fields = text_fields(payload, filename)
        workflow = payload.get('workflow')
        if workflow is not None:
            try:
                if not isinstance(workflow,(dict,list)) or len(json.dumps(workflow,allow_nan=False))>8*1024*1024: raise ValueError()
            except (ValueError,TypeError): raise ValueError('保存JSONが不正です。JSONを外すか選び直してください。') from None
        # An explicit null means the user chose not to attach a workflow.
        if 'workflow' not in payload: workflow = details['workflow']
        signature = hashlib.sha256(json.dumps([details['image_sha256'],fields,workflow],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        with self.lock:
            catalog = self.read_items()
            for item in catalog['items']:
                if item.get('operation_id') == operation_id:
                    if item.get('request_digest') != signature: raise ValueError('同じ処理IDに別の内容が指定されています。')
                    return {'saved':True,'key':'user/'+item['id'],'image_sha256':item['image_sha256']}
            duplicates_by_key = {e['key']:e for e in existing if e['image_sha256']==details['image_sha256']}
            for item in catalog['items']:
                if item['image_sha256']==details['image_sha256']:
                    duplicates_by_key['user/'+item['id']]={**item,'key':'user/'+item['id']}
            duplicates=list(duplicates_by_key.values())
            if duplicates and payload.get('allow_duplicate') is not True:
                return {'status':'duplicate','duplicates':[{k:e.get(k) for k in ('key','name','copyright','kind')} for e in duplicates]}
            uid = operation_id
            folder = self.path('user_items/'+uid)
            incoming = self.path('user_items/.incoming/'+uid)
            if folder.exists() or incoming.exists(): raise ValueError('登録途中のファイルがあります。既存データは変更していません。')
            incoming.mkdir(parents=True)
            extension = details['extension']; files={'image':f'user_items/{uid}/original.{extension}'}
            try:
                (incoming/('original.'+extension)).write_bytes(data)
                for field,suffix in [('copy_prompt','.copy.txt'),('copy_tags','.tags.txt')]:
                    (incoming/('original'+suffix)).write_text(fields[field],encoding='utf-8')
                    files[field+'_file']=f'user_items/{uid}/original{suffix}'
                if workflow is not None:
                    atomic_json(incoming/'workflow.json', workflow)
                    files['workflow']=f'user_items/{uid}/workflow.json'
                incoming.rename(folder)
                item={**fields,'id':uid,'image_format':extension,'image_mime':details['mime'],
                      'source_filename':filename.replace('\\','/').rsplit('/',1)[-1],
                      'image_sha256':details['image_sha256'],'files':files,'added_at':utc(),'updated_at':utc(),
                      'generation_prompt':details['generation_prompt'],
                      'operation_id':operation_id,'request_digest':signature}
                catalog['items'].append(item)
                atomic_json(self.catalog_file,catalog)
            except Exception:
                # Only this operation's newly-owned paths may be rolled back.
                for owned in (incoming,folder):
                    if owned.exists():
                        assert owned.is_relative_to(self.path('user_items')) and owned.name==uid
                        shutil.rmtree(owned)
                raise
            return {'saved':True,'key':'user/'+uid,'image_sha256':details['image_sha256']}

    def edit(self, payload, record):
        if record['image_sha256'] != payload.get('image_sha256'):
            raise ValueError('画像が変更されています。開き直してから編集してください。')
        if hashlib.sha256(self.path(record['files']['image']).read_bytes()).hexdigest()!=record['image_sha256']:
            raise ValueError('元画像の内容が変わっています。変更は保存していません。')
        supplied = payload.get('fields',{})
        if not isinstance(supplied,dict) or not supplied or any(k not in FIELDS for k in supplied):
            raise ValueError('変更する入力項目が不正です。')
        for k,v in supplied.items():
            if not isinstance(v,str) or len(v)>100000: raise ValueError('入力項目が不正です。')
        merged = text_fields({**{k:record.get(k,'') for k in FIELDS},**supplied},record.get('source_filename') or Path(record['files']['image']).name)
        with self.lock:
            edits = self.read_edits(); old=edits['edits'].get(record['key'],{})
            fields=dict(old.get('fields',{})) if old.get('image_sha256')==record['image_sha256'] else {}
            fields.update({k:merged[k] for k in supplied})
            edits['edits'][record['key']]={'image_sha256':record['image_sha256'],'fields':fields,'updated_at':utc()}
            atomic_json(self.edits_file,edits)
        return {'saved':True,'key':record['key'],'image_sha256':record['image_sha256']}

    def workflow(self, record):
        relative = record['files'].get('workflow')
        if relative:
            path=self.path(relative)
            if not path.is_relative_to(self.path('user_items')): raise ValueError('JSONの保存場所が不正です。')
            return json.loads(path.read_text(encoding='utf-8'))
        return inspect_image(self.path(record['files']['image']).read_bytes())['workflow']

    def reveal(self, record):
        path=self.path(record['files']['image'])
        if not path.is_file(): raise ValueError('画像が見つかりません。')
        return reveal_image(path)

    def csv_rows(self, data, query='', mapping=None):
        if not isinstance(query,str): raise ValueError('検索語を文字で指定してください。')
        if isinstance(data,bytes):
            for encoding in ('utf-8-sig','utf-16','cp932'):
                try: text=data.decode(encoding); break
                except UnicodeError: pass
            else: raise ValueError('CSVの文字コードを読み込めません。')
        else: text=data
        reader=csv.DictReader(io.StringIO(text,newline=''))
        columns=reader.fieldnames or []
        known='tag' in columns or 'prompt' in columns or 'name_en' in columns
        if not known and not mapping: return {'columns':columns,'needs_mapping':True,'rows':[]}
        if mapping and (not isinstance(mapping,dict) or any(k not in FIELDS or v not in columns for k,v in mapping.items())):
            raise ValueError('CSVの列の対応が不正です。')
        result=[]; q=query.casefold().strip()
        for number,row in enumerate(reader):
            if None in row: raise ValueError('CSVの列数が一致しません。カンマを含む値は引用符で囲んでください。')
            if mapping:
                candidate={k:row.get(v,'') or '' for k,v in mapping.items()}
            elif 'tag' in columns:
                raw=row.get('tag','') or '';parts=raw.split(',')
                clean=lambda s:unicodedata.normalize('NFKC',s).replace('_',' ').replace('\\(','(').replace('\\)',')').strip()
                candidate={'name':clean(parts[0]),'copyright':clean(parts[1]) if len(parts)>1 else '', 'copy_tags':raw,'copy_prompt':''}
            elif 'name_en' in columns:
                candidate={'name':row.get('name_en') or row.get('name_jp') or '', 'copyright':row.get('category','') or '',
                           'copy_prompt':row.get('prompt','') or '', 'copy_tags':row.get('source_names','') or ''}
            else: candidate={'name':'','copyright':'','copy_prompt':row.get('prompt','') or '', 'copy_tags':''}
            if q and q not in ' '.join(candidate.values()).casefold():continue
            result.append({**candidate,'row':number,'source_id':row.get('id','') or ''})
            if len(result)>=60:break
        return {'columns':columns,'needs_mapping':False,'rows':result}

    def builtin_csv(self, source, query):
        paths={'characters':'original_tags/anima_characters.csv','styles':'original_tags/styles/selected_all_styles.csv','sample':'comfyui/inputs/thumbnail_prompts.csv'}
        if source not in paths: raise ValueError('CSVの種類が違います。')
        path=self.root/paths[source]
        if not path.is_file():raise ValueError('参考CSVがありません。別のCSVを選ぶか手入力できます。')
        return self.csv_rows(path.read_bytes(),query)
