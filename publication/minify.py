"""Pinned standalone publication minification, measured separately."""
import hashlib,json,subprocess,time

def minify(root,force=False):
 start=time.perf_counter();statefile=root/'.generated/minify-state.json';previous=json.loads(statefile.read_text()) if statefile.exists() else {};state=previous.get('pages',{});nextstate={};pending=[]
 binary=root/'.cache/html-minifier'
 if not binary.exists():raise RuntimeError('Publication minifier missing: run scripts/build.py --setup')
 implementation=hashlib.sha256(binary.read_bytes()).hexdigest()
 force=force or previous.get('implementation')!=implementation
 scan_start=time.perf_counter()
 for file in sorted((root/'public').rglob('*.html')):
  if 'pagefind' in file.parts:continue
  key=file.relative_to(root/'public').as_posix()
  if force:pending.append(file);continue
  digest=hashlib.sha256(file.read_bytes()).hexdigest();nextstate[key]=digest
  if state.get(key)!=digest:pending.append(file)
 scan_wall=time.perf_counter()-scan_start;worker_start=time.perf_counter();workers=0;svg_metrics={}
 if pending:
  response=subprocess.run([str(binary)],input=json.dumps({'Paths':list(map(str,pending)),'Workers':8})+'\n',capture_output=True,text=True,check=True)
  result=json.loads(response.stdout);workers=result['workers'];svg_metrics={k:v for k,v in result.items() if k.startswith('svg_cache_')}
  for item in result['results']:
   if item.get('error'):raise RuntimeError(item)
   nextstate[str(__import__('pathlib').Path(item['path']).relative_to(root/'public'))]=item['digest']
 worker_wall=time.perf_counter()-worker_start
 statefile.parent.mkdir(parents=True,exist_ok=True);statefile.write_text(json.dumps({'implementation':implementation,'pages':nextstate},sort_keys=True)+'\n')
 return {'html_minification_s':time.perf_counter()-start,'minification_scan_hash_s':scan_wall,'minification_workers_s':worker_wall,'minification_workers':workers,'minified_pages':len(pending),**svg_metrics}
