#!/usr/bin/env python3
"""One-time HTML migration metadata for nonvisible diagram/alert source text."""
from pathlib import Path
import json,sys,re,html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'));from extract import Spans
agent=ROOT.parent/'docker-agent';byroute={v['route']:v for v in json.loads((agent/'data/composition.json').read_text())['pages']};changed=0;attributes=0
for rec in json.loads((ROOT/'data/composition.json').read_text())['pages']:
 if rec.get('kind')=='auxiliary':continue
 human=(ROOT/rec['body']).read_text();target=agent/byroute[rec['route']]['body'];source=target.read_text();hn=Spans(human).nodes;an=Spans(source).nodes;edits=[]
 for tag,attribute in [('blockquote','data-export-alert-marker'),('div','data-export-code'),('button','data-export-code')]:
  select=lambda ns:[n for n in ns if n.tag==tag and (tag in ['blockquote','button'] or 'goat' in n.attrs.get('class','').split())]
  hs,aa=select(hn),select(an)
  if len(hs)!=len(aa):raise ValueError((rec['route'],tag,len(hs),len(aa)))
  for h,a in zip(hs,aa):
   if h.attrs.get(attribute)!=a.attrs.get(attribute):
    opening=source[a.start:a.open_end];opening=re.sub(r'\s'+attribute+r'=(?:"[^"]*"|[^ >]+)','',opening)
    if attribute in h.attrs:opening=opening[:-1]+' '+attribute+'="'+html.escape(h.attrs[attribute],quote=True)+'">'
    edits.append((a.start,a.open_end,opening));attributes+=1
 for start,end,value in sorted(edits,reverse=True):source=source[:start]+value+source[end:]
 contracts=[human[n.start:n.end] for n in hn if n.tag=='template' and 'data-export-contracts' in n.attrs]
 if contracts:
  source=re.sub(r'<template data-export-contracts="[^"]*"></template>','',source)+''.join(contracts)
  if source!=target.read_text() and not edits:edits.append((0,0,''))
 if edits:target.write_text(source);changed+=1
print('Annotated maintained HTML pages',changed,'export-only attributes',attributes)
