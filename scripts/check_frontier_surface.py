#!/usr/bin/env python3
"""Check the public reading map, paper routes and shared glossary joins."""
import json
import re
from html import unescape
from pathlib import Path
from build_absolute_frontier import SOURCE, INDEX, BEGIN, END, NUMBERS, TERM, project


def main():
    payload=json.loads(SOURCE.read_text())
    markup=INDEX.read_text()
    text=TERM.sub(r'\1',markup)
    if TERM.sub(r'\1',project(markup,payload))!=text:
        raise SystemExit('generated reading map or problem portraits have drifted')
    assert [p['problem'] for p in payload['items']]==NUMBERS
    assert all(p['status']=='open' for p in payload['items'])
    region=text[text.index(BEGIN):text.index(END)]
    # The root page routes to the complete mathematics index. It does not
    # duplicate eight research introductions and the paper catalogue.
    assert 'class="flagship"' not in region
    assert 'https://wcook04.github.io/plectis/maths/' in region
    assert 'https://wcook04.github.io/plectis/docs/papers.html' in region
    assert 'https://wcook04.github.io/plectis/#demo-videos' in region
    assert 'id="eight-problem-frontier" tabindex="-1"' in region
    assert len(re.findall(r'<a\s', region)) <= 6
    assert [p['paper_id'] for p in payload['systems']]==['claim-faithful-publication-systems','open-source-mathematics-strategy']
    for row in payload['items']:
        assert f'data-problem="{row["problem"]}"' in text
        assert row['paper_href'] and row['page_href']
        assert row['page_href'] in text
    assert 'https://github.com/wcook04/plectis-erdos' in text  # renamed 2026-09; the old address redirects
    assert 'https://github.com/wcook04/plectis' in text
    assert 'plectis-ai-reader-complete.json' in text
    assert '13-paper' not in text and 'Five results' not in text
    ids=re.findall(r'\bid="([^"]+)"',markup)
    assert len(ids)==len(set(ids)), 'duplicate HTML ids'
    glossary=json.loads((Path(__file__).resolve().parents[1]/'data/glossary-terms.json').read_text())
    for term in re.findall(r'data-term="([^"]+)"',markup):
        assert unescape(term) in glossary['terms'], f'undefined glossary term {term}'
    assert 'BEGIN generated glossary terms' in markup
    print('Public front door: compact destinations, eight-problem source, keyboard entry and glossary verified')

if __name__=='__main__': main()
