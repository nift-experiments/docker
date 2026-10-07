"""Analyze maintained/rendered HTML once for TOCs and retrieval exports.

Full builds regenerate every analysis. Incremental caches are keyed by source
bytes, title/export policy and both analyzer and exporter implementations.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import hashlib,json,time,re,os,multiprocessing
from dataclasses import asdict
from .html_to_markdown import Document,Node,convert

def analyze_page(job):
 path,title,policy,base,need_headings=job;body=Path(path).read_text();started=time.perf_counter();document=Document(body).root;parsed=time.perf_counter()-started
 headings=[]
 def walk(n):
  for c in n.children:
   if isinstance(c,Node):yield c;yield from walk(c)
 if need_headings:headings=[asdict(n) for n in walk(document) if n.tag in ['h1','h2','h3','h4','h5','h6'] and 'scroll-mt-20' in n.attrs.get('class','') and n.attrs.get('id')]
 started=time.perf_counter();text='# '+title+'\n' if policy=='header-only' else convert(body,title,document=document)
 if '<redoc ' in body:
  spec=re.search(r'''spec-url=["']?([^"' >]+)''',body).group(1);spec=spec if spec.startswith('http') else base+spec
  text='# '+title+'\n\n\n\n**OpenAPI Specification:** ['+title+' API Spec]('+spec+')\n\nThis page provides interactive API documentation. For the machine-readable OpenAPI specification, see the link above.\n'
 return {'headings':headings,'markdown':text},parsed,time.perf_counter()-started

def prepare(root,manifest,model,force=False):
 started=time.perf_counter();statefile=root/'.generated/analysis-state.json';state=json.loads(statefile.read_text()) if statefile.exists() else {};nextstate={};results={};jobs=[];keys=[];paths={};scan_start=time.perf_counter()
 implementation=hashlib.sha256(Path(__file__).read_bytes()+(root/'publication/html_to_markdown.py').read_bytes()).hexdigest()
 for record in manifest['pages']:
  if record.get('kind')=='auxiliary':continue
  route=record['route'];meta=model['pages'][route];body=root/record['body'];headings=record.get('family')=='ordinary' and record.get('model') in ['markdown','maintained-html'];fingerprint=hashlib.sha256(body.read_bytes()+json.dumps([implementation,meta['title'],meta.get('export'),model['base_url'],headings]).encode()).hexdigest();nextstate[route]=fingerprint;path=root/'.generated/analysis'/(hashlib.sha256(route.encode()).hexdigest()+'.json');paths[route]=path
  if not force and state.get(route)==fingerprint and path.exists():results[record['body']]=json.loads(path.read_text());continue
  keys.append((route,record['body']));jobs.append((str(body),meta['title'],meta.get('export'),model['base_url'],headings))
 scan_wall=time.perf_counter()-scan_start;workers=min(4,len(jobs),os.cpu_count() or 1);parsed=converted=0.;worker_start=time.perf_counter()
 if jobs:
  with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('fork')) as pool:
   for (route,body),(result,parse_time,convert_time) in zip(keys,pool.map(analyze_page,jobs,chunksize=8)):
    parsed+=parse_time;converted+=convert_time;results[body]=result;path=paths[route];path.parent.mkdir(parents=True,exist_ok=True);value=json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n'
    if not path.exists() or path.read_text()!=value:path.write_text(value)
 worker_wall=time.perf_counter()-worker_start;statefile.parent.mkdir(parents=True,exist_ok=True);statefile.write_text(json.dumps(nextstate,sort_keys=True)+'\n')
 return results,{'body_analysis_s':time.perf_counter()-started,'analysis_scan_hash_cache_s':scan_wall,'analysis_workers_wall_s':worker_wall,'analysis_workers':workers,'analyzed_pages':len(jobs),'worker_html_parse_wall_sum_s':parsed,'worker_download_conversion_wall_sum_s':converted}

def heading_nodes(values):
 def node(value):return value if isinstance(value,str) else Node(value['tag'],value['attrs'],[node(v) for v in value['children']])
 return [node(v) for v in values]
