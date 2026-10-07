from pathlib import Path
import sys,json,re
from lxml import html
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1];records=[v for v in json.loads((root/'data/composition.json').read_text())['pages'] if v.get('kind')!='auxiliary'];results=[]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
BLOCK={'p','div','li','br','h1','h2','h3','h4','h5','h6','tr','td','th','pre','dt','dd','section','time','article','nav','aside'}
def text(e):
 out=[]
 def walk(v):
  if not isinstance(v.tag,str) or v.tag in ['script','style']:
   if v.tail:out.append(v.tail)
   return
  if v.tag in BLOCK:out.append(' ')
  if v.text:out.append(v.text)
  for child in v:walk(child)
  if v.tag in BLOCK:out.append(' ')
  if v.tail:out.append(v.tail)
 walk(e);return norm(''.join(out))
def props(file):
 p=html.fromstring(file.read_text().replace(chr(27),''));main=p.xpath('//main')[0]
 return {'text':text(main),'headings':[(v.tag,v.get('id'),norm(v.text_content())) for v in main.xpath('.//h1|.//h2|.//h3|.//h4|.//h5|.//h6')],'links':[(v.get('href'),text(v)) for v in main.xpath('.//a')],'images':[(v.get('src'),v.get('alt')) for v in main.xpath('.//img')]}
for rec in records:
 try:
  a=props(root/'public'/rec['route'].strip('/')/'index.html');b=props(root.parent/'docker-baseline/site'/rec['route'].strip('/')/'index.html');checks={k:a[k]==b[k] for k in a};v={'route':rec['route'],'model':rec['model'],'checks':checks}
  if not all(checks.values()):v.update(actual=a,expected=b)
  results.append(v)
 except Exception as e:results.append({'route':rec['route'],'error':repr(e)})
path=root.parent/'docker-baseline/c4'/('content-'+root.name+'.json');path.write_text(json.dumps(results,indent=2)+'\n')
from collections import Counter
print('pages',len(results),'errors',sum('error' in v for v in results));print(Counter(k for v in results for k,b in v.get('checks',{}).items() if not b));print([(v['route'],v['error']) for v in results if 'error' in v][:3]);print([(v['route'],[k for k,b in v.get('checks',{}).items() if not b]) for v in results if v.get('checks') and not all(v['checks'].values())][:30])
