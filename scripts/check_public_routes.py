#!/usr/bin/env python3
"""Verify the destinations in the generated reading map, including the full handoff."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
BASE='https://wcook04.github.io/plectis/'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--site-base',default=BASE,help='Plectis site URL; localhost is useful before deployment')
    args=ap.parse_args()
    data=json.loads((ROOT/'data/absolute-frontier.json').read_text())
    urls={p['href'] for p in data['systems']}
    urls.update(BASE+'maths/papers/'+p['paper_id']+'.html' for p in data['systems'])
    for p in data['items']:
        urls.update([p['paper_href'],p['page_href']])
        urls.update(r['href'] for r in p['long_records'])
    urls.update(BASE+p for p in ('docs/papers.html','docs/glossary.html','maths/index.html','plectis-ai-reader-complete.json'))
    def check(url):
        actual=url.replace(BASE,args.site_base.rstrip('/')+'/',1)
        req=Request(actual,headers={'User-Agent':'Plectis-public-route-check/1.0'})
        with urlopen(req,timeout=30) as response:
            body=response.read()
            if response.status!=200: raise ValueError(f'{url}: {response.status}')
        if url.endswith('.pdf') and not body.startswith(b'%PDF-'): raise ValueError(f'{url}: not a PDF')
        if url.endswith('plectis-ai-reader-complete.json'):
            if hashlib.sha256(body).hexdigest() != data['source_hashes']['plectis-ai-reader-complete.json']:
                raise ValueError('The Plectis handoff changed; refresh the root reading map before publishing')
            packet=json.loads(body);corpus=packet['scholarly_corpus']
            assert all(p['source_embedded'] and p['body'] for p in corpus['papers'])
            for node in corpus['reading_graph']['nodes']:
                value=packet
                for key in node['pointer'].split('/')[1:]:
                    value=value[int(key)] if isinstance(value,list) else value[key]
            assert {p['paper_id'] for p in corpus['papers']} >= {p['paper_id'] for p in data['systems']}
        return url
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked=list(pool.map(check,sorted(urls)))
    print(f'{len(checked)} published paper, problem, glossary and handoff destinations verified at {args.site_base}')

if __name__=='__main__': main()
