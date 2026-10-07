#!/usr/bin/env python3
"""Warm Hugo CLI full publications after equivalent edits; not Hugo server timings."""
from pathlib import Path
import subprocess,json,os,time,re,statistics,shutil
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;root=ROOT/'.cache/benchmark-hugo';OUT=BASE/'docker-baseline/c6/hugo-changed';OUT.mkdir(parents=True,exist_ok=True);TOOLS=BASE/'docker-baseline/tools';env=dict(os.environ,PATH=str(TOOLS/'node-v24.21.0-linux-x64/bin')+':'+os.environ['PATH'],NODE_ENV='production',HUGO_CACHEDIR=str(BASE/'docker-baseline/c6/hugo-cache'));runs=json.loads((OUT/'runs.json').read_text()) if '--resume' in __import__('sys').argv and (OUT/'runs.json').exists() else [];site=OUT/'site';temporary=ROOT/'.cache/benchmark-tmp';temporary.mkdir(parents=True,exist_ok=True);env['TMPDIR']=str(temporary)
commands=[('hugo',[TOOLS/'hugo','--gc','--minify','--panicOnWarning','--printPathWarnings','--printUnusedTemplates','-b','https://docs.docker.com','-e','production','--destination',site]),('flatten-tests',['node','--test','hack/test/flatten-and-resolve.mjs']),('flatten',['node','hack/flatten-and-resolve.js',site]),('api-verify',['node','hack/api-docs/verify-output.mjs',site]),('pagefind',['node',ROOT/'.cache/publication-tools/node_modules/pagefind/lib/runner/bin.cjs','--site',site,'--output-path',site/'pagefind'])]
records=json.loads((ROOT/'data/composition.json').read_text())['pages'];pages=[v for v in records if v.get('family')=='ordinary' and v.get('source','').startswith('authored/content/')];ubuntu=next(v for v in pages if v['route']=='/engine/install/ubuntu/');pages=[ubuntu]+[v for v in pages if v!=ubuntu]
for case in ['1-page','10-pages','100-pages','layout','navigation','metadata']:
 for i in range(5):
  if any(v['case']==case and v['iteration']==i+1 for v in runs):continue
  saved={};sentinel=f'C6 {case} iteration {i+1} sentinel'
  def save(path,value):saved[path]=path.read_bytes();path.write_bytes(value)
  if case.endswith(('page','pages')):
   for v in pages[:int(case.split('-')[0])]:
    p=root/v['source'].removeprefix('authored/');save(p,p.read_bytes()+('\n\n'+sentinel+'\n').encode())
  elif case=='layout':
   p=root/'layouts/_partials/footer.html';save(p,p.read_bytes()+('<p>'+sentinel+'</p>').encode())
  else:
   p=root/ubuntu['source'].removeprefix('authored/');text=p.read_text()
   if case=='metadata':text,n=re.subn(r'(?m)^title:.*$',lambda _:'title: '+sentinel,text,count=1);assert n
   else:
    text,n=re.subn(r'(?m)^linkTitle:.*$',lambda _:'linkTitle: '+sentinel,text,count=1)
    if not n:text=text.replace('---\n','---\nlinkTitle: '+sentinel+'\n',1)
   save(p,text.encode())
  try:
   directory=OUT/case/str(i+1);directory.mkdir(parents=True,exist_ok=True);started=time.perf_counter();components={}
   for name,command in commands:
    phase=time.perf_counter()
    if name=='pagefind':shutil.rmtree(site/'pagefind',ignore_errors=True)
    with (directory/(name+'.log')).open('w') as log:subprocess.run(['/usr/bin/time','-v','-o',str(directory/(name+'.time')),*map(str,command)],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    components[name]={'wall_s':time.perf_counter()-phase,'peak_rss_kib':int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',(directory/(name+'.time')).read_text()).group(1))}
   row={'project':'hugo','case':case,'iteration':i+1,'mode':'warm CLI full publication after edit; not server incremental','wall_s':time.perf_counter()-started,'peak_rss_kib':max(v['peak_rss_kib'] for v in components.values()),'components':components};targets=pages[:int(case.split('-')[0])] if case.endswith(('page','pages')) else [ubuntu]
   for rec in targets:
    text=(site/(rec['name']+'.html')).read_text();assert sentinel in text,(case,rec['route'],'sentinel missing')
    if case.endswith(('page','pages')) or case=='metadata':assert sentinel in (site/(rec['route'].strip('/')+'.md')).read_text(),(case,'download stale')
   row['semantic_output_checked']=True;runs.append(row);(OUT/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print('hugo',case,i+1,round(row['wall_s'],3),flush=True)
  finally:
   for p,value in saved.items():p.write_bytes(value)
(OUT/'summary.json').write_text(json.dumps({case:statistics.median(v['wall_s'] for v in runs if v['case']==case) for case in ['1-page','10-pages','100-pages','layout','navigation','metadata']},indent=2)+'\n')
