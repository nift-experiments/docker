#!/usr/bin/env python3
"""Five repeated changed-input publications, plus forced-full correctness.

Every measured edit is restored and rebuilt outside its timed interval. Case
names identify equivalent output intentions, not identical authoring formats.
"""
from pathlib import Path
import os,json,time,subprocess,re,hashlib,statistics,copy
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent;OUT=BASE/'docker-baseline/c6/changed';OUT.mkdir(parents=True,exist_ok=True);env=dict(os.environ,PATH=str(BASE/'docker-baseline/tools/node-v24.21.0-linux-x64/bin')+':'+os.environ['PATH']);results=[]
def hashes(root):return {p.relative_to(root/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'public').rglob('*') if p.is_file()}
def build(root,full=False,log=None):
 command=['python3','scripts/build.py',*(['--all'] if full else [])]
 if log:command=['/usr/bin/time','-v','-o',str(log.with_suffix('.time')),*command]
 with open(log or os.devnull,'w') as f:subprocess.run(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
for project in ['docker','docker-agent']:
 root=BASE/project;manifest=json.loads((root/'data/composition.json').read_text());pages=[v for v in manifest['pages'] if v.get('family')=='ordinary' and (project=='docker-agent' or v.get('source','').startswith('authored/content/'))];ubuntu=next(v for v in pages if v['route']=='/engine/install/ubuntu/');pages=[ubuntu]+[v for v in pages if v!=ubuntu];chrome=json.loads((root/'data/chrome.json').read_text());build(root);baseline=hashes(root)
 for case in ['1-page','10-pages','100-pages','layout','navigation','metadata']:
  directory=OUT/project/case;directory.mkdir(parents=True,exist_ok=True)
  for iteration in range(5):
   saved={};sentinel=f'C6 {case} iteration {iteration+1} sentinel'
   def save(path,value):saved[path]=path.read_bytes();path.write_bytes(value)
   if case.endswith(('page','pages')):
    count=int(case.split('-')[0])
    for record in pages[:count]:
     path=root/(record['source'] if project=='docker' else record['body']);save(path,path.read_bytes()+('\n\n'+sentinel+'\n' if project=='docker' else '<p>'+sentinel+'</p>').encode())
   elif case=='layout':
    path=root/chrome[ubuntu['route']]['slots']['FOOTER'];save(path,path.read_bytes()+('<p>'+sentinel+'</p>').encode())
   elif case=='navigation':
    path=root/'data/navigation.json';data=json.loads(path.read_text());node=next(v for v in data['nodes'].values() if v.get('route')==ubuntu['route']);key='label' if 'label' in node else 'title';node[key]=sentinel;save(path,(json.dumps(data,ensure_ascii=False)+'\n').encode())
   elif project=='docker':
    path=root/ubuntu['source'];text=path.read_text();text,n=re.subn(r'(?m)^title:.*$',lambda _: 'title: '+sentinel,text,count=1);assert n;save(path,text.encode())
   else:
    path=root/'data/publication.json';data=json.loads(path.read_text());page=data['pages'][ubuntu['route']];page['title']=sentinel
    for meta in page['meta']:
     if (meta.get('name') or meta.get('property')) in ['twitter:title','og:title']:meta['content']=sentinel
    for schema in page['schema']:
     if schema.get('@type')=='TechArticle':schema['headline']=sentinel
     elif schema.get('@type')=='BreadcrumbList':schema['itemListElement'][-1]['item']['name']=sentinel
    save(path,(json.dumps(data,ensure_ascii=False)+'\n').encode())
   try:
    started=time.perf_counter();build(root,log=directory/f'{iteration+1}.log');wall=time.perf_counter()-started;partial=hashes(root);components=json.loads((root/'.generated/build-report.json').read_text());changed=[p for p in baseline if baseline[p]!=partial.get(p)];assert changed,(project,case,'no output changed')
    targets=pages[:int(case.split('-')[0])] if case.endswith(('page','pages')) else [ubuntu]
    for rec in targets:
     text=(root/'public'/(rec['name']+'.html')).read_text();assert sentinel in text,(project,case,rec['route'],'sentinel missing')
     if case.endswith(('page','pages')) or case=='metadata':assert sentinel in (root/'public'/(rec['route'].strip('/')+'.md')).read_text(),(project,case,'download stale')
    if case=='metadata':assert '<title>'+sentinel in text,(project,case,'title stale')
    if iteration==0:
     build(root,True);assert hashes(root)==partial,(project,case,'incremental != full')
    result={'project':project,'case':case,'iteration':iteration+1,'wall_s':wall,'peak_rss_kib':int(re.search(r'Maximum resident set size \(kbytes\): (\d+)',(directory/f'{iteration+1}.time').read_text()).group(1)),'edited_routes':[v['route'] for v in pages[:int(case.split('-')[0])]] if case.endswith(('page','pages')) else [ubuntu['route']],'semantic_output_checked':True,'changed_outputs':len(changed),'components':components,'incremental_equals_full':iteration==0};results.append(result);(OUT/'runs.json').write_text(json.dumps(results,indent=2)+'\n');print(project,case,iteration+1,round(wall,3),flush=True)
   finally:
    for path,value in saved.items():path.write_bytes(value)
    build(root)
   assert hashes(root)==baseline,(project,case,'restoration failed')
summary={project:{case:statistics.median(r['wall_s'] for r in results if r['project']==project and r['case']==case) for case in ['1-page','10-pages','100-pages','layout','navigation','metadata']} for project in ['docker','docker-agent']};(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
