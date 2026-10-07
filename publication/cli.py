"""Typed Docker/Cobra YAML → Docker CLI component markup."""
from pathlib import Path
import html,re,yaml
E=lambda x:html.escape(str(x),quote=True)
class CLI:
 def __init__(self,renderer,records):self.r=renderer;self.records=records;self.context=None;self.root=renderer.upstream.parent
 def md(self,value):
  # Five pinned command descriptions use this legacy block attribute. Docker's
  # alert hook consumes it without exposing the class in the rendered block.
  value=re.sub(r'(?m)^\{ \.warning \}\s*$','',str(value or ''))
  return self.r.markdown(value,self.context)
 def inline(self,value):return self.md(value).strip().removeprefix('<p>').removesuffix('</p>')
 def heading(self,label):return self.md('## '+label)
 def badge(self,label,color='blue'):
  colors={'blue':'bg-blue-500 dark:bg-blue-400','red':'bg-red-500 dark:bg-red-400','violet':'bg-violet-500 dark:bg-violet-400'}
  return '<span class="not-prose '+colors[color]+' rounded-sm px-1 text-xs text-white">'+E(label)+'</span> '
 def experimental(self):
  icon=(self.r.assets/'beaker.svg').read_text()
  return '<div class="px-4 border-l-2 border-l-magenta-light dark:border-l-magenta-dark"><p class="not-prose flex gap-2 items-center text-magenta-light dark:text-magenta-dark"><span class="icon-svg pb-1">'+icon+'</span><strong>Experimental</strong></p><p><strong>This command is experimental.</strong></p><p>Experimental features are intended for testing and feedback as their functionality or design may change between releases without warning or can be removed entirely in a future release.</p></div>'
 def summary(self,d,sbx=False):
  rows=[]
  for key,label in [('synopsis' if sbx else 'short','Description'),('usage','Usage')]:
   if d.get(key):rows.append('<tr><th class="text-left w-32">'+label+'</th><td>'+('<code>'+E(d[key])+'</code>' if key=='usage' else E(d[key]))+'</td></tr>')
  if d.get('aliases') and not sbx:
   aliases=d['aliases'].replace(d['command']+', ','');icon=(self.r.assets/'question-mark-circle.svg').read_text();tip='<div data-tooltip-wrapper><div data-tooltip-button class="icon-svg text-blue-light flex items-center dark:text-blue-700">'+icon+'</div><div data-tooltip-body class="absolute top-0 left-0 hidden max-w-56 rounded-sm bg-gray-700 p-2 text-white dark:text-gray-800 dark:bg-gray-300" role="tooltip">An alias is a short or memorable alternative for a longer command.<div data-tooltip-arrow class="absolute h-2 w-2 rotate-45 bg-gray-700 dark:bg-gray-300"></div></div></div>'
   rows.append('<tr><th class="text-left w-32 flex items-center gap-2"><span>Aliases</span>'+tip+'</th><td><div class="flex gap-3">'+' '.join('<code>'+E(v)+'</code>' for v in aliases.split(', '))+'</div></td></tr>')
  return '<div class="overflow-x-auto"><table><tbody>'+''.join(rows)+'</tbody></table></div>'
 def children(self,record):
  sections=[v['route'] for v in self.records if v['section']]
  return sorted([v for v in self.records if v['route']!=record['route'] and v['family']==record['family'] and max((s for s in sections if v['route'].startswith(s) and v['route']!=s),key=len,default=None)==record['route']],key=lambda v:v['title'])
 def options(self,options,sbx=False):
  out='<div class="overflow-x-auto"><table><thead class="bg-gray-100 dark:bg-gray-800"><tr><th class="p-2">Option</th><th class="p-2">Default</th><th class="p-2">Description</th></tr></thead><tbody>'
  for p in options:
   short=p.get('shorthand');long=p['name'] if sbx else p['option'];flag='<code>'+('-'+E(short)+', ' if short else '')+'--'+E(long)+'</code>'
   if not sbx and p.get('details_url'):flag='<a class="link" href="'+E(p['details_url'])+'">'+flag+'</a>'
   raw=p.get('default_value','');default=str(raw) if raw else '';skip='[],false,' if sbx else '[],map[],false,0,0s,default,\'\',""'
   default='<code>'+(default if isinstance(raw,str) else '%!s(int64='+str(raw)+')')+'</code>' if default and default not in skip else '';desc=''
   if sbx:desc='<span class="inline-flex items-center gap-2">'+(self.badge('experimental','violet') if p.get('experimental') else '')+E(str(p.get('usage','')).strip())+'</span> '
   else:
    for key,label,color in [('min_api_version','API '+str(p.get('min_api_version',''))+'+','blue'),('deprecated','Deprecated','red'),('experimental','experimental (daemon)','violet'),('experimentalcli','experimental (CLI)','violet'),('kubernetes','Kubernetes','blue'),('swarm','Swarm','blue')]:
     if p.get(key):desc+=self.badge(label,color)
    if p.get('description'):desc+=self.inline(p['description'].replace('\n','<br>'))
   out+='<tr'+(' class="p-2"' if not sbx else '')+'><td>'+flag+'</td><td>'+default+'</td><td>'+desc+'</td></tr>'
  return out+'</tbody></table></div>'
 def render(self,record):
  d=yaml.safe_load((self.root/record['source']).read_text());sbx=record['family']=='sbx-cli';self.context={'route':record['route'],'logical':record['logical'],'index':record['section'],'frontmatter':{},'records':{}}
  out=self.summary(d,sbx)
  if not sbx and d.get('deprecated'):out+=self.md('> [!WARNING]\n> This command is deprecated\n>\n> It may be removed in a future Docker version. For more information, see the\n> [Docker roadmap](https://github.com/docker/roadmap/issues/209)')
  if d.get('experimental') or d.get('experimentalcli'):out+=self.experimental()
  if not sbx:
   for key,label in [('kubernetes','Kubernetes'),('swarm','Swarm')]:
    if d.get(key):out+='<p>'+self.badge(label)+' This command works with the '+label+' orchestrator.</p>'
  description=d.get('description' if sbx else 'long')
  if description:out+=self.heading('Description')+self.md(description)
  def subcommands():
   children=self.children(record);result=self.heading('Commands' if sbx else 'Subcommands')+'<table><thead><tr><th class="text-left">Command</th><th class="text-left">Description</th></tr></thead><tbody>'
   for v in children:
    child=yaml.safe_load((self.root/v['source']).read_text());summary=E(child.get('synopsis' if sbx else 'short',''))
    if sbx:summary='<span class="inline-flex items-center gap-2">'+(self.badge('experimental','violet') if child.get('experimental') else '')+summary+'</span> '
    result+='<tr><td class="text-left"><a class="link" href="https://docs.docker.com'+E(v['route'])+'"><code>'+E(v['title'])+'</code></a></td><td class="text-left">'+summary+'</td></tr>'
   return result+'</tbody></table>'
  if sbx and record['section']:out+=subcommands()
  for key,label in [('options','Options'),('inherited_options','Global options')]:
   if key=='inherited_options' and not sbx:continue
   opts=[p for p in d.get(key,[]) if (p['name']!='help' if sbx else p.get('hidden') is False)]
   if opts:out+=self.heading(label)+self.options(opts,sbx)
  examples=d.get('example' if sbx else 'examples')
  if examples:
   if sbx:examples='```console\n'+re.sub(r'(?m)^ {2,6}','',examples).strip()+'\n```'
   out+=self.heading('Examples')+self.md(examples)
  if not sbx and record['section']:out+=subcommands()
  return out
