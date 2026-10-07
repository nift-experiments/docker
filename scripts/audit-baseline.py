#!/usr/bin/env python3
"""Audit the frozen publication contract without fetching external URLs."""
import collections
import gzip
import hashlib
import json
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

site, inventory, output = map(Path, sys.argv[1:4])
output.mkdir(parents=True, exist_ok=True)
with gzip.open(inventory / 'pages.json.gz', 'rt') as stream:
    pages = json.load(stream)
files = {row['path']: row for row in json.loads((inventory / 'files.json').read_text())}
routes = {row['route']: row for row in pages}
anchors = {row['route']: set(row['ids']) for row in pages}
redirects = json.loads((site / 'redirects.json').read_text())
issues = collections.defaultdict(list)
counts = collections.Counter()
external = collections.Counter()

def resolve(url, source):
    parsed = urlsplit(urljoin('https://docs.docker.com' + source, url))
    if parsed.scheme not in ('http', 'https'):
        return None
    if parsed.hostname != 'docs.docker.com':
        external[parsed.hostname or ''] += 1
        return None
    path = unquote(parsed.path) or '/'
    route = path
    filename = path.lstrip('/')
    if path.endswith('/'):
        filename += 'index.html'
    elif filename not in files and filename + '/index.html' in files:
        filename += '/index.html'
        route += '/'
    if filename not in files:
        # Production redirects are valid references even without alias HTML.
        if path in redirects or path.rstrip('/') + '/' in redirects:
            return ('redirect', path, '')
        return ('missing', path, parsed.fragment)
    return ('file', route, unquote(parsed.fragment))

for page in pages:
    route = page['route']
    alias = any(m.get('http-equiv', '').lower() == 'refresh' for m in page['meta'])
    counts['redirect_documents' if alias else 'non_redirect_documents'] += 1
    if alias or route.startswith('/google'):
        continue
    counts['audited_content_and_404'] += 1
    metadata = {m.get('name') or m.get('property'): m.get('content', '') for m in page['meta']}
    canonicals = [l.get('href', '') for l in page['links'] if l.get('rel') == 'canonical']
    if not page['title']:
        issues['missing_title'].append({'route': route})
    if not metadata.get('description'):
        issues['missing_description'].append({'route': route})
    if canonicals != ['https://docs.docker.com' + route]:
        issues['canonical_mismatch'].append({'route': route, 'canonical': canonicals})
    if len(page['ids']) != len(anchors[route]):
        duplicates = [key for key, n in collections.Counter(page['ids']).items() if n > 1]
        issues['duplicate_ids'].append({'route': route, 'ids': duplicates})
    if 'noindex' in metadata.get('robots', ''):
        counts['noindex_documents'] += 1
    # Preserve exact references and distinguish URL requirements from assets.
    references = set(page['hrefs'])
    for asset in page['assets']:
        if asset['attribute'] == 'srcset':
            references.update(part.strip().split()[0] for part in asset['value'].split(',') if part.strip())
        else:
            references.add(asset['value'])
    for url in sorted(url for url in references if isinstance(url, str) and url):
        counts['unique_page_references'] += 1
        result = resolve(url, route)
        if result is None:
            continue
        kind, target, fragment = result
        counts['internal_references'] += 1
        if kind == 'missing':
            issues['missing_internal_targets'].append({'route': route, 'url': url, 'target': target})
        elif kind == 'file' and fragment and target in anchors and fragment not in anchors[target]:
            # Browser text fragments do not require an ID.
            if not fragment.startswith(':~:text='):
                issues['missing_fragments'].append({'route': route, 'url': url, 'target': target, 'fragment': fragment})

for filename in files:
    if not filename.endswith('.css'):
        continue
    for url in re.findall(r'url\(\s*[\"\']?([^\"\')]+)', (site / filename).read_text()):
        counts['css_asset_references'] += 1
        result = resolve(url.strip(), '/' + filename)
        if result and result[0] == 'missing':
            issues['missing_css_assets'].append({'file': filename, 'url': url, 'target': result[1]})

for filename in ['sitemap.xml', 'security/security-announcements/index.xml']:
    if not (site / filename).exists():
        continue
    tree = ET.parse(site / filename)
    counts['valid_xml_outputs'] += 1
    if filename == 'sitemap.xml':
        for element in tree.iter():
            if element.tag.endswith('}loc'):
                counts['sitemap_urls'] += 1
                result = resolve(element.text, '/')
                if result and result[0] == 'missing':
                    issues['sitemap_missing_targets'].append({'url': element.text})

metadata = json.loads((site / 'metadata.json').read_text())
counts['metadata_records'] = len(metadata)
for index, record in enumerate(metadata):
    if not record.get('url'):
        issues['metadata_empty_urls'].append({'index': index, 'title': record.get('title')})
        continue
    result = resolve(record['url'], '/')
    if result and result[0] == 'missing':
        issues['metadata_missing_targets'].append(record)
for filename in ['robots.txt', 'llms.txt', 'llms-full.txt', 'pagefind/pagefind-entry.json']:
    counts['ancillary_' + filename.replace('/', '_')] = (site / filename).stat().st_size
entry = json.loads((site / 'pagefind/pagefind-entry.json').read_text())
counts['searchable_pages'] = sum(language['page_count'] for language in entry['languages'].values())

for source, target in sorted(redirects.items()):
    counts['redirect_rules'] += 1
    result = resolve(target, source)
    if result and result[0] == 'missing':
        issues['redirect_missing_targets'].append({'source': source, 'target': target})
    seen = {source}
    cursor = target
    while cursor in redirects:
        if cursor in seen:
            issues['redirect_cycles'].append({'source': source, 'cycle': sorted(seen)})
            break
        seen.add(cursor)
        cursor = redirects[cursor]

summary = {'counts': dict(counts), 'issue_counts': {k: len(v) for k, v in issues.items()},
           'external_hosts': dict(external), 'scope': 'Local targets, IDs, metadata and redirects; no external requests.',
           'classification': 'Inherited upstream observations; must not be silently repaired during migration.'}
(output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
with gzip.open(output / 'issues.json.gz', 'wt') as stream:
    json.dump(issues, stream, indent=2)
print(json.dumps(summary, indent=2))
