import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';

const require = createRequire(process.env.PLAYWRIGHT_MODULE_ROOT + '/package.json');
const {chromium} = require('playwright');
const origin = process.env.REFERENCE_ORIGIN || 'http://127.0.0.1:4180';
const output = path.resolve(process.argv[2]);
fs.mkdirSync(output, {recursive:true});
const fixtures = [
  ['home','/'],['section','/engine/install/'],['standard-doc','/engine/install/ubuntu/'],
  ['get-started','/get-started/'],['guide-landing','/guides/'],['guide','/guides/nodejs/'],
  ['learning-series','/get-started/docker-concepts/building-images/'],
  ['cli','/reference/cli/docker/container/run/'],['api-catalog','/reference/api/'],
  ['api-overview','/reference/api/ai-governance/latest/'],
  ['api-operation','/reference/api/ai-governance/latest/operations/createPolicy/'],['glossary','/reference/glossary/'],
  ['api-schema','/reference/api/ai-governance/latest/schemas/CreatePolicyRequest/'],['legacy-api','/reference/api/engine/version/v1.56/'],
  ['samples','/reference/samples/react/'],['wide','/reference/'],['hidden','/bot-detection/'],
  ['tabs','/desktop/setup/install/linux/'],['accordion','/compose/intro/compose-application-model/'],
  ['mermaid','/ai/sandboxes/governance/access-controls/mcp/'],['diagram','/ai/sandboxes/architecture/'],
  ['topology','/ai/sandboxes/security/'],['redirect','/glossary/'],['404','/missing-parity-fixture/'],
];
const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH,headless:true});
const records = [];
const allExternal=[];
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const snapshot = page => page.evaluate(() => ({
  title:document.title,url:location.pathname,theme:document.documentElement.className,
  themePreference:document.documentElement.dataset.themePreference,
  viewport:[innerWidth,innerHeight],bodySize:[document.body.scrollWidth,document.body.scrollHeight],
  headings:[...document.querySelectorAll('h1,h2,h3')].map(e=>[e.tagName,e.id,e.textContent.trim()]),
  currentNavigation:[...document.querySelectorAll('[aria-current]')].map(e=>[e.getAttribute('href'),e.getAttribute('aria-current')]),
  tabs:[...document.querySelectorAll('.tabs')].map(e=>({labels:[...e.querySelectorAll('.tab-item')].map(b=>b.textContent.trim()),visiblePanels:[...e.querySelectorAll('[aria-role="tab"]')].filter(b=>getComputedStyle(b).display!=='none').length})),
  accordions:document.querySelectorAll('[x-collapse]').length,
  diagrams:[...document.querySelectorAll('[data-interactive-diagram]')].map(e=>({type:e.dataset.diagramType,rendered:!!e.querySelector('[data-diagram-stage] svg')})),
  mermaid:document.querySelectorAll('pre.mermaid svg').length,
  activeElement:document.activeElement?.outerHTML.slice(0,400),
  apiView:document.querySelector('[data-api-view]')?.dataset.apiView,
}));

for (const [width,height] of [[1440,900],[390,844]]) {
  for (const [mode,scheme] of (process.env.ONLY_BEHAVIORS ? [['light','light']] : [['light','light'],['dark','dark'],['system-light','light'],['system-dark','dark']])) {
    const context=await browser.newContext({viewport:{width,height},colorScheme:scheme,deviceScaleFactor:1,reducedMotion:'reduce',permissions:['clipboard-read','clipboard-write']});
    context.setDefaultTimeout(5000);
    const external=[];
    await context.route('**/*',async route=>{
      const url=new URL(route.request().url());
      if (url.origin===origin) return route.continue();
      if (url.hostname==='docs.docker.com') {
        const response=await route.fetch({url:origin+url.pathname+url.search});
        return route.fulfill({response});
      }
      const request={host:url.hostname,path:url.pathname,method:route.request().method()};
      external.push(request);allExternal.push(request);
      // No remote telemetry or AI requests. Remote scripts are inert fixtures.
      if (route.request().resourceType()==='script') return route.fulfill({status:200,contentType:'text/javascript',body:''});
      return route.abort('blockedbyclient');
    });
    await context.addInitScript(({mode})=>{
      if (mode.startsWith('system')) localStorage.removeItem('theme-preference');
      else localStorage.setItem('theme-preference',mode);
      // Stabilize time-dependent analytics bootstrapping; no requests reach services.
      window.__parityFixture=true;
    },{mode});
    for (const [family,route] of fixtures.filter(([family])=>(!process.env.FIXTURES || process.env.FIXTURES.split(',').includes(family)) && (!process.env.ONLY_BEHAVIORS || ['standard-doc','tabs','accordion','diagram','topology','cli'].includes(family)))) {
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',error=>errors.push(error.message));
      const response=await page.goto(origin+route,{waitUntil:'networkidle'});
      await page.evaluate(()=>document.fonts.ready);
      await page.waitForTimeout(150);
      const record={family,route,width,height,mode,status:response.status(),initial:await snapshot(page),errors,externalBoundary:'remote scripts inert; remote non-script requests blocked'};
      const name=`${family}-${width}-${mode}`;
      const image=await page.screenshot({type:'jpeg',quality:82,animations:'disabled'});
      fs.writeFileSync(path.join(output,name+'.jpg'),image);
      record.screenshot={file:name+'.jpg',sha256:sha(image)};
      // Detailed behavior runs on both viewport sizes in explicit light mode.
      if (mode==='light' && ['standard-doc','tabs','accordion','diagram','topology','cli'].includes(family)) {
        record.behaviors={};
        const attempt=async(name,fn)=>{
          try {record.behaviors[name]=await fn();}
          catch(error){record.behaviors[name]={error:error.message.split('\n')[0]};}
        };
        await attempt('search-keyboard',async()=>{
          await page.keyboard.press('Control+k');
          await page.waitForTimeout(100);
          const before=await page.evaluate(()=>({open:document.querySelector('pagefind-modal dialog')?.open,focus:document.activeElement?.tagName,input:!!document.querySelector('pagefind-modal input')}));
          const input=page.locator('pagefind-modal input').first();
          await input.fill('container');
          await page.locator('pagefind-results a[href]').first().waitFor({state:'visible'});
          const results=await page.locator('pagefind-results a[href]').count();
          const focus=await page.evaluate(()=>document.activeElement?.outerHTML.slice(0,300));
          await page.keyboard.press('Escape');
          return {before,results,focus,after:await page.evaluate(()=>document.activeElement?.id)};
        });
        if (width<768 && family!=='home') await attempt('mobile-sidebar',async()=>{
          await page.getByRole('button',{name:'Menu',exact:true}).click();
          const opened=await page.evaluate(()=>window.Alpine.store('showSidebar'));
          await page.getByRole('button',{name:'Back',exact:true}).click();
          return {opened,closed:await page.evaluate(()=>window.Alpine.store('showSidebar'))};
        });
        await attempt('tabs',async()=>{
          const group=page.locator('.tabs').first();
          if (!await group.count()) return {applicable:false};
          const buttons=group.locator('.tab-item');
          if(await buttons.count()<2)return {applicable:false};
          await buttons.nth(1).click();
          return await group.evaluate(e=>({selected:window.Alpine.$data(e).selected,visible:[...e.querySelectorAll('[aria-role="tab"]')].filter(p=>getComputedStyle(p).display!=='none').map(p=>p.textContent.trim().slice(0,120))}));
        });
        await attempt('accordion',async()=>{
          const panel=page.locator('[x-collapse]').first();
          if (!await panel.count())return {applicable:false};
          const before=await panel.isVisible();
          await panel.locator('..').locator('button').first().click();
          await page.waitForTimeout(300);
          return {before,after:await panel.isVisible()};
        });
        await attempt('copy-markdown',async()=>{
          const button=page.getByRole('button',{name:'Copy Markdown',exact:true}).first();
          if(!await button.count())return {applicable:false};
          await button.click();await page.waitForTimeout(100);
          const text=await page.evaluate(()=>navigator.clipboard.readText());
          return {length:text.length,sha256:sha(text),export:await page.locator('link[type="text/markdown"]').getAttribute('href')};
        });
        await attempt('code-copy',async()=>{
          const candidate=page.locator('button[x-on\\:click*="clipboard"], button[\\@click*="clipboard"]').first();
          if(!await candidate.count())return {applicable:false};
          await candidate.locator('..').hover();
          await candidate.click();await page.waitForTimeout(100);
          const text=await page.evaluate(()=>navigator.clipboard.readText());
          return {length:text.length,sha256:sha(text)};
        });
        await attempt('diagram-keyboard',async()=>{
          const next=page.locator('[data-step-next]').first();
          if(!await next.count())return {applicable:false};
          const before=await page.locator('[data-step-number]').first().textContent();
          await next.focus();await page.keyboard.press('Enter');
          return {before,after:await page.locator('[data-step-number]').first().textContent()};
        });
        record.after=await snapshot(page);
      }
      records.push(record);
      fs.writeFileSync(path.join(output,'observations.json'),JSON.stringify({browser:browser.version(),fixtures,records,externalRequests:allExternal},null,2));
      await page.close();
      console.log(name,response.status(),errors.length);
    }
    await context.close();
  }
}
await browser.close();
