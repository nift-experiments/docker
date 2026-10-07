"""Two-pass shell extraction with bounded memory for the full Docker corpus.

Only exact repeated non-body subtrees are shared. Values are materialized during
pass two, avoiding retaining the complete publication or nested HTML copies.
"""
from pathlib import Path
from collections import Counter
import hashlib,re
from extract import frame

def extract_stream(documents,root,body_frame=None):
 root=Path(root);counts=Counter();labels={}
 for name,file in documents.items():
  source=file.read_text()
  try:nodes,start,end=body_frame(source,name) if body_frame else frame(source)
  except StopIteration:raise ValueError('no composition body in '+str(file))
  seen=set()
  for n in nodes:
   if not n.end or not(n.end<=start or n.start>=end) or n.end-n.start<1024:continue
   digest=hashlib.sha256(source[n.start:n.end].encode()).hexdigest();seen.add(digest)
   labels.setdefault(digest,n.tag+'-'+re.sub(r'[^a-zA-Z0-9_-]','-',n.attrs.get('id') or n.attrs.get('class','').split(' ')[0])[:45])
  counts.update(seen)
 shared={h:'layouts/shared/'+labels[h]+'-'+h[:12]+'.html' for h,c in counts.items() if c>=2};used=set();result={}
 for name,file in documents.items():
  source=file.read_text();nodes,start,end=body_frame(source,name) if body_frame else frame(source);selected=[]
  for n in sorted(nodes,key=lambda n:(n.start,-n.end)):
   if not n.end or not(n.end<=start or n.start>=end) or n.end-n.start<1024:continue
   if any(n.start<e and n.end>s for s,e,_ in selected):continue
   digest=hashlib.sha256(source[n.start:n.end].encode()).hexdigest()
   if digest in shared:
    selected.append((n.start,n.end,shared[digest]));dest=root/shared[digest]
    if shared[digest] not in used:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(source[n.start:n.end]);used.add(shared[digest])
  pieces=[];cursor=0;gap=0
  for s,e,file in sorted([*selected,(start,end,None)]):
   if s>cursor:
    path='layouts/pages/'+name+'/frame-'+str(gap)+'.html';dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(source[cursor:s]);pieces.append(path);gap+=1
   pieces.append(file);cursor=e
  if cursor<len(source):
   path='layouts/pages/'+name+'/frame-'+str(gap)+'.html';dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(source[cursor:]);pieces.append(path)
  result[name]={'pieces':pieces,'body':source[start:end]}
 return result,{'shared_candidates':len(shared),'shared_used':len(used),'rule':'Exact shell subtrees >=1024 characters shared by at least two documents; body excluded; two-pass bounded-memory extraction.'}
