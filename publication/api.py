"""Typed Docker API presentation model → maintained component markup.

Direct port of Docker's api-docs/schema/websocket templates. No Hugo evaluator.
"""
import json,re,html,base64
E=lambda x:html.escape(str(x),quote=True)
def go_json(value):
 def numeric(v):
  if isinstance(v,float) and v.is_integer():return int(v)
  if isinstance(v,list):return [numeric(x) for x in v]
  if isinstance(v,dict):return {k:numeric(x) for k,x in v.items()}
  return v
 return json.dumps(numeric(value),indent=2,ensure_ascii=False,sort_keys=True).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
def pre(value):return '<pre><code>'+html.escape(go_json(value),quote=False)+'</code></pre>'
def path_html(value):return '<wbr>/'.join(E(x) for x in value.split('/'))
class API:
 def __init__(self,model,renderer,registry):self.model=model;self.r=renderer;self.registry=registry;self.api=None;self.context=None
 def md(self,value,rewrites=False):
  text=str(value or '')
  if rewrites:
   for op in self.api['operations']:
    text=text.replace('(#operation/'+op['id']+')','('+op['url']+')');text=re.sub(r'\(#tag/[^)]+/operation/'+re.escape(op['id'])+r'\)',lambda _: '('+op['url']+')',text)
   for s in self.api['schemas']:text=text.replace('(#schema-'+s['name']+')','('+s['url']+')')
   for t in self.api['tags']:text=text.replace('(#tag/'+t['name']+')','('+self.api['url']+'#tag-'+self.r.urlize(t['name'])+')')
  return self.r.markdown(text,self.context)
 def schema(self,s,depth=0):
  if not isinstance(s,dict):return '<p>'+('No value satisfies this schema.' if s is False else 'Any value satisfies this schema.' if s is True else 'No schema is declared.')+'</p>'
  out='';ref=s.get('$ref')
  if ref:
   url=self.api['schemaURLs'].get(ref);out+='<p class="api-ref">Schema: '+('<a href="'+E(url)+'"><code>'+E(ref.removeprefix('#/components/schemas/'))+'</code></a>' if url else '<code>'+E(ref)+'</code>')+'</p>'
  if s.get('type'):out+='<p class="api-type">Type: <code>'+E(' | '.join(s['type']) if isinstance(s['type'],list) else s['type'])+'</code></p>'
  if s.get('description'):out+='<div class="prose dark:prose-invert">'+self.md(s['description'])+'</div>'
  if depth<3:
   for name,v in sorted(s.get('properties',{}).items()):
    required=' · required' if name in s.get('required',[]) else '';read=' · response only' if isinstance(v,dict) and v.get('readOnly') else '';write=(' · request only' if required else '· request only') if isinstance(v,dict) and v.get('writeOnly') else ''
    out+='<details class="api-field"'+(' open' if depth==0 else '')+'><summary><code>'+E(name)+'</code>'+required+read+write+'</summary>'+self.schema(v,depth+1)+'</details>'
   for key,label in [('allOf','All constraints apply'),('oneOf','Exactly one alternative must match'),('anyOf','One or more alternatives must match')]:
    if s.get(key):out+='<details class="api-field" open><summary>'+label+'</summary>'+''.join(self.schema(x,depth+1) for x in s[key])+'</details>'
   if 'items' in s:out+='<details class="api-field"><summary>Array item</summary>'+self.schema(s['items'],depth+1)+'</details>'
  if depth>=3 or not ref or len(s)>1:out+='<details class="api-constraints"><summary>All schema constraints and annotations</summary>'+pre(s)+'</details>'
  return out
 def socket(self,s):
  out='<section><h2>WebSocket session</h2><p>Subprotocol: <code>'+E(s['subprotocol'])+'</code></p>'
  out+=''.join('<p>'+E(s[k])+'</p>' for k in ['authentication','browser','reconnect','terminalFrame'] if s.get(k))
  out+=''.join('<h3>'+label+'</h3>'+self.schema(s[k]) for k,label in [('requestFrame','Client frames'),('responseFrame','Server frames'),('errorFrame','Error frames')] if s.get(k))
  return out+'<details><summary>Handshake, resume fields, and close codes</summary>'+pre(s)+'</details></section>'
 def overview(self):
  a=self.api;out='<p class="api-eyebrow">'+('User-operated API' if a['connection']=='unix' else 'Hosted API')+'</p><h1>'+E(a['title'])+' API</h1><p class="api-lead">API '+E(a['version'])+' · '+str(len(a['operations']))+' operations · '+str(len(a['schemas']))+' named schemas</p><section class="api-overview" aria-labelledby="api-overview-title"><h2 id="api-overview-title">Overview</h2><div class="prose dark:prose-invert">'+self.md(a['description'],True)+'</div></section><section class="api-connection" id="authentication"><h2>'+('Connecting to '+a['title'] if a['connection']=='unix' else 'Connecting to the '+a['title']+' API')+'</h2>'
  for name,scheme in sorted(a['securitySchemes'].items()):
   if scheme.get('description'):out+='<h3>'+E(scheme.get('x-displayName',name))+'</h3><div class="prose dark:prose-invert">'+self.md(scheme['description'])+'</div>'
  if a['connection']=='unix':out+='<pre><code>curl --unix-socket /var/run/docker.sock http://localhost/v'+E(a['version'])+'/version</code></pre>'
  else:out+=''.join('<code>'+E(v['url'])+'</code>' for v in a['servers'])
  for guide in a['guides']:
   record=self.registry.get(guide.split('#')[0].lstrip('/'));title=record['frontmatter']['title'] if record else guide
   out+='<p><a href="'+E(self.r.resolve_ref(guide,self.context))+'">'+E(title)+'</a></p>'
  out+='</section><div class="api-overview">';visible=[]
  for t in a['tags']:
   desc=t.get('description','').strip();placeholder=desc in [t['summary']+' reference.',t['name']+' operations.'] or re.fullmatch(r'\[[^\]]+\]\(#schema-[^)]+\)',desc)
   if desc and not placeholder:visible.append(t)
   else:out+='<span id="tag-'+E(self.r.urlize(t['name']))+'"></span>'
  for t in visible:out+='<section id="tag-'+E(self.r.urlize(t['name']))+'"><h2>'+E(t['summary'])+'</h2><div class="prose dark:prose-invert">'+self.md(t.get('description'),True)+'</div></section>'
  out+='</div><h2>Operations</h2><label class="api-filter-label">Filter operations <input type="search" placeholder="Method, path, or operation name" data-api-filter></label><div class="api-operation-list">'
  out+=''.join('<a class="api-operation-row" href="'+E(v['url'])+'" data-api-filter-item><span class="api-method" data-method="'+E(v['method'])+'">'+E(v['method'])+'</span><code>'+path_html(v['path'])+'</code><span>'+E(v['summary'])+'</span></a> ' for v in a['operations'])
  return out+'</div><h2 id="schemas">Schemas</h2><ul class="api-schema-links" aria-label="Schemas">'+''.join('<li><a href="'+E(v['url'])+'"><code>'+E(v['name'])+'</code></a></li>' for v in a['schemas'])+'</ul>'
 def operation(self,o):
  a=self.api;out='<h1>'+E(o['summary'])+'</h1><div class="api-signature"><span class="api-method" data-method="'+E(o['method'])+'">'+E(o['method'])+'</span><code>'+path_html(o['path'])+'</code>'+(' <span>Deprecated</span>' if o['deprecated'] else '')+'</div><div class="api-operation-grid"><div class="api-reading"><div class="api-description prose dark:prose-invert">'+self.md(o['description'],True)+'</div><h2>Connection and access</h2><p><a href="'+E(a['url'])+'#authentication">API connection and authentication guidance</a></p>'
  if a['product']=='engine' and any(v['name']=='X-Registry-Auth' for v in o['parameters']):out+='<p><code>X-Registry-Auth</code> delegates registry credentials and does not authenticate the daemon caller.</p>'
  for v in o['servers']:out+='<p><code>'+E(v['url'])+'</code>'+(' — '+E(v['description']) if v.get('description') else '')+'</p>'
  for v in o['servers']:
   for name,value in sorted(v.get('variables',{}).items()):out+='<p><code>'+E(name)+'</code>: '+E(value.get('description',''))+'</p>'
  if not o['security']:out+='<p>No HTTP authentication requirement is declared for this operation. Transport access controls can still apply.</p>'
  else:
   out+='<p>Use one of these alternatives. Requirements within an alternative apply together.</p><ul>'
   for alternative in o['security']:
    out+='<li>'+(' AND '.join('<code>'+E(name)+'</code>'+(' ('+E(', '.join(scopes))+')' if scopes else '') for name,scopes in sorted(alternative.items())) if alternative else 'Anonymous access')+'</li>'
   out+='</ul>'
  if o['raw'].get('x-websocket'):out+=self.socket(o['raw']['x-websocket'])
  out+='<h2>Parameters</h2>'+('<p>No parameters are declared.</p>' if not o['parameters'] else '')
  for p in o['parameters']:
   out+='<section class="api-field" data-api-parameter="'+E(p['name'])+'"><h3><code>'+E(p['name'])+'</code> <small>'+E(p['in'])+'</small>'+(' <small class="api-required">Required</small>' if p.get('required') else '')+'</h3><div class="prose dark:prose-invert">'+self.md(p.get('description'),True)+'</div>'
   if 'schema' in p:out+=self.schema(p['schema'])
   if p.get('content'):out+=pre(p['content'])
   if p.get('style'):out+='<p>Serialization: <code>'+E(p['style'])+'</code></p>'
   out+='</section>'
  out+='<h2>Request and responses</h2><label>Media type <select data-api-media-select><option value="">All media types</option>'+''.join('<option value="'+E(v)+'">'+E(v)+'</option>' for v in sorted({v['media'] for v in o['variants'] if v['media']}))+'</select></label>'
  for v in o['variants']:
   out+='<section class="api-variant" data-api-variant="'+E(v['pointer'])+'" data-api-media="'+E(v['media'])+'"><h3><span>'+E(v['direction'].capitalize())+'</span>'+(' <code class="api-status">'+E(v['status'])+'</code>' if v.get('status') else '')+'</h3><div class="prose dark:prose-invert">'+self.md(v['description'],True)+'</div>'+('<p class="api-media"><code>'+E(v['media'])+'</code></p>' if v['media'] else '<p>No response content is declared.</p>')
   if v.get('headers'):
    out+='<h4>Headers</h4>'
    for name,h in sorted(v['headers'].items()):out+='<div class="api-field"><code>'+E(name)+'</code><p>'+E(h.get('description',''))+'</p>'+pre(h)+'</div>'
   if 'schema' in v:out+=self.schema(v['schema'])
   if 'itemSchema' in v:out+='<h4>Stream item</h4>'+self.schema(v['itemSchema'])
   for key in ['encoding','itemEncoding','prefixEncoding']:
    if v.get(key):out+='<details><summary>'+key+': content types and part headers</summary>'+pre(v[key])+'</details>'
   if v['examples']:
    out+='<div data-api-examples>'
    if len(v['examples'])>1:out+='<label>Example <select data-api-example-select>'+''.join('<option value="'+str(i)+'">'+E(ex['name'])+'</option>' for i,ex in enumerate(v['examples']))+'</select></label>'
    out+=''.join('<div data-api-example="'+str(i)+'"><h4>'+E(ex['name'])+'</h4><pre><code>'+E(ex['text'])+'</code></pre></div>' for i,ex in enumerate(v['examples']))+'</div>'
   out+='</section>'
  out+='<h2>Referenced schemas</h2>'+''.join('<p><a href="'+E(ref['url'])+'">'+E(ref['ref'])+'</a></p>' for ref in o['references'] if ref.get('url'))+'<details><summary>Complete operation contract</summary>'+pre(o['raw'])+'</details></div><aside class="api-request"><div class="api-request-heading"><h2>'+('Example request' if o['curl'] else 'WebSocket client')+'</h2>'+('<span>Shell</span>' if o['curl'] else '')+'</div>'
  if o['curl']:out+='<p>Replace placeholders and supply the required credentials or request body.</p><pre><code data-api-copy-source>'+E(o['curl'])+'</code></pre><button type="button" data-api-copy>Copy request</button>'
  # Download-only contract fields are maintained with the HTML, because the
  # visible schema renderer intentionally summarizes these objects.
  contracts=[o['security']]+o['parameters']
  for variant in o['variants']:
   contracts += [variant[key] for key in ['schema','itemSchema','headers','encoding','itemEncoding','prefixEncoding'] if variant.get(key)]
  payload=base64.b64encode(json.dumps([go_json(v) for v in contracts],ensure_ascii=False).encode()).decode()
  return out+''.join('<p>'+E(v)+'</p>' for v in o['curlNotes'])+'</aside></div><template data-export-contracts="'+payload+'"></template>'
 def render(self,record):
  self.context={'route':record['route'],'logical':record['logical'],'index':True,'frontmatter':{},'records':self.registry};view=record['view'];out='<article class="api-reference" data-api-view="'+view+'">'
  if view=='catalog':
   out+='<p class="api-eyebrow">Developer reference</p><h1>Docker APIs</h1><p class="api-lead">Build with Docker, from your local daemon to hosted services.</p><p>Choose an API to find connection guidance, operations, and data models.</p><div class="api-cards">'
   for a in self.model['apis']+self.model['legacyAPIs']:
    out+='<a class="api-card" href="'+E(a['url'])+'"><span class="api-label">'+('Your daemon' if a['connection']=='unix' else 'Hosted service')+'</span><h2>'+E(a['title'])+('· Experimental' if a.get('experimental') else '')+'</h2><p>'+(('API '+E(a['version'])+' · '+str(len(a['operations']))+' operations') if 'operations' in a else E(a['description']))+'</p><span>Explore reference →</span></a> '
   return out+'</div></article>'
  a=self.api=next(a for a in self.model['apis'] if a['id']==record['api_id'])
  out+='<nav class="api-crumbs" aria-label="API breadcrumb"><a href="/reference/api/">APIs</a> / <a href="'+E(a['url'])+'">'+E(a['title'])+'</a> / <span>API '+E(a['version'])+'</span></nav>'
  if a['experimental']:out+='<p class="api-label">Experimental</p>'+('<p>This API is experimental. Features, interfaces, and behavior may change.</p>' if view=='overview' else '')
  versions=[v for v in self.model['apis'] if v['product']==a['product']]
  out+='<div class="api-tools"><label>API version <select data-api-version>'+''.join('<option value="'+E(v['url'])+'"'+(' selected' if v['id']==a['id'] else '')+'>'+E(v['version'])+'</option>' for v in versions)+'</select></label><a href="'+E(self.r.resolve_ref(a['manual'],self.context))+'">Product manual</a><a href="'+E(a['sourceURL'])+'">Download OpenAPI specification</a><a href="https://docs.docker.com'+E(record['route'].rstrip('/'))+'.md">Markdown</a></div><meta data-pagefind-meta="title:'+E(record['title'])+' — '+E(a['title'])+' API '+E(a['version'])+'">'
  if view=='overview':out+=self.overview()
  elif view=='schema':out+='<p class="api-eyebrow">Schema</p><h1>'+E(record['schema_name'])+'</h1>'+self.schema(next(s['schema'] for s in a['schemas'] if s['name']==record['schema_name']))
  elif view=='operation':out+=self.operation(next(o for o in a['operations'] if o['id']==record['operation_id']))
  else:raise ValueError('unsupported API view '+view)
  return out+'</article>'
