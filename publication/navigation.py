"""Docker's observed sidebar rules, over an explicit navigation data tree."""
from pathlib import Path
import html,json
E=lambda v:html.escape(str(v),quote=True)
class Navigation:
 def __init__(self,root,registry=None,api=None):
  self.root=root;self.model=json.loads((root/'data/navigation.json').read_text());self.nodes=self.model['nodes'];self.registry=registry or {};self.original=json.loads((root/'data/source-registry.json').read_text()) if registry else {};self.api=api or json.loads((root/'data/api-navigation.json').read_text())
  self.icons={n:(root/'publication/icons'/(n+'.svg')).read_text().strip() for n in ['chevron-down','chevron-up']}
 def node(self,key):
  seed=self.nodes[key];value=dict(seed)
  if seed.get('source') in self.registry:
   front=self.registry[seed['source']]['frontmatter'];p={**front,**front.get('params',{})};side=p.get('sidebar',{});oldfront=self.original.get(seed['source'],{}).get('frontmatter',{});old={**oldfront,**oldfront.get('params',{})}
   if p.get('linkTitle',p.get('title'))!=old.get('linkTitle',old.get('title')):value['title']=p.get('linkTitle',p.get('title',value['title']))
   for field,key2 in [('hidden','sitemap'),('active_children_only','activeChildrenOnly'),('reverse','reverse'),('goto','goto'),('badge','badge')]:
    if field=='hidden' and key2 in p:value[field]=p[key2] is False
    elif key2 in side:value[field]=side[key2]
  return value
 def render(self,scope,record):
  current=record['route'];active={};values={}
  def mark(key):
   n=self.node(key);values[key]=n;own=n.get('route')==current and not n.get('goto');logical=n.get('source','');source_ancestor=n['kind']=='section' and logical.endswith('_index.md') and record.get('logical','').startswith(logical.removesuffix('_index.md'))
   children=[mark(v) for v in n.get('children',[])];active[key]=own or source_ancestor or any(children);return active[key]
  roots=self.model['roots'].get(scope,{}).get('children',[])
  for key in roots:mark(key)
  colors={'blue':'bg-blue-500 dark:bg-blue-400','red':'bg-red-500 dark:bg-red-400','violet':'bg-violet-500 dark:bg-violet-400','gray':'bg-gray-500 dark:bg-gray-400','green':'bg-green-500 dark:bg-green-700','amber':'bg-amber-500 dark:bg-amber-400'}
  def title(n):
   result=E(n['title']);badge=n.get('badge')
   if badge:result+=' <span><span class="not-prose '+colors[badge['color']]+' rounded-sm px-1 text-xs text-white">'+E(badge['text'])+'</span></span>'
   return result
  def children(keys,parent=None,reveal=False):
   if parent and parent.get('reverse')!=self.nodes[parent['key']].get('reverse'):keys=list(reversed(keys))
   return ''.join(render(k,reveal) for k in keys if (not parent or not parent.get('active_children_only') or active[k]) and (not values[k].get('hidden') or active[k] or reveal))
  def render(key,reveal):
   n=values[key];n['key']=key
   if n['kind']=='group':return '<div class="navbar-group"><li class="navbar-group-font-title">'+E(n['title'])+'</li>'+children(n.get('children',[]),reveal=reveal)+'</div>'
   own=n.get('route')==current and not n.get('goto');selected=' aria-current="page" id="sidebar-current-page"' if own else ''
   if n['kind']=='page':
    if n.get('goto'):return '<li class="navbar-entry-margin hover:text-blue hover:dark:text-blue-400"><a class="block w-full truncate" href="'+E(n['href'])+'" title="'+E(n['title'])+'">'+title(n)+'</a></li>'
    return '<li class="navbar-entry-margin hover:text-blue '+(' navbar-entry-background-current ' if own else '')+' rounded-sm hover:dark:text-blue-400"><a'+selected+' class="block w-full truncate" href="'+E(n.get('href',''))+'" title="'+E(n['title'])+'">'+title(n)+'</a></li>'
   expanded=active[key];revealed=reveal or n.get('hidden') and expanded;items=children(n.get('children',[]),n,revealed)
   out='<li class="" x-data="{ expanded: '+str(bool(expanded)).lower()+' }"><div class="'+(' navbar-entry-background-current ' if own else '')+' flex w-full items-center justify-between rounded-sm"><div class="navbar-entry-margin w-full truncate">'
   out+=('<a'+selected+' class="hover:text-blue block select-none hover:dark:text-blue-400" href="'+E(n['href'])+'">'+title(n)+'</a>') if n.get('href') else '<button @click="expanded = !expanded" class="hover:text-blue w-full text-left select-none hover:dark:text-blue-400">'+title(n)+'</button>'
   out+='</div>'
   if items:out+='<button @click="expanded = !expanded" class="rounded-sm px-1 hover:bg-gray-200 hover:dark:bg-gray-800"><span :class="{ \'hidden\' : expanded }" class="icon-svg icon-sm '+('hidden' if expanded else '')+'">'+self.icons['chevron-down']+'</span><span :class="{ \'hidden\' : !expanded }" class="icon-svg icon-sm '+('' if expanded else 'hidden')+'">'+self.icons['chevron-up']+'</span></button>'
   return out+'</div><ul :class="{ \'hidden\' : !expanded }" class="'+('' if expanded else 'hidden')+' ml-3">'+items+'</ul></li>'
  return '<nav class="navbar-font mx-1 mt-1 flex flex-col"><ul>'+children(roots)+'</ul></nav>'
 def api_nav(self,record):
  a=next(v for v in self.api['apis'] if v['id']==record['api_id']);selected=' aria-current="page" id="sidebar-current-page"';out='<nav class="api-nav" aria-label="API navigation"><a class="api-nav-back" href="/reference/api/">← API catalog</a><h2>'+E(a['title'])+'</h2><p class="api-nav-version">API '+E(a['version'])+'</p><a href="'+E(a['url'])+'"'+(selected if record['view']=='overview' else '')+'>Overview</a>'
  for tag in a['tags']:
   if tag['kind']!='nav':continue
   out+='<h3>'+E(tag['summary'])+'</h3>'
   for op in a['operations']:
    if op['tags'][0]!=tag['name']:continue
    out+='\n<a class="api-nav-operation" href="'+E(op['url'])+'"'+(selected if op['id']==record.get('operation_id') else '')+'><small data-method="'+E(op['method'])+'">'+E(op['method'])+'</small><span>'+E(op['summary'])+'</span></a>'
  return out+'</nav>'
