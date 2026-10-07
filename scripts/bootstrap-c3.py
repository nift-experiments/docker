#!/usr/bin/env python3
"""One-time corpus migration; normal builds read only maintained project inputs."""
from pathlib import Path
import sys,json,shutil
from urllib.parse import urlparse
from lxml import html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'))
from docker import source_routes
from extract_stream import extract_stream
U=ROOT.parent/'docker-upstream';SITE=ROOT.parent/'docker-baseline/site'
refs,records=source_routes(U,SITE)
# Docker's generated landing/sample families are reconstructed at C4. Ordinary
# authored guide/docs pages and leaf bundles belong to this corpus checkpoint.
selected={logical:v for logical,v in records.items() if Path(logical).name!='_index.md' and not logical.startswith('reference/samples/') and v['frontmatter'].get('build',{}).get('render')!='never' and v['frontmatter'].get('layout')!='glossary'}
fixtures={v['route'].strip('/')+'/index':SITE/v['route'].strip('/')/'index.html' for v in selected.values()}
extracted,evidence=extract_stream(fixtures,ROOT)
for repo,assets in [('docker','static'),('docker-agent','public-assets')]:
 p=ROOT.parent/repo
 if repo=='docker':
  shutil.copytree(U/'content',p/'authored/content',dirs_exist_ok=True)
  for logical,v in records.items():
   src=Path(v['physical']);dest=p/'authored'/src.relative_to(U);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  shutil.copytree(U/'data',p/'authored/data',dirs_exist_ok=True)
  (p/'data/refs.json').write_text(json.dumps(refs,indent=2)+'\n')
  registry={logical:{'route':v['route'],'index':v['index'],'source':'authored/'+Path(v['physical']).relative_to(U).as_posix(),'frontmatter':v['frontmatter']} for logical,v in records.items()}
  (p/'data/source-registry.json').write_text(json.dumps(registry,indent=2,default=str)+'\n')
 else:
  # Shared chrome stays exactly deduplicated; maintained bodies remain HTML.
  for file in (ROOT/'layouts').rglob('*.html'):
   dest=p/file.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
 manifest=json.loads((p/'data/composition.json').read_text());pages={v['route']:v for v in manifest['pages']}
 for logical,v in selected.items():
  name=v['route'].strip('/')+'/index';info=extracted[name]
  rec={'name':name,'route':v['route'],'title':v['frontmatter'].get('title',''),'pieces':info['pieces']}
  if repo=='docker':rec.update(model='markdown',logical=logical,index=v['index'],source=registry[logical]['source'],body='.generated/bodies/'+name+'.html')
  else:
   rec.update(model='maintained-html',body='pages/'+name+'.html');dest=p/rec['body'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(info['body'])
  pages[v['route']]=rec
  doc=html.parse(str(fixtures[name]))
  for e in doc.xpath('//*[@src] | //link[@href]'):
   url=urlparse(e.get('src') or e.get('href'))
   if url.hostname and url.hostname!='docs.docker.com':continue
   source=SITE/url.path.lstrip('/')
   if source.is_file():
    dest=p/assets/source.relative_to(SITE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
 manifest['pages']=list(pages.values());manifest['checkpoint']='C3 ordinary corpus, C2 generated-family prototypes pending C4'
 (p/'data/composition.json').write_text(json.dumps(manifest,indent=2)+'\n');(p/'data/shell-extraction-c3.json').write_text(json.dumps(evidence,indent=2)+'\n')
 (p/'.nift/tracked.json').write_text(json.dumps({'tracked':[{'name':v['name'],'title':v['title'],'template':'templates/template.html'} for v in manifest['pages']]},indent=2)+'\n')
 print(repo,len(manifest['pages']),'tracked pages',evidence,flush=True)
