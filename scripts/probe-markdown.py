#!/usr/bin/env python3
"""Bounded native-renderer and raw-composition probe; never edits Nift."""
import hashlib,json,pathlib,shutil,subprocess,sys,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
fixtures=root/'investigation/markdown-probe'
output=pathlib.Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
results=[]
with tempfile.TemporaryDirectory(prefix='docker-markdown-proof-') as directory:
 project=pathlib.Path(directory)
 for folder in ['.nift','content','templates']:(project/folder).mkdir()
 for name in ['config.json','tracked.json']:shutil.copy(root/'.nift'/name,project/'.nift'/name)
 (project/'templates/template.html').write_text('@content')
 for name in ['docker-table.md','docker-code.md','highlight.html','highlight-only.html','literal.md']:shutil.copy(fixtures/name,project/'content'/name)
 cases={
  'native-table':'@markup(md, "content/docker-table.md")',
  'native-code':'@markup(md, "content/docker-code.md")',
  'profile-argument':'@markup(md, "content/docker-table.md", "extended")',
  'native-highlight':'@input("content/highlight-only.html")',
  'native-literal-sigil':'@markup(md, "content/literal.md")',
  'raw-composition':'@dep("content/highlight.html")@script { f := file("content/highlight.html"); f.open(); value := f.read_all(); f.close(); return value; }',
 }
 for name,source in cases.items():
  (project/'content/index.html').write_text(source)
  result=subprocess.run(['nift','build','--all'],cwd=project,text=True,capture_output=True)
  (output/(name+'.log')).write_text(result.stdout+result.stderr)
  record={'case':name,'exit':result.returncode,'source':source}
  if not result.returncode:
   data=(project/'public/index.html').read_bytes();(output/(name+'.html')).write_bytes(data)
   record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   if name=='native-table':record.update(table_rendered=b'<table' in data,heading_id=b'id="lifecycle-stage"' in data)
   if name=='native-highlight':record['span_preserved']=b'<span class="k">' in data
   if name=='raw-composition':
    expected=(project/'content/highlight.html').read_bytes();record['exact']=data==expected
    # Verify explicit dependency invalidation and compare against a full build.
    (project/'content/highlight.html').write_bytes(expected.replace(b'alpine',b'ubuntu'))
    incremental=subprocess.run(['nift','build'],cwd=project,text=True,capture_output=True)
    after=(project/'public/index.html').read_bytes()
    full=subprocess.run(['nift','build','--all'],cwd=project,text=True,capture_output=True)
    record['changed_input']={'incremental_exit':incremental.returncode,'full_exit':full.returncode,'changed':after!=data,'incremental_equals_full':after==(project/'public/index.html').read_bytes()}
    (output/'raw-composition-changed.log').write_text(incremental.stdout+incremental.stderr+full.stdout+full.stderr)
  results.append(record)
version=subprocess.run(['nift','--version'],text=True,capture_output=True)
(output/'results.json').write_text(json.dumps({'nift_version':version.stdout+version.stderr,'results':results},indent=2)+'\n')
print(json.dumps(results,indent=2))
