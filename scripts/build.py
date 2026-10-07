#!/usr/bin/env python3
"""Markdown compatibility compilation → transient HTML → Nift composition.

Use --setup once (outside timings), then --all for a forced full renderer build.
This C2 pipeline is a partial-site architecture proof; publication/search follows.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'))
from docker import Renderer,read_markdown
parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');parser.add_argument('--setup',action='store_true');args=parser.parse_args()
def write_changed(file,value):
    file.parent.mkdir(parents=True,exist_ok=True)
    if not file.exists() or file.read_text()!=value:file.write_text(value)
def emit(file):
    literal=json.dumps(file);return '@dep('+literal+')$[rawHtml('+literal+')]'
def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
start=time.perf_counter();cache=ROOT/'.cache';binary=cache/'docker-renderer'
if args.setup:
    cache.mkdir(exist_ok=True);env=dict(os.environ,GOTOOLCHAIN='local');env.setdefault('GOMODCACHE',str(cache/'go-modules'));env.setdefault('GOCACHE',str(cache/'go-build'))
    subprocess.run(['go','build','-mod=readonly','-buildvcs=false','-o',str(binary),'.'],cwd=ROOT/'compatibility/renderer',env=env,check=True)
    print('Renderer setup completed; excluded from production benchmarks.');raise SystemExit()
if not binary.is_file():raise SystemExit('Run python3 scripts/build.py --setup before building; setup is not included in benchmark phases.')
manifest=json.loads((ROOT/'data/composition.json').read_text());statefile=ROOT/'.generated/render-state.json';state=json.loads(statefile.read_text()) if statefile.exists() else {};nextstate={}
registry=json.loads((ROOT/'data/source-registry.json').read_text()) if (ROOT/'data/source-registry.json').exists() else {}
renderer=Renderer(binary,ROOT/'authored',ROOT/'data/refs.json',ROOT/'compatibility/assets');compiled=0
common=[ROOT/'data/refs.json',ROOT/'authored/hugo.yaml',*sorted((ROOT/'authored/content/includes').rglob('*')),*sorted((ROOT/'compatibility/assets').glob('*.svg')),*sorted((ROOT/'compatibility/renderer').glob('*.go')),ROOT/'compatibility/docker.py',*sorted((ROOT/'compatibility').glob('*.py')),*sorted((ROOT/'compatibility').glob('*.json')),*sorted((ROOT/'compatibility/templates').glob('*')),*sorted((ROOT/'compatibility/pinned').glob('*')),*sorted((ROOT/'authored/data').rglob('*'))]
commonhash=hashlib.sha256(''.join(sha(p) for p in common if p.is_file()).encode()).hexdigest()
for record in manifest['pages']:
    name=record['name'];body=record['body'];dependencies=['data/composition.json']
    if record['model']=='markdown':
        source=ROOT/record['source'];meta,text=read_markdown(source);context={'route':record['route'],'logical':record['logical'],'index':record['index'],'frontmatter':meta,'records':registry}
        fingerprint=hashlib.sha256((commonhash+sha(source)).encode()).hexdigest();nextstate[name]=fingerprint;dependencies.extend([record['source'],'data/refs.json','authored/hugo.yaml'])
        dependencies.extend(str(p.relative_to(ROOT)) for p in common if p.is_file())
        if args.all or state.get(name)!=fingerprint or not (ROOT/body).exists():
            rendered=renderer.render(text,context);write_changed(ROOT/body,rendered);compiled+=1
    wrapper=''.join('@dep('+json.dumps(p)+')' for p in sorted(set(dependencies)))
    for piece in record['pieces']:wrapper+=emit(piece if piece else body)
    write_changed(ROOT/'.generated/content'/((name if name!='/' else 'index')+'.html'),wrapper)
renderer.close();write_changed(statefile,json.dumps(nextstate,sort_keys=True)+'\n')
compatibility_wall=time.perf_counter()-start
asset_start=time.perf_counter();asset_count=0
for file in (ROOT/'static').rglob('*'):
    if not file.is_file():continue
    target=ROOT/'public'/file.relative_to(ROOT/'static');target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() or target.stat().st_size!=file.stat().st_size or target.read_bytes()!=file.read_bytes():shutil.copy2(file,target)
    asset_count+=1
asset_wall=time.perf_counter()-asset_start
compose_start=time.perf_counter();subprocess.run(['nift','build',*(['--all'] if args.all else [])],cwd=ROOT,check=True);nift_wall=time.perf_counter()-compose_start
metrics={key:sum(m[key] for m in renderer.metrics) for key in ['MarkdownParseNS','MarkdownRenderNS','HookNS','ChromaNS']}
report={'model':'maintained Markdown → Docker compatibility renderer → transient HTML → Nift','compiled_pages':compiled,'compatibility_wall_s':compatibility_wall,'compatibility_expansion_ns':renderer.expansion_ns,'renderer_components_ns':metrics,'asset_publication_s':asset_wall,'asset_files':asset_count,'nift_composition_s':nift_wall,'total_s':time.perf_counter()-start,'search':'C2 frozen reference search fixture; fresh publication/indexing is a C4/C5 obligation, not benchmarked here.'}
write_changed(ROOT/'.generated/build-report.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
