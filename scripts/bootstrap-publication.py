#!/usr/bin/env python3
"""Migrate asset ownership and structured publication records from the pin."""
from pathlib import Path
import sys,json,gzip,shutil,re,xml.etree.ElementTree as ET
from lxml import html
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT.parent/'docker-baseline/site';sys.path.insert(0,str(ROOT/'compatibility'))
from extract_stream import extract_stream
inventory=json.loads((ROOT/'investigation/inventory/files.json').read_text());page_inventory=json.loads(gzip.open(ROOT/'investigation/inventory/pages.json.gz','rt').read());composition=json.loads((ROOT/'data/composition.json').read_text());byroute={v['route']:v for v in composition['pages']};metadata=json.loads((SITE/'metadata.json').read_text());sitemap=ET.parse(SITE/'sitemap.xml');NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'};urls=[]
for u in sitemap.getroot():urls.append({e.tag.rsplit('}',1)[-1]:e.text for e in u})
model={'site_title':'Docker Docs','base_url':'https://docs.docker.com','metadata':metadata,'sitemap':urls,'pages':{},'aliases':[],'rss_build_date':ET.parse(SITE/'security/security-announcements/index.xml').findtext('channel/lastBuildDate')}
for p in page_inventory:
 if p['route'] not in byroute:continue
 md=next(e['href'] for e in p['links'] if e.get('type')=='text/markdown');tech=next((v for v in p['json_ld'] if isinstance(v,dict) and v.get('@type')=='TechArticle'),{})
 model['pages'][p['route']]={'title':tech.get('headline',byroute[p['route']]['title']),'markdown':md,'meta':p['meta'],'schema':p['json_ld'],'source':byroute[p['route']].get('logical')}
 if byroute[p['route']]['model']=='landing' or byroute[p['route']]['family']=='glossary':model['pages'][p['route']]['export']='header-only'
for p in page_inventory:
 if p['route'] in byroute or p['file'] in ['404.html','google161104f9fdea6089.html','googlecbe7fee896be512c.html']:continue
 doc=html.parse(str(SITE/p['file']));refresh=doc.xpath('//meta[translate(@http-equiv,"REFSH","refsh")="refresh"]')
 if refresh:model['aliases'].append({'route':p['route'],'target':doc.xpath('//link[@rel="canonical"]/@href')[0]})
assert len(model['aliases'])==1728
# 404 shares the same raw composition primitive, using owned HTML for its fixed
# explanatory text. Verification files are maintained static HTML.
extra,evidence=extract_stream({'404':SITE/'404.html'},ROOT)
for repo,assets in [('docker','static'),('docker-agent','public-assets')]:
 dest=ROOT.parent/repo;owned=dest/assets
 for entry in inventory:
  path=entry['path']
  if path.endswith(('.html','.md','.xml')) or path.startswith('pagefind/') or path in ['metadata.json','redirects.json','llms.txt','llms-full.txt','robots.txt']:continue
  target=owned/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SITE/path,target)
 # Retire frozen search/Markdown fixtures; builders own these outputs now.
 for path in list(owned.rglob('*.md')):path.unlink()
 if (owned/'pagefind').exists():shutil.rmtree(owned/'pagefind')
 for key in ['metadata.json','redirects.json','llms.txt','llms-full.txt','robots.txt','sitemap.xml','security/security-announcements/index.xml']:
  p=owned/key
  if p.exists():p.unlink()
 if repo=='docker-agent':
  for file in (ROOT/'layouts/pages/404').glob('*.html'):
   target=dest/file.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
 body='pages/404.html' if repo=='docker-agent' else 'publication/templates/404.html';target=dest/body;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(extra['404']['body'])
 manifest=json.loads((dest/'data/composition.json').read_text());manifest['pages']=[v for v in manifest['pages'] if v.get('kind')!='auxiliary'];manifest['pages'].append({'name':'404','route':'/404.html','title':'404 Page not found','model':'maintained-html','kind':'auxiliary','family':'404','body':body,'pieces':extra['404']['pieces']})
 for name in ['google161104f9fdea6089','googlecbe7fee896be512c']:
  target=dest/'pages'/(name+'.html');target.parent.mkdir(exist_ok=True);shutil.copy2(SITE/(name+'.html'),target);manifest['pages'].append({'name':name,'route':'/'+name+'.html','title':'','model':'maintained-html','kind':'auxiliary','family':'verification','body':'pages/'+name+'.html','pieces':[None]})
 for alias in model['aliases']:
  name=alias['route'].strip('/')+'/index';record={'name':name,'route':alias['route'],'title':alias['target'],'model':'redirect','kind':'auxiliary','family':'redirect','target':alias['target'],'body':'.generated/redirects/'+name+'.html','pieces':[None]}
  if repo=='docker-agent':
   record.update(model='maintained-html',body='pages/'+name+'.html');target=dest/record['body'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SITE/name.replace('/index','/index.html'),target)
  manifest['pages'].append(record)
 (dest/'data/composition.json').write_text(json.dumps(manifest,indent=2)+'\n');(dest/'data/publication.json').write_text(json.dumps(model,indent=2)+'\n');(dest/'data/redirects-base.json').write_text((SITE/'redirects.json').read_text())
 (dest/'.nift/tracked.json').write_text(json.dumps({'tracked':[{'name':v['name'],'title':v['title'],'template':'templates/template.html'} for v in manifest['pages']]},indent=2)+'\n')
 for name in ['llms.txt','llms-full.txt']:
  target=dest/'publication/templates'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SITE/name,target)
 print(repo,len(manifest['pages']),'tracked HTML routes; assets',sum(v.is_file() for v in owned.rglob('*')),flush=True)
