import os
from pathlib import Path
import sys,json,re,time
from lxml import html
from copy import deepcopy
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'compatibility'));sys.path.insert(0,str(root))
from docker import Renderer
from publication.api import API
out=Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(root.parent/'docker-baseline/c4')))/'api';out.mkdir(parents=True,exist_ok=True);r=Renderer(root/'.cache/docker-renderer',root/'authored',root/'data/refs.json',root/'compatibility/assets');model=json.loads((root/'authored/data/api-reference.json').read_text());registry=json.loads((root/'data/source-registry.json').read_text());a=API(model,r,registry);results=[]
records=[{'route':'/reference/api/','logical':'reference/api/_index.md','title':'Docker APIs','view':'catalog'}]
for v in model['apis']:
 records.append({'route':v['url'],'logical':'reference/api/'+v['id']+'/latest/_index.md','title':v['title']+' API '+v['version'],'view':'overview','api_id':v['id']})
 for op in v['operations']:records.append({'route':op['url'],'logical':'reference/api/'+v['id']+'/latest/operations/'+op['id']+'.md','title':op['summary'],'view':'operation','api_id':v['id'],'operation_id':op['id']})
 for s in v['schemas']:records.append({'route':s['url'],'logical':'reference/api/'+v['id']+'/latest/schemas/'+s['name']+'.md','title':s['name'],'view':'schema','api_id':v['id'],'schema_name':s['name']})
norm=lambda v:re.sub(r'\s+',' ',v).strip()
def visible(p):
 p=deepcopy(p)
 for e in p.iter():
  if e.tag in ['p','div','li','br','h1','h2','h3','h4','h5','h6','tr','td','th','pre','dt','dd','summary','section']:e.text=' '+(e.text or '');e.tail=' '+(e.tail or '')
 return norm(p.text_content())
def properties(p):
 return {'headings':[(e.tag,e.get('id'),norm(e.text_content())) for e in p.xpath('.//*[self::h1 or self::h2 or self::h3 or self::h4]')],'code':[''.join(e.itertext()) for e in p.xpath('.//pre/code')],'hrefs':[e.get('href') for e in p.xpath('.//a')],'controls':[(e.tag,sorted((k,norm(v) if k in ['@click',':class','class'] else v) for k,v in e.attrib.items()),norm(e.text_content())) for e in p.xpath('.//select|.//input|.//button')],'text':visible(p)}
for rec in records:
 try:
  rendered=a.render(rec);file=out/rec['route'].strip('/')/'body.html';file.parent.mkdir(parents=True,exist_ok=True);file.write_text(rendered)
  actual=properties(html.fromstring(rendered));expected=properties(html.parse(str(root.parent/'docker-baseline/site'/rec['route'].strip('/')/'index.html')).xpath('//article[@class="api-reference"]')[0]);checks={k:actual[k]==expected[k] for k in actual};result={'record':rec,'checks':checks}
  if not all(checks.values()):result.update(actual=actual,expected=expected)
  results.append(result)
 except Exception as e:results.append({'record':rec,'error':str(e)})
r.close();(out/'results.json').write_text(json.dumps(results,indent=2)+'\n');print('pages',len(records),'errors',sum('error' in v for v in results));from collections import Counter;print(Counter(k for v in results for k,ok in v.get('checks',{}).items() if not ok));print([(v['record']['route'],v['error']) for v in results if 'error' in v][:10])

assert results and all('error' not in v and all(v['checks'].values()) for v in results), 'Real-corpus parity failed'
