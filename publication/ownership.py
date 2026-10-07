"""Reconcile the explicit publication manifest with Nift and owned outputs.

Source bodies and layouts are never deleted. A removed route retires only its
previous generated HTML and transient wrapper. Retrieval export ownership is
handled independently by publish.py.
"""
from pathlib import Path
import json

def reconcile(root,manifest):
 pages=manifest['pages'];names={v['name'] for v in pages}
 tracked=root/'.nift/tracked.json';previous=json.loads(tracked.read_text())['tracked']
 value={'tracked':[{'name':v['name'],'title':v['title'],'template':'templates/template.html'} for v in pages]}
 if value!={'tracked':previous}:tracked.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
 for name in {v['name'] for v in previous}-names:
  if name.startswith('/') or '..' in Path(name).parts:raise ValueError('Unsafe publication name '+name)
  for directory in ['public','.generated/content']:
   path=root/directory/(name+'.html')
   if path.is_file():path.unlink()
