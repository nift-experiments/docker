#!/usr/bin/env python3
"""One-time migration bootstrap, never a routine renderer or benchmark step."""
from pathlib import Path
import json,shutil,sys
from urllib.parse import urlparse
from lxml import html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'))
from docker import source_routes
from extract import extract_frames
SITE=ROOT.parent/'docker-baseline/site';UPSTREAM=ROOT.parent/'docker-upstream'
refs,records=source_routes(UPSTREAM,SITE)
logical=['manuals/release-lifecycle.md','manuals/engine/install/ubuntu.md','get-started/docker-overview.md','manuals/ai/sandboxes/governance/access-controls/mcp.md','manuals/engine/storage/drivers/device-mapper-driver.md']
fixtures=[{'name':records[source]['route'].strip('/')+'/index','route':records[source]['route'],'logical':source,'index':records[source]['index'],'title':records[source]['frontmatter']['title'],'model':'markdown'} for source in logical]
fixtures.extend([{'name':'/','route':'/','title':'Docker Docs','model':'generated-family-prototype'}, {'name':'reference/cli/docker/container/run/index','route':'/reference/cli/docker/container/run/','title':'docker container run','model':'generated-family-prototype'}, {'name':'reference/api/ai-governance/latest/operations/createPolicy/index','route':'/reference/api/ai-governance/latest/operations/createPolicy/','title':'Create policy','model':'generated-family-prototype'}])
documents={f['name']: (SITE/(f['route'].strip('/')+'/index.html' if f['route']!='/' else 'index.html')).read_text() for f in fixtures}
for repo in ['docker','docker-agent']:
    root=ROOT.parent/repo;frame_info,evidence=extract_frames(documents,root);pages=[];owned_assets='static' if repo=='docker' else 'public-assets'
    for fixture in fixtures:
        record=dict(fixture);record['pieces']=frame_info[record['name']]['pieces']
        if repo=='docker' and record['model']=='markdown':
            record['source']='authored/content/'+record['logical'];target=root/record['source'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(records[record['logical']]['physical'],target)
            record['body']='.generated/bodies/'+record['name']+'.html'
        elif repo=='docker':
            record['body']='layouts/prototypes/'+('home' if record['name']=='/' else record['name'])+'.html';target=root/record['body'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(frame_info[record['name']]['body'])
        else:
            record={'name':record['name'],'route':record['route'],'title':record['title'],'pieces':record['pieces'],'model':'maintained-html','body':'pages/'+('home' if record['name']=='/' else record['name'])+'.html'}
            target=root/record['body'];target.parent.mkdir(parents=True,exist_ok=True);target.write_text(frame_info[record['name']]['body'])
        pages.append(record)
        parsed=html.fromstring(documents[fixture['name']])
        for element in parsed.xpath('//*[@src] | //link[@href]'):
            u=urlparse(element.get('src') or element.get('href'))
            if u.hostname and u.hostname!='docs.docker.com':continue
            file=SITE/u.path.lstrip('/')
            if file.is_file():
                dest=root/owned_assets/file.relative_to(SITE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
        # C2 reference exports remain frozen fixtures, not synchronized migration output.
        export=SITE/(fixture['route'].rstrip('/')+'.md').lstrip('/')
        if export.is_file():
            target=root/owned_assets/export.relative_to(SITE);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(export,target)
    (root/'data').mkdir(exist_ok=True);(root/'data/composition.json').write_text(json.dumps({'checkpoint':'C2 partial-site architecture proof','pages':pages},indent=2)+'\n');(root/'data/shell-extraction.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (root/'templates/template.html').write_text('@script { fn(rawHtml(path)) { f := file(path); f.open(); value := f.read_all(); f.close(); return value; } }@content')
    config=json.loads((root/'.nift/config.json').read_text());config['config']['content-dir']='.generated/content/';(root/'.nift/config.json').write_text(json.dumps(config,indent=2)+'\n')
    (root/'.nift/tracked.json').write_text(json.dumps({'tracked':[{'name':p['name'],'title':p['title'],'template':'templates/template.html'} for p in pages]},indent=2)+'\n')
    for folder in ['assets','css','pagefind']:shutil.copytree(SITE/folder,root/owned_assets/folder,dirs_exist_ok=True)
    for file in SITE.iterdir():
        if file.is_file() and file.suffix in ['.js','.css','.png','.ico','.svg']:shutil.copy2(file,root/owned_assets/file.name)
    shutil.copy2(SITE/'metadata.json',root/owned_assets/'metadata.json')
    with (root/'.gitignore').open('a') as f:f.write('\n# Transient renderer/composition state and generated publication.\n.generated/\n.cache/\npublic/\n')
    if repo=='docker':
        (root/'authored').mkdir(exist_ok=True);shutil.copy2(UPSTREAM/'hugo.yaml',root/'authored/hugo.yaml');(root/'data/refs.json').write_text(json.dumps(refs,indent=2)+'\n')
        include_evidence=json.loads((ROOT.parent/'docker-baseline/c2/compatibility/results.json').read_text())
        for include in include_evidence['include_dependencies']:
            target=root/'authored'/include;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(UPSTREAM/include,target)
    print(repo,len(pages),evidence)
