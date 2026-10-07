#!/usr/bin/env python3
"""One-time full route/family migration; never invoked by routine builds."""
from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'))
from extract import Spans,frame
from extract_stream import extract_stream
SITE=ROOT.parent/'docker-baseline/site';registry=json.loads((ROOT/'data/source-registry.json').read_text());pages={}
for logical,v in registry.items():
 if v['frontmatter'].get('build',{}).get('render')=='never':continue
 route=v['route'];kind='home' if route=='/' else ('get-started' if route=='/get-started/' else ('guides' if route=='/guides/' else ('samples' if logical.startswith('reference/samples/') and not v['index'] else v['frontmatter'].get('layout'))))
 legacy='<redoc ' in (SITE/route.strip('/')/'index.html').read_text()
 model='landing' if kind in ['home','get-started','guides'] else ('special' if kind in ['samples','glossary','series'] else ('legacy-api' if legacy else 'markdown'))
 pages[route]={'route':route,'title':v['frontmatter'].get('title',''),'logical':logical,'index':v['index'],'source':v['source'],'model':model,'family':kind or 'ordinary'}
for v in json.loads((ROOT/'data/cli-registry.json').read_text()):pages[v['route']]={**v,'index':v['section'],'model':'cli','family':v['family']}
api=json.loads((ROOT/'authored/data/api-reference.json').read_text());generated=[{'route':'/reference/api/','logical':'reference/api/_index.md','title':'Docker APIs','view':'catalog'}]
for a in api['apis']:
 generated.append({'route':a['url'],'logical':'reference/api/'+a['id']+'/latest/_index.md','title':a['title']+' API '+a['version'],'view':'overview','api_id':a['id']})
 for op in a['operations']:generated.append({'route':op['url'],'logical':'reference/api/'+a['id']+'/latest/operations/'+op['id']+'.md','title':op['summary'],'view':'operation','api_id':a['id'],'operation_id':op['id']})
 for s in a['schemas']:generated.append({'route':s['url'],'logical':'reference/api/'+a['id']+'/latest/schemas/'+s['name']+'.md','title':s['name'],'view':'schema','api_id':a['id'],'schema_name':s['name']})
for v in generated:pages[v['route']]={**v,'model':'api','family':'api','index':True,'source':'authored/data/api-reference.json'}
assert len(pages)==2170,len(pages)
for v in pages.values():v['name']=(v['route'].strip('/')+'/index').lstrip('/');v['body']='.generated/bodies/'+v['name']+'.html'
# Ordinary frames already recovered at C3 remain valid. Only missing/family
# prototype frames are extracted; frame() deliberately excludes authored body.
existing=json.loads((ROOT/'data/composition.json').read_text());old={v['route']:v for v in existing['pages']}
new={v['name']:SITE/v['route'].strip('/')/'index.html' for v in pages.values() if v['route'] not in old or v['model']!='markdown'};byname={v['name']:v for v in pages.values()}
def span(source,name):
 rec=byname[name];nodes=Spans(source).nodes;model=rec['model'];kind=rec['family']
 if model=='cli':
  article=next(n for n in nodes if n.tag=='article');start=next(n for n in article.children if n.attrs.get('class')=='overflow-x-auto').start;return nodes,start,article.close_start
 if model=='api':
  article=next(n for n in nodes if n.tag=='article' and n.attrs.get('class')=='api-reference');return nodes,article.start,article.end
 if model=='special' and kind in ['samples','glossary']:
  article=next(n for n in nodes if n.tag=='article');return nodes,next(n for n in article.children if n.tag=='h1').end,article.close_start
 if model=='landing' and kind=='get-started':
  article=next(n for n in nodes if n.tag=='article');return nodes,next(n for n in article.children if n.tag=='header').start,article.close_start
 return frame(source)
extracted,evidence=extract_stream(new,ROOT,span)
for repo,assets in [('docker','static'),('docker-agent','public-assets')]:
 dest=ROOT.parent/repo
 if repo=='docker-agent':
  for file in (ROOT/'layouts').rglob('*.html'):
   target=dest/file.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,target)
 records=[]
 for route,original in pages.items():
  rec=dict(original);info=extracted.get(rec['name']);rec['pieces']=info['pieces'] if info else old[route]['pieces']
  if repo=='docker-agent':
   rec={k:v for k,v in rec.items() if k not in ['source','logical','index','view','api_id','operation_id','schema_name','section']};rec.update(model='maintained-html',body='pages/'+rec['name']+'.html')
   if info:target=dest/rec['body'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(info['body'])
  records.append(rec)
 manifest={'pages':records,'checkpoint':'C4 full content routes; ancillary pipeline integration in progress'};(dest/'data/composition.json').write_text(json.dumps(manifest,indent=2)+'\n');(dest/'data/shell-extraction-c4.json').write_text(json.dumps(evidence,indent=2)+'\n');(dest/'.nift/tracked.json').write_text(json.dumps({'tracked':[{'name':v['name'],'title':v['title'],'template':'templates/template.html'} for v in records]},indent=2)+'\n')
 print(repo,len(records),'tracked content routes',flush=True)
