#!/usr/bin/env python3
import os
"""Full HTML contract and fresh indexed-search corpus comparison."""
from pathlib import Path
import gzip,json,re,sys,collections
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1];BASE=ROOT.parent/'docker-baseline';OUT=Path(os.environ.get('DOCKER_EVIDENCE_ROOT',str(BASE/'c5')))/ROOT.name;OUT.mkdir(parents=True,exist_ok=True)
def pages(path):
 with gzip.open(path/'pages.json.gz','rt') as f:return {r['route']:r for r in json.load(f)}
a=pages(ROOT/'investigation/inventory');b=pages(OUT/'inventory');diff=[]
for route,expected in a.items():
 actual=b.get(route)
 if not actual:diff.append({'route':route,'fields':['missing']});continue
 fields=[]
 for field in ['title','meta','links','assets','ids','hrefs','json_ld']:
  aa,bb=expected[field],actual[field]
  if field=='json_ld':
   aa=[json.loads(s) if isinstance(s,str) else s for s in aa];bb=[json.loads(s) if isinstance(s,str) else s for s in bb]
  if aa!=bb:fields.append(field)
 if fields:diff.append({'route':route,'fields':fields})
def fragments(site):
 values={}
 for path in (site/'pagefind/fragment').glob('*'):
  v=json.loads(gzip.decompress(path.read_bytes()).removeprefix(b'pagefind_dcd'));values[v['url']]=v
 return values
fa,fb=fragments(BASE/'site'),fragments(ROOT/'public');search=[];punctuation=0
for route,expected in fa.items():
 actual=fb.get(route)
 if not actual:search.append({'route':route,'fields':['missing']});continue
 fields=[]
 for field in expected:
  if field=='content':
   if expected[field]!=actual[field]:punctuation+=1
   # Pagefind inserts sentence separators at HTML block boundaries. Keep
   # those literal differences visible, and require all words, per-page
   # counts, metadata and every anchor/location to match.
   if re.findall(r"[\w'-]+",expected[field])!=re.findall(r"[\w'-]+",actual[field]):fields.append(field)
  elif expected[field]!=actual[field]:fields.append(field)
 if fields:search.append({'route':route,'fields':fields})
result={'html_pages':len(a),'missing_routes':sorted(a.keys()-b.keys()),'extra_routes':sorted(b.keys()-a.keys()),'html_differences':diff,'html_field_counts':dict(collections.Counter(k for d in diff for k in d['fields'])),'indexed_pages':len(fb),'search_differences':search,'pagefind_block_punctuation_differences':punctuation};(OUT/'site-parity.json').write_text(json.dumps(result,indent=2)+'\n');print({k:len(v) if isinstance(v,list) else v for k,v in result.items()});print(diff[:12]);print(search[:5])

assert not result['missing_routes'] and not result['extra_routes'] and not result['html_differences'] and not result['search_differences'], 'Site parity failed'
