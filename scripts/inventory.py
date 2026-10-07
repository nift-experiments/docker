#!/usr/bin/env python3
"""Inventory every built file and HTML document; preserve hashes and metadata."""
import argparse
import collections
import hashlib
import gzip
import json
from html.parser import HTMLParser
from pathlib import Path

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''
        self.in_title = False
        self.meta = []
        self.links = []
        self.assets = []
        self.ids = []
        self.hrefs = []
        self.json_ld = []
        self.in_json_ld = False
        self.behaviors = collections.Counter()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json_ld = True
        if 'href' in attrs:
            self.hrefs.append(attrs['href'])
        if tag == 'meta':
            self.meta.append(attrs)
        if tag == 'link':
            self.links.append(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ['src', 'poster', 'srcset']:
            if key in attrs:
                self.assets.append({'tag': tag, 'attribute': key, 'value': attrs[key]})
        for key in attrs:
            if key.startswith(('x-', '@', 'data-api', 'data-pagefind')):
                self.behaviors[key] += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script':
            self.in_json_ld = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_json_ld:
            self.json_ld.append(json.loads(data))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files, pages = [], []
    for file in sorted(args.site.rglob('*')):
        if not file.is_file():
            continue
        relative = file.relative_to(args.site).as_posix()
        raw = file.read_bytes()
        files.append({'path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        if file.suffix == '.html':
            doc = Document()
            doc.feed(raw.decode('utf-8'))
            route = '/' + relative
            if route.endswith('index.html'):
                route = route[:-len('index.html')]
            pages.append({'route': route, 'file': relative, 'title': doc.title,
                          'meta': doc.meta, 'links': doc.links, 'assets': doc.assets,
                          'ids': doc.ids, 'hrefs': doc.hrefs, 'json_ld': doc.json_ld,
                          'behaviors': doc.behaviors})
    summary = {'files': len(files), 'html_documents': len(pages),
               'html_redirect_documents': sum(any(m.get('http-equiv', '').lower() == 'refresh' for m in p['meta']) for p in pages),
               'bytes': sum(f['bytes'] for f in files),
               'extensions': dict(collections.Counter(Path(f['path']).suffix for f in files)),
               'route_prefixes': dict(collections.Counter(p['route'].split('/')[1] for p in pages))}
    summary['html_non_redirect_documents'] = summary['html_documents'] - summary['html_redirect_documents']
    redirects = args.site / 'redirects.json'
    if redirects.exists():
        summary['redirect_rules'] = len(json.loads(redirects.read_text()))
    for name, value in [('files', files), ('pages', pages), ('summary', summary)]:
        serialized = json.dumps(value, indent=2) + '\n'
        if name == 'pages':
            with gzip.open(args.output / 'pages.json.gz', 'wt', encoding='utf-8') as stream:
                stream.write(serialized)
        else:
            (args.output / (name + '.json')).write_text(serialized)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
