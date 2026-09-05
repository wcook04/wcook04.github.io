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
LEAN = 'https://github.com/wcook04/plectis-lean-erdos249-257'
NUMBERS = [68, 243, 249, 251, 257, 269, 1041, 1049]
TERM = re.compile(r'<a class="term(?: is-again)?" data-term="[^"]*" href="[^"]*">(.*?)</a>', re.S)
e = html.escape


def snapshot(site: Path) -> dict:
    names = ['plectis-ai-reader-complete.json', 'lean/problems.json']
    raw = {name: (site/name).read_bytes() for name in names}
    packet = json.loads(raw[names[0]])
    source = json.loads(raw[names[1]])
    corpus = packet['scholarly_corpus']
    if not all(p.get('source_embedded') for p in corpus['papers']):
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
            'public_source_commit':next(r['revision'] for r in corpus['repository_maps'] if r['repository']=='plectis-lean-erdos249-257'),
            'reading_graph_path':BASE+'plectis-ai-reader-complete.json#/scholarly_corpus/reading_graph',
            'systems':[{'title':p['title'],'href':p['public_pdf_url'],'paper_id':p['paper_id']} for p in systems],
            'items':items}


def render(payload: dict) -> str:
    labels = {'claim-faithful-publication-systems':'How this project works', 'open-source-mathematics-strategy':'How to contribute'}
    systems = '\n'.join(f'<p class="af-route"><a href="{BASE}maths/papers/{e(p["paper_id"])}.html">{labels[p["paper_id"]]}</a> <span>— {e(p["title"])}</span></p>' for p in payload['systems'])
    rows = []
    for p in payload['items']:
        links = f'<a href="{e(p["paper_href"])}" data-dest="paper-{p["problem"]}">Short note</a> · <a href="{e(p["page_href"])}#frontier">Results and remaining work</a>'
        for long in p['long_records']:
            links += f' · <a href="{e(long["href"])}">Long working record</a>'
        rows.append(f'''<article class="flagship" tabindex="0" data-dest="problem-{p['problem']}">
          <p class="flagship__line"><span class="flagship__number">#{p['problem']}</span><span class="flagship__kind">{e(p['status'].capitalize())}</span></p>
          <div class="flagship__body"><h3><a href="{e(p['page_href'])}">{e(p['title'])}</a></h3>
          <p class="flagship__question">{e(p['question'])}</p>
          <p class="flagship__exits">{links}</p></div></article>''')
    return f'''{BEGIN}
      <section class="absolute-frontier" aria-labelledby="absolute-frontier-title">
        <p class="absolute-frontier__eyebrow">The research and how to join</p>
        <h2 id="absolute-frontier-title">Start with the research.</h2>
        <p class="absolute-frontier__thesis">Choose a problem to see its question, results and remaining work. You can read everything in your browser.</p>
        <p><a class="btn" href="{BASE}maths/index.html#problems">Explore the eight problems</a></p>
        <p class="absolute-frontier__thesis">Contributors receive credit for their work. If you solve a problem, the result and credit are yours and your collaborators’. <a href="{LEAN}/blob/main/docs/research-commons/CREDIT_POLICY.md">How credit works</a></p>
        {systems}
        <details class="route-more"><summary>Source code and contribution instructions</summary><p class="af-route"><a data-to="repo" href="{LEAN}">Lean repository and README</a> · <a href="{LEAN}/blob/main/CONTRIBUTING.md">Contribution instructions</a></p></details>
        <details class="route-more"><summary>Browse the problem notes here</summary>
        <p class="absolute-frontier__note">In numerical order. Each short note describes one problem; the longer records retain additional working context.</p>
        <div class="flagships">{''.join(rows)}</div></details>
        <p class="absolute-frontier__note">Lean checks formal statements. It does not establish novelty, significance or peer review.</p>
        <p class="af-route"><a href="{BASE}docs/papers.html">All papers and PDFs</a> · <a href="{BASE}docs/glossary.html">Glossary</a></p>
      </section>
{END}'''


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
        text,count=re.subn(pattern,lambda _:sheet,text,count=1,flags=re.S)
        if count!=1: raise ValueError(f'missing portrait #{n}')
        text=re.sub(rf'(<span class="frontier-plate__number">{n}</span><span class="frontier-plate__handle">).*?(</span>)',lambda m:m[1]+e(p['title'])+m[2],text,count=1,flags=re.S)
    text=re.sub(r'(<span class="frontier-plate__boundary">).*?(</span>)', r'\1Original problem remains open.\2', text, flags=re.S)
    # The interactive portrait opens the same current page as its row.
    text=re.sub(r'    /\* This is presentation text for the destination bar.*?    var DEST =', '    var DEST =', text, count=1, flags=re.S)
    for p in payload['items']:
        n=p['problem']
        route=f'"problem-{n}": {{ to: "page", view: "problem", problem: "{n}", host: "wcook04.github.io", path: "/plectis/maths/problems/erdos_{n}.html", href: "{p["page_href"]}" }}'
        text=re.sub(rf'"problem-{n}":\s*\{{.*?\}}',lambda _:route,text,count=1,flags=re.S)
    text=re.sub(r'"math-frontier":\s*\{.*?\}', '"math-frontier": { to: "page", view: "frontier", host: "wcook04.github.io", path: "/plectis/maths/", href: "https://wcook04.github.io/plectis/maths/" }', text, count=1, flags=re.S)
    text=re.sub(r'"lean-github":\s*\{.*?\}', '"lean-github": { to: "repo", host: "github.com", path: "/wcook04/plectis-lean-erdos249-257", src: "assets/previews/lean-github.jpg", href: "'+LEAN+'" }', text, count=1, flags=re.S)
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
