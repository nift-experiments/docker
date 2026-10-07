#!/usr/bin/env python3
"""Recover the observed Docker navigation tree, with explicit source bindings."""
from pathlib import Path
from collections import defaultdict
import json,html as H,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"compatibility"))
from docker import read_markdown
from lxml import html
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT.parent/'docker-baseline/site';registry=json.loads((ROOT/'data/source-registry.json').read_text());publication=json.loads((ROOT/'data/publication.json').read_text());manifest=json.loads((ROOT/'data/composition.json').read_text());byroute=defaultdict(list);bylabel=defaultdict(list)
def params(v):return {**v,**v.get('params',{})}
for key,v in registry.items():
 byroute[v['route']].append(key);f=params(v['frontmatter']);bylabel[f.get('linkTitle',f.get('title',''))].append(key)
# Eight render-never section indexes still govern navigation visibility.
for file in (ROOT/'authored/content').rglob('_index.md'):
 logical=file.relative_to(ROOT/'authored/content').as_posix()
 if logical not in registry:
  front,_=read_markdown(file);route='/'+logical.removesuffix('_index.md').removeprefix('manuals/')
  registry[logical]={'route':route,'source':file.relative_to(ROOT).as_posix(),'frontmatter':front}
  bylabel[params(front).get('linkTitle',front.get('title',''))].append(logical)
nodes={};roots={};counts=defaultdict(int)
def merge(parent,sequence):
 existing=parent.setdefault('children',[]);next_id=None
 for key in reversed(sequence):
  if key not in existing:existing.insert(existing.index(next_id) if next_id in existing else len(existing),key)
  next_id=key

def parse(el,parent,scope):
 classes=el.get('class','').split();group=el.tag=='div' and 'navbar-group' in classes
 if group:
  title=' '.join(el.xpath('./li')[0].text_content().split());key=parent+'|group:'+title;node={'kind':'group','title':title}
 else:
  if el.tag!='li':return None
  section=el.get('x-data') is not None
  anchors=el.xpath('./div/div/a|./div/div/button') if section else el.xpath('./a')
  if not anchors:return None
  a=anchors[0];title=a.get('title') or (a.text or '').strip();href=a.get('href','');key=parent+'|'+title+'|'+href;node={'kind':'section' if section else 'page','title':title,'href':href}
  candidates=byroute.get(href.removeprefix(publication['base_url']),[]) or bylabel.get(title,[])
  candidates=[k for k in candidates if params(registry[k]['frontmatter']).get('linkTitle',registry[k]['frontmatter'].get('title',''))==title] or candidates
  candidates=[k for k in candidates if k.endswith('_index.md')==section]
  ancestor=nodes.get(parent,{}).get('source','').removesuffix('_index.md')
  if ancestor and not href:candidates=[k for k in candidates if k.startswith(ancestor)]
  if href and not href.startswith(publication['base_url']):candidates=[k for k in candidates if params(registry[k]['frontmatter']).get('sidebar',{}).get('goto')==href]
  candidates=[k for k in candidates if k.split('/')[0]==scope] or candidates
  if candidates:
   logical=candidates[0];f=params(registry[logical]['frontmatter']);sidebar=f.get('sidebar',{});node.update(source=logical,route=registry[logical]['route'],hidden=f.get('sitemap') is False,active_children_only=bool(sidebar.get('activeChildrenOnly')),reverse=bool(sidebar.get('reverse')),goto=sidebar.get('goto',''),badge=sidebar.get('badge'))
  else:
   own='/reference/cli/'+title.replace(' ','/')+'/' if title.startswith('docker ') else href.removeprefix(publication['base_url']);node.update(route=own,hidden=False,active_children_only=False,goto=href if href.startswith('http') and not href.startswith(publication['base_url']) else '',badge=None)
  metas=publication['pages'].get(node['route'],{}).get('meta',[])
  if any(v.get('name')=='robots' and v.get('content')=='noindex' for v in metas):node['hidden']=True
 if key not in nodes:nodes[key]=node
 children=el.xpath('./li|./div') if group else el.xpath('./ul/li|./ul/div')
 ids=[v for c in children if (v:=parse(c,key,scope))];merge(nodes[key],ids);return key
for i,rec in enumerate(v for v in manifest['pages'] if v.get('kind')!='auxiliary'):
 route=rec['route'];schema=publication['pages'][route]['schema'];scope=next((v.get('articleSection') for v in schema if v.get('@type')=='TechArticle'),None)
 if not scope:continue
 doc=html.parse(str(SITE/route.strip('/')/'index.html'));nav=doc.xpath('//nav[contains(concat(" ",normalize-space(@class)," ")," navbar-font ")]')
 if not nav:continue
 parent='scope:'+scope;roots.setdefault(scope,{'children':[]});sequence=[v for el in nav[0].xpath('./ul/li|./ul/div') if (v:=parse(el,parent,scope))];merge(roots[scope],sequence);counts[scope]+=1
model={'roots':roots,'nodes':nodes,'observed_pages':dict(counts),'provenance':'Union of the pinned corpus sidebar states, preserving observed ordering; authored source bindings update labels, visibility and Docker-specific sidebar flags.'};(ROOT/'data/navigation.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n')
api=json.loads((ROOT/'authored/data/api-reference.json').read_text());api_navigation={'apis':[{k:a[k] for k in ['id','title','version','url','tags']}|{'operations':[{k:o[k] for k in ['id','url','method','summary','tags']} for o in a['operations']]} for a in api['apis']]};(ROOT/'data/api-navigation.json').write_text(json.dumps(api_navigation,ensure_ascii=False,indent=2)+'\n')
print('Navigation nodes',len(nodes),'scopes',counts)
