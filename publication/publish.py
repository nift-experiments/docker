#!/usr/bin/env python3
"""Fresh retrieval, discovery, redirects, feeds and search publication.

HTML-to-Markdown export is a publication component. Neither project imports a
Markdown parser here; docker-agent routine builds remain HTML-only.
"""
from pathlib import Path
import sys,json,time,re,subprocess,html,hashlib,shutil,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from publication.discovery import outputs
from publication.html_to_markdown import Document,Node,convert,descendants
ROOT=Path(__file__).resolve().parents[1]
def write_changed(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 if not path.exists() or path.read_text()!=value:path.write_text(value)
def publish(search=True,model=None,force=False,analysis=None):
 started=time.perf_counter();model=model or json.loads((ROOT/'data/publication.json').read_text());manifest=json.loads((ROOT/'data/composition.json').read_text());records=[v for v in manifest['pages'] if v.get('kind')!='auxiliary'];out=ROOT/'public';exports_start=time.perf_counter();exported=0;converted=0;statefile=ROOT/'.generated/export-state.json';state=json.loads(statefile.read_text()) if statefile.exists() else {};nextstate={};exporter=hashlib.sha256((ROOT/'publication/html_to_markdown.py').read_bytes()+Path(__file__).read_bytes()).hexdigest()
 for rec in records:
  meta=model['pages'][rec['route']];title=meta['title'];destination=meta['markdown'].removeprefix(model['base_url']).lstrip('/')
  if analysis is not None:
   text=analysis[rec['body']]['markdown'];fingerprint=hashlib.sha256(text.encode()).hexdigest();nextstate[destination]=fingerprint
   if not force and state.get(destination)==fingerprint and (out/destination).exists():exported+=1;continue
   converted+=1
  else:
   meta=model['pages'][rec['route']];body=(ROOT/rec['body']).read_text();title=meta['title'];destination=meta['markdown'].removeprefix(model['base_url']).lstrip('/')
   fingerprint=hashlib.sha256((exporter+title+body).encode()).hexdigest();nextstate[destination]=fingerprint
   if not force and state.get(destination)==fingerprint and (out/destination).exists():exported+=1;continue
   converted+=1
   text='# '+title+'\n' if meta.get('export')=='header-only' else convert(body,title)
   if '<redoc ' in body:
    spec=re.search(r'''spec-url=["']?([^"' >]+)''',body).group(1);spec=spec if spec.startswith('http') else model['base_url']+spec
    text='# '+title+'\n\n\n\n**OpenAPI Specification:** ['+title+' API Spec]('+spec+')\n\nThis page provides interactive API documentation. For the machine-readable OpenAPI specification, see the link above.\n'
  write_changed(out/destination,text);exported+=1
 for destination in state.keys()-nextstate.keys():
  target=out/destination
  if target.exists():target.unlink()
 statefile.parent.mkdir(parents=True,exist_ok=True);statefile.write_text(json.dumps(nextstate,sort_keys=True)+'\n')
 exports_wall=time.perf_counter()-exports_start;ancillary_start=time.perf_counter()
 write_changed(out/'metadata.json',json.dumps(model['metadata'],ensure_ascii=False,separators=(',',':'))+'\n')
 redirects=model.get('redirects',json.loads((ROOT/'data/redirects-base.json').read_text()));write_changed(out/'redirects.json',json.dumps(redirects,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
 # Structured sitemap rows retain pinned Git-date provenance, ordering and
 # intentional empty-URL behavior; metadata edits update these records.
 def tag(name,value):return '<'+name+'>'+html.escape('' if value is None else str(value),quote=False)+'</'+name+'>'
 xml='<?xml version="1.0" encoding="utf-8" standalone="yes"?><?xml-stylesheet type="text/xsl" href="'+model['base_url']+'/sitemap.xsl"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
 for row in model['sitemap']:xml+='<url>'+''.join(tag(k,v) for k,v in row.items())+'</url>'
 write_changed(out/'sitemap.xml',xml+'</urlset>')
 for name,text in outputs(ROOT,model).items():write_changed(out/name,text)
 write_changed(out/'robots.txt','User-agent: *\nContent-Signal: ai-train=yes, search=yes, ai-input=yes\n\n\nSitemap: '+model['base_url']+'/sitemap.xml\n')
 security=next(rec for rec in records if rec['route']=='/security/security-announcements/');document=Document((ROOT/security['body']).read_text()).root;items=[v for v in descendants(document,'h2') if v.attrs.get('id')]
 url=model['base_url']+security['route'];rss='<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>Docker Docs - Security Announcements</title><description>Docker security announcements and updates</description>'+tag('link',url)+'<generator>Nift Docker publication</generator><language>en</language>'+tag('lastBuildDate',model['rss_build_date'])+'<atom:link href="'+url+'index.xml" rel="self" type="application/rss+xml"/>'
 for item in items:rss+='<item>'+tag('title',item.text())+tag('link',url+'#'+item.attrs['id'])+tag('guid','security-'+item.attrs['id'])+'</item>'
 write_changed(out/'security/security-announcements/index.xml',rss+'</channel></rss>');ancillary_wall=time.perf_counter()-ancillary_start;search_wall=0;search_prepare=0;search_index=0
 if search:
  phase=time.perf_counter();shutil.rmtree(out/'pagefind',ignore_errors=True);search_prepare=time.perf_counter()-phase;index_start=time.perf_counter();subprocess.run(['node',str(ROOT/'.cache/publication-tools/node_modules/pagefind/lib/runner/bin.cjs'),'--site',str(out)],cwd=ROOT,check=True);search_wall=time.perf_counter()-phase;search_index=time.perf_counter()-index_start
 result={'markdown_exports_s':exports_wall,'markdown_export_count':exported,'converted_exports':converted,'ancillary_s':ancillary_wall,'search_s':search_wall,'search_prepare_s':search_prepare,'search_index_s':search_index,'publication_s':time.perf_counter()-started};write_changed(ROOT/'.generated/publication-report.json',json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':print(json.dumps(publish('--no-search' not in sys.argv),indent=2))
