#!/usr/bin/env python3
"""Thin hierarchical wall timers. Diagnostic overhead is excluded from benchmarks."""
from pathlib import Path
import sys,time,json,runpy,functools,os
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'compatibility'))
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
if (OUT/(ROOT.name+'-wall-hierarchy.json')).exists():raise SystemExit('Diagnostic evidence already exists')
stack=[];tree={}
def wrap(owner,name,label):
 original=getattr(owner,name)
 @functools.wraps(original)
 def timed(*args,**kwargs):
  key=tuple(stack+[label]);stack.append(label);started=time.perf_counter()
  try:return original(*args,**kwargs)
  finally:
   elapsed=time.perf_counter()-started;stack.pop();row=tree.setdefault(key,{'calls':0,'wall_s':0});row['calls']+=1;row['wall_s']+=elapsed
 setattr(owner,name,timed)
from publication.chrome import Chrome
from publication.navigation import Navigation
from publication import publish,html_to_markdown,ownership,analysis
for owner,name,label in [(Chrome,'__init__','shared_shell_setup'),(Chrome,'render','per_page_shell'),(Chrome,'toc','heading_toc_binding'),(Chrome,'expand','template_binding'),(Chrome,'fragment','fragment_hash_write'),(Navigation,'__init__','navigation_setup'),(Navigation,'render','navigation_binding'),(Navigation,'api_nav','api_navigation_binding'),(publish,'publish','publication'),(analysis,'prepare','shared_html_analysis'),(publish,'convert','markdown_download_conversion'),(html_to_markdown,'convert','markdown_download_conversion'),(html_to_markdown.Document,'__init__','html_parse'),(ownership,'reconcile','route_registry_reconciliation')]:wrap(owner,name,label)
if ROOT.name=='docker':
 import docker,yaml
 from publication import yaml_data
 from publication import api,cli,special,metadata,minify
 import components
 for module in [docker,components,cli,special]:wrap(module,'load_yaml','yaml_data_parse')
 for owner,name,label in [(docker,'read_markdown','frontmatter_source_loading'),(docker.Renderer,'__init__','compatibility_setup'),(docker.Renderer,'render','shortcode_markdown_pipeline'),(docker.Renderer,'markdown','goldmark_request'),(api.API,'render','api_body_generation'),(cli.CLI,'render','cli_body_generation'),(special.Special,'render','special_body_generation'),(special.Special,'landing','landing_body_generation'),(metadata,'refresh','publication_metadata_binding'),(minify,'minify','html_minification'),(yaml_data,'load','yaml_data_parse')]:wrap(owner,name,label)
import hashlib,subprocess
wrap(hashlib,'sha256','content_hash')
wrap(subprocess,'run','external_process')
wrap(json,'loads','structured_data_parse')
wrap(Path,'read_text','filesystem_text_read');wrap(Path,'read_bytes','filesystem_binary_read');wrap(Path,'write_text','filesystem_text_write');wrap(Path,'write_bytes','filesystem_binary_write')
sys.argv=['scripts/build.py','--all'];started=time.perf_counter();runpy.run_path(str(ROOT/'scripts/build.py'),run_name='__main__');elapsed=time.perf_counter()-started
rows=[]
for key,row in tree.items():
 direct=sum(v['wall_s'] for k,v in tree.items() if len(k)==len(key)+1 and k[:-1]==key)
 rows.append({'path':list(key),**row,'exclusive_s':max(0,row['wall_s']-direct)})
(OUT/(ROOT.name+'-wall-hierarchy.json')).write_text(json.dumps({'diagnostic_wall_s':elapsed,'timings':sorted(rows,key=lambda v:v['wall_s'],reverse=True)},indent=2)+'\n')
