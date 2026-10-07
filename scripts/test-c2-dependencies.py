from pathlib import Path
import json,hashlib,subprocess,time
root=Path(__file__).resolve().parents[2]
results=[]
for repo in ['docker','docker-agent']:
 p=root/repo;m=json.loads((p/'data/composition.json').read_text());ordinary=next(x for x in m['pages'] if x['route']=='/engine/install/ubuntu/')
 def hashes():return {x['route']:hashlib.sha256((p/'public'/x['route'].strip('/')/'index.html').read_bytes()).hexdigest() for x in m['pages']}
 def build(full=False):subprocess.run(['python3','scripts/build.py',*(['--all'] if full else [])],cwd=p,check=True,stdout=subprocess.DEVNULL)
 for case,file in [('content',p/(ordinary.get('source') or ordinary['body'])),('shared',p/next(x for x in ordinary['pieces'] if x and x.startswith('layouts/shared/')))]:
  old=file.read_bytes();before=hashes()
  try:
   file.write_bytes(old+b'\n<!-- C2 dependency proof -->\n');build();modified=hashes();build(True);full=hashes()
   changed=[k for k in before if modified[k]!=before[k]]
   assert modified==full,(repo,case,'incremental/full mismatch')
   assert ordinary['route'] in changed,(repo,case,'missing dependent')
   if case=='content':assert changed==[ordinary['route']],changed
   results.append({'project':repo,'case':case,'changed':changed,'incremental_equals_full':True})
  finally:file.write_bytes(old);build()
  assert hashes()==before,(repo,case,'restore mismatch')
out=root/'docker-baseline/c2/dependencies.json';out.write_text(json.dumps(results,indent=2)+'\n');print(out.read_text())
