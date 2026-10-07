"""Typed metadata updates; pinned Git provenance is separate from authored fields."""
from pathlib import Path
from copy import deepcopy
import json,posixpath,re

def parameters(front):return {**{k.lower():v for k,v in front.items()},**{k.lower():v for k,v in front.get('params',{}).items()}}
def keywords(value):return [str(v).strip(', ') for v in value] if isinstance(value,list) else [v.strip() for v in str(value).replace('\n',' ').split(',')]
def refresh(root,registry=None,api=None,redirect_data=None,site_title=None):
 seed=json.loads((root/'data/publication.json').read_text());model=deepcopy(seed);changes={};titles={};urls={};fresh_byroute={}
 original=json.loads((root/'data/source-registry.json').read_text()) if registry else {}
 for logical,rec in (registry or {}).items():
  route=rec['route'];old=parameters(original.get(logical,{}).get('frontmatter',{}));new=parameters(rec['frontmatter'])
  if old==new or route not in model['pages']:continue
  page=model['pages'][route];before=seed['pages'][route];delta={}
  for field in ['title','description','keywords','linktitle','sitemap']:
   if old.get(field)!=new.get(field):delta[field]=new.get(field)
  if not delta:continue
  title=str(new.get('title',page['title']));description=str(new.get('description','')).replace('\n',' ');kw=keywords(new.get('keywords',[]))
  if 'title' in delta:page['title']=title
  for meta in page['meta']:
   key=meta.get('name') or meta.get('property','')
   if 'title' in delta and key in ['twitter:title','og:title']:meta['content']=title
   if 'description' in delta and key in ['description','twitter:description','og:description']:meta['content']=description
   if 'keywords' in delta and key=='keywords':meta['content']=', '.join(kw)
  for schema in page['schema']:
   if schema.get('@type')=='TechArticle':
    if 'title' in delta:schema['headline']=title[:110]
    if 'description' in delta:schema['description']=description
    if 'keywords' in delta:schema['keywords']=kw
   elif schema.get('@type')=='BreadcrumbList' and 'title' in delta:schema['itemListElement'][-1]['item']['name']=title[:110]
  if 'sitemap' in delta:
   page['meta']=[v for v in page['meta'] if v.get('name')!='robots']
   if new.get('sitemap') is False:page['meta'].append({'name':'robots','content':'noindex'})
   if new.get('sitemap') is False:model['sitemap']=[v for v in model['sitemap'] if v.get('loc')!=model['base_url']+route]
  for item in model['metadata']:
   if item.get('url')!=model['base_url']+route:continue
   if 'title' in delta or 'linktitle' in delta:item['title']=new.get('linktitle',title)
   if 'description' in delta:item['description']=description
   if 'keywords' in delta:item['keywords']=kw
  titles[route]={'old':old.get('linktitle',old.get('title',before['title'])),'new':new.get('linktitle',title)};changes[route]=delta;fresh_byroute[route]=new
 # Ordinary source aliases and the four API adapter aliases have distinct
 # maintained inputs. Redirect data intentionally overrides authored aliases.
 redirects=json.loads((root/'data/redirects-base.json').read_text())
 if registry is not None:
  redirects={}
  for rec in registry.values():
   aliases=rec['frontmatter'].get('aliases',[]);aliases=[aliases] if isinstance(aliases,str) else aliases
   for alias in aliases:redirects[alias]=rec['route']
  # AddPage's top-level API aliases produce HTML redirects but are absent
  # from .Params.aliases in the pinned redirects.json template.
  for target,aliases in (redirect_data or {}).items():
   for alias in aliases:redirects[alias]=target
 model['redirects']=redirects;model['changes']=changes;model['navigation_title_changes']=titles
 if site_title:model['site_title']=site_title
 return model,seed
