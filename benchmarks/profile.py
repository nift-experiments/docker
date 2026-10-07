#!/usr/bin/env python3
"""Serialized diagnostic profiles; instrumentation overhead is not a benchmark."""
from pathlib import Path
import subprocess,os,pstats,json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=BASE/'docker-optimization/initial-profile';OUT.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,PATH=str(BASE/'docker-baseline/tools/node-v24.21.0-linux-x64/bin')+':'+os.environ['PATH'])
for name in ['docker','docker-agent']:
 root=BASE/name
 def hashes():return {p.relative_to(root/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'public').rglob('*') if p.is_file()}
 accepted=hashes();(OUT/(name+'-accepted-hashes.json')).write_text(json.dumps(accepted,sort_keys=True)+'\n')
 with (OUT/(name+'.log')).open('w') as log:subprocess.run(['python3','-m','cProfile','-o',str(OUT/(name+'.prof')),'scripts/build.py','--all'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert hashes()==accepted,(name,'profile changed accepted output')
 report=json.loads((root/'.generated/build-report.json').read_text());(OUT/(name+'-components.json')).write_text(json.dumps(report,indent=2)+'\n')
 with (OUT/(name+'-cumulative.txt')).open('w') as f:pstats.Stats(str(OUT/(name+'.prof')),stream=f).strip_dirs().sort_stats('cumulative').print_stats(90)
 print(name,'diagnostic profile complete; output hashes unchanged',flush=True)
