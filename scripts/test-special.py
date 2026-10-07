#!/usr/bin/env python3
import os
from pathlib import Path
import sys,json,re,copy
from lxml import html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'compatibility'))
from docker import Renderer,read_markdown
from extract import Spans,frame
from publication.special import Special
r=Renderer(ROOT/'.cache/docker-renderer',ROOT/'authored',ROOT/'data/refs.json',ROOT/'compatibility/assets');registry=json.loads((ROOT/'data/source-registry.json').read_text());special=Special(r,registry);OUT=Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(ROOT.parent/'docker-baseline/c4')))/'special';OUT.mkdir(parents=True,exist_ok=True);results=[]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
def visible(e):
 e=copy.deepcopy(e)
 for v in e.iter():
  if v.tag in ['p','div','li','br','h1','h2','h3','h4','h5','h6','tr','td','th','pre','dt','dd','section','time']:v.text=' '+(v.text or '');v.tail=' '+(v.tail or '')
 return norm(e.text_content())
def props(e):return {'headings':[(v.tag,v.get('id'),norm(v.text_content())) for v in e.xpath('.//h1|.//h2|.//h3|.//h4')],'links':[(v.get('href'),norm(v.text_content())) for v in e.xpath('.//a')],'text':visible(e),'guides':[(v.get('data-search'),visible(v)) for v in e.xpath('.//*[@data-guide]')]}
for logical,v in registry.items():
 kind='home' if v['route']=='/' else ('get-started' if v['route']=='/get-started/' else ('guides' if v['route']=='/guides/' else ('samples' if logical.startswith('reference/samples/') and not v['index'] else v['frontmatter'].get('layout'))))
 if kind not in ['home','get-started','guides','samples','glossary','series']:continue
 try:
  front,text=read_markdown(ROOT/v['source']);c=dict(v,logical=logical,frontmatter=front,records=registry);rendered=special.landing(kind,c) if kind in ['home','get-started','guides'] else special.render(kind,text,c)
  source=(ROOT.parent/'docker-baseline/site'/v['route'].strip('/')/'index.html').read_text();nodes=Spans(source).nodes
  if kind in ['home','guides']:n=next(n for n in nodes if n.tag=='main');start=n.open_end;end=n.close_start
  elif kind=='get-started':n=next(n for n in nodes if n.tag=='article');start=next(n for n in n.children if n.tag=='header').start;end=n.close_start
  elif kind in ['samples','glossary']:n=next(n for n in nodes if n.tag=='article');start=next(n for n in n.children if n.tag=='h1').end;end=n.close_start
  else:nodes,start,end=frame(source)
  expected=source[start:end];actual=props(html.fragment_fromstring(rendered,create_parent='div'));expected=props(html.fragment_fromstring(expected,create_parent='div'));checks={k:actual[k]==expected[k] for k in actual};rec={'route':v['route'],'kind':kind,'checks':checks}
  if not all(checks.values()):rec.update(actual=actual,expected=expected)
  results.append(rec);path=OUT/v['route'].strip('/')/'body.html';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(rendered)
 except Exception as e:results.append({'route':v['route'],'kind':kind,'error':repr(e)})
r.close();(OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n');print('pages',len(results));print([(v['route'],v.get('error') or [k for k,ok in v['checks'].items() if not ok]) for v in results if v.get('error') or not all(v['checks'].values())])

assert results and all('error' not in v and all(v['checks'].values()) for v in results), 'Real-corpus parity failed'
