import os
from pathlib import Path
import sys,json,re,copy,base64
from lxml import html
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'compatibility'))
from docker import Renderer
from publication.cli import CLI
out=Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(root.parent/'docker-baseline/c4')))/'cli';out.mkdir(parents=True,exist_ok=True)
r=Renderer(root/'.cache/docker-renderer',root/'authored',root/'data/refs.json',root/'compatibility/assets');records=json.loads((root/'data/cli-registry.json').read_text());cli=CLI(r,records);results=[]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
def visible(e):
 e=copy.deepcopy(e)
 for v in e.iter():
  if v.tag in ['p','div','li','br','h1','h2','h3','h4','h5','h6','tr','td','th','pre','dt','dd']:v.text=' '+(v.text or '');v.tail=' '+(v.tail or '')
 return norm(e.text_content())
def props(e):
 return {'headings':[(v.tag,v.get('id'),norm(v.text_content())) for v in e.xpath('.//h2|.//h3|.//h4|.//h5|.//h6')], 'tables':[[[visible(c) for c in row.xpath('./td|./th')] for row in t.xpath('.//tr')] for t in e.xpath('.//table')], 'copies':[base64.b64decode(re.search("code: '([^']*)'",v.get('x-data')).group(1)).decode() for v in e.xpath('.//button[@title="copy"]')], 'tokens':[[(v.get('class'),v.text_content()) for v in code.xpath('.//span[not(span)]')] for code in e.xpath('.//div[@class="highlight"]//code')], 'links':[(v.get('href'),norm(v.text_content())) for v in e.xpath('.//a')], 'text':visible(e)}
for record in records:
 try:
  value=cli.render(record);target=out/record['route'].strip('/')/'body.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value)
  actual=props(html.fragment_fromstring(value.replace(chr(27),''),create_parent='div'));article=html.fromstring((root.parent/'docker-baseline/site'/record['route'].strip('/')/'index.html').read_text().replace(chr(27),'')).xpath('//article')[0];expected=html.Element('div');start=False
  for child in article:
   if child.tag=='div' and child.get('class')=='overflow-x-auto':start=True
   if start:expected.append(copy.deepcopy(child))
  expected=props(expected);checks={k:actual[k]==expected[k] for k in actual};res={'record':record,'checks':checks}
  if not all(checks.values()):res.update(actual=actual,expected=expected)
  results.append(res)
 except Exception as e:results.append({'record':record,'error':repr(e)})
r.close();(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
from collections import Counter
print('pages',len(results),'errors',sum('error' in v for v in results));print(Counter(k for v in results for k,ok in v.get('checks',{}).items() if not ok));print([(v['record']['route'],v['error']) for v in results if 'error' in v][:10])

assert results and all('error' not in v and all(v['checks'].values()) for v in results), 'Real-corpus parity failed'
