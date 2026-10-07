#!/usr/bin/env python3
"""Prove optimization retained every accepted file and initial benchmark."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=BASE/'docker-optimization/validation';result={}
for name in ['docker','docker-agent']:
 root=BASE/name;accepted=json.loads((BASE/'docker-optimization/initial-profile'/(name+'-accepted-hashes.json')).read_text());actual={p.relative_to(root/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'public').rglob('*') if p.is_file()};assert actual==accepted,name;result[name]={'all_publication_files_byte_identical':len(actual)}
for name in ['human','agent']:
 old=json.loads((BASE/'docker-baseline/c5'/(name+'-controls.json')).read_text());new=json.loads((OUT/(name+'-controls.json')).read_text())
 assert old['browser']==new['browser'] and len(old['results'])==len(new['results'])
 def checks(row):
  import re
  return re.sub(r'http://127\.0\.0\.1:\d+', 'LOCAL_ORIGIN',json.dumps(row['checks'],sort_keys=True))
 assert all(a['width']==b['width'] and checks(a)==checks(b) for a,b in zip(old['results'],new['results'])),(name,'controls changed')
 groups=lambda v:{(r['host'],r['path'],r['method']) for row in v['results'] for r in row['external']}
 assert groups(old)==groups(new),(name,'unexpected external attempt group')
 result[name+'-controls']='all checks identical to C5 after normalizing local server port; external attempts mocked by capture'
for name,digest in json.loads((BASE/'docker-optimization/initial-benchmark-sha256.json').read_text()).items():assert hashlib.sha256((BASE/'docker-baseline/c6'/name).read_bytes()).hexdigest()==digest,name
result['initial_benchmarks']='unchanged';(OUT/'accepted-hash-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
