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


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def png(color, name=None, workflow=None):
    info=PngImagePlugin.PngInfo()
    if name:
        info.add_text('krea2_catalog_prompts',json.dumps({'record':{'name':name,'copyright':name+' WORK','copy_prompt':name+' PROMPT','copy_tags':name+' TAGS'}}))
    if workflow is not None:info.add_text('workflow',json.dumps(workflow))
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
            code_root=workspace/'release/Krea2-Character-Catalog'
        else:code_root=Path(code_root).resolve()
        sys.path.insert(0,str(code_root/'review'))
        from server import make_server
        spec=importlib.util.spec_from_file_location('tested_comparison_skill',code_root/'skills/krea2-animadex-review/scripts/review.py')
        skill=importlib.util.module_from_spec(spec);spec.loader.exec_module(skill)
        catalog=workspace/'Catalog 本体';catalog.mkdir()
        shutil.copy2(code_root/'VERSION',catalog/'VERSION')
        shutil.copytree(code_root/'review',catalog/'review')
        server=make_server(catalog,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();servers.append((server,thread))
        base='http://127.0.0.1:'+str(server.server_port)
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
            pairs=skill.read(review_dir/'pairs.json')['pairs']
            assert all(Path(p['reference_image']).is_file() and Path(p['catalog_image']).is_file() for p in pairs)
            checks.append('readonly_sqlite_exact_csv_pairs_unicode_case_paths')
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
            assert not (review_dir/'apply-checkpoint.json').exists()
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
            checkpoint=skill.read(review_dir/'apply-checkpoint.json')
            assert not checkpoint['completed'] and checkpoint['applied']==[rows[0]['key']] and journal.read_bytes()==journal_before
            resumed=skill.apply(env,review_dir,decisions)
            assert resumed['visibility_changes']==1 and resumed['verified']
            assert skill.read(review_dir/'apply-checkpoint.json')['completed']
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
        finally:browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();where=parser.add_mutually_exclusive_group(required=True)
    where.add_argument('--archive',type=Path);where.add_argument('--root',type=Path)
    parser.add_argument('--report',type=Path,required=True);parser.add_argument('--browser-test',action='store_true')
    args=parser.parse_args();run(args.archive,args.report,args.browser_test,args.root)
