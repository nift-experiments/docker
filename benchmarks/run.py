#!/usr/bin/env python3
"""Serialized, cache-labelled component/full publication measurements.

Run only after parity acceptance and with no other build/browser task running.
Setup and analysis are excluded. No OS cache eviction or cold-machine claim.
"""
from pathlib import Path
import json,os,time,subprocess,argparse,statistics,re,shutil
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
p=argparse.ArgumentParser();p.add_argument('--repetitions',type=int,default=5);p.add_argument('--output',type=Path,default=BASE/'docker-baseline/c6');p.add_argument('--projects',default='hugo,docker,docker-agent');args=p.parse_args();OUT=args.output.resolve();
if (OUT/'runs.json').exists():raise SystemExit('Evidence already exists; choose a new --output directory: '+str(OUT))
OUT.mkdir(parents=True,exist_ok=True)
TOOLS=BASE/'docker-baseline/tools';env=dict(os.environ,PATH=str(TOOLS/'node-v24.21.0-linux-x64/bin')+':'+str(TOOLS)+':'+os.environ['PATH'],NODE_ENV='production',GOTOOLCHAIN='local');results=[]
def timed(command,cwd,directory,name):
 directory.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
 with (directory/(name+'.log')).open('w') as log:subprocess.run(['/usr/bin/time','-v','-o',str(directory/(name+'.time')),*map(str,command)],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 wall=time.perf_counter()-started;text=(directory/(name+'.time')).read_text();rss=int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',text).group(1));return {'wall_s':wall,'peak_rss_kib':rss,'command':list(map(str,command))}
for project in args.projects.split(','):
 if project=='hugo':
  root=ROOT/'.cache/benchmark-hugo'
  if not root.exists():raise SystemExit('Prepare .cache/benchmark-hugo as a full-history local clone outside timings.')
 else:root=BASE/project
 for repetition in range(args.repetitions):
  directory=OUT/project/f'full-{repetition+1}';directory.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
  if project=='hugo':
   site=directory/'site';cache=OUT/'hugo-cache';env['HUGO_CACHEDIR']=str(cache)
   components={}
   commands=[('hugo',[TOOLS/'hugo','--gc','--minify','--panicOnWarning','--printPathWarnings','--printUnusedTemplates','-b','https://docs.docker.com','-e','production','--destination',site]),('flatten-tests',['node','--test','hack/test/flatten-and-resolve.mjs']),('flatten',['node','hack/flatten-and-resolve.js',site]),('api-verify',['node','hack/api-docs/verify-output.mjs',site]),('pagefind',['node',ROOT/'.cache/publication-tools/node_modules/pagefind/lib/runner/bin.cjs','--site',site,'--output-path',site/'pagefind'])]
   for name,command in commands:components[name]=timed(command,root,directory,name)
   value={'project':project,'repetition':repetition+1,'mode':'full fresh destination; warm dependencies; application cache reused','wall_s':time.perf_counter()-started,'components':components,'peak_rss_kib':max(v['peak_rss_kib'] for v in components.values())}
  else:
   measure=timed(['python3','scripts/build.py','--all'],root,directory,'pipeline');value={'project':project,'repetition':repetition+1,'mode':'forced full; warm dependencies and application caches',**measure,'components':json.loads((root/'.generated/build-report.json').read_text())}
  results.append(value);(OUT/'runs.json').write_text(json.dumps(results,indent=2)+'\n');print(project,repetition+1,round(value['wall_s'],3),flush=True)
  # Fresh Hugo destinations are benchmark-owned and expensive (~1 GiB each).
  # Keep the last full publication for verification; retire earlier copies.
  if project=='hugo' and repetition+1<args.repetitions:shutil.rmtree(directory/'site')
summary={project:{'samples':len(vs),'median_s':statistics.median(v['wall_s'] for v in vs),'min_s':min(v['wall_s'] for v in vs),'max_s':max(v['wall_s'] for v in vs),'median_peak_rss_kib':statistics.median(v['peak_rss_kib'] for v in vs)} for project in args.projects.split(',') if (vs:=[v for v in results if v['project']==project])};(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
