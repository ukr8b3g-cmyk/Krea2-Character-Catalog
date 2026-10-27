const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {chromium,expect}=require('playwright/test');const root=process.env.KREA_TEST_ROOT||path.resolve(__dirname,'..');
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j9ZkAAAAASUVORK5CYII=','base64');
const code=fs.readFileSync(path.join(root,'review/review.js'),'utf8');const fn=name=>{const i=code.indexOf('function '+name+'(');return code.slice(i,code.indexOf('\n  }',i)+4);};
const compare=vm.runInNewContext(fn('generationTime')+'\n('+fn('compareRecords')+')',{Date,catalogCollator:new Intl.Collator('en'),ensureCatalog:()=>({items:new Map(['old','new','same','generated','missing'].map(key=>[key,{generationSort:'added'}]))})});
const row=(key,id,date,run='user-added')=>({key,id,rendered_at:date,run_id:run,kind:'character'});
const old=row('old','u90000','2026-10-01T00:00:00Z'),fresh=row('new','u10000','2026-10-24T00:00:00Z'),same=row('same','ufffff','2026-10-24T00:00:00Z'),generated=row('generated','a00001','2026-10-10T00:00:00Z','run-20261010-000000'),missing=row('missing','ufff','bad');
assert.deepEqual([old,fresh,generated].sort((a,b)=>compare(a,b,'newest')).map(x=>x.key),['new','generated','old']);
assert.deepEqual([fresh,generated,old].sort((a,b)=>compare(a,b,'generation')).map(x=>x.key),['old','generated','new']);
assert.equal(compare(fresh,same,'newest'),compare(fresh,same,'newest'));assert(Number.isFinite(compare(missing,old,'newest')));console.log('PASS chronological user-added and mixed sorting');
assert(compare(same,old,'newest')<0);assert(compare(old,same,'generation')<0);
const generatedFirst={...generated,key:'old',id:'a00001',source_index:1},generatedSecond={...generated,key:'new',id:'a00002',source_index:2};
assert(compare(generatedFirst,generatedSecond,'generation')<0);assert(compare(generatedFirst,generatedSecond,'newest')>0);
for(const a of [old,fresh,same,generated,missing])for(const b of [old,fresh,same,generated,missing])for(const c of [old,fresh,same,generated,missing])if(compare(a,b,'newest')<=0&&compare(b,c,'newest')<=0)assert(compare(a,c,'newest')<=0);
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});let passed=0;
 async function scenario(title,check){const context=await browser.newContext();try{
  const page=await context.newPage(),added=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{const url=new URL(route.request().url()),p=url.pathname;
   if(p==='/editor')return route.fulfill({contentType:'text/html',body:fs.readFileSync(path.join(root,'review/editor.html'),'utf8')});
   if(p==='/editor.js')return route.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.join(root,'review/editor.js'),'utf8')});
   if(p==='/api/editor/bootstrap')return route.fulfill({json:{token:'test-token',sources:[],folder_available:false}});
   if(p==='/api/editor/inspect')return route.fulfill({json:{image_sha256:'test-sha',width:1,height:1,mime:'image/png',metadata:{},workflow:{marker:'OLD'}}});
   if(p==='/api/editor/add'){added.push(route.request().postDataJSON());return route.fulfill({json:{status:'duplicate',duplicates:[]}});}
   return route.fulfill({body:'<!doctype html>'});});
  await page.goto('http://127.0.0.1:18797/editor');await page.waitForFunction(()=>document.getElementById('csv-source').value==='file');await page.locator('.extras > summary').click();
  await page.locator('#file').setInputFiles({name:'image.png',mimeType:'image/png',buffer:png});await expect(page.locator('#register')).toBeEnabled();
  await page.evaluate(()=>{window.pendingJson={};const original=File.prototype.text;File.prototype.text=function(){if(this.name.endsWith('.json'))return new Promise((resolve,reject)=>window.pendingJson[this.name]={resolve,reject});return original.call(this);};window.close=()=>{window.requestedClose=true;};});
  const select=async name=>{await page.locator('#workflow').setInputFiles({name,mimeType:'application/json',buffer:Buffer.from('{}')});await page.waitForFunction(n=>!!window.pendingJson[n],name);};
  const finish=async(name,text)=>page.evaluate(({name,text})=>window.pendingJson[name].resolve(text),{name,text});
  await check({page,context,select,finish,added});assert.deepEqual(errors,[]);console.log('PASS '+title);passed++;
 }finally{await context.close();}}
 try{
  await scenario('pending workflow blocks submit; completed selection is saved',async({page,select,finish,added})=>{await select('new.json');await expect(page.locator('#register')).toBeDisabled();await page.locator('#form').dispatchEvent('submit');assert.equal(added.length,0);await finish('new.json','{"marker":"NEW"}');await expect(page.locator('#register')).toBeEnabled();await page.locator('#register').click();await expect.poll(()=>added.length).toBe(1);assert.equal(added[0].workflow.marker,'NEW');});
  await scenario('A/B reverse completion keeps B',async({page,select,finish,added})=>{await select('A.json');await select('B.json');await finish('B.json','{"marker":"B"}');await expect(page.locator('#register')).toBeEnabled();await finish('A.json','{"marker":"A"}');await page.locator('#register').click();await expect.poll(()=>added.length).toBe(1);assert.equal(added[0].workflow.marker,'B');});
  await scenario('remove during read defeats late success',async({page,select,finish,added})=>{await select('A.json');await page.locator('#remove-workflow').click();await expect(page.locator('#register')).toBeEnabled();await finish('A.json','{"marker":"A"}');await page.locator('#register').click();await expect.poll(()=>added.length).toBe(1);assert.equal(added[0].workflow,null);});
  await scenario('invalid JSON blocks saving until removed',async({page,select,finish})=>{await select('bad.json');await finish('bad.json','broken');await expect(page.locator('#workflow-info')).toContainText('Cannot read JSON');await expect(page.locator('#register')).toBeDisabled();await page.locator('#remove-workflow').click();await expect(page.locator('#register')).toBeEnabled();});
  await scenario('Close waits for JSON and preserves image plus selected workflow in IndexedDB',async({page,select,finish,added})=>{await select('new.json');await page.locator('#close-editor').click();await expect(page.locator('#close-editor')).toBeDisabled();await page.locator('#form').dispatchEvent('submit');assert.equal(added.length,0);await finish('new.json','{"marker":"DRAFT"}');await page.waitForURL('http://127.0.0.1:18797/');await page.goto('http://127.0.0.1:18797/editor');await expect(page.locator('#register')).toBeEnabled();await page.locator('#register').click();await expect.poll(()=>added.length).toBe(1);assert.equal(added[0].workflow.marker,'DRAFT');});
  console.log(passed+' JSON workflow browser scenarios passed');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
