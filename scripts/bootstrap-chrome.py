#!/usr/bin/env python3
"""One-time recovery of explicit Docker shell slots, never a routine dependency."""
from pathlib import Path
import sys,json,hashlib,re,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'))
from extract import Spans
human=json.loads((ROOT/'data/composition.json').read_text());agent=json.loads((ROOT.parent/'docker-agent/data/composition.json').read_text());agent_by={r['route']:r for r in agent['pages']};configs={};shared={}
def save(value,label):
 key=hashlib.sha256(value.encode()).hexdigest()[:16];path='layouts/chrome/'+label+'-'+key+'.html'
 if path not in shared:
  p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value);shared[path]=True
 return path
for i,r in enumerate(human['pages']):
 if r['model']=='redirect' or r.get('family')=='verification':continue
 a=agent_by[r['route']];body=(ROOT.parent/'docker-agent'/a['body']).read_text();source=(ROOT.parent/'docker-baseline/site'/((r['route'].strip('/')+'/index.html').lstrip('/') if r['route']!='/404.html' else '404.html')).read_text();start=source.index(body);end=start+len(body)
 nodes=Spans(source).nodes;slots=[];config={'slots':{}}
 def take(n,label,transform=None):
  if n.start<end and n.end>start:return
  if any(n.start<s2 and n.end>s1 for s1,s2,_ in slots):return
  value=source[n.start:n.end];value=transform(value) if transform else value
  config['slots'][label]=save(value,label);slots.append((n.start,n.end,'@@'+label+'@@'))
 for n in nodes:
  if n.tag=='head':take(n,'HEAD')
  elif n.tag=='header' and n.start<start:take(n,'HEADER')
  elif 'page_title:' in (n.attrs.get('x-data') or ''):take(n,'GORDON',lambda v:re.sub(r'(page_title:\s*)(?:&#34;.*?&#34;|&quot;.*?&quot;)',r'\1@@PAGE_TITLE_JSON@@',v,count=1))
  elif n.tag=='footer':take(n,'FOOTER')
  elif n.tag=='nav' and 'navbar-font' in n.attrs.get('class','').split():take(n,'NAV')
  elif n.tag=='nav' and 'api-nav' in n.attrs.get('class','').split():take(n,'API_NAV')
  elif n.attrs.get('id')=='breadcrumbs':take(n,'BREADCRUMBS')
  elif n.attrs.get('id')=='TableOfContents':take(n,'TOC')
  elif n.tag=='h1' and n.start<start:take(n,'TITLE')
 # Preserve mobile TOC / publication controls as explicit shared slot.
 for n in nodes:
  if n.attrs.get('class')=='block lg:hidden':take(n,'MOBILE_META')
 cursor=0;parts=[]
 for s,e,value in sorted([*slots,(start,end,'@@BODY@@')]):parts.append(source[cursor:s]);parts.append(value);cursor=e
 parts.append(source[cursor:]);template=''.join(parts);left,right=template.split('@@BODY@@');config['prefix']=save(left,'prefix');config['suffix']=save(right,'suffix');configs[r['route']]=config
 for rec in [r,a]:rec['pieces']=['.generated/chrome/'+rec['name']+'/prefix.html',None,'.generated/chrome/'+rec['name']+'/suffix.html']
 if i%250==0:print(i,flush=True)
for root,manifest in [(ROOT,human),(ROOT.parent/'docker-agent',agent)]:
 (root/'data/chrome.json').write_text(json.dumps(configs,ensure_ascii=False,indent=2)+'\n');(root/'data/composition.json').write_text(json.dumps(manifest,indent=2)+'\n')
 if root!=ROOT:
  for path in shared:
   target=root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
print('Shell profiles',len(configs),'shared fragments',len(shared),flush=True)
