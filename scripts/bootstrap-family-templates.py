#!/usr/bin/env python3
"""One-time recovery of owned HTML component templates from the pinned build.

The output has explicit typed slots, never a Go-template interpreter. Builds do
not read the frozen site. Static markup remains human-editable HTML.
"""
from pathlib import Path
import sys,json,re,html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'compatibility'))
from extract import Spans
SITE=ROOT.parent/'docker-baseline/site';OUT=ROOT/'publication/templates';OUT.mkdir(parents=True,exist_ok=True)
def replace(source,edits):
 for a,b,v in sorted(edits,reverse=True):source=source[:a]+v+source[b:]
 return source
def attr(source,node,key,value):
 match=re.search(r'(?<![\w:-])'+re.escape(key)+r'=(?:"[^"]*"|\x27[^\x27]*\x27|[^\s>]+)',source[node.start:node.open_end]);return node.start+match.start(),node.start+match.end(),key+'="'+value+'"'
def inner(n,v):return n.open_end,n.close_start,v
def save(name,value):(OUT/(name+'.html')).write_text(value+'\n')
# Get-started cards are driven exclusively by maintained frontmatter.
s=(SITE/'get-started/index.html').read_text();nodes=Spans(s).nodes;article=next(n for n in nodes if n.tag=='article');edits=[]
for kind,heading in [('install','install-heading'),('tutorial','tutorials-heading')]:
 section=next(n for n in nodes if n.tag=='section' and n.attrs.get('aria-labelledby')==heading);grid=next(n for n in section.children if n.tag=='div');card=next(n for n in grid.children if n.tag=='a');p=[n for n in card.children if n.tag=='p'];h=next(n for n in card.children if n.tag=='h3')
 tpl=replace(s,[attr(s,card,'href','@@link@@'),inner(p[0],'@@eyebrow@@' if kind=='install' else '@@audience@@'),inner(h,'@@title@@'),inner(p[1],'@@description@@')])[card.start:]
 # replacements changed length; retain exactly the first recovered anchor.
 card2=next(n for n in Spans(tpl).nodes if n.tag=='a');save(kind+'-card',tpl[:card2.end]);edits.append(inner(grid,'@@'+kind.upper()+'S@@'))
header=next(n for n in article.children if n.tag=='header');body=replace(s,edits)[header.start:];close=body.index('</article>');save('get-started',body[:close])
# Home: owned hero and quick-link markup, data-driven news component.
s=(SITE/'index.html').read_text();nodes=Spans(s).nodes;main=next(n for n in nodes if n.tag=='main');news=next(n for n in main.children if n.attrs.get('x-data')=='{ expanded: false }');news_source=s[news.start:news.end];save('home',s[main.open_end:news.start]+'@@NEWS@@'+s[news.end:main.close_start]);nodes=Spans(news_source).nodes;ol=next(n for n in nodes if n.tag=='ol');li=ol.children[0];times=[n for n in nodes if n.tag=='time' and li.start<=n.start<li.end];link=next(n for n in li.children if n.tag=='a');spans=[n for n in link.children if n.tag=='span'];product=spans[1];product_text=news_source[product.open_end:product.children[0].start];title=next(n for n in spans[2].children if n.tag=='span');description=spans[3]
edits=[attr(news_source,link,'href','@@url@@'),inner(title,'@@title@@'),inner(description,'@@description@@'),(product.open_end,product.children[0].start,'@@product@@')]
for t in times:edits.extend([attr(news_source,t,'datetime','@@published@@'),inner(t,'@@date@@')])
li_template=replace(news_source,edits)[li.start:];li2=Spans(li_template).nodes[0];save('news-item',li_template[:li2.end].replace('<li ', '<li @@VISIBILITY@@ '));save('news',replace(news_source,[inner(ol,'@@ITEMS@@')]))
# Guides: repeated rows and tag sections from the pinned authored layout.
s=(SITE/'guides/index.html').read_text();nodes=Spans(s).nodes;main=next(n for n in nodes if n.tag=='main');sections=[n for n in nodes if n.tag=='section' and 'data-tag' in n.attrs];first=sections[0];row=next(n for n in nodes if 'data-guide' in n.attrs);link=next(n for n in row.children if n.tag=='a');summary=next(n for n in row.children if n.tag=='span');tpl=replace(s,[attr(s,row,'data-search','@@search@@'),attr(s,link,'href','@@url@@'),inner(link,'@@title@@'),inner(summary,'@@summary@@')])[row.start:];end=Spans(tpl).nodes[0].end;save('guide-row',tpl[:end]);container=next(n for n in first.children if 'divide-y' in n.attrs.get('class',''));h=next(n for n in nodes if n.tag=='h2' and first.start<n.start<first.end);ps=[n for n in nodes if n.tag=='p' and first.start<n.start<container.start];sectiontpl=replace(s,[attr(s,first,'id','@@tag@@'),attr(s,first,'data-tag','@@tag@@'),inner(container,'@@ROWS@@'),inner(h,'@@title@@'),inner(ps[0],'@@number@@'),inner(ps[1],'@@description@@')])[first.start:];save('guide-section',sectiontpl[:Spans(sectiontpl).nodes[0].end]);tagbuttons=[n for n in nodes if n.tag=='button' and n.attrs.get('@click','').startswith('selectTag(')];button=tagbuttons[0];label=button.children[0].children[0];count=button.children[1];tpl=replace(s,[attr(s,button,'@click',"selectTag('@@tag@@')"),attr(s,button,':class',button.attrs[':class'].replace('languages','@@tag@@')),inner(label,'@@title@@'),inner(count,'@@count@@')])[button.start:];save('guide-tag-button',tpl[:Spans(tpl).nodes[0].end]);featured=next(n for n in nodes if n.tag=='div' and n.attrs.get('x-show')=='!filtering()' and n.attrs.get('class')=='mb-12');grid=next(n for n in featured.children if n.tag=='div');card=grid.children[0];tpl=replace(s,[attr(s,card,'href','@@url@@'),inner(card.children[0],'@@title@@'),inner(card.children[1],'@@summary@@')])[card.start:];save('guide-featured',tpl[:Spans(tpl).nodes[0].end]);edits=[(sections[0].start,sections[-1].end,'@@SECTIONS@@'),(tagbuttons[0].start,tagbuttons[-1].end,'@@TAG_BUTTONS@@'),inner(grid,'@@FEATURED@@')];value=replace(s,edits);start=main.open_end;value=value[start:];save('guides',value[:value.index('</main>')])
print('Recovered explicit family templates:',len(list(OUT.glob('*.html'))))
