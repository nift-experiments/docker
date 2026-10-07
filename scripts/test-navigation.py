#!/usr/bin/env python3
import os
from pathlib import Path
import sys,json,re
from lxml import html
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from publication.navigation import Navigation
registry=json.loads((ROOT/'data/source-registry.json').read_text());nav=Navigation(ROOT,registry);model=json.loads((ROOT/'data/publication.json').read_text());records=json.loads((ROOT/'data/composition.json').read_text())['pages'];results=[]
norm=lambda v:re.sub(r'\s+',' ',v or '').strip()
def props(e):
 return {'links':[(v.get('href'),norm(v.text_content()),v.get('aria-current'),v.get('id')) for v in e.xpath('.//a')],'sections':[(norm(v.get('x-data')),norm(v.get('class'))) for v in e.xpath('.//li[@x-data]')],'groups':[norm(v.text_content()) for v in e.xpath('.//li[@class="navbar-group-font-title"]')],'buttons':[(norm(v.get('@click')),norm(v.get('class')),norm(v.text_content())) for v in e.xpath('.//button')],'ul':[(norm(v.get('class')),norm(v.get(':class'))) for v in e.xpath('.//ul')]}
for rec in records:
 if rec.get('kind')=='auxiliary':continue
 scope=next((v.get('articleSection') for v in model['pages'][rec['route']]['schema'] if v.get('@type')=='TechArticle'),None)
 if not scope:continue
 doc=html.parse(str(ROOT.parent/'docker-baseline/site'/rec['route'].strip('/')/'index.html'));original=doc.xpath('//nav[contains(concat(" ",normalize-space(@class)," ")," navbar-font ")]')
 if not original:continue
 a=props(html.fromstring(nav.render(scope,rec)));b=props(original[0]);checks={k:a[k]==b[k] for k in a};item={'route':rec['route'],'checks':checks}
 if not all(checks.values()):item.update(actual=a,expected=b)
 results.append(item)
path=ROOT.parent/'docker-baseline/c4/navigation-results.json';path.write_text(json.dumps(results,indent=2)+'\n')
from collections import Counter
print('pages',len(results),'failures',sum(not all(v['checks'].values()) for v in results));print(Counter(k for v in results for k,ok in v['checks'].items() if not ok));print([(v['route'],[k for k,ok in v['checks'].items() if not ok]) for v in results if not all(v['checks'].values())][:8])

assert results and all('error' not in v and all(v['checks'].values()) for v in results), 'Real-corpus parity failed'
