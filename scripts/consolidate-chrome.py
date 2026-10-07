#!/usr/bin/env python3
"""One-time consolidation of observed shell variables into explicit shared slots."""
from pathlib import Path
import sys,json,hashlib,re,shutil,html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'));from extract import Spans
model=json.loads((ROOT/'data/publication.json').read_text());configs=json.loads((ROOT/'data/chrome.json').read_text());new={}
def save(value,label):
 path='layouts/chrome/'+label+'-'+hashlib.sha256(value.encode()).hexdigest()[:16]+'.html';new[path]=value;return path
for route,config in configs.items():
 page=model['pages'].get(route);bindings={};config['bindings']=bindings
 for side in ['prefix','suffix']:
  text=(ROOT/config[side]).read_text();nodes=Spans(text).nodes;edits=[]
  # Pagefind metadata is data, not a per-page layout.
  metas=[n for n in nodes if n.tag=='meta' and 'data-pagefind-meta' in n.attrs]
  if metas:
   bindings['PAGEFIND_META']=''.join(text[n.start:n.end] for n in metas)
   edits.extend((n.start,n.end,'@@PAGEFIND_META@@' if i==0 else '') for i,n in enumerate(metas))
  for s,e,v in sorted(edits,reverse=True):text=text[:s]+v+text[e:]
  # The two GitHub links vary by source path/published URL only.
  for key,pattern in [('GITHUB_EDIT',r'https://github\.com/docker/docs/edit/main/content/[^ >\"]+'),('GITHUB_ISSUE',r'https://github\.com/docker/docs/issues/new\?[^\"]+')]:
   found=re.search(pattern,text)
   if found:bindings[key]=found.group();text=text.replace(found.group(),'@@'+key+'@@')
  config[side]=save(text,side)
 if not page:continue
 path=config['slots'].get('HEAD')
 if path:
  text=(ROOT/path).read_text();nodes=Spans(text).nodes;edits=[];schema_index=0
  for n in nodes:
   if n.tag=='meta':
    key='HEAD_META_'+str(len([k for k in bindings if k.startswith('HEAD_META_')]));bindings[key]=text[n.start:n.end];edits.append((n.start,n.end,'@@'+key+'@@'))
   elif n.tag=='title':bindings['HEAD_TITLE']=text[n.open_end:n.close_start];edits.append((n.open_end,n.close_start,'@@HEAD_TITLE@@'))
   elif n.tag=='script' and n.attrs.get('type')=='application/ld+json':
    key='LD_SCHEMA_'+str(schema_index);schema_index+=1;bindings[key]=text[n.open_end:n.close_start];edits.append((n.open_end,n.close_start,'@@'+key+'@@'))
  for s,e,v in sorted(edits,reverse=True):text=text[:s]+v+text[e:]
  for key,url in [('MARKDOWN_URL',page['markdown']),('CANONICAL_URL',model['base_url']+route)]:
   if url in text:bindings[key]=url;text=text.replace(url,'@@'+key+'@@')
  config['slots']['HEAD']=save(text,'HEAD')
 # Small per-page HTML slots become explicit metadata values. Templates and
 # partial ownership now reside in the shared layout directory.
 for slot in ['TITLE','BREADCRUMBS','TOC','MOBILE_META']:
  path=config['slots'].get(slot)
  if not path:continue
  key='PAGE_'+slot;bindings[key]=(ROOT/path).read_text();config['slots'][slot]=save('@@'+key+'@@',slot)
for repo in [ROOT,ROOT.parent/'docker-agent']:
 (repo/'data/chrome.json').write_text(json.dumps(configs,ensure_ascii=False,indent=2)+'\n')
 used={v for c in configs.values() for v in [c['prefix'],c['suffix'],*c['slots'].values()] if v}
 for path,value in new.items():
  dest=repo/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(value)
 for file in (repo/'layouts/chrome').glob('*.html'):
  if file.relative_to(repo).as_posix() not in used:file.unlink()
 print(repo.name,'shared chrome files',len(used),'template bytes',sum((repo/p).stat().st_size for p in used),flush=True)
