import fs from 'node:fs';
import {createRequire} from 'node:module';
import crypto from 'node:crypto';
const require=createRequire(process.env.PLAYWRIGHT_MODULE_ROOT+'/package.json');
const {chromium}=require('playwright');
const origin=process.env.REFERENCE_ORIGIN||'http://127.0.0.1:4180';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH});
const results=[];
for(const width of [1440,390]) {
 const context=await browser.newContext({viewport:{width,height:900},permissions:['clipboard-read','clipboard-write'],colorScheme:'light'});
 context.setDefaultTimeout(5000);
 await context.addInitScript(()=>localStorage.setItem('theme-preference','light'));
 const external=[];
 await context.route('**/*',async r=>{
  const u=new URL(r.request().url());
  if(u.origin===origin)return r.continue();
  if(u.hostname==='docs.docker.com')return r.fulfill({response:await r.fetch({url:origin+u.pathname+u.search})});
  external.push({host:u.hostname,path:u.pathname,method:r.request().method()});
  if(r.request().resourceType()==='script')return r.fulfill({status:200,contentType:'text/javascript',body:''});
  return r.abort();
 });
 const page=await context.newPage();
 const record={width,checks:{},external};
 const check=async(name,fn)=>{try{record.checks[name]=await fn();}catch(e){record.checks[name]={error:e.message.split('\n')[0]};}};
 await page.goto(origin+'/engine/install/ubuntu/',{waitUntil:'networkidle'});
 await check('theme-cycle-and-system-change',async()=>{
  const states=[];
  for(let i=0;i<3;i++){
   states.push(await page.evaluate(()=>({theme:document.documentElement.className,preference:localStorage.getItem('theme-preference')})));
   if(i<2){await page.locator('#theme-switch').focus();await page.keyboard.press('Enter');}
  }
  await page.emulateMedia({colorScheme:'dark'});await page.waitForTimeout(100);
  return {states,systemDark:await page.evaluate(()=>document.documentElement.className)};
 });
 await check('gordon-open-escape-focus',async()=>{
  await page.getByRole('button',{name:'Ask Gordon, AI assistant',exact:true}).click();await page.waitForTimeout(100);
  const opened=await page.evaluate(()=>({open:Alpine.store('gordon').isOpen,focus:document.activeElement.tagName}));
  await page.keyboard.press('Escape');
  return {opened,closed:await page.evaluate(()=>!Alpine.store('gordon').isOpen)};
 });
 await check('markdown-view',async()=>{
  const button=page.getByRole('button',{name:'View Markdown',exact:true});
  if(!await button.count())return {applicable:false};
  const popupPromise=context.waitForEvent('page');await button.click();const popup=await popupPromise;
  await popup.waitForLoadState();
  const response=await context.request.get(origin+'/engine/install/ubuntu.md');
  const bytes=await response.body();await popup.close();
  return {url:popup.url(),status:response.status(),bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
 });
 await page.goto(origin+'/reference/api/ai-governance/latest/',{waitUntil:'networkidle'});
 await check('api-filter',async()=>{
  const rows=page.locator('[data-api-filter-item]');const total=await rows.count();
  await page.locator('[data-api-filter]').fill('Create policy');
  return {total,visible:await rows.evaluateAll(es=>es.filter(e=>!e.hidden).map(e=>e.textContent.trim()))};
 });
 await page.goto(origin+'/reference/api/ai-governance/latest/operations/createPolicy/',{waitUntil:'networkidle'});
 await check('api-copy',async()=>{
  const button=page.locator('[data-api-copy]').first();await button.click();
  const text=await page.evaluate(()=>navigator.clipboard.readText());
  return {label:await button.textContent(),bytes:text.length,sha256:crypto.createHash('sha256').update(text).digest('hex')};
 });
 await check('api-example-media-controls',async()=>{
  const out=[];
  for(const selector of ['[data-api-example-select]','[data-api-media-select]']){
   const selects=page.locator(selector);
   for(let i=0;i<await selects.count();i++){
    const select=selects.nth(i),options=await select.locator('option').evaluateAll(es=>es.map(e=>e.value));
    if(options.length>1)await select.selectOption(options[1]);out.push({selector,options,value:await select.inputValue()});
   }
  }
  return out;
 });
 results.push(record);await context.close();
}
await browser.close();
fs.writeFileSync(process.argv[2],JSON.stringify({browser:browser.version(),results},null,2));
