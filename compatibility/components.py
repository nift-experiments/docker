"""Docker-specific components, translated from pinned source templates.

This module receives decoded shortcode values; it never evaluates Go templates.
Only corpus-used names and fields are admitted by the dispatcher.
"""
from pathlib import Path
import html,json,hashlib,re,yaml
E=lambda value:html.escape(str(value),quote=True)
class Components:
 def __init__(self,renderer,context,materialize):
  self.r=renderer;self.c=context;self.materialize=materialize
 def inline(self,text):return self.r.markdown(str(text or ''),self.c).strip().removeprefix('<p>').removesuffix('</p>')
 def icon(self,name):
  p=self.r.assets/(Path(name).name if name.endswith('.svg') else name+'.svg')
  if not p.exists():raise ValueError('missing corpus icon '+name)
  self.r.dependencies.add(p);return p.read_text().strip()
 def data(self,name):
  p=self.r.upstream/'data'/name;self.r.dependencies.add(p)
  cache=getattr(self.r,'data_cache',{});self.r.data_cache=cache
  if name not in cache:cache[name]=yaml.safe_load(p.read_text())
  return cache[name]
 def card(self,v):
  title=self.inline(v.get('title',''));desc=self.inline(v.get('description',''));inside='<div class="card-header">'
  if v.get('image'):inside+='<img class="card-image" src="'+E(v['image'])+'" alt="">'
  if v.get('icon'):inside+='<div class="card-icon"><span class="card-img svg">'+self.icon(v['icon'])+'</span></div>'
  inside+='<h3 class="card-title">'+title+'</h3></div><div class="card-content"><p class="card-description">'+desc+'</p></div>'
  if v.get('link'):inside='<a href="'+E(v['link'])+'" class="card-link">'+inside+'</a>'
  return '<div class="card">'+inside+'</div>'
 def render(self,node,k,args):
  name=node.name
  if name=='release-date':return '<em class="text-gray-400 italic dark:text-gray-500">'+E(k['date'])+'</em>'
  if name=='badge':
   colors={'amber':'bg-amber-500 dark:bg-amber-400','blue':'bg-blue-500 dark:bg-blue-400','gray':'bg-gray-500 dark:bg-gray-400','green':'bg-green-500 dark:bg-green-700','red':'bg-red-500 dark:bg-red-400','violet':'bg-violet-500 dark:bg-violet-400'}
   return '<span class="not-prose '+colors[k['color']]+' rounded-sm px-1 text-xs text-white">'+E(k['text'])+'</span>'
  if name=='inline-image':
   src=k['src'];src=('../'+src) if not self.c['index'] and not src.startswith('/') else src
   return '\n<img loading="lazy" src="'+E(src)+'" alt="'+E(k.get('alt',''))+'"'+(' title="'+E(k['title'])+'"' if k.get('title') else '')+' class="inline my-0 not-prose">\n'
  if name=='youtube-embed':return '<div id="youtube-player-'+E(args[0])+'" data-video-id="'+E(args[0])+'" class="youtube-video aspect-video h-fit w-full py-2"></div>'
  if name=='card':return self.card(k)
  if name=='grid':
   cols=int(k.get('cols',3));key=k.get('items','grid');items=self.c['frontmatter'].get(key,self.c['frontmatter'].get('params',{}).get(key,[]))
   return f'<div class="not-prose md:grid-cols-{max(2,cols-1)} xl:grid-cols-{cols} grid grid-cols-1 gap-4 mb-6">'+''.join(self.card(v) for v in items)+'</div>'
  if name=='accordion':
   title=k['title'];identifier=re.sub(r'[^\w\s-]','',title.lower()).strip().replace(' ','-');body=self.r.markdown(self.materialize(node.children),self.c)
   icon='<span class="icon-svg -mt-1">'+self.icon(k['icon'])+'</span>' if k.get('icon') else ''
   return '<div id="'+E(identifier)+'" x-data="{ open: '+k.get('open','false')+' }" class="my-6 rounded-sm border border-gray-200 bg-white py-2 dark:border-gray-700 dark:bg-gray-900"><button class="not-prose flex w-full justify-between px-4 py-2" x-on:click="open = ! open"><div class="'+('text-xl' if k.get('large') else '')+' flex items-center gap-2">'+icon+E(title)+'</div><span :class="{ \'hidden\' : !open }" class="icon-svg icon-sm">'+self.icon('chevron-up')+'</span><span :class="{ \'hidden\' : open }" class="icon-svg icon-sm">'+self.icon('chevron-down')+'</span></button><div x-show="open" x-collapse class="px-4">'+body+'</div></div>'
  if name=='experimental':
   if node.delimiter=='%':
    return '<div class="px-4 border-l-2 border-l-magenta-light dark:border-l-magenta-dark">\n  <p class="not-prose flex gap-2 items-center text-magenta-light dark:text-magenta-dark">\n    <span class="icon-svg pb-1">\n      '+self.icon('beaker')+'\n\n    </span>\n    <strong>'+E(k.get('title','Experimental'))+'</strong>\n  </p>\n  '+self.r.deindent(self.materialize(node.children))+'\n</div>'
   return '<div class="px-4 border-l-2 border-l-magenta-light dark:border-l-magenta-dark"><p class="not-prose flex gap-2 items-center text-magenta-light dark:text-magenta-dark"><span class="icon-svg pb-1">'+self.icon('beaker')+'</span><strong>'+E(k.get('title','Experimental'))+'</strong></p>'+self.materialize(node.children)+'</div>'
  if name=='button':
   url=k['url'];url=self.r.resolve_ref(url,self.c) if not url.startswith('http') else url
   return '<a class="button not-prose" href="'+E(url)+'"'+(' marlin-label="'+E(k['marlin_label'])+'"' if k.get('marlin_label') else '')+'>'+E(k['text'])+'</a>'
  if name=='labspace-launch':
   url=k.get('browserUrl','http://localhost:3030');md='1. Start the labspace:\n\n   ```console\n   $ docker compose -p labspace -f oci://'+k['image']+' up -d\n   ```'
   if k.get('model-download')=='true':md+='\n\n   > [!NOTE]\n   >\n   > This lab uses an AI model, which requires [the Docker Model Runner to be enabled](https://docs.docker.com/ai/model-runner/get-started/). The model may take some time to download.'
   md+='\n\n2. Open your browser to ['+url+']('+url+').\n\n3. When you\'re done, tear down the labspace:\n\n   ```console\n   $ docker compose -p labspace down\n   ```'
   return self.r.markdown(md,self.c)
  if name=='setting-metadata':
   entries=[('Type',k['type'],False),('Default',k['default'],False)]
   if k.get('env'):entries.append(('Environment variable','<code>'+E(k['env'])+'</code>',True))
   return '<dl class="not-prose my-4 grid grid-cols-2 gap-x-6 gap-y-3 rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm shadow-sm dark:border-gray-700 dark:bg-gray-900">'+''.join('<div class="'+('col-span-2 ' if raw else '')+'min-w-0"><dt class="text-gray-600 dark:text-gray-400">'+label+'</dt><dd class="mt-1 wrap-anywhere">'+(v if raw else E(v))+'</dd></div>' for label,v,raw in entries)+'</dl>'
  if name=='summary-bar':
   feature=self.data('summary.yaml')[k['feature_name']];body=''
   subscription={'Business':'building-office','Team':'user-group','Pro':'user-plus','Personal':'user','Available to all':'globe-alt','Docker Hardened Images Enterprise':'/icons/dhi.svg','Docker Hardened Images Select or Enterprise':'/icons/dhi.svg','Docker Offload':'cloud','AI Governance':'shield-check'}
   for key,label in [('subscription','Subscription'),('availability','Availability'),('requires','Requires'),('for','For')]:
    value=feature.get(key)
    if not value:continue
    inside='<span class="font-bold">'+label+':</span>\n'
    if key=='subscription':
     for v in value:inside+='<span>'+E(v)+'</span>\n<span class="icon-svg icon-sm">'+self.icon(subscription.get(v,'question-mark-circle'))+'</span>'
    elif key=='availability':
     icons={'Experimental':'beaker','Beta':'bolt','Early Access':'rocket-launch','GA':'check-circle','Retired':'archive-box'}
     inside+='<span>'+E(value)+''.join('<span class="icon-svg icon-sm">'+self.icon(icons[v])+'</span>' for v in sorted(icons) if v in value)+'</span>'
    else:
     inside+='<span>'+(self.inline(value) if key=='requires' else E(value))+'</span>'
     icon='arrow-down-circle' if key=='requires' else {'Administrators':'shield-check','Individuals':'user-circle'}.get(value)
     if icon:inside+='<span class="icon-svg icon-sm">'+self.icon(icon)+'</span>'
    body+='<div class="flex flex-wrap gap-1">'+inside+'</div>'
   return '<div class="not-prose summary-bar">'+body+'</div>'
  if name=='sectionlinks':
   records=self.c['records'];parent=Path(self.c['logical']).parent
   children=[(logical,rec) for logical,rec in records.items() if (Path(logical).parent.parent if Path(logical).name=='_index.md' else Path(logical).parent)==parent and logical!=self.c['logical']]
   children.sort(key=lambda x:(x[1]['frontmatter'].get('weight',0) or 1000000,x[1]['frontmatter'].get('linkTitle',x[1]['frontmatter'].get('title','')).casefold()))
   return self.r.markdown('\n'.join('- ['+rec['frontmatter'].get('title','')+']('+rec['route']+')' for logical,rec in children),self.c)
  if name=='recipe-list':
   parent=Path(self.c['logical']).parent
   recipes=[rec for logical,rec in self.c['records'].items() if Path(logical).parent==parent and Path(logical).stem not in ['index','_index'] and rec['frontmatter'].get('sidebar',rec['frontmatter'].get('params',{}).get('sidebar',{})).get('group')==k['group']]
   recipes.sort(key=lambda v:(v['frontmatter'].get('weight',0) or 1000000,v['frontmatter'].get('linkTitle',v['frontmatter'].get('title','')).casefold()))
   return '<ul class="not-prose mb-8 grid list-none grid-cols-1 gap-x-8 p-0 md:grid-cols-2">'+''.join('<li class="border-t border-gray-200 py-4 dark:border-gray-700"><a class="font-semibold text-blue-600 hover:underline dark:text-blue-400" href="'+E(v['route'])+'">'+E(v['frontmatter'].get('linkTitle',v['frontmatter'].get('title','')))+'</a><p class="mt-2 text-sm text-gray-600 dark:text-gray-400">'+E(v['frontmatter'].get('description',''))+'</p></li>' for v in recipes)+'</ul>'
  if name=='figure':
   src=k['src'];width=(' width="'+E(k['width'])+'"') if k.get('width') else '';height=(' height="'+E(k['height'])+'"') if k.get('height') else ''
   return '<figure'+(' class="'+E(k['class'])+'"' if k.get('class') else '')+'><img src="'+E(src)+'"'+width+height+(' alt="'+E(k['alt'])+'"' if k.get('alt') else '')+'>'+('<figcaption><h4>'+E(k['title'])+'</h4></figcaption>' if k.get('title') else '')+'</figure>'
  if name=='create_panel.inline':
   self.c.setdefault('inline_definitions',{})
   if node.children:self.c['inline_definitions'][name]=self.materialize(node.children)
   return self.r.markdown(self.c['inline_definitions'][name],self.c)
  if name=='apiVersionPrevious.inline':
   major,minor=str(self.r.global_params['latest_engine_api_version']).split('.')
   return self.r.markdown('```console\n$ DOCKER_API_VERSION='+major+'.'+str(int(minor)-1)+'\n```',self.c)
  if name=='dockerfile.inline':
   file=Path(__file__).parent/'pinned/gha-Dockerfile';self.r.dependencies.add(file)
   return self.r.markdown('```dockerfile {collapse=true}\n'+file.read_text().rstrip('\n')+'\n```',self.c)
  if name=='interactive-diagram':
   file=self.r.upstream/'content'/Path(self.c['logical']).parent/k['src'];self.r.dependencies.add(file);v=yaml.safe_load(file.read_text());kind=v.get('type','sequence');identifier='interactive-diagram-'+hashlib.md5(self.c['logical'].encode()).hexdigest()+'-'+str(self.c.get('shortcode_ordinal',0))
   out='<figure id="'+identifier+'" class="interactive-diagram interactive-diagram--'+E(kind)+' not-prose my-6" data-interactive-diagram data-diagram-type="'+E(kind)+'" aria-labelledby="'+identifier+'-title"><figcaption class="interactive-diagram__header"><div class="interactive-diagram__header-copy"><p id="'+identifier+'-title" class="interactive-diagram__title">'+E(v['title'])+'</p><p class="interactive-diagram__description">'+E(v['description'])+'</p></div></figcaption><div class="interactive-diagram__stage" data-diagram-stage></div>'
   if kind=='topology':
    overview=v['overview'];out+='<div class="interactive-diagram__topology-detail" data-topology-detail aria-live="polite" aria-atomic="true"><p class="interactive-diagram__topology-category" data-topology-category>'+E(overview['category'])+'</p><div class="interactive-diagram__topology-detail-copy"><p class="interactive-diagram__topology-title" data-topology-title>'+E(overview['label'])+'</p><p class="interactive-diagram__topology-body" data-topology-body>'+E(overview['body'])+'</p></div></div>';fallback='<ul>'+''.join('<li>'+E(x['label'])+': '+E(x['details'])+'</li>' for x in v['nodes']+v['edges'])+'</ul>'
   else:
    out+='<div class="interactive-diagram__status" aria-live="polite" aria-atomic="true"><div class="interactive-diagram__step-copy"><span class="interactive-diagram__step-number" data-step-number></span><div><p class="interactive-diagram__step-title" data-step-title></p><p class="interactive-diagram__step-body" data-step-body></p></div></div><p class="interactive-diagram__state" data-step-state></p></div><div class="interactive-diagram__controls" data-diagram-controls><button type="button" class="interactive-diagram__button" data-step-previous>Previous</button><div class="interactive-diagram__progress" data-step-progress aria-label="Diagram steps"></div><button type="button" class="interactive-diagram__button" data-step-next>Next</button></div>';fallback='<ol>'+''.join('<li>'+E(x['label'])+': '+E(x['body'])+'</li>' for x in v['steps'])+'</ol>'
   return out+'<div class="interactive-diagram__fallback">'+fallback+'</div><script type="application/json" data-interactive-diagram-config>'+json.dumps(v,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')+'</script></figure>'
  if name=='whats-new':
   from datetime import datetime
   items=self.data('whats-new.json')['items'];lines=[]
   for v in items:
    d=datetime.fromisoformat(str(v['published']).replace('Z','+00:00'));date=d.strftime('%b')+' '+str(d.day)+', '+str(d.year)
    lines.append('- ['+v['product']+': '+v['title']+']('+v['url']+'): '+v['description']+' ('+date+')')
   return self.r.markdown("## What's new\n\n"+'\n'.join(lines),self.c)
  if name in ['desktop-install-v2','desktop-install']:
   all_=k.get('all');build=k.get('build_path','');groups=[]
   def link(os,arch,label,file,tag):
    base='https://desktop.docker.com/'+os+'/main/'+arch+build
    query='?utm_source=docker&utm_medium=webreferral&utm_campaign=docs-driven-download-'+tag if name.endswith('v2') else ''
    marlin={'win':'download_exe_click','mac':'download_dmg_click'}.get(os)
    return '<a rel="noopener"'+(' marlin-label="'+marlin+'"' if marlin else '')+' href="'+E(base+file+query)+'">'+E(label)+'</a>'
   def checksum(os,arch):return '(<a rel="noopener" href="https://desktop.docker.com/'+os+'/main/'+arch+E(build)+'checksums.txt">checksum</a>)'
   windows=[]
   if all_ or k.get('win'):windows.append(link('win','amd64','Windows','Docker%20Desktop%20Installer.exe','windows')+' '+checksum('win','amd64'))
   if k.get('win_arm_release'):windows.append(link('win','arm64','Windows ARM '+k['win_arm_release'],'Docker%20Desktop%20Installer.exe','windows')+' '+checksum('win','arm64'))
   if windows:groups.append(windows)
   if all_ or k.get('mac'):groups.append([link('mac','arm64','Mac with Apple chip','Docker.dmg','mac-arm64')+' '+checksum('mac','arm64'),link('mac','amd64','Mac with Intel chip','Docker.dmg','mac-amd64')+' '+checksum('mac','amd64')])
   if all_ or k.get('linux'):
    version='' if name.endswith('v2') else k.get('version','')+'-'
    linux=link('linux','amd64','Debian','docker-desktop-'+version+'amd64.deb','linux-amd64')+' - '+link('linux','amd64','RPM','docker-desktop-'+version+'x86_64.rpm','linux-amd64')+' - '+link('linux','amd64','Arch','docker-desktop-'+version+'x86_64.pkg.tar.zst','linux-amd64')+' '+checksum('linux','amd64');groups.append([linux])
   if name.endswith('v2'):return '<blockquote'+(' class="tip"' if build=='/' else '')+' class="not-prose download-links"><p class="font-semibold mb-1">Download Docker Desktop</p><div class="download-links-subcontainer">'+''.join('<ul>'+''.join('<li>'+v+'</li>' for v in group)+'</ul>' for group in groups)+'</div></blockquote>'
   return '<blockquote'+(' class="tip"' if build=='/' else '')+'><p>Download Docker Desktop</p><p>'+' | '.join(v for group in groups for v in group)+'</p></blockquote>'
  if name=='sandbox-auth':
   file=Path(__file__).parent/'templates/sandbox-auth.html';self.r.dependencies.add(file);out=file.read_text()
   for service in ['openai','anthropic','openrouter','google']:
    code=self.r.markdown('```console\n$ sbx secret set '+service+'\n```',self.c)
    start=code.index('<div class="highlight">');end=code.index('</div>',start)+6
    out=out.replace('@@HIGHLIGHT_'+service+'@@',code[start:end])
   return out
  if name=='files':
   from files import render_files
   return render_files(self,node,k)
  return None
