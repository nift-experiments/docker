#!/usr/bin/env python3
"""Explicit route registration/rename/removal proof, restoring maintained inputs."""
from pathlib import Path
import json,copy,subprocess,os,hashlib,gzip,html
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=BASE/'docker-baseline/c6/routes'
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--projects',default='docker,docker-agent');parser.add_argument('--repetitions',type=int,default=5);args=parser.parse_args();OUT=args.output.resolve()
if (OUT/'results.json').exists():raise SystemExit('Evidence already exists; choose a new --output directory: '+str(OUT))
OUT.mkdir(parents=True,exist_ok=True);env=dict(os.environ,PATH=str(BASE/'docker-baseline/tools/node-v24.21.0-linux-x64/bin')+':'+os.environ['PATH']);results=[]
def hashes(root):return {p.relative_to(root/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'public').rglob('*') if p.is_file()}
def build(root,full=False,name='build'):
 with (OUT/(root.name+'-'+name+'.log')).open('w') as log:subprocess.run(['python3','scripts/build.py',*(['--all'] if full else [])],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
for project in args.projects.split(','):
 root=BASE/project;build(root,name='baseline');baseline=hashes(root);saved={};created=[]
 def save(path,data):
  if path not in saved:saved[path]=path.read_bytes()
  path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 files=['data/composition.json','data/chrome.json','data/publication.json','data/navigation.json']+(['data/source-registry.json','data/refs.json'] if project=='docker' else [])
 originals={f:json.loads((root/f).read_text()) for f in files};old='/engine/install/ubuntu/';oldrec=next(v for v in originals['data/composition.json']['pages'] if v['route']==old)
 def install(route):
  manifest=copy.deepcopy(originals['data/composition.json']);record=copy.deepcopy(oldrec);record['route']=route;record['name']=route.strip('/')+'/index';record['title']='C6 route lifecycle proof';record['pieces']=[None]
  record['body']=('.generated/bodies/' if project=='docker' else 'pages/')+route.strip('/')+'/index.html'
  logical='manuals/'+route.strip('/')+'.md'
  if project=='docker':
   record['logical']=logical;record['source']='authored/content/'+logical;path=root/record['source'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text('---\ntitle: C6 route lifecycle proof\ndescription: Corpus migration lifecycle fixture\nkeywords: Docker, C6\n---\n\n## Lifecycle heading\n\nC6 lifecycle content sentinel. Literal `$[rawHtml("example")]` stays literal.\n');created.append(path)
   registry=copy.deepcopy(originals['data/source-registry.json']);registry[logical]={'route':route,'index':False,'source':record['source'],'frontmatter':{'title':record['title'],'description':'Corpus migration lifecycle fixture','keywords':'Docker, C6'}};save(root/'data/source-registry.json',registry)
   refs=copy.deepcopy(originals['data/refs.json']);refs[logical]=route;save(root/'data/refs.json',refs)
  else:
   path=root/record['body'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text('<h2 class="scroll-mt-20" id="lifecycle-heading">Lifecycle heading</h2><p>C6 lifecycle content sentinel. Literal <code>$[rawHtml("example")]</code> stays literal.</p>');created.append(path)
  manifest['pages'].append(record);save(root/'data/composition.json',manifest)
  navigation=copy.deepcopy(originals['data/navigation.json']);key,node=next((k,v) for k,v in navigation['nodes'].items() if v.get('route')==old);newkey='c6:'+route;newnode=copy.deepcopy(node);newnode.update(title=record['title'],route=route,href=originals['data/publication.json']['base_url']+route,source=logical);navigation['nodes'][newkey]=newnode
  parent=next(v for v in navigation['nodes'].values() if key in v.get('children',[]));parent['children'].append(newkey);save(root/'data/navigation.json',navigation)
  chrome=copy.deepcopy(originals['data/chrome.json']);chrome[route]=copy.deepcopy(chrome[old]);chrome[route]['logical']=logical;save(root/'data/chrome.json',chrome)
  model=copy.deepcopy(originals['data/publication.json']);base=model['base_url']
  def replace(value):
   if isinstance(value,str):return value.replace(old,route).replace('/engine/install/ubuntu.md',route.rstrip('/')+'.md')
   if isinstance(value,list):return [replace(v) for v in value]
   if isinstance(value,dict):return {k:replace(v) for k,v in value.items()}
   return value
  page=replace(model['pages'][old]);page['title']=record['title'];page['markdown']=base+route.rstrip('/')+'.md'
  for meta in page['meta']:
   key=meta.get('name') or meta.get('property')
   if key in ['twitter:title','og:title']:meta['content']=record['title']
   elif key in ['description','twitter:description','og:description']:meta['content']='Corpus migration lifecycle fixture'
   elif key=='keywords':meta['content']='Docker, C6'
  for schema in page['schema']:
   if schema.get('@type')=='TechArticle':schema.update(headline=record['title'],description='Corpus migration lifecycle fixture',keywords=['Docker','C6'])
   elif schema.get('@type')=='BreadcrumbList':schema['itemListElement'][-1]['item']['name']=record['title']
  model['pages'][route]=page
  config=replace(chrome[route]);config['logical']=logical
  config['bindings']={k:v.replace(oldrec['logical'] if project=='docker' else 'manuals/engine/install/ubuntu.md',logical).replace(originals['data/publication.json']['pages'][old]['title'],record['title']) if isinstance(v,str) else v for k,v in config['bindings'].items()}
  config['bindings']['PAGE_BREADCRUMBS']=config['bindings']['PAGE_BREADCRUMBS'].replace('>Ubuntu<','>'+html.escape(record['title'])+'<')
  config['bindings']['PAGEFIND_META']='<meta data-pagefind-meta="description:Corpus migration lifecycle fixture"><meta data-pagefind-meta="keywords:Docker, C6">'
  config['bindings']['GITHUB_EDIT']='https://github.com/nift-experiments/'+project+'/edit/master/'+record.get('source',record['body']);chrome[route]=config;save(root/'data/chrome.json',chrome)
  metadata=replace(next(v for v in model['metadata'] if v.get('url')==base+old));metadata['title']=record['title'];metadata['description']='Corpus migration lifecycle fixture';metadata['keywords']=['Docker','C6'];model['metadata'].append(metadata)
  model['sitemap'].append({'loc':base+route});model['llms_pages'].append({'title':record['title'],'url':base+route,'markdown':page['markdown']});save(root/'data/publication.json',model)
  return record
 try:
  previous=None
  for case,route in [('addition','/engine/install/c6-added/'),('rename','/engine/install/c6-renamed/')]:
   rec=install(route);build(root,name=case);partial=hashes(root);output=root/'public'/(route.strip('/')+'/index.html');text=output.read_text();assert 'C6 lifecycle content sentinel' in text and '$[rawHtml' in text and 'href=#lifecycle-heading' in text.replace('"',''),(project,case,'body/TOC/literal failed')
   assert (root/'public'/(route.strip('/')+'.md')).exists()
   from html.parser import HTMLParser
   class Metadata(HTMLParser):
    def __init__(self):super().__init__();self.meta={};self.links={};self.inschema=False;self.schemas=[]
    def handle_starttag(self,tag,attrs):
     a=dict(attrs)
     if tag=='meta':self.meta[a.get('name') or a.get('property')]=a.get('content')
     if tag=='link':self.links[a.get('rel')]=a.get('href')
     if tag=='script' and a.get('type')=='application/ld+json':self.inschema=True
    def handle_endtag(self,tag):
     if tag=='script':self.inschema=False
    def handle_data(self,value):
     if self.inschema:self.schemas.append(json.loads(value))
   md=Metadata();md.feed(text);assert md.meta['og:title']==rec['title'] and md.meta['description']=='Corpus migration lifecycle fixture';assert md.links['canonical']==originals['data/publication.json']['base_url']+route;assert next(v for v in md.schemas if v['@type']=='TechArticle')['headline']==rec['title']
   assert route in (root/'public/sitemap.xml').read_text();assert 'C6 route lifecycle proof' in text and route in (root/'public/engine/install/ubuntu/index.html').read_text()
   indexed={json.loads(gzip.decompress(p.read_bytes()).removeprefix(b'pagefind_dcd'))['url'] for p in (root/'public/pagefind/fragment').glob('*')};assert route in indexed
   if previous:
    assert previous not in indexed
    assert not (root/'public'/(previous.strip('/')+'/index.html')).exists();assert not (root/'public'/(previous.strip('/')+'.md')).exists()
   build(root,True,name=case+'-full');assert hashes(root)==partial,(project,case,'incremental differs full');results.append({'project':project,'case':case,'incremental_equals_full':True,'body_anchor_toc_literal_download_sitemap_search_navigation_metadata':True,'retired_previous_outputs':bool(previous)});previous=route
  for f in files:save(root/f,originals[f])
  for path in created:
   if path.exists():path.unlink()
  build(root,name='deletion');partial=hashes(root);assert partial==baseline,(project,'deletion/restoration mismatch');build(root,True,name='deletion-full');assert hashes(root)==partial
  results.append({'project':project,'case':'deletion','incremental_equals_full':True,'restored_all_output_hashes':True})
 finally:
  for path,data in saved.items():path.write_bytes(data)
  for path in created:
   if path.exists():path.unlink()
  build(root,name='restored')
 (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(project,'route lifecycle passed',flush=True)
