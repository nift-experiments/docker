"""Pinned standalone publication minification, measured separately."""
import hashlib,json,subprocess,time
from pathlib import Path

def minify(root,force=False):
 start=time.perf_counter();statefile=root/'.generated/minify-state.json';state=json.loads(statefile.read_text()) if statefile.exists() else {};nextstate={};count=0
 binary=root/'.cache/html-minifier'
 if not binary.exists():raise RuntimeError('Publication minifier missing: run scripts/build.py --setup')
 process=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 try:
  for file in sorted((root/'public').rglob('*.html')):
   if 'pagefind' in file.parts:continue
   key=file.relative_to(root/'public').as_posix();digest=hashlib.sha256(file.read_bytes()).hexdigest()
   if force or state.get(key)!=digest:
    process.stdin.write(json.dumps({'Path':str(file)})+'\n');process.stdin.flush();result=json.loads(process.stdout.readline())
    if result.get('error'):raise RuntimeError(result)
    digest=hashlib.sha256(file.read_bytes()).hexdigest();count+=1
   nextstate[key]=digest
 finally:
  process.stdin.close();process.wait()
 if process.returncode:raise RuntimeError('Minifier failed')
 statefile.parent.mkdir(parents=True,exist_ok=True);statefile.write_text(json.dumps(nextstate,sort_keys=True)+'\n')
 return {'html_minification_s':time.perf_counter()-start,'minified_pages':count}
