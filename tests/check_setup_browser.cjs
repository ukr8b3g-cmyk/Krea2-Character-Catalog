// Disposable browser only, never connects to a user's browser profile.
const fs=require('fs'),path=require('path');
const [modulePath,workspace,chromiumPath]=process.argv.slice(2);
const {chromium}=require(modulePath);
const ready=JSON.parse(fs.readFileSync(path.join(workspace,'ready.json'),'utf8'));
const progress=value=>{fs.writeFileSync(path.join(workspace,'browser-progress.json'),JSON.stringify(value));console.log(JSON.stringify(value));};
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:chromiumPath});
 try{
  const page=await browser.newPage();await page.goto(ready.url);await page.locator('#catalog_root').waitFor();
  await page.locator('#language').selectOption('ja');
  await page.waitForFunction(()=>document.querySelector('#catalog_root').value.length>0);
  async function choose(field,target){
   await page.locator(`[data-pick="${field}"]`).click();await page.waitForFunction(()=>document.querySelector('#picker-path').textContent.length>0);
   const parts=target.replaceAll('\\','/').split('/'),drive=parts[0]?parts.shift()+'/':'/';if(!parts[0])parts.shift();
   await page.locator('#picker-roots').selectOption(drive);await page.waitForFunction(drive=>document.querySelector('#picker-path').textContent.replaceAll('\\','/')===drive,drive);
   for(const name of parts){await page.getByRole('button',{name:'📁 '+name,exact:true}).click();await page.waitForFunction(name=>document.querySelector('#picker-path').textContent.replaceAll('\\','/').endsWith('/'+name),name);}
   await page.locator('#picker-use').click();
  }
  await choose('catalog_root',ready.catalog);progress({step:'choose_catalog',folder:ready.catalog});
  await choose('animadex_root',ready.animadex);progress({step:'choose_animadex',folder:ready.animadex});
  if(ready.output_parent){await page.locator('details summary').click();await choose('output',ready.output_parent);}
  if(await page.locator('#catalog_root').inputValue()!==ready.catalog)throw Error('Catalog folder picker result mismatch');
  if(await page.locator('#animadex_root').inputValue()!==ready.animadex)throw Error('AnimaDex folder picker result mismatch');
  await page.locator('#check').click();await page.locator('#save').waitFor({state:'visible'});
  await page.waitForFunction(()=>!document.querySelector('#save').disabled);
  if(!(await page.locator('#result').innerText()).includes('比較可能：1件'))throw Error('Pair count missing');
  await page.screenshot({path:path.join(workspace,'setup.png'),fullPage:true});
  await page.locator('#save').click();await page.waitForURL(url=>url.origin!==new URL(ready.url).origin);
  await page.locator('#grid .card').waitFor();
  const images=await page.locator('#grid .card img').evaluateAll(imgs=>imgs.map(i=>({loaded:i.complete&&i.naturalWidth>0,src:i.src})));
  if(images.length!==2||images.some(i=>!i.loaded))throw Error('Both comparison images must load');
  await page.screenshot({path:path.join(workspace,'comparison.png'),fullPage:true});
  await page.locator('#comparison-settings').click();await page.waitForURL(ready.url);await page.waitForFunction(()=>document.querySelector('#animadex_root').value.length>0);
  if(await page.locator('#animadex_root').inputValue()!==ready.animadex)throw Error('Settings not persisted');
  progress({passed:true,on_screen_folder_navigation:true,checks:['folder_selection_buttons','drive_and_folder_navigation','connection_pair_count','save_redirect_comparison','both_images_decode','comparison_settings_link','saved_folder_settings'],comparison_images:images});
 }finally{await browser.close();}
})().catch(e=>{progress({passed:false,error:e.stack});process.exitCode=1;});
