#!/usr/bin/env python3
import os
"""Whole-publication obligations and retrieval-code preservation against the pin."""
from pathlib import Path
import json,re,sys,hashlib,subprocess,xml.etree.ElementTree as ET
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1];BASE=ROOT.parent/'docker-baseline/site';OUT=ROOT/'public';inventory=json.loads((ROOT/'investigation/inventory/files.json').read_text());files={v['path']:v for v in inventory};paths={p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()};gold={p for p in files if not p.startswith('pagefind/')};actual={p for p in paths if not p.startswith('pagefind/')};result={'missing':sorted(gold-actual),'extra':sorted(actual-gold),'json':{},'text':{},'xml':{},'assets':{},'code_exports':[]}
for name in ['metadata.json','redirects.json']:result['json'][name]=json.loads((OUT/name).read_text())==json.loads((BASE/name).read_text())
for name in ['llms.txt','llms-full.txt','robots.txt']:result['text'][name]=(OUT/name).read_text().strip()==(BASE/name).read_text().strip()
for name in ['sitemap.xml','security/security-announcements/index.xml']:
 props=lambda p:[(n.tag,n.text or '',n.attrib) for n in ET.parse(p).iter() if n.tag!='generator'];result['xml'][name]=props(OUT/name)==props(BASE/name)
assetroot=ROOT/('static' if ROOT.name=='docker' else 'public-assets')
for p in assetroot.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(assetroot).as_posix();result['assets'][rel]=rel in files and hashlib.sha256((OUT/rel).read_bytes()).hexdigest()==files[rel]['sha256']
# Validation only: inspect downloads with the pinned Goldmark parser. Routine
# docker-agent builds do not import or invoke this tool/Markdown parser.
worker=subprocess.Popen([str(ROOT.parent/'docker/.cache/docker-renderer'),'--inspect-fences'],cwd=ROOT.parent/'docker',stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
def fences(text):
 worker.stdin.write(json.dumps({'Markdown':text})+'\n');worker.stdin.flush();response=json.loads(worker.stdout.readline())
 if response.get('Error'):raise RuntimeError(response['Error'])
 return [(value.rstrip(),'') for value in response.get('Fences',[])]

for name in sorted(p for p in gold if p.endswith('.md')):
 expected=fences((BASE/name).read_text());current=fences((OUT/name).read_text());payloads=[v[0] for v in current]
 def equivalent(code):
  if code in payloads:return True
  # Goldmark expands tabs against the Markdown container column. The same
  # preserved XML payload under a differently indented list has different
  # parser whitespace; compare the XML tree, including all scalar values.
  if code.startswith('<?xml'):
   def tree(value):return [(n.tag,n.attrib,(n.text or '').strip()) for n in ET.fromstring(value).iter()]
   for value in payloads:
    if value.startswith('<?xml'):
     try:
      if tree(code)==tree(value):return True
     except ET.ParseError:pass
  return False
 missing=[{'code':code[:160],'language':language} for code,language in expected if not equivalent(code)]
 if missing:result['code_exports'].append({'file':name,'missing':missing,'expected_blocks':len(expected),'actual_blocks':len(current)})
worker.stdin.close();worker.wait()
path=Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(ROOT.parent/'docker-baseline/c4')))/('publication-'+ROOT.name+'.json');path.write_text(json.dumps(result,indent=2)+'\n');print({k:v if isinstance(v,list) and k not in ['code_exports'] else (len(v) if isinstance(v,list) else sum(not x for x in v.values())) for k,v in result.items()});print(result['code_exports'][:3])

assert not result['missing'] and not result['extra'] and not result['code_exports'] and all(all(v.values()) for v in [result['json'],result['text'],result['xml'],result['assets']]), 'Publication parity failed'
