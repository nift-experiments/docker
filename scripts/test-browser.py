#!/usr/bin/env python3
import os
"""Compare 192 states, corrected behavior fixtures and initial viewport images."""
from pathlib import Path
import json,re,sys,collections
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'docker-baseline';references={}
for folder in ['browser-v2','api-supplement']:
 for row in json.loads((BASE/'c1'/folder/'observations.json').read_text())['records']:references[(row['family'],row['width'],row['mode'])]=(row,BASE/'c1'/folder)
behavior={}
for row in json.loads((BASE/'c1/behavior/observations.json').read_text())['records']:behavior[(row['family'],row['width'],row['mode'])]=row
key=lambda r:(r['family'],r['width'],r['mode']);norm=lambda v:re.sub(r'\s+',' ',v).strip()
for name in sys.argv[1:] or ['human','agent']:
 folder=Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(BASE/'c5')))/(name+'-browser');rows=json.loads((folder/'observations.json').read_text())['records'];differences=[];visual=[];behaviors=[]
 for row in rows:
  old,refdir=references[key(row)];fields=[]
  for field,value in old['initial'].items():
   if field=='activeElement':continue # explicit keyboard/focus controls tested separately
   actual=row['initial'].get(field)
   if field=='headings':value=[(tag,id,norm(text)) for tag,id,text in value];actual=[(tag,id,norm(text)) for tag,id,text in actual]
   if value!=actual:fields.append(field)
  if old['status']!=row['status']:fields.append('status')
  if old['errors']!=row['errors']:fields.append('errors')
  if fields:differences.append({'state':key(row),'fields':fields})
  if 'behaviors' in row:
   reference=behavior.get(key(row),old).get('behaviors',{});current=row['behaviors']
   mismatches=[]
   for field,value in reference.items():
    actual=current.get(field)
    if field=='search-keyboard':
     clean=lambda v:re.sub(r'pf(?:mod-input|-input-hint)-[a-z-]+','GENERATED-ID',json.dumps(v,sort_keys=True))
     equal=clean(value)==clean(actual)
    elif field=='copy-markdown' and value.get('export'):
     import hashlib
     path=value['export'].removeprefix('https://docs.docker.com').lstrip('/');project='docker' if name=='human' else 'docker-agent'
     equal=actual.get('export')==value['export'] and actual.get('length',0)>0 and actual.get('sha256')==hashlib.sha256((ROOT.parent/project/'public'/path).read_bytes()).hexdigest()
    elif field=='tabs' and value and 'visible' in value:
     av=value['visible'];bv=actual.get('visible',[]);equal=value.get('selected')==actual.get('selected') and len(av)==len(bv) and all(norm(x).startswith(norm(y)) or norm(y).startswith(norm(x)) for x,y in zip(av,bv))
    else:equal=value==actual
    if not equal:mismatches.append(field)
   if mismatches:behaviors.append({'state':key(row),'fields':mismatches,'expected':reference,'actual':current})
  a=Image.open(refdir/old['screenshot']['file']).convert('RGB');b=Image.open(folder/row['screenshot']['file']).convert('RGB')
  if a.size!=b.size:visual.append({'state':key(row),'size_mismatch':[a.size,b.size]});continue
  difference=ImageChops.difference(a,b);mae=sum(ImageStat.Stat(difference).mean)/3;visual.append({'state':key(row),'mean_absolute_rgb_error':mae,'pixel_identical':difference.getbbox() is None})
 summary={'states':len(rows),'unique_states':len(set(map(key,rows))),'dom_differences':differences,'behavior_differences':behaviors,'visual':visual,'maximum_visual_mae':max((v.get('mean_absolute_rgb_error',255) for v in visual),default=255),'pixel_identical_states':sum(v.get('pixel_identical',False) for v in visual)};(Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(BASE/'c5')))/(name+'-browser-parity.json')).write_text(json.dumps(summary,indent=2)+'\n');print(name,{k:len(v) if isinstance(v,list) else v for k,v in summary.items() if k!='visual'});print(differences[:6]);print([(v['state'],v.get('mean_absolute_rgb_error')) for v in sorted(visual,key=lambda v:v.get('mean_absolute_rgb_error',255),reverse=True)[:8]]);print([(v['state'],list(v['actual'])) for v in behaviors[:6]])

 assert summary['states']==192 and summary['unique_states']==192 and not summary['dom_differences'] and not summary['behavior_differences'] and summary['pixel_identical_states']==192, 'Browser parity failed'
