#!/usr/bin/env python3
"""C4 changed-input proof over all outputs, including regenerated retrieval/search."""
from pathlib import Path
import hashlib,json,subprocess,sys
BASE=Path(__file__).resolve().parents[2];result=[]
for name in sys.argv[1:] or ['docker','docker-agent']:
 root=BASE/name;manifest=json.loads((root/'data/composition.json').read_text());rec=next(v for v in manifest['pages'] if v['route']=='/engine/install/ubuntu/');chrome=json.loads((root/'data/chrome.json').read_text())
 def hashes():return {p.relative_to(root/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'public').rglob('*') if p.is_file()}
 def build(all=False):subprocess.run(['python3','scripts/build.py',*(['--all'] if all else [])],cwd=root,check=True,stdout=subprocess.DEVNULL)
 build();baseline=hashes()
 for case,path in [('content',root/(rec.get('source') or rec['body'])),('layout',root/chrome[rec['route']]['slots']['FOOTER'])]:
  saved=path.read_bytes()
  try:
   path.write_bytes(saved+b'\n<p data-c4-dependency-proof>Dependency proof sentinel.</p>\n');build();partial=hashes();build(True);full=hashes();assert partial==full,(name,case,'incremental/full mismatch')
   changed=[v for v in baseline if baseline[v]!=partial.get(v)];assert 'engine/install/ubuntu/index.html' in changed
   if case=='content':assert 'engine/install/ubuntu.md' in changed
   result.append({'project':name,'case':case,'changed_outputs':len(changed),'incremental_equals_full':True})
  finally:path.write_bytes(saved);build()
  assert hashes()==baseline,(name,case,'restored outputs differ')
  print(result[-1],flush=True)
(BASE/'docker-baseline/c4/dependencies.json').write_text(json.dumps(result,indent=2)+'\n')
