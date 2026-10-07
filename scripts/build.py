#!/usr/bin/env python3
"""Markdown compatibility compilation → transient HTML → Nift composition.

Use --setup once (outside timings), then --all for a forced full renderer build.
Complete Docker publication; setup is measured separately from routine builds.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'));sys.path.insert(0,str(ROOT))
from docker import Renderer,read_markdown
from publication.api import API
from publication.cli import CLI
from publication.special import Special
from publication.metadata import refresh
from publication.chrome import Chrome
from publication.ownership import reconcile
from publication.publish import publish
from publication.minify import minify
import yaml
parser=argparse.ArgumentParser();parser.add_argument('--all',action='store_true');parser.add_argument('--setup',action='store_true');args=parser.parse_args()
def write_changed(file,value):
    file.parent.mkdir(parents=True,exist_ok=True)
    if not file.exists() or file.read_text()!=value:file.write_text(value)
def emit(file):
    literal=json.dumps(file);return '@dep('+literal+')$[rawHtml('+literal+')]'
digests={}
def sha(file):
    if file not in digests:digests[file]=hashlib.sha256(file.read_bytes()).hexdigest()
    return digests[file]
start=time.perf_counter();cache=ROOT/'.cache';binary=cache/'docker-renderer'
if args.setup:
    cache.mkdir(exist_ok=True);env=dict(os.environ,GOTOOLCHAIN='local');env.setdefault('GOMODCACHE',str(cache/'go-modules'));env.setdefault('GOCACHE',str(cache/'go-build'))
    env.setdefault('GOTMPDIR',str(cache/'go-tmp'));Path(env['GOTMPDIR']).mkdir(parents=True,exist_ok=True)
    for directory,output in [('compatibility/renderer',binary),('publication/minifier',cache/'html-minifier')]:
        subprocess.run(['go','build','-mod=readonly','-buildvcs=false','-o',str(output),'.'],cwd=ROOT/directory,env=env,check=True)
    write_changed(cache/'setup-fingerprint',hashlib.sha256(b''.join(p.read_bytes() for directory in ['compatibility/renderer','publication/minifier'] for p in sorted((ROOT/directory).glob('*')) if p.is_file())).hexdigest())
    subprocess.run(['npm','install','--prefix',str(cache/'publication-tools'),'--cache',str(cache/'npm-cache'),'--no-audit','--no-fund','pagefind@1.5.2'],cwd=ROOT,check=True)
    print('Pinned renderer, minifier and Pagefind setup completed; excluded from production benchmarks.');raise SystemExit()
setuphash=hashlib.sha256(b''.join(p.read_bytes() for directory in ['compatibility/renderer','publication/minifier'] for p in sorted((ROOT/directory).glob('*')) if p.is_file())).hexdigest()
if (cache/'setup-fingerprint').exists() and (cache/'setup-fingerprint').read_text()!=setuphash:raise SystemExit('Renderer/publication compiler inputs changed. Run scripts/build.py --setup outside build timings.')
if not binary.is_file():raise SystemExit('Run python3 scripts/build.py --setup before building; setup is not included in benchmark phases.')
manifest=json.loads((ROOT/'data/composition.json').read_text());reconcile(ROOT,manifest);statefile=ROOT/'.generated/render-state.json';state=json.loads(statefile.read_text()) if statefile.exists() else {};nextstate={}
registry=json.loads((ROOT/'data/source-registry.json').read_text()) if (ROOT/'data/source-registry.json').exists() else {}
renderer=Renderer(binary,ROOT/'authored',ROOT/'data/refs.json',ROOT/'compatibility/assets');compiled=0
markdown_sources={}
for logical,v in registry.items():
    source=ROOT/v['source'];markdown_sources[source]=read_markdown(source);v['frontmatter']=markdown_sources[source][0]
for source in (ROOT/'authored/content').rglob('_index.md'):
    logical=source.relative_to(ROOT/'authored/content').as_posix()
    if logical not in registry:
        meta,text=read_markdown(source);registry[logical]={'source':str(source.relative_to(ROOT)),'frontmatter':meta,'route':'/'+logical.removesuffix('_index.md').removeprefix('manuals/'),'index':True}
api_model=json.loads((ROOT/'authored/data/api-reference.json').read_text());publication_model,_=refresh(ROOT,registry,api_model,yaml.safe_load((ROOT/'authored/data/redirects.yml').read_text()),yaml.safe_load((ROOT/'authored/hugo.yaml').read_text()).get('title'));chrome=Chrome(ROOT,publication_model,registry,force=args.all);api=API(api_model,renderer,registry);cli=CLI(renderer,json.loads((ROOT/'data/cli-registry.json').read_text()));special=Special(renderer,registry);family_ns={}
common=[ROOT/'data/refs.json',ROOT/'authored/hugo.yaml',*sorted((ROOT/'authored/content/includes').rglob('*')),*sorted((ROOT/'compatibility/assets').glob('*.svg')),*sorted((ROOT/'compatibility/renderer').glob('*.go')),ROOT/'compatibility/docker.py',*sorted((ROOT/'compatibility').glob('*.py')),*sorted((ROOT/'compatibility').glob('*.json')),*sorted((ROOT/'compatibility/templates').glob('*')),*sorted((ROOT/'compatibility/pinned').glob('*')),*sorted((ROOT/'authored/data').rglob('*')),*sorted((ROOT/'publication').rglob('*.py')),*sorted((ROOT/'publication/templates').glob('*.html')),ROOT/'data/cli-registry.json',ROOT/'data/data-mounts.json',*sorted((ROOT/'authored/_vendor/github.com/docker/compose').rglob('*.yaml')),*sorted((ROOT/'authored/_vendor/github.com/docker/model-runner').rglob('*.yaml'))]
commonhash=hashlib.sha256((''.join(sha(p) for p in common if p.is_file())+json.dumps({k:v['frontmatter'] for k,v in registry.items()},sort_keys=True,default=str)).encode()).hexdigest();chrome_ns=0
# Explicit compiler-input manifest carries shared dependency changes once,
# rather than repeating hundreds of identical paths in every Nift wrapper.
compiler_inputs={str(p.relative_to(ROOT)):sha(p) for p in common if p.is_file()}
write_changed(ROOT/'.generated/compatibility-inputs.json',json.dumps({'inputs':compiler_inputs,'frontmatter_digest':commonhash},sort_keys=True)+'\n')
for record in manifest['pages']:
    name=record['name'];body=record['body'];dependencies=['data/composition.json']
    if record['model']=='redirect':
        import html
        target=html.escape(record['target']);write_changed(ROOT/body,'<!doctype html><html lang=en><head><title>'+target+'</title><link rel=canonical href='+target+'><meta charset=utf-8><meta http-equiv=refresh content="0; url='+target+'"></head></html>')
    if record['model'] in ['markdown','special','landing','legacy-api','cli','api']:
        source=ROOT/record['source'];meta,text=markdown_sources.get(source) or read_markdown(source) if record['model'] in ['markdown','special','landing','legacy-api'] else ({},'');context={'route':record['route'],'logical':record['logical'],'index':record['index'],'frontmatter':meta,'records':registry}
        fingerprint=hashlib.sha256((commonhash+sha(source)).encode()).hexdigest();nextstate[name]=fingerprint;dependencies.extend([record['source'],'data/refs.json','authored/hugo.yaml'])
        dependencies.append('.generated/compatibility-inputs.json')
        if args.all or state.get(name)!=fingerprint or not (ROOT/body).exists():
            family_start=time.perf_counter_ns()
            model=record['model']
            if model=='api':rendered=api.render(record)
            elif model=='cli':rendered=cli.render(record)
            elif model=='special':rendered=special.render(record['family'],text,context)
            elif model=='landing':rendered=special.landing(record['family'],context)
            elif model=='legacy-api':
                import html
                spec='/'+record['logical'].removesuffix('.md')+'.yaml';absolute='https://docs.docker.com'+spec;mdurl='https://docs.docker.com'+record['route'].rstrip('/')+'.md';hide='' if record['route'].startswith(('/reference/api/hub/','/reference/api/registry/')) else ' hide-hostname="true"'
                rendered='<article class="redoc-container"><noscript><p style="padding: 32px 24px; max-width: 72ch">This reference uses JavaScript for the interactive explorer. View the <a href="'+html.escape(mdurl)+'">Markdown page</a> or <a href="'+html.escape(absolute)+'">download the OpenAPI specification</a> if JavaScript is unavailable.</p></noscript><redoc spec-url="'+html.escape(spec)+'"'+hide+' suppress-warnings="true" lazy-rendering></redoc></article>'
            else:
                import html
                rendered=renderer.render(text,context);prefix='';params={**meta,**meta.get('params',{})}
                if params.get('apiReferenceBanner') is not False:
                    for a in api_model['apis']:
                        manual=registry.get(a['manual'].lstrip('/').removesuffix('/').removesuffix('.md')+'.md') or registry.get(a['manual'].lstrip('/').rstrip('/')+'/_index.md')
                        if manual and manual['route']==record['route']:prefix+='<p class="my-4 rounded border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900"><a href="'+html.escape(a['url'])+'">Explore the '+html.escape(a['title'])+' API '+html.escape(a['version'])+' →</a></p>'
                sections=[v for v in registry.values() if v['index'] and record['route'].startswith(v['route']) and v['route']!=record['route']];parent=max(sections,key=lambda v:len(v['route']),default=None)
                if parent and {**parent['frontmatter'],**parent['frontmatter'].get('params',{})}.get('recipeCatalog') and not record['index']:prefix+='<p><a href="'+html.escape(parent['route'])+'">Browse all recipes</a></p>'
                rendered=prefix+rendered
            family_ns[model]=family_ns.get(model,0)+time.perf_counter_ns()-family_start
            write_changed(ROOT/body,rendered);compiled+=1
    chrome_start=time.perf_counter_ns();dependencies.extend(chrome.render(record));chrome_ns+=time.perf_counter_ns()-chrome_start
    wrapper=''.join('@dep('+json.dumps(p)+')' for p in sorted(set(dependencies)))
    for piece in record['pieces']:wrapper+=emit(piece if piece else body)
    write_changed(ROOT/'.generated/content'/((name if name!='/' else 'index')+'.html'),wrapper)
chrome.close();renderer.close();write_changed(statefile,json.dumps(nextstate,sort_keys=True)+'\n')
compatibility_wall=time.perf_counter()-start
asset_start=time.perf_counter();asset_count=0
for file in (ROOT/'static').rglob('*'):
    if not file.is_file():continue
    target=ROOT/'public'/file.relative_to(ROOT/'static');target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() or target.stat().st_size!=file.stat().st_size or target.read_bytes()!=file.read_bytes():shutil.copy2(file,target)
    asset_count+=1
asset_wall=time.perf_counter()-asset_start
compose_start=time.perf_counter();subprocess.run(['nift','build',*(['--all'] if args.all else [])],cwd=ROOT,check=True);nift_wall=time.perf_counter()-compose_start
minification_report=minify(ROOT,args.all)
publication_report=publish(model=publication_model,force=args.all)
metrics={key:sum(m[key] for m in renderer.metrics) for key in ['MarkdownParseNS','MarkdownRenderNS','HookNS','ChromaNS']}
report={'model':'maintained Markdown → Docker compatibility renderer → transient HTML → Nift','compiled_pages':compiled,'compatibility_wall_s':compatibility_wall-chrome_ns/1e9,'shell_prepare_s':chrome_ns/1e9,'compatibility_expansion_ns':renderer.expansion_ns,'renderer_components_ns':metrics,'family_wall_ns':family_ns,'asset_publication_s':asset_wall,'asset_files':asset_count,'nift_composition_s':nift_wall,'total_s':time.perf_counter()-start,'publication':publication_report,'minification':minification_report}
write_changed(ROOT/'.generated/build-report.json',json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
