"""Preserve raw HTML boundaries; extract only observed repeated shell subtrees."""
from dataclasses import dataclass,field
from html.parser import HTMLParser
from collections import Counter
from pathlib import Path
import hashlib,re

@dataclass
class Node:
    tag:str;attrs:dict;start:int;open_end:int;end:int=0;close_start:int=0;children:list=field(default_factory=list)
class Spans(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,source):
        super().__init__(convert_charrefs=False);self.source=source;self.offsets=[0];self.offsets.extend(m.end() for m in re.finditer('\n',source));self.stack=[];self.nodes=[];self.feed(source)
    def position(self):line,col=self.getpos();return self.offsets[line-1]+col
    def handle_starttag(self,tag,attrs):
        start=self.position();node=Node(tag,dict(attrs),start,start+len(self.get_starttag_text()));self.nodes.append(node)
        if self.stack:self.stack[-1].children.append(node)
        if tag in self.VOID:node.end=node.open_end;node.close_start=node.open_end
        else:self.stack.append(node)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in self.VOID:
            node=self.stack.pop();node.end=node.open_end;node.close_start=node.open_end
    def handle_endtag(self,tag):
        start=self.position();end=self.source.index('>',start)+1
        for index in range(len(self.stack)-1,-1,-1):
            if self.stack[index].tag==tag:
                for inner in self.stack[index+1:]:inner.end=inner.close_start=start
                node=self.stack[index];node.close_start=start;node.end=end;del self.stack[index:];break

def frame(source):
    nodes=Spans(source).nodes
    articles=[n for n in nodes if n.tag=='article' and 'prose' in n.attrs.get('class','').split()]
    if articles:
        article=articles[0];toolbar=[n for n in nodes if article.open_end<=n.start<article.close_start and n.attrs.get('class')=='block lg:hidden']
        if not toolbar:return nodes,article.open_end,article.close_start
        return nodes,toolbar[0].end,article.close_start
    main=next(n for n in nodes if n.tag=='main');return nodes,main.open_end,main.close_start

def extract_frames(documents,root):
    root=Path(root);parsed={};counts=Counter();candidates={}
    for name,source in documents.items():
        nodes,start,end=frame(source);parsed[name]=(nodes,start,end);seen=set()
        for node in nodes:
            if not node.end or not (node.end<=start or node.start>=end):continue
            value=source[node.start:node.end]
            if len(value)<1024:continue
            digest=hashlib.sha256(value.encode()).hexdigest();candidates[digest]=(node,value);seen.add(digest)
        counts.update(seen)
    shared={};shared_values={}
    for digest,count in counts.items():
        if count<2:continue
        node,value=candidates[digest];label=node.tag+'-'+re.sub(r'[^a-zA-Z0-9_-]','-',node.attrs.get('id') or node.attrs.get('class','').split(' ')[0])[:45]
        file='layouts/shared/'+label+'-'+digest[:12]+'.html';shared[digest]=file;shared_values[file]=value
    result={}
    for name,source in documents.items():
        nodes,start,end=parsed[name];pieces=[];ordinal=0
        def unique(value):
            nonlocal ordinal
            file='layouts/pages/'+name+'/frame-'+str(ordinal)+'.html';ordinal+=1;(root/file).parent.mkdir(parents=True,exist_ok=True);(root/file).write_text(value);return file
        for low,high in [(0,start),(end,len(source))]:
            selected=[]
            for node in nodes:
                if low<=node.start and node.end<=high and node.end>node.start:
                    digest=hashlib.sha256(source[node.start:node.end].encode()).hexdigest()
                    if digest in shared:selected.append((node.start,node.end,shared[digest]))
            selected.sort(key=lambda item:(item[0],-item[1]));cursor=low
            for first,last,file in selected:
                if first<cursor:continue
                if first>cursor:pieces.append(unique(source[cursor:first]))
                pieces.append(file);cursor=last
            if cursor<high:pieces.append(unique(source[cursor:high]))
            if low==0:pieces.append(None)
        result[name]={'pieces':pieces,'body':source[start:end]}
    used={p for v in result.values() for p in v['pieces'] if p and p.startswith('layouts/shared/')}
    for file in used:(root/file).parent.mkdir(parents=True,exist_ok=True);(root/file).write_text(shared_values[file])
    return result,{'shared_candidates':len(shared),'shared_used':len({p for v in result.values() for p in v['pieces'] if p and p.startswith('layouts/shared/')}),'rule':'Exact shared shell subtrees of at least 1024 characters in at least two distinct fixture documents; no Markdown body extraction as shared chrome.'}
