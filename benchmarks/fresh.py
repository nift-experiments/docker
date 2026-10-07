#!/usr/bin/env python3
"""Application-cold local checkouts; prepared tools excluded; OS caches uncontrolled."""
from pathlib import Path
import subprocess,json,os,time,shutil,re,statistics
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=BASE/'docker-baseline/c6/fresh'
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--projects',default='hugo,docker,docker-agent');parser.add_argument('--repetitions',type=int,default=5);args=parser.parse_args();OUT=args.output.resolve()
if (OUT/'runs.json').exists():raise SystemExit('Evidence already exists; choose a new --output directory: '+str(OUT))
OUT.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,PATH=str(BASE/'docker-baseline/tools/node-v24.21.0-linux-x64/bin')+':'+os.environ['PATH']);runs=[]
for project in args.projects.split(','):
 source=BASE/('docker-upstream' if project=='hugo' else project)
 for i in range(args.repetitions):
  target=ROOT/'.cache'/f'fresh-{project}-{i+1}'
  if target.exists():raise SystemExit('Fresh checkout already exists: '+str(target))
  subprocess.run(['git','clone','--quiet','--local',str(source),str(target)],check=True)
  if project=='hugo':
   (target/'node_modules').symlink_to(BASE/'docker-upstream/node_modules',target_is_directory=True)
   directory=OUT/project/str(i+1);directory.mkdir(parents=True)
   tools=BASE/'docker-baseline/tools';site=target/'public';env['HUGO_CACHEDIR']=str(target/'.cache/hugo');components={};start=time.perf_counter()
   commands=[('hugo',[tools/'hugo','--gc','--minify','--panicOnWarning','--printPathWarnings','--printUnusedTemplates','-b','https://docs.docker.com','-e','production','--destination',site]),('flatten-tests',['node','--test','hack/test/flatten-and-resolve.mjs']),('flatten',['node','hack/flatten-and-resolve.js',site]),('api-verify',['node','hack/api-docs/verify-output.mjs',site]),('pagefind',['node',ROOT/'.cache/publication-tools/node_modules/pagefind/lib/runner/bin.cjs','--site',site,'--output-path',site/'pagefind'])]
   for name,command in commands:
    phase=time.perf_counter()
    with (directory/(name+'.log')).open('w') as log:subprocess.run(['/usr/bin/time','-v','-o',str(directory/(name+'.time')),*map(str,command)],cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    components[name]={'wall_s':time.perf_counter()-phase,'peak_rss_kib':int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',(directory/(name+'.time')).read_text()).group(1))}
   row={'project':project,'iteration':i+1,'mode':'fresh full-history checkout; empty application cache/output; prepared node_modules; uncontrolled OS caches','wall_s':time.perf_counter()-start,'components':components,'peak_rss_kib':max(v['peak_rss_kib'] for v in components.values())};assert len(list(site.rglob('*.html')))==3901;assert len(list(site.rglob('*.md')))==2170;assert 'Indexed 2142 pages' in (directory/'pagefind.log').read_text();row['publication_counts_verified']=True;runs.append(row);(OUT/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(project,'fresh',i+1,round(row['wall_s'],3),flush=True);shutil.rmtree(target);continue
  cache=target/'.cache';cache.mkdir()
  for name in ['docker-renderer','html-minifier','setup-fingerprint']:
   if (source/'.cache'/name).is_file():shutil.copy2(source/'.cache'/name,cache/name)
  (cache/'publication-tools').symlink_to(source/'.cache/publication-tools',target_is_directory=True)
  directory=OUT/project/str(i+1);directory.mkdir(parents=True)
  start=time.perf_counter()
  with (directory/'pipeline.log').open('w') as log:subprocess.run(['/usr/bin/time','-v','-o',str(directory/'pipeline.time'),'python3','scripts/build.py','--all'],cwd=target,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  row={'project':project,'iteration':i+1,'mode':'fresh committed checkout; empty .generated/public; prepared binaries and Pagefind; uncontrolled OS caches','wall_s':time.perf_counter()-start,'components':json.loads((target/'.generated/build-report.json').read_text()),'peak_rss_kib':int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',(directory/'pipeline.time').read_text()).group(1))}
  # Every fresh checkout must produce the same bytes as the accepted source build.
  import hashlib
  def hashes(root):return {p.relative_to(root/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'public').rglob('*') if p.is_file()}
  assert hashes(target)==hashes(source),(project,i,'fresh output mismatch')
  row['fresh_equals_accepted']=True;runs.append(row);(OUT/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(project,'fresh',i+1,round(row['wall_s'],3),flush=True)
  shutil.rmtree(target)
(OUT/'summary.json').write_text(json.dumps({p:{'median_s':statistics.median(r['wall_s'] for r in runs if r['project']==p),'min_s':min(r['wall_s'] for r in runs if r['project']==p),'max_s':max(r['wall_s'] for r in runs if r['project']==p)} for p in args.projects.split(',')},indent=2)+'\n')
