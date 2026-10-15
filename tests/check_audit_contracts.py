"""Disposable actual-HTTP regressions using released code and fictitious data."""
from pathlib import Path
from contextlib import closing
import argparse
import base64
import csv
import hashlib
import importlib.util
import io
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from unittest.mock import patch
from PIL import Image, PngImagePlugin

SOURCE = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(SOURCE/'tools'))
from package_release import safe_extract
from catalog_layout import app_root


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def png(color, name=None, workflow=None, prompt=None):
    info=PngImagePlugin.PngInfo()
    if name:
        info.add_text('krea2_catalog_prompts',json.dumps({'record':{'name':name,'copyright':name+' WORK','copy_prompt':name+' PROMPT','copy_tags':name+' TAGS'}}))
    if workflow is not None:info.add_text('workflow',json.dumps(workflow))
    if prompt is not None:info.add_text('prompt',json.dumps(prompt))
    stream=io.BytesIO();Image.new('RGB',(19,23),color).save(stream,'PNG',pnginfo=info)
    return stream.getvalue()


def run(archive,report_path,browser_test=False,code_root=None):
    checks=[];servers=[]
    report={'platform':sys.platform,'python':sys.version.split()[0], 'checks':checks,'passed':False,
            'synthetic_animadex_contracts_tested':True,'real_animadex_installation_tested':False,
            'cross_os_migration_tested':False,'desktop_file_manager_manually_tested':False}
    with tempfile.TemporaryDirectory(prefix='Krea2 audit contracts ') as temporary:
        workspace=Path(temporary)/'日本語 fixture with spaces';workspace.mkdir()
        if archive:
            safe_extract(archive,workspace/'release')
            code_root=app_root(workspace/'release/Krea2-Character-Catalog')
        else:code_root=Path(code_root).resolve()
        sys.path.insert(0,str(code_root/'review'))
        from server import make_server
        spec=importlib.util.spec_from_file_location('tested_comparison_skill',code_root/'skills/krea2-animadex-review/scripts/review.py')
        skill=importlib.util.module_from_spec(spec);spec.loader.exec_module(skill)
        catalog=workspace/'Catalog 本体';catalog.mkdir()
        shutil.copy2(code_root/'VERSION',catalog/'VERSION')
        shutil.copytree(code_root/'review',catalog/'review')
        shutil.copytree(code_root/'tools',catalog/'tools')
        shutil.copytree(code_root/'skills',catalog/'skills')
        server=make_server(catalog,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();servers.append((server,thread))
        base='http://127.0.0.1:'+str(server.server_port)
        write_json(catalog/'outputs/review_service.json',{'url':base})
        api=lambda route,body=None:skill.api(base,route,body,server.token)
        anima=workspace/'AnimaDex test data';thumbs=anima/'data/characters/thumbs';thumbs.mkdir(parents=True)
        source=catalog/'original_tags/anima_characters.csv';source.parent.mkdir()
        rows=[];originals={}
        try:
            with closing(sqlite3.connect(anima/'data/animadex.db')) as db,source.open('w',encoding='utf-8-sig',newline='') as csv_stream:
                db.execute('CREATE TABLE characters(character TEXT,name TEXT,trigger TEXT,thumbname TEXT)')
                writer=csv.DictWriter(csv_stream,fieldnames=['tag','category','count','insert_mode']);writer.writeheader()
                for index in range(4):
                    name='Audit '+chr(65+index);tags=name.lower()+', test work'
                    raw=png((index*41+11,29,93));ref=png((index*37+13,41,88))
                    ref_name='Reference '+chr(65+index)+'.PnG';(thumbs/ref_name).write_bytes(ref)
                    db.execute('INSERT INTO characters VALUES(?,?,?,?)',(name.lower(),name,tags,ref_name))
                    writer.writerow({'tag':tags,'category':'test','count':1,'insert_mode':'test'})
                    saved=api('/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':name+'.PnG',
                              'image_base64':base64.b64encode(raw).decode(),'name':name,'copyright':'Test Work','copy_tags':tags})
                    originals[saved['key']]=raw
                db.commit()
            config=workspace/'private config.json'
            write_json(config,{'catalog_root':str(catalog),'animadex_root':str(anima),'catalog_url':base})
            env=skill.environment(config);review_dir=workspace/'comparison with spaces'
            prepared=skill.prepare(env,review_dir)
            assert prepared['available_pairs']==4 and prepared['missing_or_ambiguous_identity']==0
            pairs=skill.read(skill.review_root(review_dir)/'pairs.json')['pairs']
            assert all(Path(p['reference_image']).is_file() and Path(p['catalog_image']).is_file() for p in pairs)
            checks.append('readonly_sqlite_exact_csv_pairs_unicode_case_paths')
            manual_dir=workspace/'manual comparison without skill'
            manual=subprocess.run([sys.executable,'-B',str(catalog/'tools/create_comparison.py'),'--animadex-root',str(anima),'--output',str(manual_dir),'--json'],capture_output=True,text=True,timeout=30)
            assert manual.returncode==0,manual.stderr
            assert json.loads(manual.stdout)['stats']['available_pairs']==4
            assert (manual_dir/'START_COMPARISON - Windows.cmd').is_file() and (manual_dir/'app/settings.json').is_file()
            checks.append('manual_comparison_setup_without_skill_installation_or_json_editing')
            for pair in pairs:
                row={k:pair[k] for k in ['key','catalog_image_sha256','reference_image_sha256']}
                row.update({'decision':'match' if len(rows)<2 else 'mismatch','selected':True,'confirmed':True});rows.append(row)
                api('/api/favorite',{'key':pair['key'],'enabled':True});api('/api/similarity',{'key':pair['key'],'rating':2})
            api('/api/hide',{'keys':[rows[1]['key'],rows[3]['key']]})
            decisions=review_dir/'confirmed.json'
            export=lambda values:write_json(decisions,{'schema':'krea2-portable-human-review-v1','decisions':values})
            export(rows)
            state_file=catalog/'outputs/review_state.json';before=state_file.read_bytes()
            plan=skill.apply(env,review_dir,decisions,dry_run=True)
            assert plan['visibility_changes']==2 and plan['unchanged']==2 and state_file.read_bytes()==before
            assert not (catalog/'outputs/user_comparison_decisions.json').exists()
            assert not (skill.review_root(review_dir)/'apply-checkpoint.json').exists()
            checks.append('dry_run_plans_two_changes_two_noops_without_writes')
            actual_api=skill.api;writes=[]
            def observe(url,route,body=None,token=''):
                if body is not None:writes.append((route,body))
                return actual_api(url,route,body,token)
            with patch.object(skill,'api',side_effect=observe):result=skill.apply(env,review_dir,decisions)
            assert result['verified'] and [route for route,_ in writes]==['/api/restore','/api/hide']
            journal=catalog/'outputs/user_comparison_decisions.json';assert len(skill.read(journal)['decisions'])==4
            listing={r['key']:r for r in api('/api/list')['entries']}
            for row in rows:
                record=listing[row['key']]
                assert record['hidden']==(row['decision']=='mismatch') and record['favorite'] and record['similarity']==2
                assert (catalog/'outputs'/record['files']['image']).read_bytes()==originals[row['key']]
            checks.append('four_visibility_verdict_states_actual_api_preserve_images_favorites_ratings')
            journal_before=journal.read_bytes();state_before=state_file.read_bytes();writes.clear()
            with patch.object(skill,'api',side_effect=observe):repeated=skill.apply(env,review_dir,decisions)
            assert repeated['visibility_changes']==0 and repeated['unchanged']==4 and not writes
            assert journal.read_bytes()==journal_before and state_file.read_bytes()==state_before
            checks.append('repeat_apply_no_visibility_writes_no_duplicate_judgments')

            api('/api/hide',{'keys':[rows[0]['key']]});api('/api/restore',{'keys':[rows[2]['key']]})
            export([rows[0],rows[2]]);journal_before=journal.read_bytes()
            def fail_hide(url,route,body=None,token=''):
                if route=='/api/hide':raise OSError('test interruption after restore')
                return actual_api(url,route,body,token)
            try:
                with patch.object(skill,'api',side_effect=fail_hide):skill.apply(env,review_dir,decisions)
                raise AssertionError('Expected interruption')
            except OSError:pass
            checkpoint=skill.read(skill.review_root(review_dir)/'apply-checkpoint.json')
            assert not checkpoint['completed'] and checkpoint['applied']==[rows[0]['key']] and journal.read_bytes()==journal_before
            resumed=skill.apply(env,review_dir,decisions)
            assert resumed['visibility_changes']==1 and resumed['verified']
            assert skill.read(skill.review_root(review_dir)/'apply-checkpoint.json')['completed']
            checks.append('partial_failure_checkpoint_safe_retry')

            state_before=state_file.read_bytes();journal_before=journal.read_bytes()
            export([{**rows[0],'decision':'hold'},{**rows[1],'selected':False},
                    {**rows[2],'confirmed':False},{**rows[3],'decision':None}])
            skipped=skill.apply(env,review_dir,decisions)
            assert skipped['selected_confirmed']==0 and state_file.read_bytes()==state_before and journal.read_bytes()==journal_before
            checks.append('hold_unselected_unconfirmed_absent_leave_state_unchanged')
            export([rows[0]])
            for image_path in [Path(pairs[0]['catalog_image']),Path(pairs[0]['reference_image'])]:
                original=image_path.read_bytes();image_path.write_bytes(png((101,202,43)))
                try:
                    try:skill.apply(env,review_dir,decisions);raise AssertionError('Expected changed-image refusal')
                    except ValueError:pass
                    assert state_file.read_bytes()==state_before and journal.read_bytes()==journal_before
                finally:image_path.write_bytes(original)
            checks.append('changed_catalog_or_reference_image_rejects_before_visibility_writes')

            embedded={'nodes':[{'id':1,'type':'AuditFakeWorkflow'}]};raw=png((22,55,99),workflow=embedded)
            for selected,available in [({},True),({'workflow':None},False),({'workflow':{'nodes':[]}},True)]:
                saved=api('/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':'JSON 原画像.PnG',
                          'image_base64':base64.b64encode(raw).decode(),'allow_duplicate':True,**selected})
                detail=api('/api/editor/record?'+urllib.parse.urlencode({'key':saved['key']}))
                assert detail['workflow_available']==available
                assert (catalog/'outputs'/detail['record']['files']['image']).read_bytes()==raw
            checks.append('workflow_auto_removed_explicit_actual_api_original_bytes')

            for second,expected in [('POSITIVE','POSITIVE'),('DIFFERENT','')]:
                prompt={
                    'positive':{'class_type':'CLIPTextEncode','inputs':{'text':'POSITIVE'}},
                    'second':{'class_type':'CLIPTextEncode','inputs':{'text':second}},
                    'concat':{'class_type':'ConditioningConcat','inputs':{'conditioning_to':['positive',0],'conditioning_from':['second',0]}},
                    'sampler':{'class_type':'KSampler','inputs':{'positive':['concat',0]}},
                    'decode':{'class_type':'VAEDecode','inputs':{'samples':['sampler',0]}},
                    'save':{'class_type':'SaveImage','inputs':{'images':['decode',0]}},
                }
                details=api('/api/editor/inspect',{'image_base64':base64.b64encode(png((47,59,71),prompt=prompt)).decode()})
                assert details['generation_prompt']==expected
            checks.append('concat_core_inputs_same_text_resolved_different_text_unset_actual_api')

            for value in [None,[],42,'invalid']:
                raw=png((83,97,109),prompt={'save':{'class_type':'SaveImage','inputs':value}})
                payload={'image_base64':base64.b64encode(raw).decode()}
                details=api('/api/editor/inspect',payload)
                assert details['generation_prompt']=='' and details['mime']=='image/png'
                saved=api('/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':'Invalid optional metadata.PnG',**payload})
                record=api('/api/editor/record?'+urllib.parse.urlencode({'key':saved['key']}))['record']
                assert record['generation_prompt']=='' and (catalog/'outputs'/record['files']['image']).read_bytes()==raw
            checks.append('invalid_optional_metadata_actual_http_inspect_register_original_bytes')

            if browser_test:
                check_browser(base,api,catalog,workspace,checks)
            report['passed']=True
        finally:
            for running,worker in servers:
                port=running.server_port;running.shutdown();worker.join(5);running.server_close()
                assert not worker.is_alive()
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=.5):raise AssertionError('Test listener remains open')
                except OSError:pass
            report['test_servers_stopped']=True
            write_json(report_path,report)
    print(json.dumps(report,ensure_ascii=False))


def check_browser(base,api,catalog,workspace,checks):
    from playwright.sync_api import sync_playwright,expect
    workflow={'nodes':[{'id':7,'type':'AuditEmbeddedWorkflow'}]}
    alpha=workspace/'Alpha 架空.PnG';alpha.write_bytes(png((54,43,32),'AUTO_ALPHA',workflow))
    beta=workspace/'Beta 架空.PnG';beta.write_bytes(png((21,43,65),'AUTO_BETA',workflow))
    empty=workspace/'No metadata.PnG';empty.write_bytes(png((95,73,51)))
    with sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            page=browser.new_page();page.goto(base+'/editor')
            expect(page.locator('#register')).to_be_disabled()
            for image,name in [(alpha,'AUTO_ALPHA'),(beta,'AUTO_BETA')]:
                page.locator('#file').set_input_files(str(image));expect(page.locator('#name')).to_have_value(name)
                expect(page.locator('#copyright')).to_have_value(name+' WORK')
                expect(page.locator('#prompt')).to_have_value(name+' PROMPT')
                expect(page.locator('#tags')).to_have_value(name+' TAGS')
            page.locator('#register').click();expect(page.locator('#status')).to_contain_text('Saved to the catalog.',timeout=20000)
            stored=next(r for r in api('/api/list')['entries'] if r['name']=='AUTO_BETA')
            assert stored['copyright']=='AUTO_BETA WORK' and stored['copy_prompt']=='AUTO_BETA PROMPT'
            assert (catalog/'outputs'/stored['files']['image']).read_bytes()==beta.read_bytes()
            page.reload();record=api('/api/editor/record?'+urllib.parse.urlencode({'key':stored['key']}))
            assert record['record']['name']=='AUTO_BETA' and record['workflow_available']
            checks.append('chromium_replace_autofill_register_save_reload')

            page.goto(base+'/editor');page.locator('#file').set_input_files(str(alpha))
            expect(page.locator('#name')).to_have_value('AUTO_ALPHA')
            page.locator('#name').fill('MANUAL NAME');page.locator('#prompt').fill('')
            page.locator('#file').set_input_files(str(beta));expect(page.locator('#copyright')).to_have_value('AUTO_BETA WORK')
            expect(page.locator('#name')).to_have_value('MANUAL NAME');expect(page.locator('#prompt')).to_have_value('')
            page.locator('#file').set_input_files(str(empty));expect(page.locator('#image-info')).to_contain_text(empty.name)
            expect(page.locator('#name')).to_have_value('MANUAL NAME');expect(page.locator('#copyright')).to_have_value('')
            expect(page.locator('#tags')).to_have_value('');expect(page.locator('#prompt')).to_have_value('')
            checks.append('chromium_manual_edits_and_explicit_blanks_preserved_missing_metadata_cleared')

            page.locator('#file').set_input_files(str(alpha));expect(page.locator('#tags')).to_have_value('AUTO_ALPHA TAGS')
            page.locator('#name').fill('WORKFLOW REMOVED')
            page.locator('details summary').click();page.locator('#remove-workflow').click()
            page.locator('#register').click();expect(page.locator('#status')).to_contain_text('Saved to the catalog.',timeout=20000)
            saved=next(r for r in api('/api/list')['entries'] if r['name']=='WORKFLOW REMOVED')
            detail=api('/api/editor/record?'+urllib.parse.urlencode({'key':saved['key']}))
            assert not detail['workflow_available']
            assert (catalog/'outputs'/saved['files']['image']).read_bytes()==alpha.read_bytes()
            page.goto(base+'/editor?'+urllib.parse.urlencode({'key':saved['key']}))
            expect(page.locator('#name')).to_have_value('WORKFLOW REMOVED')
            expect(page.locator('#existing-workflow')).to_be_hidden()
            checks.append('chromium_remove_json_register_reopen_remains_removed')

            # Normal user controls must reach bulk restoration of hidden cards.
            page.goto(base);page.locator('#search').fill('AUTO_BETA')
            expect(page.locator('#grid .card')).to_have_count(1)
            page.locator('#select-visible').click();page.locator('#delete-selected').click()
            expect(page.locator('#grid .card')).to_have_count(0)
            page.locator('#hidden-only').click();expect(page.locator('#grid .card')).to_have_count(1)
            expect(page.locator('#grid .pick input')).to_be_visible()
            page.locator('#select-visible').click();expect(page.locator('#restore-selected')).to_be_enabled()
            expect(page.locator('#delete-selected')).to_be_disabled()
            page.locator('#restore-selected').click();expect(page.locator('#grid .card')).to_have_count(0)
            page.locator('#hidden-only').click();expect(page.locator('#grid .card')).to_have_count(1)
            checks.append('chromium_hidden_selection_bulk_restore_normal_controls')

            tagged=api('/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':'tagged.png','name':'TAG SEARCH',
                       'copy_tags':'1girl, red_hair, blue_eyes, UNIQUE_RAW_TAG',
                       'image_base64':base64.b64encode(png((117,33,55))).decode()})
            record=api('/api/editor/record?'+urllib.parse.urlencode({'key':tagged['key']}))['record']
            assert record['facets']['gender']==['Female'] and record['facets']['hairColor']==['red hair']
            page.reload();page.locator('#search').fill('UNIQUE_RAW_TAG')
            expect(page.locator('#grid .card')).to_have_count(1)
            checks.append('chromium_raw_tag_search_and_unprefixed_facets')

            # Build actual static data with conflicting original artist metadata.
            style=api('/api/editor/add',{'operation_id':str(uuid.uuid4()),'filename':'edited style.png','kind':'style',
                      'name':'Old style','image_base64':base64.b64encode(png((139,71,21))).decode()})
            record=api('/api/editor/record?'+urllib.parse.urlencode({'key':style['key']}))['record']
            api('/api/editor/edit',{'key':style['key'],'image_sha256':record['image_sha256'],
                                   'fields':{'name':'Corrected style','copy_tags':'CORRECTED_STYLE_TAG'}})
            page.goto(base+'/?tab=styles');page.locator('#tab-styles').click()
            page.locator('#search').fill('CORRECTED_STYLE_TAG');expect(page.locator('#grid .card')).to_have_count(1)
            expect(page.locator('#grid .card')).to_contain_text('Corrected style')
            listing=api('/api/list');record=next(r for r in listing['entries'] if r['key']==style['key'])
            listing['style_candidates'].append({'id':record['id'],'name':'Original artist name','copy_tags':'ORIGINAL_STYLE_TAG','artist_metadata_revision':'1'})
            sys.path.insert(0,str(SOURCE/'tools'))
            from build_static_demo import build
            from server import ReviewStore
            with patch.object(ReviewStore,'list',return_value=listing):build(catalog,workspace/'demo')
            data=json.loads((workspace/'demo/catalog.json').read_text(encoding='utf-8'))
            exported=next(r for r in data['entries'] if r['key']==record['key'])
            assert exported['user_edited'] and exported['copy_tags']==record['copy_tags']
            from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
            from functools import partial
            static=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(workspace/'demo')))
            worker=threading.Thread(target=static.serve_forever,daemon=True);worker.start()
            try:
                demo=browser.new_page();demo.goto('http://127.0.0.1:'+str(static.server_port))
                expect(demo.locator('#stop-server')).to_be_hidden()
                demo.locator('#tab-styles').click();demo.locator('#search').fill('CORRECTED_STYLE_TAG')
                expect(demo.locator('#grid .card')).to_have_count(1)
                expect(demo.locator('#grid .card')).to_contain_text('Corrected style')
                demo.close()
            finally:static.shutdown();worker.join(5);static.server_close();assert not worker.is_alive()
            checks.append('chromium_local_static_edited_style_name_tags_agree')
        finally:browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();where=parser.add_mutually_exclusive_group(required=True)
    where.add_argument('--archive',type=Path);where.add_argument('--root',type=Path)
    parser.add_argument('--report',type=Path,required=True);parser.add_argument('--browser-test',action='store_true')
    args=parser.parse_args();run(args.archive,args.report,args.browser_test,args.root)
