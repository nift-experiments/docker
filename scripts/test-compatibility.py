#!/usr/bin/env python3
"""Real-source C2 parity assertions, independently read from frozen pages."""
from pathlib import Path
import base64,json,re,sys,time
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'compatibility'))
from docker import Renderer,read_markdown,source_routes
UPSTREAM=ROOT.parent/'docker-upstream';SITE=ROOT.parent/'docker-baseline/site'
output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
binary=Path(sys.argv[2]).resolve()
refs,records=source_routes(UPSTREAM,SITE);refpath=output/'refs.json';refpath.write_text(json.dumps(refs,indent=2)+'\n')
fixtures=['manuals/release-lifecycle.md','manuals/engine/install/ubuntu.md','get-started/docker-overview.md','manuals/ai/sandboxes/governance/access-controls/mcp.md','manuals/engine/storage/drivers/device-mapper-driver.md']
renderer=Renderer(binary,UPSTREAM,refpath,ROOT/'compatibility/assets');results=[]
normalize=lambda value:re.sub(r'\s+',' ',value).strip()
def properties(root):
    return {
      'headings':[(e.tag,e.get('id'),normalize(''.join(e.itertext()))) for e in root.xpath('.//h2|.//h3|.//h4|.//h5|.//h6')],
      'tables':[[[normalize(''.join(c.itertext())) for c in row.xpath('./th|./td')] for row in e.xpath('.//tr')] for e in root.xpath('.//table')],
      'copies':[base64.b64decode(re.search("code: '([^']*)'",e.get('x-data')).group(1)).decode() for e in root.xpath('.//button[@title="copy"]')],
      'code_tokens':[[ (e.get('class'),''.join(e.itertext())) for e in code.xpath('.//span[not(span)]')] for code in root.xpath('.//div[@class="highlight"]//code')],
      'tab_labels':[[normalize(''.join(e.itertext())) for e in group.xpath('.//button[contains(@class,"tab-item")]')] for group in root.xpath('.//div[@class="tabs"]')],
      'images':[(e.get('src'),e.get('alt')) for e in root.xpath('.//figure[@x-data]//img')],
      'mermaid':[''.join(e.itertext()) for e in root.xpath('.//pre[contains(@class,"mermaid")]')],
      'alert_titles':[normalize(''.join(e.itertext())) for e in root.xpath('.//span[@class="admonition-title"]')],
    }
for logical in fixtures:
    context=dict(records[logical],logical=logical);_,body=read_markdown(Path(context['physical']));metrics_start=len(renderer.metrics)
    rendered=renderer.render(body,context);(output/(Path(logical).stem+'.html')).write_text(rendered)
    actual=html.fragment_fromstring(rendered,create_parent='div');reference=html.parse(str(SITE/context['route'].strip('/')/'index.html')).xpath('//article')[0]
    observed=properties(actual);expected=properties(reference);checks={name:observed[name]==expected[name] for name in observed}
    # Markdown-body refs must occur among the reference article's links, which
    # additionally includes breadcrumbs, heading rail and Markdown toolbar.
    expected_links={(e.get('href'),normalize(''.join(e.itertext()))) for e in reference.xpath('.//a[@class="link"]')}
    checks['refs']=all((e.get('href'),normalize(''.join(e.itertext()))) in expected_links for e in actual.xpath('.//a[@class="link"]'))
    results.append({'source':logical,'route':context['route'],'checks':checks,'metrics':renderer.metrics[metrics_start:],'observed':observed,'expected':expected})
    print(logical,checks,flush=True)
renderer.close()
report={'fixtures':results,'include_dependencies':sorted(str(p.relative_to(UPSTREAM)) for p in renderer.dependencies),'shortcodes':renderer.counts,'compatibility_expansion_ns':renderer.expansion_ns,'worker_exchange_ns':renderer.calls_ns,'scope':'C2 render-hook/body semantics; not whole-site or browser parity.'}
(output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
failed=[(r['source'],key) for r in results for key,value in r['checks'].items() if not value]
if failed:raise SystemExit('Parity mismatches: '+repr(failed))
