"""Explicit Docker shell slots over maintained HTML templates and page metadata."""
import html,json,re,hashlib
from pathlib import Path
from .navigation import Navigation
E=lambda v:html.escape(str(v),quote=True)
class Chrome:
 def __init__(self,root,model,registry=None,api=None,force=False):
  self.root=root;self.model=model;self.registry=registry or {};self.config=json.loads((root/'data/chrome.json').read_text());self.nav=Navigation(root,registry,api);self.cache={};self.fragments_written=set();self._toc_body=None;self._toc_headings=None;self.analysis={};self._analysis_headings=None;self.seed=json.loads((root/'data/publication.json').read_text());self.force=force;self.statefile=root/'.generated/chrome-state.json';self.state=json.loads(self.statefile.read_text()) if self.statefile.exists() else {};self.nextstate={}
  owned={v for c in self.config.values() for v in [c['prefix'],c['suffix'],*c['slots'].values()] if v}
  files=list((root/'publication').glob('*.py'))+list((root/'publication/icons').glob('*.svg'))
  self.common=hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest();self.layout_hashes={v:hashlib.sha256(self.read(v).encode()).hexdigest() for v in owned};self.scope_hashes={}
  for scope,group in self.nav.model['roots'].items():
   keys=set()
   def collect(key):
    if key in keys:return
    keys.add(key)
    for child in self.nav.values[key].get('children',[]):collect(child)
   for key in group.get('children',[]):collect(key)
   self.scope_hashes[scope]=hashlib.sha256(json.dumps({k:self.nav.values[k] for k in sorted(keys)},sort_keys=True,default=str).encode()).hexdigest()
  self.api_hash=hashlib.sha256(json.dumps(self.nav.api,sort_keys=True).encode()).hexdigest()
 def read(self,path):
  if path not in self.cache:self.cache[path]=(self.root/path).read_text()
  return self.cache[path]
 def toc(self,body,original,config):
  # Docker's Markdown heading hook marks headings; authored raw card headings
  # are excluded, matching the pinned fragment collection.
  from .html_to_markdown import Document,descendants
  def walk(n):
   for child in n.children:
    if isinstance(child,str):continue
    yield child;yield from walk(child)
  if self._analysis_headings is not None:
   headings=self._analysis_headings
  elif self._toc_body is not body:
   self._toc_body=body;self._toc_headings=[n for n in walk(Document(body).root) if n.tag in ['h1','h2','h3','h4','h5','h6'] and 'scroll-mt-20' in n.attrs.get('class','') and n.attrs.get('id')]
  if self._analysis_headings is None:headings=self._toc_headings
  current=[(n.tag,n.attrs.get('id'),re.sub(r'\s+',' ',n.text()).strip()) for n in headings]
  if current==[tuple(v) for v in config.get('full_outline',config.get('outline',[]))]:return original
  def inline(v):
   if isinstance(v,str):return E(v)
   if v.tag in ['svg','button']:return ''
   value=''.join(inline(c) for c in v.children)
   return value if v.tag=='a' else '<'+v.tag+'>'+value+'</'+v.tag+'>'
  # Docker emits child ULs as siblings of their parent's LI.
  tree=[];stack=[(0,tree)]
  for n in headings:
   level=int(n.tag[1])
   while stack[-1][0]>=level:stack.pop()
   entry=[n,[]];stack[-1][1].append(entry);stack.append((level,entry[1]))
  front=self.registry.get(config.get('logical',''),{}).get('frontmatter',{})
  params={**front,**front.get('params',{})};bounds=config.get('toc_bounds',[2,3]);minimum=int(params.get('toc_min',bounds[0]));maximum=int(params.get('toc_max',bounds[1]))
  def emit(items):
   return '<ul class="pl-2">'+''.join(('<li><a class="link lg:no-underline" href="#'+E(n.attrs['id'])+'">'+''.join(inline(c) for c in n.children)+'</a></li>' if minimum<=int(n.tag[1])<=maximum else '')+(emit(children) if children else '') for n,children in items)+'</ul>'
  replacement=emit(tree) if not params.get('notoc',config.get('notoc',False)) else ''
  # Keep pinned TOC wrappers/styles. Empty TOCs remain empty.
  return re.sub(r'(<nav[^>]*>).*?(</nav>)',lambda m:m.group(1)+replacement+m.group(2),original,flags=re.S)
 def render(self,record):
  config=self.config.get(record['route'])
  if not config:return []
  route=record['route'];bindings=config.get('bindings',{});page=self.model['pages'].get(route)
  scope=next((v.get('articleSection') for v in (page or {}).get('schema',[]) if v.get('@type')=='TechArticle'),None)
  front=self.registry.get(config.get('logical',''),{}).get('frontmatter',{});params={**front,**front.get('params',{})}
  metadata={'site_title':self.model['site_title'],'page':page,'params':{k:params.get(k) for k in ['toc_min','toc_max','notoc']},'changes':self.model.get('changes',{}).get(route,{})}
  breadcrumbs=self.expand(self.read(config['slots']['BREADCRUMBS']),bindings) if config['slots'].get('BREADCRUMBS') else ''
  metadata['breadcrumb_changes']={k:v for k,v in self.model.get('navigation_title_changes',{}).items() if v['old']!=v['new'] and '>'+E(v['old'])+'<' in breadcrumbs}
  shared={'layouts':{v:self.layout_hashes[v] for v in [config['prefix'],config['suffix'],*config['slots'].values()] if v},'navigation':self.scope_hashes.get(scope) if 'NAV' in config['slots'] else None,'api_navigation':self.api_hash if 'API_NAV' in config['slots'] else None}
  body_bytes=(self.root/record['body']).read_bytes();fingerprint=hashlib.sha256((self.common+json.dumps({'record':record,'config':config,'metadata':metadata,'shared':shared},sort_keys=True,default=str)).encode()+body_bytes).hexdigest();cached=self.state.get(route)
  inputs='.generated/chrome-inputs/'+hashlib.sha256(route.encode()).hexdigest()+'.json';destination=self.root/inputs;destination.parent.mkdir(parents=True,exist_ok=True)
  if not destination.exists() or destination.read_text()!=fingerprint:destination.write_text(fingerprint)
  if not self.force and cached and cached['fingerprint']==fingerprint and all((self.root/p).exists() for p in cached['pieces'] if p):
   record['pieces']=cached['pieces'];self.nextstate[route]=cached;return cached['dependencies']
  page=self.model['pages'].get(route);bindings=dict(bindings)
  if page and 'PAGEFIND_META' in bindings:
   delta=self.model.get('changes',{}).get(route,{})
   for field in ['description','keywords']:
    if field in delta:
     content=next((m['content'] for m in page['meta'] if m.get('name')==field),'');bindings['PAGEFIND_META']=re.sub(r'(data-pagefind-meta=\"'+field+r':)[^\"]*',lambda m:m.group(1)+E(content),bindings['PAGEFIND_META'])
  seed=self.seed['pages'].get(route);body=body_bytes.decode();self._analysis_headings=None
  if record['body'] in self.analysis:
   from .analysis import heading_nodes
   self._analysis_headings=heading_nodes(self.analysis[record['body']]['headings'])
  values={};dependencies=[inputs,'publication/chrome.py','publication/navigation.py']
  for slot,path in config['slots'].items():
   if path:dependencies.append(path)
   value=self.expand(self.read(path),bindings) if path else ''
   if slot=='NAV' and page:
    scope=next((v.get('articleSection') for v in page['schema'] if v.get('@type')=='TechArticle'),None)
    if scope:value=self.nav.render(scope,record)
   elif slot=='API_NAV':
    a=next((v for v in self.nav.api['apis'] if route.startswith(v['url'])),None)
    if a:
     op=next((v for v in a['operations'] if v['url']==route),None);view='overview' if route==a['url'] else ('operation' if op else 'schema');value=self.nav.api_nav({**record,'api_id':a['id'],'view':view,'operation_id':op['id'] if op else None})
   elif slot=='GORDON':value=value.replace('@@PAGE_TITLE_JSON@@',E(json.dumps(page['title'] if page else (config.get('title_seed') or record['title']),ensure_ascii=False)))
   elif slot=='HEAD' and page:
    if page['title']!=config['title_seed'] or self.model['site_title']!=self.seed['site_title']:
     title=self.model['site_title'] if route=='/' else page['title']+' | '+self.model['site_title'];value=re.sub(r'<title>.*?</title>','<title>'+E(title)+'</title>',value,flags=re.S)
    # Every maintained metadata attribute has an explicit seed record.
    oldmetas=seed['meta'];newmetas=page['meta'];lookup={(v.get('name') or v.get('property') or v.get('http-equiv')):v for v in newmetas}
    def meta(m):
     raw=m.group();key=re.search(r'(?:name|property|http-equiv)=(?:"([^"]*)"|([^ >]+))',raw)
     if not key:return raw
     attrs=lookup.get(key.group(1) or key.group(2))
     if not attrs:return raw
     return '<meta '+ ' '.join(k if v is None else k+'="'+E(v)+'"' for k,v in attrs.items())+'>'
    value=re.sub(r'<meta\b[^>]*>',meta,value)
    schemas=iter(page['schema'])
    value=re.sub(r'(<script[^>]*type=["\']?application/ld\+json["\']?[^>]*>).*?(</script>)',lambda m:m.group(1)+json.dumps(next(schemas),ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')+m.group(2),value,flags=re.S)
   elif slot=='TITLE' and page and seed and page['title']!=config['title_seed']:value=re.sub(r'(<h1[^>]*>).*?(</h1>)',lambda m:m.group(1)+E(page['title'])+m.group(2),value,flags=re.S)
   # Breadcrumbs use maintained route/title associations, independent of body.
   elif slot=='BREADCRUMBS':
    for change_route,change in self.model.get('navigation_title_changes',{}).items():
     value=value.replace('>'+E(change['old'])+'<','>'+E(change['new'])+'<')
   if slot in ['TOC','MOBILE_META'] and record.get('model') in ['markdown','maintained-html'] and record.get('family')=='ordinary':
    value=self.toc(body,value,config)
   values[slot]=value
  # Nift composes the actual shared/static fragments and dynamic slots.
  # Python only materializes the bounded data slots; it does not join the shell.
  pieces=[]
  for side in ['prefix','suffix']:
   dependencies.append(config[side]);value=self.expand(self.read(config[side]),bindings);cursor=0
   for match in re.finditer(r'@@([A-Z_]+)@@',value):
    static=value[cursor:match.start()]
    if static:pieces.append(self.fragment(static))
    slot=match.group(1);original=config['slots'][slot]
    pieces.append(original if original and values[slot]==self.read(original) else self.fragment(values[slot]));cursor=match.end()
   if value[cursor:]:pieces.append(self.fragment(value[cursor:]))
   if side=='prefix':pieces.append(None)
  record['pieces']=pieces
  dependencies.extend(str(p.relative_to(self.root)) for p in (self.root/'publication/icons').glob('*.svg'))
  self.nextstate[route]={'fingerprint':fingerprint,'pieces':pieces,'dependencies':dependencies}
  return dependencies
 def close(self):
  self.statefile.parent.mkdir(parents=True,exist_ok=True);self.statefile.write_text(json.dumps(self.nextstate,sort_keys=True)+'\n')
 def expand(self,value,bindings):
  return re.sub(r'@@([A-Z_0-9]+)@@',lambda m:bindings.get(m.group(1),m.group()),value)
 def fragment(self,value):
  digest=hashlib.sha256(value.encode()).hexdigest();path='.generated/chrome-fragments/'+digest+'.html'
  if path not in self.fragments_written:
   destination=self.root/path;destination.parent.mkdir(parents=True,exist_ok=True)
   if not destination.exists() or destination.read_text()!=value:destination.write_text(value)
   self.fragments_written.add(path)
  return path
