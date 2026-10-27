"""Browser regressions for the CSV/JSON/origin/sort review fixes; fictitious data only."""
from pathlib import Path
import argparse
import base64
import json
import os
import sys
import tempfile
from playwright.sync_api import sync_playwright, expect

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE/'tools'))
from package_release import safe_extract
from catalog_layout import app_root


def run(root, report):
    checks = []
    png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9ZkAAAAASUVORK5CYII=')
    with sync_playwright() as engine:
        options = {'headless': True}
        if os.environ.get('KREA_BROWSER_CHANNEL'): options['channel'] = os.environ['KREA_BROWSER_CHANNEL']
        browser = engine.chromium.launch(**options)
        try:
            for scenario in ('register', 'reverse', 'remove', 'invalid', 'close'):
                context = browser.new_context()
                try:
                    page = context.new_page(); added = []; errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    def route(request):
                        path = request.request.url.split('18797',1)[-1].split('?',1)[0]
                        if path == '/editor': return request.fulfill(content_type='text/html', body=(root/'review/editor.html').read_text(encoding='utf8'))
                        if path == '/editor.js': return request.fulfill(content_type='text/javascript', body=(root/'review/editor.js').read_text(encoding='utf8'))
                        if path == '/api/editor/bootstrap': return request.fulfill(json={'token':'test','sources':[],'folder_available':False})
                        if path == '/api/editor/inspect': return request.fulfill(json={'image_sha256':'test','width':1,'height':1,'mime':'image/png','metadata':{},'workflow':{'marker':'OLD'}})
                        if path == '/api/editor/add':
                            added.append(request.request.post_data_json)
                            return request.fulfill(json={'status':'duplicate','duplicates':[]})
                        return request.fulfill(body='<!doctype html>')
                    page.route('**/*', route)
                    page.goto('http://127.0.0.1:18797/editor')
                    page.wait_for_function("document.getElementById('csv-source').value==='file'")
                    page.locator('.extras > summary').click()
                    page.locator('#file').set_input_files({'name':'image.png','mimeType':'image/png','buffer':png})
                    expect(page.locator('#register')).to_be_enabled()
                    page.evaluate("""() => {window.pendingJson={};const original=File.prototype.text;File.prototype.text=function(){if(this.name.endsWith('.json'))return new Promise((resolve,reject)=>window.pendingJson[this.name]={resolve,reject});return original.call(this);};window.close=()=>{};}""")
                    def select(name):
                        page.locator('#workflow').set_input_files({'name':name,'mimeType':'application/json','buffer':b'{}'})
                        page.wait_for_function('name=>!!window.pendingJson[name]',arg=name)
                    def finish(name, value):
                        page.evaluate('value=>window.pendingJson[value.name].resolve(value.text)',{'name':name,'text':json.dumps({'marker':value}) if value!='INVALID' else 'broken'})
                    def registered(marker):
                        with page.expect_response('**/api/editor/add'):
                            page.locator('#register').click()
                        assert len(added)==1, added
                        assert added[0]['workflow']==({'marker':marker} if marker else None), added
                    select('A.json')
                    if scenario=='register':
                        expect(page.locator('#register')).to_be_disabled();page.locator('#form').dispatch_event('submit');assert not added
                        finish('A.json','NEW');expect(page.locator('#register')).to_be_enabled();registered('NEW')
                    elif scenario=='reverse':
                        select('B.json');finish('B.json','B');expect(page.locator('#register')).to_be_enabled();finish('A.json','A');registered('B')
                    elif scenario=='remove':
                        page.locator('#remove-workflow').click();expect(page.locator('#register')).to_be_enabled();finish('A.json','A');registered(None)
                    elif scenario=='invalid':
                        finish('A.json','INVALID');expect(page.locator('#workflow-info')).to_contain_text('Cannot read JSON');expect(page.locator('#register')).to_be_disabled()
                        page.locator('#remove-workflow').click();expect(page.locator('#register')).to_be_enabled()
                    else:
                        page.locator('#close-editor').click();expect(page.locator('#close-editor')).to_be_disabled();page.locator('#form').dispatch_event('submit');assert not added
                        finish('A.json','DRAFT');page.wait_for_url('http://127.0.0.1:18797/');page.goto('http://127.0.0.1:18797/editor')
                        expect(page.locator('#register')).to_be_enabled();registered('DRAFT')
                    assert not errors, errors
                    checks.append('workflow_'+scenario)
                    if scenario=='close':
                        code=(root/'review/review.js').read_text(encoding='utf8')
                        def function(name):
                            start=code.index('function '+name+'(');return code[start:code.index('\n  }',start)+4]
                        result=page.evaluate('''code=>{const catalogCollator=new Intl.Collator('en'),ensureCatalog=()=>({items:new Map(['old','new','same','generated','missing'].map(k=>[k,{generationSort:'added'}]))});const compare=eval(code);const row=(key,id,date,run='user-added')=>({key,id,rendered_at:date,run_id:run,kind:'character'});const old=row('old','u900','2026-10-01T00:00:00Z'),fresh=row('new','u100','2026-10-24T00:00:00Z'),same=row('same','ufff','2026-10-24T00:00:00Z'),gen=row('generated','a001','2026-10-10T00:00:00Z','run-20261010-000000'),missing=row('missing','ufff','bad');const rows=[old,fresh,same,gen,missing];const assert=(v)=>{if(!v)throw new Error('sort regression');};assert(JSON.stringify([old,fresh,gen].sort((a,b)=>compare(a,b,'newest')).map(x=>x.key))==='["new","generated","old"]');assert(JSON.stringify([fresh,gen,old].sort((a,b)=>compare(a,b,'generation')).map(x=>x.key))==='["old","generated","new"]');assert(compare(same,old,'newest')<0);for(const a of rows)for(const b of rows)for(const c of rows)if(compare(a,b,'newest')<=0&&compare(b,c,'newest')<=0)assert(compare(a,c,'newest')<=0);return true;}''', function('generationTime')+'\n('+function('compareRecords')+')')
                        assert result;checks.append('chronological_mixed_sort_transitivity')
                finally: context.close()
        finally: browser.close()
    report.parent.mkdir(parents=True,exist_ok=True)
    result={'passed':True,'checks':checks,'synthetic_data':True,'gpu_tested':False}
    report.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser();where=parser.add_mutually_exclusive_group(required=True)
    where.add_argument('--root',type=Path);where.add_argument('--archive',type=Path);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.archive:
        with tempfile.TemporaryDirectory(prefix='krea2-review-browser-') as folder:
            safe_extract(args.archive,Path(folder));run(app_root(Path(folder)/'Krea2-Character-Catalog'),args.report)
    else:run(app_root(args.root),args.report)
