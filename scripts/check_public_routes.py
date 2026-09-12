#!/usr/bin/env python3
"""Verify the front door's destinations and reading-map source snapshot."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://wcook04.github.io/plectis/'


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get('href', '')
        if tag == 'a' and href.startswith(BASE):
            self.urls.add(urldefrag(href).url)


def destinations(data: dict, markup: str) -> list[str]:
    urls = {p['href'] for p in data['systems']}
    urls.update(BASE + 'maths/papers/' + p['paper_id'] + '.html' for p in data['systems'])
    for problem in data['items']:
        urls.update([problem['paper_href'], problem['page_href']])
        urls.update(row['href'] for row in problem['long_records'])
    urls.update(BASE + path for path in (
        'docs/papers.html', 'docs/glossary.html', 'maths/index.html',
        'plectis-ai-reader-complete.json', 'plectis-reviewer-brief.json',
    ))
    links = PageLinks()
    links.feed(markup)
    urls.update(links.urls)
    return sorted({urldefrag(url).url for url in urls})


def validate_body(url: str, body: bytes, data: dict) -> None:
    path = urlsplit(url).path
    if path.endswith('.pdf') and not body.startswith(b'%PDF-'):
        raise ValueError('not a PDF')
    if path.endswith('.json'):
        packet = json.loads(body)
        if path.endswith('/plectis-ai-reader-complete.json'):
            if hashlib.sha256(body).hexdigest() != data['source_hashes']['plectis-ai-reader-complete.json']:
                raise ValueError('the Plectis handoff changed; refresh the root reading map before publishing')
            corpus = packet['scholarly_corpus']
            if not corpus['papers'] or not all(p.get('source_embedded') and p.get('body') for p in corpus['papers']):
                raise ValueError('the reading packet has missing manuscripts')
            for node in corpus['reading_graph']['nodes']:
                pointer = node['pointer']
                if pointer and not pointer.startswith('/'):
                    raise ValueError(f'invalid reading-graph pointer: {pointer}')
                value = packet
                for key in pointer.split('/')[1:]:
                    key = key.replace('~1', '/').replace('~0', '~')
                    value = value[int(key)] if isinstance(value, list) else value[key]
            if not {p['paper_id'] for p in corpus['papers']} >= {p['paper_id'] for p in data['systems']}:
                raise ValueError('the reading packet is missing an orientation paper')


def read_destination(url: str, site_base: str, site_root: Path | None) -> bytes:
    if not url.startswith(BASE):
        raise ValueError('destination is outside the Plectis site')
    relative = url[len(BASE):]
    if site_root is not None:
        root = site_root.resolve()
        path = (root / unquote(urlsplit(relative).path)).resolve()
        if not path.is_relative_to(root):
            raise ValueError('destination escapes the Plectis site directory')
        if path.is_dir():
            path = path / 'index.html'
        return path.read_bytes()
    actual = urljoin(site_base.rstrip('/') + '/', relative)
    req = Request(actual, headers={'User-Agent': 'Plectis-public-route-check/1.0'})
    with urlopen(req, timeout=30) as response:
        if response.status != 200:
            raise ValueError(f'HTTP {response.status}')
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    location = parser.add_mutually_exclusive_group()
    location.add_argument('--site-base', default=BASE, help='Plectis site URL; localhost is useful before deployment')
    location.add_argument('--site-root', type=Path, help='validate a local published site checkout without network requests')
    args = parser.parse_args()
    data = json.loads((ROOT / 'data/absolute-frontier.json').read_text())
    urls = destinations(data, (ROOT / 'index.html').read_text())

    def check(url):
        try:
            validate_body(url, read_destination(url, args.site_base, args.site_root), data)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
            return f'{url}: {error}'
        return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        failures = [error for error in pool.map(check, urls) if error]
    if failures:
        raise SystemExit(f'{len(failures)} of {len(urls)} public destinations failed:\n' + '\n'.join(failures))
    print(f'{len(urls)} published destinations and the reading-map snapshot verified at {args.site_root or args.site_base}')


if __name__ == '__main__':
    main()
