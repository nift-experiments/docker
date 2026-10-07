"""Bounded Docker shortcode expansion; no Hugo template interpreter.

Maintained source is untouched. Explicit source/route maps and discovered include
files are dependencies. Unsupported corpus constructs fail with source context.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import fnmatch,html,json,re,shlex,subprocess,textwrap,time
import yaml
from components import Components

@dataclass
class Shortcode:
    name: str
    parameters: list[str]
    children: list = field(default_factory=list)
    delimiter: str = '<'
    position: int = 0

LEAVES={'include','param','summary-bar','release-date','badge','inline-image','interactive-diagram','youtube-embed','button','sectionlinks','setting-metadata','recipe-list','labspace-launch','desktop-install-v2','desktop-install','figure','grid','card','sandbox-auth','whats-new'}

def parse_shortcodes(source: str):
    """Read quoted shortcode tags with a nesting stack, including code contexts.

    Hugo processes shortcodes inside fences too (Docker uses param there).
    Escaped Hugo examples are recognized explicitly; Nift sigils are plain text.
    """
    root=[];stack=[];current=root;offset=0
    while True:
        match=re.search(r'\{\{([<%])',source[offset:])
        if not match:
            current.append(source[offset:]);break
        start=offset+match.start();delimiter=match.group(1);current.append(source[offset:start])
        body_start=start+3;finish=body_start;quote=None;escaped=False;terminator=('>' if delimiter=='<' else '%')+'}}'
        while finish<len(source):
            character=source[finish]
            if quote:
                if escaped:escaped=False
                elif character=='\\':escaped=True
                elif character==quote:quote=None
            elif character in ['"',"'",'`']:quote=character
            elif source.startswith(terminator,finish):break
            finish+=1
        if finish==len(source):raise ValueError(f'unclosed shortcode at byte {start}')
        tag=source[body_start:finish].strip();offset=finish+3
        if tag.startswith('/*') and tag.endswith('*/'):
            current.append('{{'+delimiter+tag[2:-2]+terminator);continue
        closing=tag.startswith('/');self_closing=tag.endswith('/')
        if closing:
            name=tag[1:].strip()
            if not stack or stack[-1][0].name!=name:raise ValueError(f'mismatched shortcode close {name} at {start}')
            _,current=stack.pop();continue
        if self_closing:tag=tag[:-1].rstrip()
        words=shlex.split(tag);name=words[0];node=Shortcode(name,words[1:],delimiter=delimiter,position=start);current.append(node)
        if name not in LEAVES and not self_closing:
            stack.append((node,current));current=node.children
    if stack:raise ValueError(f'unclosed shortcode {stack[-1][0].name}')
    return root

def read_markdown(path: Path):
    source=path.read_text()
    opening=re.match(r'\A---[ \t]*\n',source)
    if opening:
        close=re.search(r'^---[ \t]*$',source[opening.end():],re.M)
        if not close:raise ValueError(f'unclosed frontmatter {path}')
        stop=opening.end()+close.start();frontmatter=yaml.safe_load(source[opening.end():stop]) or {};return frontmatter,source[opening.end()+close.end():].lstrip('\n')
    return {},source

def source_routes(upstream: Path,site: Path):
    """C2 explicit file→published URL registry, verified against frozen outputs.

    Full vendored mounts and generated adapters are separate migration work.
    No speculative route is admitted just because a path resembles a URL.
    """
    refs={};records={}
    sources={file.relative_to(upstream/'content').as_posix():file for file in (upstream/'content').rglob('*.md')}
    config=yaml.safe_load((upstream/'hugo.yaml').read_text())
    for module in config['module']['imports']:
        vendor=upstream/'_vendor'/module['path']
        for mount in module.get('mounts',[]):
            target=mount['target']
            if not target.startswith('content/'):continue
            origin=vendor/mount['source']
            if not origin.exists():raise ValueError(f'missing pinned mount {origin}')
            candidates=[origin] if origin.is_file() else sorted(origin.rglob('*.md'))
            patterns=mount.get('files',[]);positive=[p for p in patterns if not p.startswith('!')];negative=[p[1:].strip() for p in patterns if p.startswith('!')]
            for file in candidates:
                if file.suffix!='.md':continue
                relative=file.name if origin.is_file() else file.relative_to(origin).as_posix()
                if positive and not any(fnmatch.fnmatch(relative,p) for p in positive):continue
                if any(fnmatch.fnmatch(relative,p) for p in negative):continue
                logical=target.removeprefix('content/') if origin.is_file() else target.removeprefix('content/')+'/'+relative
                sources.setdefault(logical,file)
    for logical,file in sorted(sources.items()):
        meta,_=read_markdown(file)
        if not isinstance(meta,dict):raise ValueError(f'non-map frontmatter {file}')
        stem=Path(logical).with_suffix('');is_index=stem.name in ['_index','index'];route_path=stem.parent if is_index else stem
        if meta.get('slug') and not is_index:route_path=route_path.parent/str(meta['slug'])
        parts=route_path.parts
        if parts and parts[0]=='manuals':route_path=Path(*parts[1:])
        route='/'+route_path.as_posix().strip('./')+'/'
        if route=='//':route='/'
        if meta.get('url'):route=str(meta['url'])
        target=site/(route.strip('/')+'/index.html' if route!='/' else 'index.html')
        if not target.is_file():continue
        refs[logical]=route;refs[str(stem)]=route
        if not is_index:
            refs[str(stem/'_index.md')]=route
        if is_index:
            refs[stem.parent.as_posix()]=route;refs[stem.parent.as_posix()+'/']=route
            refs[stem.parent.as_posix()+'.md']=route
            refs[stem.parent.as_posix()+'/index.md']=route
        records[logical]={'route':route,'frontmatter':meta,'index':is_index,'physical':str(file)}
    # Hugo's pinned ref hook accepts globally unique source basenames too.
    names={}
    for logical,record in records.items():
        names.setdefault(Path(logical).name,set()).add(record['route'])
        names.setdefault(Path(logical).stem.lower(),set()).add(record['route'])
        stem=Path(logical).with_suffix('')
        if stem.name in ['index','_index']:names.setdefault(stem.parent.name+'.md',set()).add(record['route'])
        for key in [record['frontmatter'].get('title'),record['frontmatter'].get('linkTitle')]:
            if key:names.setdefault(str(key).lower(),set()).add(record['route'])
    for name,routes in names.items():
        if len(routes)==1:refs.setdefault(name,next(iter(routes)))
    # Published generated routes provide explicit adapter-reference aliases.
    for file in site.rglob('index.html'):
        route='/'+file.parent.relative_to(site).as_posix().strip('.')+'/'
        if route=='//':route='/'
        refs.setdefault(route.strip('/'),route);refs.setdefault(route.lstrip('/'),route)
        if route.startswith('/reference/api/') or route.startswith('/reference/cli/'):
            refs.setdefault(route.strip('/')+'.md',route)
    return refs,records

class Renderer:
    def __init__(self,binary: Path,upstream: Path,refs: Path,assets: Path):
        self.upstream=upstream;self.assets=assets;self.refs=json.loads(refs.read_text());self.global_params=(yaml.safe_load((upstream/'hugo.yaml').read_text()) or {}).get('params',{})
        self.process=subprocess.Popen([str(binary),'-refs',str(refs),'-assets',str(assets)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
        self.legacy_anchors=json.loads((assets.parent/'legacy-anchors.json').read_text()) if (assets.parent/'legacy-anchors.json').exists() else {};self.metrics=[];self.dependencies=set();self.calls_ns=0;self.expansion_ns=0;self.counts={}
    def close(self):
        self.process.stdin.close();result=self.process.wait()
        if result:raise RuntimeError(f'renderer exited {result}')
    def markdown(self,source,context):
        begin=time.perf_counter_ns();request={'Markdown':source,'Route':context['route'],'Source':context['logical'],'Index':context['index'],'LegacyAnchors':self.legacy_anchors.get(context['logical'],{})}
        self.process.stdin.write(json.dumps(request)+'\n');self.process.stdin.flush();line=self.process.stdout.readline()
        if not line:raise RuntimeError('renderer closed unexpectedly')
        result=json.loads(line);self.calls_ns+=time.perf_counter_ns()-begin
        if result['Error']:raise ValueError(context['logical']+': '+result['Error'])
        self.metrics.append(result['Metrics']);return result['HTML']
    def render(self,source,context):
        begin=time.perf_counter_ns();calls_before=self.calls_ns
        slots={}
        def materialize(nodes):
            out=[]
            for item in nodes:
                if isinstance(item,str):out.append(item);continue
                self.counts[item.name]=self.counts.get(item.name,0)+1
                kwargs={};args=[]
                for parameter in item.parameters:
                    if '=' in parameter:
                        key,value=parameter.split('=',1);kwargs[key]=value
                    else:args.append(parameter)
                if item.name=='param':
                    key=args[0];value=context['frontmatter'].get(key,context['frontmatter'].get('params',{}).get(key,self.global_params.get(key)))
                    if value is None:raise ValueError(f'unknown param {key} in {context["logical"]}')
                    out.append(str(value));continue
                if item.name=='include':
                    file=(self.upstream/'content/includes'/args[0]).resolve();folder=(self.upstream/'content/includes').resolve()
                    if not file.is_relative_to(folder):raise ValueError('include escapes snippet directory')
                    if str(file) in context.get('includes',[]):raise ValueError(f'cyclic include {file}')
                    self.dependencies.add(file);child=dict(context,includes=context.get('includes',[])+[str(file)])
                    out.append(self.expand_include(file.read_text(),child,slots));continue
                if item.name=='tabs':
                    children=[n for n in item.children if isinstance(n,Shortcode)]
                    if not children or any(n.name!='tab' for n in children):raise ValueError('tabs requires tab children')
                    labels=[];panels=[]
                    for child in children:
                        parameters=dict(p.split('=',1) for p in child.parameters);label=parameters['name'].strip();identifier=self.urlize(label)
                        labels.append((label,identifier));body=self.deindent(materialize(child.children));panels.append(self.markdown(body,context))
                    first=labels[0][1];group=kwargs.get('group');persist=kwargs.get('persist')
                    state="{ selected: '"+first+"' }"
                    if group and persist:state="{ selected: $persist('"+first+"').as('tabgroup-"+self.urlize(group)+"') }"
                    group_attr=(' @tab-select.window="'+html.escape("$event.detail.group === '"+group+"' ? selected = $event.detail.name : null",quote=True)+'"') if group else ''
                    buttons=[]
                    for label,identifier in labels:
                        action=("$dispatch('tab-select', { group: '"+group+"', name: '"+identifier+"'})") if group else "selected = '"+identifier+"'"
                        label_html=self.markdown(label,context).strip();label_html=label_html.removeprefix('<p>').removesuffix('</p>')
                        buttons.append('<button class="tab-item" :class="'+html.escape("selected === '"+identifier+"' && 'border-blue border-b-4 dark:border-b-blue-600'",quote=True)+'" @click="'+html.escape(action,quote=True)+'">'+label_html+'</button>')
                    panels_html=''.join('<div aria-role="tab" :class="'+html.escape("selected !== '"+identifier+"' && 'hidden'",quote=True)+'">'+panel+'</div>' for (_,identifier),panel in zip(labels,panels))
                    rendered='<div class="tabs" x-data="'+html.escape(state,quote=True)+'"'+group_attr+' aria-role="tabpanel"><div aria-role="tablist" class="tablist">'+''.join(buttons)+'</div><div>'+panels_html+'</div></div>'
                    token='<div data-docker-slot="'+str(len(slots))+'"></div>';slots[token]=rendered;out.append(token);continue
                component=Components(self,context,materialize).render(item,kwargs,args)
                if component is not None:
                    token='<div data-docker-slot="'+str(len(slots))+'"></div>';slots[token]=component;out.append(token);continue
                raise ValueError(f'unsupported corpus shortcode {item.name} in {context["logical"]} at {item.position}')
            return ''.join(out)
        prepared=materialize(parse_shortcodes(source));self.expansion_ns+=time.perf_counter_ns()-begin-(self.calls_ns-calls_before)
        rendered=self.markdown(prepared,context)
        for token,value in reversed(list(slots.items())):rendered=rendered.replace(token,value)
        if 'data-docker-slot=' in rendered:raise ValueError('unresolved shortcode output slot')
        return rendered
    def expand_include(self,source,context,slots):
        # Includes participate in the parent's Markdown parse, preserving lists,
        # reference definitions, tables and heading numbering across the boundary.
        nodes=parse_shortcodes(source)
        out=[]
        for item in nodes:
            if isinstance(item,str):out.append(item)
            elif item.name=='param':
                key=item.parameters[0];value=context['frontmatter'].get(key,context['frontmatter'].get('params',{}).get(key,self.global_params.get(key)))
                if value is None:raise ValueError(f'unknown include param {key}')
                out.append(str(value))
            elif item.name=='include':
                childfile=(self.upstream/'content/includes'/item.parameters[0]).resolve();folder=(self.upstream/'content/includes').resolve()
                if not childfile.is_relative_to(folder):raise ValueError('include escapes snippet directory')
                if str(childfile) in context.get('includes',[]):raise ValueError('cyclic include')
                self.dependencies.add(childfile);out.append(self.expand_include(childfile.read_text(),dict(context,includes=context.get('includes',[])+[str(childfile)]),slots))
            else:raise ValueError(f'include shortcode {item.name} needs a real corpus fixture')
        return ''.join(out)
    @staticmethod
    def deindent(value):
        # Hugo's InnerDeindent preserves whitespace-only code lines; Python's
        # textwrap.dedent normalizes those lines and corrupts copy payloads.
        lines=value.splitlines(keepends=True)
        widths=[len(line)-len(line.lstrip(' \t')) for line in lines if line.strip()]
        width=min(widths,default=0)
        return ''.join(line[min(width,len(line)-len(line.lstrip(' \t'))):] for line in lines)
    def resolve_ref(self,url,context):
        from urllib.parse import urlsplit
        import posixpath
        u=urlsplit(url);path=u.path
        candidates=[path.lstrip('/'),posixpath.normpath(posixpath.join(posixpath.dirname(context['logical']),path)),posixpath.basename(path),path.lower(),path.lstrip('./')]
        for key in candidates:
            if key in self.refs:return 'https://docs.docker.com'+self.refs[key]+('#'+u.fragment if u.fragment else '')
        raise ValueError('unresolved component ref '+url)
    @staticmethod
    def urlize(value):
        return re.sub(r'\s+','-',re.sub(r'[^\w\s.-]','',value.strip()))
