#!/usr/bin/env python3
"""Refresh the public reading map from the Plectis site's published source snapshot.

The historical filename and region markers remain stable. This is an equal
problem index, not an independently ranked mathematical frontier.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/absolute-frontier.json'
INDEX = ROOT / 'index.html'
BEGIN = '      <!-- BEGIN generated absolute frontier -->'
END = '      <!-- END generated absolute frontier -->'
BASE = 'https://wcook04.github.io/plectis/'
LEAN = 'https://github.com/wcook04/plectis-erdos'
SOFTWARE = 'https://github.com/wcook04/plectis'
NUMBERS = [68, 243, 249, 251, 257, 269, 1041, 1049]
CORPUS_REPOSITORIES = ('plectis-erdos', 'plectis-lean-erdos249-257')
TERM = re.compile(r'<a class="term(?: is-again)?" data-term="[^"]*" href="[^"]*">(.*?)</a>', re.S)
e = html.escape


def corpus_revision(corpus: dict) -> str:
    """Read the current corpus identity while accepting older public packets."""
    for name in CORPUS_REPOSITORIES:
        rows = [row for row in corpus['repository_maps'] if row['repository'] == name]
        if len(rows) > 1:
            raise ValueError(f'duplicate repository map for {name}')
        if rows:
            revision = rows[0].get('revision')
            if not isinstance(revision, str) or not revision.strip():
                raise ValueError(f'missing source revision for {name}')
            return revision
    raise ValueError('the reading packet has no Plectis mathematics repository map')


def snapshot(site: Path) -> dict:
    names = ['plectis-ai-reader-complete.json', 'lean/problems.json']
    raw = {name: (site/name).read_bytes() for name in names}
    packet = json.loads(raw[names[0]])
    source = json.loads(raw[names[1]])
    corpus = packet['scholarly_corpus']
    if not corpus['papers'] or not all(p.get('source_embedded') and p.get('body') for p in corpus['papers']):
        raise ValueError('the reading packet has missing manuscripts')
    papers = {p['paper_id']: p for p in corpus['papers']}
    items = []
    for problem in sorted(source['problems'], key=lambda p:p['erdos_number']):
        paper = papers[problem['paper']['paper_id']]
        n = problem['erdos_number']
        item = {'problem':n, 'title':problem['short_title'],
                'question':problem['question'], 'status':problem['status'],
                'paper_title':paper['title'], 'paper_href':paper['public_pdf_url'],
                'page_href':BASE+f'maths/problems/erdos_{n}.html',
                'source_pointer':f"/scholarly_corpus/papers/{corpus['papers'].index(paper)}"}
        longs = [p for p in corpus['papers'] if p['paper_id'].startswith(f'erdos{n}-') and 'reasoning-surface' in p['paper_id']]
        item['long_records'] = [{'title':p['title'],'href':p['public_pdf_url']} for p in longs]
        items.append(item)
    if [p['problem'] for p in items] != NUMBERS:
        raise ValueError('source does not contain exactly the eight expected problems')
    systems = [papers[k] for k in ('claim-faithful-publication-systems','open-source-mathematics-strategy')]
    return {'schema':'public_reading_map_v1', 'generated_by':'scripts/build_absolute_frontier.py',
            'source_hashes':{name:hashlib.sha256(data).hexdigest() for name,data in raw.items()},
            'public_source_commit':corpus_revision(corpus),
            'reading_graph_path':BASE+'plectis-ai-reader-complete.json#/scholarly_corpus/reading_graph',
            'systems':[{'title':p['title'],'href':p['public_pdf_url'],'paper_id':p['paper_id']} for p in systems],
            'items':items}


def render(payload: dict) -> str:
    """Keep the personal homepage an introduction and destination index."""
    if [row['problem'] for row in payload['items']] != NUMBERS:
        raise ValueError('the source must retain all eight problems')
    problem_routes = '\n'.join(
        f'''          <p data-dest="problem-{row['problem']}"><a href="{e(row['page_href'], quote=True)}" data-dest="problem-{row['problem']}">Erdős #{row['problem']}</a> <span class="frontier-topic">{e(row['title'])}</span> · original problem remains open</p>'''
        for row in payload['items']
    )
    return f'''{BEGIN}
      <section class="absolute-frontier" id="eight-problem-frontier" tabindex="-1" aria-labelledby="absolute-frontier-title" data-scene-key="opening">
        <h2 id="absolute-frontier-title">Public work</h2>
        <p><a class="btn" href="{BASE}" data-dest="plectis-site">Explore Plectis</a></p>
        <p class="absolute-frontier__thesis">The project site introduces the research, software and recorded interface.</p>
        <p class="af-route"><a href="{BASE}maths/" data-dest="math-frontier">Mathematics</a> <span>· work on eight Erdős problems, all still open</span></p>
        <p class="frontier-instruction"><span class="frontier-instruction__wide">Hover or focus a problem to preview it; activate the link to open its page.</span><span class="frontier-instruction__narrow">Open a problem page:</span></p>
        <div class="frontier" aria-label="Eight Erdős problem pages">
{problem_routes}
        </div>
        <p class="af-route"><a href="{SOFTWARE}" data-to="repo">Software repository</a> <span>· public research and engineering tools</span></p>
        <p class="af-route"><a href="{LEAN}" data-dest="lean-github" data-to="repo">Mathematics repository</a> <span>· formal source and ways to continue the work</span></p>
        <p class="af-route"><a href="{BASE}docs/papers.html" data-dest="papers-catalogue">Papers</a> · <a href="{BASE}#demo-videos">Watch the introduction</a></p>
      </section>
{END}'''


def replace_required(text: str, pattern: str, replacement, label: str, *, expected: int = 1, flags: int = 0) -> str:
    """Replace a required projection surface and reject missing or duplicate owners."""
    text, count = re.subn(pattern, replacement, text, flags=flags)
    if count != expected:
        raise ValueError(f'expected {expected} {label}, found {count}')
    return text


def project(text: str, payload: dict) -> str:
    a=text.index(BEGIN); b=text.index(END,a)+len(END)
    text=text[:a]+render(payload)+text[b:]
    # Portraits and overview are projections of the same eight rows as the list.
    for p in payload['items']:
        n=p['problem']
        pattern=rf'<span class="shot__problem" data-problem="{n}".*?(?=\s*<span class="shot__problem"|\s*</span>\s*</a>\s*<p class="dest__hint")'
        sheet=f'''<span class="shot__problem" data-problem="{n}" aria-hidden="true">
          <span class="problem-sheet__topline"><span class="problem-sheet__number">Erdős #{n}</span><span class="problem-sheet__status">{e(p['status'].capitalize())}</span></span>
          <span class="problem-sheet__title">{e(p['title'])}</span>
          <span class="problem-sheet__question"><span class="problem-sheet__label">Question</span>{e(p['question'])}</span>
          <span class="problem-sheet__section"><span class="problem-sheet__label">Short note</span>{e(p['paper_title'])}</span>
          <span class="problem-sheet__section problem-sheet__section--open"><span class="problem-sheet__label">Research status</span>The original problem remains open. The problem page separates results, evidence and remaining work.</span></span>'''
        text=replace_required(text,pattern,lambda _:sheet,f'portrait #{n}',flags=re.S)
        text=replace_required(text,rf'(<span class="frontier-plate__number">{n}</span><span class="frontier-plate__handle">).*?(</span>)',lambda m:m[1]+e(p['title'])+m[2],f'frontier plate #{n}',flags=re.S)
    text=replace_required(text,r'(<span class="frontier-plate__boundary">).*?(</span>)',r'\1Original problem remains open.\2','frontier plate boundaries',expected=len(NUMBERS),flags=re.S)
    # The interactive portrait opens the same current page as its row.
    text=re.sub(r'    /\* This is presentation text for the destination bar.*?    var DEST =', '    var DEST =', text, count=1, flags=re.S)
    for p in payload['items']:
        n=p['problem']
        route=f'"problem-{n}": {{ to: "page", view: "problem", problem: "{n}", host: "wcook04.github.io", path: "/plectis/maths/problems/erdos_{n}.html", href: "{p["page_href"]}" }}'
        text=replace_required(text,rf'"problem-{n}":\s*\{{.*?\}}',lambda _:route,f'problem-{n} destination',flags=re.S)
    text=replace_required(text,r'"math-frontier":\s*\{.*?\}', '"math-frontier": { to: "page", view: "frontier", host: "wcook04.github.io", path: "/plectis/maths/", href: "https://wcook04.github.io/plectis/maths/" }','math-frontier destination',flags=re.S)
    text=replace_required(text,r'"lean-github":\s*\{.*?\}', '"lean-github": { to: "repo", host: "github.com", path: "/wcook04/plectis-erdos", src: "assets/previews/lean-github.jpg", href: "'+LEAN+'" }','lean-github destination',flags=re.S)
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-root',type=Path,help='refresh from a validated local Plectis site build')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--refresh-previews',action='store_true',help='render current short-note covers with Poppler; requires --site-root')
    args=parser.parse_args()
    if args.refresh_previews:
        if not args.site_root or args.check: parser.error('--refresh-previews needs --site-root and a write run')
    payload=snapshot(args.site_root) if args.site_root else json.loads(SOURCE.read_text())
    raw=INDEX.read_text(); expected=project(raw,payload)
    if args.check:
        if TERM.sub(r'\1',expected)!=TERM.sub(r'\1',raw): raise SystemExit('public reading map or portraits are stale')
        if args.site_root and payload!=json.loads(SOURCE.read_text()): raise SystemExit('public source snapshot changed; refresh the reading map')
        print('Public reading map: source, eight equal routes, papers and portraits agree')
    else:
        SOURCE.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        INDEX.write_text(expected)
        if args.refresh_previews:
            for item in payload['items']:
                pdf=args.site_root/'papers'/item['paper_href'].rsplit('/',1)[1]
                out=ROOT/'assets/previews'/f"paper-{item['problem']}-640"
                subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to-x','640','-scale-to-y','-1','-H','411','-jpeg','-jpegopt','quality=80',str(pdf),str(out)],check=True,capture_output=True)
        print('Refreshed two orientation papers and all eight problem routes')

if __name__=='__main__': main()
