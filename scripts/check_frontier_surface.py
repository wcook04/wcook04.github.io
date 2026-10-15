#!/usr/bin/env python3
"""Check the public reading map, paper routes and shared glossary joins."""
import json
import re
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlsplit
from pathlib import Path
from build_absolute_frontier import SOURCE, INDEX, BEGIN, END, NUMBERS, SYSTEM_PAPERS, project, without_term_markup


class AgentDiscoveryLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attributes):
        if tag == 'link':
            self.links.append(dict(attributes))


def check_agent_navigation(root: Path):
    """Keep static root interfaces discoverable without preloading their data."""
    assert (root / '.nojekyll').is_file(), 'raw Markdown publication requires .nojekyll'
    files = ('llms.txt', 'agent-guide.md')
    for name in files:
        assert (root / name).is_file(), f'missing root agent interface: {name}'
    entry = (root / 'llms.txt').read_text()
    guide = (root / 'agent-guide.md').read_text()
    readme = (root / 'README.md').read_text()
    links = AgentDiscoveryLinks()
    links.feed((root / 'index.html').read_text())
    required = {
        ('help', 'text/plain', '/llms.txt'),
        ('alternate', 'text/markdown', '/agent-guide.md'),
    }
    actual = {(link.get('rel'), link.get('type'), link.get('href')) for link in links.links}
    assert required <= actual, 'root agent discovery links are missing'
    for link in links.links:
        if urlsplit(link.get('href', '')).path.lstrip('/') in files:
            assert not {'prefetch', 'preload', 'modulepreload'} & set(link.get('rel', '').split()), 'agent files must load only on request'
    for project in ('plectis', 'plectis-atlas', 'plectis-zenith'):
        endpoint = f'https://wcook04.github.io/{project}/llms.txt'
        assert endpoint in entry and endpoint in guide, f'missing project route: {project}'
    for name in files:
        assert f']({name})' in readme, f'root role missing from README: {name}'
    for document in (entry, guide):
        for url in re.findall(r'\]\((https://wcook04\.github\.io/[^)]+)\)', document):
            path = urlsplit(url).path.lstrip('/')
            # Project deployments have separate owners. Check only this repo's
            # static root and data routes offline; verify project links live.
            if path in files or path.startswith('data/'):
                assert (root / path).is_file(), f'missing local directory route: {path}'
    data = json.loads((root / 'data/absolute-frontier.json').read_text())
    assert data['source_hashes'] and data['systems'] and data['items']
    assert all(row.get('paper_id') and row.get('href') for row in data['systems'])
    assert all(all(key in row for key in ('problem', 'paper_href', 'page_href', 'long_records')) for row in data['items'])
    assert 'historical' in entry.lower() and 'historical' in guide.lower(), 'legacy map must retain its status'


def main():
    check_agent_navigation(Path(__file__).resolve().parents[1])
    payload=json.loads(SOURCE.read_text())
    markup=INDEX.read_text()
    text=without_term_markup(markup)
    if without_term_markup(project(markup,payload))!=text:
        raise SystemExit('generated reading map or problem portraits have drifted')
    assert [p['problem'] for p in payload['items']]==NUMBERS
    assert all(p['status'] == ('formal statement refuted' if p['problem'] == 1041 else 'open')
               for p in payload['items'])
    region=text[text.index(BEGIN):text.index(END)]
    # The root page keeps each problem to one compact, source-backed route. It
    # does not duplicate the research introductions or paper catalogue.
    assert 'class="flagship"' not in region
    assert 'https://wcook04.github.io/plectis/maths/' in region
    assert 'https://wcook04.github.io/plectis/docs/papers.html' in region
    assert 'https://wcook04.github.io/plectis/#demo-videos' in region
    assert 'id="eight-problem-frontier" tabindex="-1"' in region
    problem_routes = re.findall(r'<a href="[^"]+" data-dest="problem-(\d+)">', region)
    assert [int(number) for number in problem_routes] == NUMBERS
    assert len(re.findall(r'<a\s', region)) == len(NUMBERS) + 8
    assert 'maths/documents/weighted-257-task.html' in region
    assert 'https://youtu.be/VoWByIOIuBE' in region
    assert 'maths/papers/claim-faithful-publication-systems.html' in region
    assert tuple(p['paper_id'] for p in payload['systems']) == SYSTEM_PAPERS
    for row in payload['items']:
        assert f'data-problem="{row["problem"]}"' in text
        assert row['paper_href'] and row['page_href']
        assert row['page_href'] in text
    assert 'https://github.com/wcook04/plectis-erdos' in text  # renamed 2026-09; the old address redirects
    assert 'href="https://github.com/wcook04/plectis"' not in text
    assert 'plectis-ai-reader-complete.json' in text
    assert '13-paper' not in text and 'Five results' not in text
    ids=re.findall(r'\bid="([^"]+)"',markup)
    assert len(ids)==len(set(ids)), 'duplicate HTML ids'
    glossary=json.loads((Path(__file__).resolve().parents[1]/'data/glossary-terms.json').read_text())
    for term in re.findall(r'data-term="([^"]+)"',markup):
        assert unescape(term) in glossary['terms'], f'undefined glossary term {term}'
    assert 'BEGIN generated glossary terms' in markup
    print('Public front door: agent directory, root routes, compact destinations, eight-problem source, keyboard entry and glossary verified')

if __name__=='__main__': main()
