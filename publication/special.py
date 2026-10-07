"""Bounded data-driven bodies for Docker's samples, glossary and learning series."""
from publication.yaml_data import load as load_yaml

from pathlib import Path
import html,json,yaml
E=lambda v:html.escape(str(v),quote=True)
class Special:
 def __init__(self,renderer,registry):self.r=renderer;self.registry={k:{**v,'frontmatter':{**v['frontmatter'],**v['frontmatter'].get('params',{})}} for k,v in registry.items()}
 def render(self,kind,text,c):
  front={**c['frontmatter'],**c['frontmatter'].get('params',{})};data=self.r.upstream/'data'
  if kind=='glossary':
   values=load_yaml((data/'glossary.yaml').read_text());out=self.r.render(text,c)+'<table><thead><tr><th>Term</th><th>Definition</th></tr></thead><tbody>'
   for term,definition in sorted(values.items()):out+='<tr><td class="not-prose"><a class="-top-16 relative" name="'+E(self.r.urlize(term))+'"></a>'+E(term)+'</td><td>'+self.r.markdown(definition,c).strip().removeprefix('<p>').removesuffix('</p>')+'</td></tr>'
   return out+'</tbody></table>'
  if kind=='samples':
   values=load_yaml((data/'samples.yaml').read_text())['samples'];out='<table><thead><tr><th>Name</th><th>Description</th></tr></thead><tbody>'
   for v in values:
    if front.get('service','') in v['services']:out+='<tr><td>'+self.r.markdown('['+v['title']+']('+v['url']+')',c).strip().removeprefix('<p>').removesuffix('</p>')+'</td><td>'+E(v['description'])+'</td></tr>'
   return out+'</tbody></table><h2>Looking for more samples?</h2><p>Visit the following GitHub repositories for more Docker samples.</p><ul><li><p><a class="link" href="https://github.com/docker/awesome-compose" rel="noopener">Awesome Compose</a>: A curated repository containing over 30 Docker Compose samples. These samples offer a starting point for how to integrate different services using a Compose file.</p></li><li><p><a class="link" href="https://github.com/dockersamples?q=&amp;type=all&amp;language=&amp;sort=stargazers" rel="noopener">Docker Samples</a>: A collection of over 30 repositories that offer sample containerized demo applications, tutorials, and labs.</p></li></ul>'
  if kind=='series':
   out='<div class="text-lg">'+E(front.get('summary',''))+'</div>'
   fields=[('proficiencyLevel','Skill level'),('time','Time to complete'),('prerequisites','Prerequisites')]
   if any(front.get(k) for k,_ in fields):out+='<div class="not-prose"><div class="mt-1.5 mb-1.5 flex flex-col gap-4 rounded-sm bg-gray-100 p-6 sm:flex-row dark:bg-gray-800">'+''.join('<div class="flex flex-grow flex-col sm:items-center"><span><strong>'+label+'</strong></span> <span>'+E(front[k])+'</span></div>' for k,label in fields if front.get(k))+'</div></div>'
   out+=self.r.render(text,c)+self.r.markdown('## Modules',c)+'<ol>'
   children=[v for v in self.registry.values() if v['route'].rstrip('/').rsplit('/',1)[0]+'/'==c['route'] and v['route']!=c['route']]
   for v in sorted(children,key=lambda v:(v['frontmatter'].get('weight',0) or 1000000,v['frontmatter'].get('title',''))):out+='<li><a class="link" href="https://docs.docker.com'+E(v['route'])+'">'+E(v['frontmatter'].get('linkTitle',v['frontmatter'].get('title','')))+'</a><p>'+E(v['frontmatter'].get('description',''))+'</p></li>'
   return out+'</ol>'
  raise ValueError('unimplemented special family '+kind)
 def template(self,name,values):
  value=(Path(__file__).parent/'templates'/(name+'.html')).read_text().rstrip('\n')
  for key,text in values.items():value=value.replace('@@'+key+'@@',str(text))
  if '@@' in value:raise ValueError('unfilled typed slot in '+name)
  return value
 def landing(self,kind,c):
  front={**c['frontmatter'],**c['frontmatter'].get('params',{})}
  if kind=='get-started':
   return self.template(kind,{k.upper()+'S':''.join(self.template(k+'-card',{key:E(value) for key,value in v.items()}) for v in front[k+'s']) for k in ['install','tutorial']})
  if kind=='home':
   from datetime import date
   data=json.loads((self.r.upstream/'data/whats-new.json').read_text());items=[]
   for v in sorted(data['items'],key=lambda v:v['published'],reverse=True):
    d=date.fromisoformat(v['published']);fields={k:E(value) for k,value in v.items()};fields['product']+=' ';fields.update(date=d.strftime('%b')+' '+str(d.day),VISIBILITY='' if v.get('featured') else 'x-cloak x-show="expanded" x-collapse.duration.300ms');items.append(self.template('news-item',fields))
   return self.template('home',{'NEWS':self.template('news',{'ITEMS':''.join(items)})})
  if kind=='guides':
   tags=load_yaml((self.r.upstream/'data/tags.yaml').read_text());order=['languages','ai','testing','cicd','security','databases','deployment','admin','labs'];records=[v for logical,v in self.registry.items() if logical.startswith('guides/') and not v['index']]
   records=sorted(records,key=lambda v:(v['frontmatter'].get('weight',0) or 1000000,v['frontmatter'].get('linkTitle',v['frontmatter']['title']).casefold()))
   sections=[];buttons=[]
   def card(v,name):
    p=v['frontmatter'];summary=self.r.markdown(p.get('summary',''),dict(c,logical='guides/_index.md')).strip().removeprefix('<p>').removesuffix('</p>');names=p.get('tags',[]);search=' '.join((p['title'],summary,' '.join(names),' '.join(tags[t]['title'] for t in names))).lower();search=' '.join(search.split());return self.template(name,{'url':'https://docs.docker.com'+E(v['route']),'title':E(p['title']),'summary':summary,'search':E(search)})
   for i,t in enumerate(order):
    values=[v for v in records if t in v['frontmatter'].get('tags',[])]
    if not values:continue
    buttons.append(self.template('guide-tag-button',{'tag':t,'title':E(tags[t]['title']),'count':len(values)}));sections.append(self.template('guide-section',{'tag':t,'title':E(tags[t]['title']),'number':f'{i+1:02d}','description':E(tags[t].get('description','')),'ROWS':''.join(card(v,'guide-row') for v in values)}))
   return self.template('guides',{'SECTIONS':''.join(sections),'TAG_BUTTONS':''.join(buttons),'FEATURED':''.join(card(v,'guide-featured') for v in records if v['frontmatter'].get('featured'))})
  raise ValueError('unimplemented landing '+kind)
