"""Question-led presentation of the existing catalogue. No runtime fetch.

The six doors are editorial navigation, not new scientific categories. The
complete catalogue remains separately addressable. Everything below is built
from the registry and explorer.json, with ordinary links as the fallback.
"""
from __future__ import annotations
import html
import json
from pathlib import Path

e = html.escape


def object_svg(kind: str) -> str:
    """Small original explanatory drawings. Not data charts or proof results."""
    common = 'viewBox="0 0 360 172" fill="none" aria-hidden="true" focusable="false"'
    line = 'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "research":
        body = '''<path class="obj-thread" d="M36 112C110 146 200 27 324 93"/>
        <g class="obj-number"><rect x="35" y="35" width="74" height="92" rx="3"/><path d="M47 52h22M47 113h48"/><text x="50" y="94" class="obj-large">257</text></g>
        <g class="obj-cube"><path d="m161 38 39-20 39 20v58l-39 22-39-22zM161 38l39 22 39-22M200 60v58"/><circle cx="200" cy="68" r="7" class="obj-solid"/></g>
        <g class="obj-magnets"><path d="M275 55v20m-5-5 5 5 5-5M305 56v20m-5-15 5-5 5 5M275 95v20m-5-5 5 5 5-5M305 95v20m-5-15 5-5 5 5"/><path class="obj-faint" d="M272 85h38M290 53v66"/></g>'''
    elif kind == "proofs":
        body = '''<g class="obj-sheet"><path d="M28 22h122v124H28z"/><path d="M44 40h60M44 58h87M44 91h82M44 111h71M44 129h48"/><rect class="obj-highlight" x="39" y="69" width="99" height="13" rx="2"/></g>
        <g class="obj-proof"><path d="M215 29h118v124H215z"/><path d="M231 47h70M231 64h45M242 98h74M242 116h51M231 137h34"/><rect class="obj-highlight" x="225" y="75" width="99" height="13" rx="2"/></g>
        <path class="obj-link" d="M138 76C174 76 182 82 226 82"/><circle class="obj-solid obj-traveller" cx="181" cy="79" r="5"/>
        <text class="obj-label" x="46" y="164">PAPER</text><text class="obj-label" x="240" y="169">LEAN PROOF</text>'''
    elif kind == "trace":
        body = '''<path class="obj-thread" d="M36 35v105c0 10 12 14 21 14h263"/>
        <g class="obj-event"><circle cx="36" cy="35" r="5" class="obj-solid"/><path d="M55 20h244v32H55z"/><text class="obj-code" x="69" y="41">read the file</text><path d="m279 32 5 5 9-11"/></g>
        <g class="obj-event"><circle cx="36" cy="83" r="5" class="obj-solid"/><path d="M55 68h244v32H55z"/><text class="obj-code" x="69" y="89">change the function</text><path d="m279 80 5 5 9-11"/></g>
        <g class="obj-event"><circle cx="36" cy="131" r="5" class="obj-solid"/><path d="M55 116h244v32H55z"/><text class="obj-code" x="69" y="137">run the tests</text><circle cx="285" cy="131" r="5" class="obj-solid"/></g>'''
    elif kind == "code":
        body = '''<g class="obj-links"><path d="M108 41C164 41 135 102 190 102M108 41C174 41 188 35 248 35M190 102C218 102 222 143 272 143M190 102C221 102 210 35 248 35M108 41C98 90 80 135 63 135"/></g>
        <g class="obj-box"><rect x="20" y="20" width="88" height="42" rx="4"/><text x="36" y="46" class="obj-code">parse</text></g>
        <g class="obj-box"><rect x="146" y="81" width="88" height="42" rx="4"/><text x="160" y="107" class="obj-code">resolve</text></g>
        <g class="obj-box"><rect x="248" y="14" width="88" height="42" rx="4"/><text x="265" y="40" class="obj-code">index</text></g>
        <circle cx="63" cy="135" r="10" class="obj-solid"/><circle cx="272" cy="143" r="10" class="obj-solid"/>
        <circle class="obj-signal" cx="191" cy="101" r="30"/>'''
    elif kind == "bugs":
        body = '''<g class="obj-bug-before"><rect x="25" y="25" width="116" height="107" rx="5"/><path d="M43 46h67M43 65h53M43 84h68M43 105h34"/><circle cx="115" cy="105" r="18" class="obj-paper"/><path d="m108 98 14 14m0-14-14 14"/></g>
        <path class="obj-link" d="M143 77h63m-10-7 10 7-10 7"/>
        <g class="obj-bug-after"><rect x="220" y="25" width="116" height="107" rx="5"/><path d="M238 46h67M238 65h53M238 84h68M238 105h34"/><circle cx="310" cy="105" r="18" class="obj-paper"/><path d="m301 105 6 6 12-14"/></g>
        <text x="43" y="156" class="obj-label">MISSED BUG</text><text x="229" y="156" class="obj-label">NEXT PROMPT</text>'''
    elif kind == "quantum":
        dots = ''.join(f'<circle cx="{35+(i%8)*25}" cy="{37+(i//8)*25}" r="6" class="obj-query"/>' for i in range(32))
        body = dots + '''<path class="obj-thread" d="M236 28v112"/><path class="obj-cube" d="m263 63 30-17 30 17v42l-30 17-30-17zM263 63l30 17 30-17M293 80v42"/><text x="31" y="161" class="obj-label">INPUT DATA</text><circle cx="293" cy="80" r="5" class="obj-solid"/>'''
    elif kind == "magnets":
        arrows=[]
        for block in range(2):
            for row in range(3):
                for col in range(4):
                    x=38+block*187+col*27; y=38+row*35
                    angle=180 if ((row*3+col+block)%3==0) else 0
                    arrows.append(f'<path class="obj-spin" transform="rotate({angle} {x} {y})" d="M{x} {y+10}v-20m-6 6 6-6 6 6"/>')
        body=''.join(arrows)+'''<path class="obj-thread" d="M174 30v95"/><text class="obj-label" x="46" y="153">ONE ARRANGEMENT</text><text class="obj-label" x="236" y="153">ANOTHER</text>'''
    else:
        body='''<path class="obj-thread" d="M66 85C110 42 153 124 202 83S267 39 319 83"/>
        <g class="obj-step"><path d="M25 35h65v82H25zM37 51h34M37 66h39M37 81h30M37 98h36"/><text class="obj-label" x="35" y="144">PROOF</text></g>
        <g class="obj-step"><path d="M135 53h69v87h-69zM149 70h38M149 85h31M149 100h37M149 119h24"/><text class="obj-label" x="148" y="164">PAPER</text></g>
        <g class="obj-step"><rect x="247" y="30" width="90" height="67" rx="3"/><path d="m281 47 24 16-24 16z"/><path d="M247 112h90M247 119h30m7 0h32"/><text class="obj-label" x="276" y="144">FILM</text></g>'''
    return f'<svg class="specimen specimen--{e(kind)}" {common}><g {line}>{body}</g></svg>'


def drawings() -> dict:
    """Door and project drawings from door_art.py, over the earlier set."""
    out = {k: object_svg(k) for k in ['research','proofs','trace','code','bugs','funnel','quantum','magnets']}
    try:
        import door_art
    except ImportError:
        return out
    out.update({k: door_art.art_svg(k) for k in [*door_art.DOOR_KINDS, *door_art.PROJECT_KINDS]})
    return out


def demo_states() -> dict:
    try:
        import door_art
    except ImportError:
        return {}
    return {k: [list(x) for x in v] for k, v in door_art.DEMO_STATES.items()}


def build_view(registry: dict, glossary: dict, root: Path) -> dict:
    config=json.loads((root/'explorer.json').read_text())
    owners={p['id']:p for p in registry['sites']+registry['projects']}
    canonical=registry.get('_canonical_v3',{})
    canonical_projects={p['slug']:p for p in canonical.get('projects',[])}
    canonical_films={f['slug']:f for f in canonical.get('resources',[]) if f['type']=='video'}
    repos={r['id']:r for r in registry['repos']}
    areas={p:a['id'] for a in registry['areas'] for p in a['items']}
    projects={}
    for pid,p in owners.items():
        projects[pid]={**p,'area':areas.get(pid,'maths'),'question':config['project_questions'][pid],
            'choice':config['project_choices'][pid], 'object':config['project_objects'][pid],
            'repo_records':[repos[r] for r in p.get('repos',[]) if r in repos],
            'term_refs':canonical_projects.get(pid,{}).get('term_refs',[])}
    films={}
    for f in registry['films']:
        text=root/'content'/'transcripts'/(f['id']+'.md')
        films[f['id']]={**f,'term_refs':canonical_films.get(f['id'],{}).get('term_refs',[]),
            'transcript':text.read_text(encoding='utf-8') if text.exists() else None}
    return {'config':config,'projects':projects,'films':films,
        'terms':glossary['terms'],'owner':registry['owner'],'links':registry.get('links',[]),
        'collections':registry.get('collections',[]),'contributions':registry.get('contributions',[]),
        'earlier':registry.get('earlier',[]),
        'objects':drawings(),'demo':demo_states()}


def door_videos(view: dict, door: dict) -> str:
    """'3 short videos, 1:38 to 1:50' from the short videos of a door's projects."""
    # The same choice as ExplorerModel.lead: the short video each project's card shows.
    import re
    secs = []
    for pid in door["projects"]:
        shorts = [view["films"][fid] for fid in view["projects"][pid]["films"]
                  if view["films"].get(fid, {}).get("format") == "short" and view["films"][fid].get("edition") != "earlier"]
        lead = None
        if door["id"] == "proofs":
            lead = next((f for f in shorts if re.search(r"reader|sk-website", f["id"])), None)
        if lead is None and pid == "maths":
            lead = next((f for f in shorts if f["id"] == "short-mathematics-overview"), None)
        lead = lead or (shorts[0] if shorts else None)
        if lead:
            secs.append(lead.get("duration_seconds") or lead.get("cut_seconds") or 0)
    n = len(secs)

    def clock(s: int) -> str:
        return f"{s // 60}:{s % 60:02d}"
    if n > 1 and min(secs) != max(secs):
        span = f", {clock(min(secs))} to {clock(max(secs))}"
    else:
        span = f", {clock(secs[0])}" if secs else ""
    return f"{n} short video{'s' if n != 1 else ''}{span}"


def _thumb_film(f: dict) -> str:
    stem = f.get("still") or f.get("poster")
    img = f'<img src="{e(stem)}-640.webp" width="1280" height="720" alt="" loading="lazy" decoding="async">' if stem else ""
    secs = f.get("duration_seconds") or f.get("cut_seconds") or 0
    time = f'<span class="thumb__time">{secs // 60}:{secs % 60:02d}</span>' if secs else ""
    label = e(f["title"]) + ("" if f.get("youtube") else " (in preparation: opens the transcript)")
    if f.get("youtube"):
        return f'<a class="thumb" href="{e(f["youtube"])}" target="_blank" rel="noopener" title="{e(f["title"])}" aria-label="Watch {label}">{img}{time}<span class="thumb__play" aria-hidden="true">▶</span></a>'
    return f'<a class="thumb is-coming" href="all.html#film-{e(f["id"])}" data-film="{e(f["id"])}" title="{e(f["title"])}" aria-label="{label}">{img}{time}</a>'


def _thumb_site(p: dict) -> str:
    if not p.get("url"):
        note = "Not released" if p["id"] == "codemap" else "No website"
        return f'<span class="cell-empty">{note}</span>'
    cap = p.get("capture")
    pics = (f'<img class="when-light" src="{e(cap)}-light-720.webp" width="720" height="405" alt="" loading="lazy" decoding="async">'
            f'<img class="when-dark" src="{e(cap)}-dark-720.webp" width="720" height="405" alt="" loading="lazy" decoding="async">') if cap else ""
    return f'<a class="thumb thumb--site" href="{e(p["url"])}" target="_blank" rel="noopener" title="{e(p["name"])}" aria-label="Open the {e(p["name"])} website">{pics}<span class="thumb__site">{e(p["name"])} ↗</span></a>'


def index_markup(view: dict) -> str:
    """Every project as one row: short videos, full videos, website, code.
    Built from the same view data as the explorer, so it needs no JavaScript."""
    films, projects = view["films"], view["projects"]
    seen, groups = set(), []
    repos = set()
    for d in view["config"]["doors"]:
        rows = []
        for pid in d["projects"]:
            if pid in seen:
                continue
            seen.add(pid)
            p = projects[pid]
            now = [films[f] for f in p["films"] if f in films and films[f].get("edition") != "earlier"
                   and not (films[f].get("superseded_by") and films.get(films[f]["superseded_by"], {}).get("youtube"))]
            shorts = [f for f in now if f.get("format") == "short"]
            longs = [f for f in now if f.get("format") != "short"]
            code = "".join(f'<a href="{e(r["href"])}" target="_blank" rel="noopener">{e(r["name"])} <span aria-hidden="true">↗</span></a>' for r in p["repo_records"]) or '<span class="cell-empty">Private</span>'
            repos.update(r["id"] for r in p["repo_records"])
            rows.append(f'''<article class="index-row ink-{e(p['area'])}" id="index-{e(pid)}">
            <div class="index-row__name"><a href="all.html#project-{e(pid)}" data-route="p={e(pid)}" data-parent="{e(d['id'])}">{e(p['name'])}</a><p>{e(p.get('plain') or '')}</p></div>
            <ol class="index-row__strand">
            <li class="cell cell--short"><span class="cell__label">Short</span><div class="cell__items">{''.join(_thumb_film(f) for f in shorts)}</div></li>
            <li class="cell cell--long"><span class="cell__label">Full</span><div class="cell__items">{''.join(_thumb_film(f) for f in longs) or '<span class="cell-empty">None yet</span>'}</div></li>
            <li class="cell cell--site"><span class="cell__label">Website</span><div class="cell__items">{_thumb_site(p)}</div></li>
            <li class="cell cell--code"><span class="cell__label">Code</span><div class="cell__items cell__items--code">{code}</div></li>
            </ol></article>''')
        if rows:
            groups.append(f'<section class="index-group ink-{e(d["ink"])}"><h3><a href="all.html#topic-{e(d["id"])}" data-route="d={e(d["id"])}">{e(d["question"])}</a></h3>{"".join(rows)}</section>')
    intro = [films[i] for i in ("short-introduction", "long-introduction", "introduction") if i in films]
    if intro:
        shorts = [f for f in intro if f.get("format") == "short"]
        longs = [f for f in intro if f.get("format") != "short"]
        groups.insert(0, f'''<section class="index-group ink-explain"><h3><a href="all.html#introductions" data-route="intro">Start here: how the projects fit together</a></h3>
        <article class="index-row ink-explain" id="index-introduction"><div class="index-row__name"><a href="all.html#introductions" data-route="intro">Introduction</a><p>The two ideas, and every project in turn</p></div>
        <ol class="index-row__strand"><li class="cell cell--short"><span class="cell__label">Short</span><div class="cell__items">{''.join(_thumb_film(f) for f in shorts)}</div></li>
        <li class="cell cell--long"><span class="cell__label">Full</span><div class="cell__items">{''.join(_thumb_film(f) for f in longs)}</div></li>
        <li class="cell cell--site"><span class="cell__label">Website</span><div class="cell__items"><span class="cell-empty">This page</span></div></li>
        <li class="cell cell--code"><span class="cell__label">Code</span><div class="cell__items cell__items--code"><a href="https://github.com/wcook04/wcook04.github.io" target="_blank" rel="noopener">wcook04.github.io <span aria-hidden="true">↗</span></a></div></li></ol></article></section>''')
    n_sites = sum(1 for p in projects.values() if p.get("url"))
    n_films = sum(1 for f in films.values() if f.get("edition") != "earlier")
    return f'''<section class="work-index" id="index" aria-labelledby="index-heading">
    <div class="index-intro"><p class="eyebrow">The index</p><h2 id="index-heading">Every project, from its short video to its code.</h2>
    <p>{len(projects)} projects, {n_films} current videos, {n_sites} websites and {len(repos)} repositories. A short video leads to its full video; the same data is in <a href="catalogue.json">catalogue.json</a> for programs.</p></div>
    <div class="index-cols" aria-hidden="true"><span>Project</span><span>Short videos</span><span>Full videos</span><span>Website</span><span>Code</span></div>
    {"".join(groups)}
    <p class="index-more"><a href="all.html#films" data-route="films">Every video, including earlier editions →</a><a href="all.html" data-route="all">Search all the work →</a><a href="all.html#terms" data-route="terms">Glossary of terms →</a></p>
    </section>'''




def home_markup(view: dict) -> str:
    doors=[]
    for i,d in enumerate(view['config']['doors']):
        shortcuts=''
        if d.get('shortcuts'):
            shortcuts='<div class="door-shortcuts">'+''.join(f'<a href="all.html#project-{e(s["project"])}" data-route="p={e(s["project"])}" data-parent="{e(d["id"])}">{e(s["label"])}</a>' for s in d['shortcuts'])+'</div>'
        doors.append(f'''<article class="door door--{e(d['id'])} ink-{e(d['ink'])}" data-door="{e(d['id'])}">
        <a class="door-open" href="all.html#topic-{e(d['id'])}" data-route="d={e(d['id'])}" aria-describedby="hint-{e(d['id'])}">
        <div class="door-object" data-shape="{e(d['id'])}">{view['objects'][d['object']]}</div>
        <h2>{e(d['question'])}<span class="open-arrow" aria-hidden="true">↗</span></h2>
        </a><p class="door-videos"><span class="knot" aria-hidden="true"></span>{door_videos(view, d)}</p><p class="door-caption" id="hint-{e(d['id'])}">{e(d['caption'])}</p>{shortcuts}</article>''')
    return f'''<section class="home-view" aria-labelledby="home-heading">
    <div class="scene-heading"><div class="principles"><p class="eyebrow">{e(view['config']['eyebrow'])}</p><h1 id="home-heading" tabindex="-1">{''.join(f'<span class="principle"><span class="principle__n" aria-hidden="true">{i}</span>{e(t)}</span>' for i, t in enumerate(view['config']['principles'], 1))}</h1>
    <p class="scene-intro">{e(view['config']['subtitle'])} <a href="all.html#introductions" data-route="intro">Watch the introduction <span aria-hidden="true">↗</span></a></p></div></div>
    <div class="question-scene"><svg class="scene-threads" aria-hidden="true"><g></g></svg>{''.join(doors)}</div>
    <div class="scene-footer"><a href="#index" data-scroll="index">The index of all {len(view['projects'])} projects <span aria-hidden="true">↓</span></a><a href="all.html" data-route="all">Search all the work <span aria-hidden="true">→</span></a></div>
    </section>{index_markup(view)}'''


def render_page(registry: dict, glossary: dict, root: Path, structured: str) -> str:
    v=build_view(registry,glossary,root)
    data=json.dumps(v,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    return f'''<!doctype html>
<html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-src 'none'">
<title>Will Cook — follow the work</title><meta name="description" content="Explore AI-assisted mathematics, tools for coding assistants, and ways to make the work understandable.">
<link rel="canonical" href="https://wcook04.github.io/"><meta name="robots" content="index, follow">
<meta name="color-scheme" content="light dark"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/hub.css"><link rel="stylesheet" href="assets/explorer.css"><link rel="stylesheet" href="assets/door-art.css"><script src="assets/explore-model.js" defer></script><script src="assets/explore.js" defer></script>
<script type="application/ld+json">{structured}</script></head>
<body class="question-studio"><a class="studio-skip" href="#main">Skip to the questions</a>
<header class="studio-header"><a class="studio-brand" href="index.html" data-route="home"><img src="assets/favicon.svg" width="27" height="27" alt=""><span>Will Cook</span></a>
<nav aria-label="Main"><a href="index.html" data-route="home" data-nav="home" aria-current="page">Explore</a><a href="all.html" data-route="all" data-nav="all">All work</a><a href="all.html#films" data-route="films" data-nav="films">Videos</a><a href="all.html#about" data-route="about" data-nav="about">About & contact</a></nav>
<button class="theme-button" type="button" aria-label="Switch to dark theme" title="Switch theme"><span aria-hidden="true">◐</span></button></header>
<main id="main" class="studio-main">{home_markup(v)}</main>
<div class="studio-announcement sr-only" role="status" aria-live="polite" aria-atomic="true"></div>
<div class="glossary-popover" id="glossary-card" hidden></div>
<dialog id="film-dialog" aria-labelledby="film-dialog-title"><div class="dialog-content"></div></dialog>
<noscript><p class="no-js-note">The questions above link to the complete <a href="all.html">static catalogue</a>. Enable JavaScript for the interactive explorer.</p></noscript>
<script type="application/json" id="explorer-data">{data}</script></body></html>'''


def render_static(registry:dict, glossary:dict, root:Path)->str:
    v=build_view(registry,glossary,root)
    def film(f):
        secs=f.get('duration_seconds') or f.get('cut_seconds')
        time=f' · {secs//60}:{secs%60:02}' if secs else ''
        title=f'<a href="{e(f["youtube"])}">{e(f["title"])}</a>' if f.get('youtube') else e(f['title'])+' — video in preparation'
        onwards=''.join(f'<li>Continue with <a href="#film-{e(x)}">{e(v["films"][x]["title"])}</a></li>' for x in f.get('leads_to',[]))
        return f'<article id="film-{e(f["id"])}"><h3>{title}</h3><p>{e(f["format"])}{time}</p><p>{e(f.get("takeaway", ""))}</p><ul>{onwards}</ul></article>'
    projects=[]
    for pid,p in v['projects'].items():
        links=[]
        if p.get('url'):links.append(f'<li><a href="{e(p["url"])}">Open {e(p["name"])}</a></li>')
        links += [f'<li><a href="{e(r["href"])}">{e(r["label"])}</a></li>' for r in p.get('routes',[])]
        links += [f'<li><a href="{e(r["href"])}">{e(r["name"])}</a> — {e(r.get("description",""))}</li>' for r in p['repo_records']]
        links += [f'<li><a href="#film-{e(f)}">{e(v["films"][f]["title"])}</a></li>' for f in p.get('films',[])]
        projects.append(f'<article id="project-{e(pid)}"><h2>{e(p["choice"])}</h2><p class="eyebrow">{e(p["name"])}</p><p>{e(p.get("line",p.get("purpose","")))}</p><ul>{"".join(links)}</ul></article>')
    topics=''.join(f'<section id="topic-{e(d["id"])}"><h2>{e(d["question"])}</h2><ul>'+''.join(f'<li><a href="#project-{e(p)}">{e(v["projects"][p]["choice"])}</a></li>' for p in d['projects'])+'</ul></section>' for d in v['config']['doors'])
    terms=''.join(f'<article id="term-{e(t["id"])}"><h3>{e(t["term"])}</h3><p>{e(t["preview"])}</p><p>{e(t["detail"])}</p></article>' for t in glossary['terms'])
    contacts=' · '.join(f'<a href="{e(c["href"])}">{e(c["label"])}</a>' for c in registry['owner']['contact'])
    contributions=''.join(f'<li><a href="https://github.com/wcook04/{e(c["repo"])}">{e(c["upstream"])}</a> — {e(c["what"])} {("<a href=" + chr(34) + e(c["evidence"]["href"]) + chr(34) + ">" + e(c["evidence"]["label"]) + "</a>") if c.get("evidence") else ""}</li>' for c in registry.get('contributions',[]))
    older=''.join(f'<li><a href="{e(c["href"])}">{e(c["name"])}</a> — {e(c["note"])}</li>' for c in registry.get('earlier',[]))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Will Cook — complete catalogue</title>
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-src 'none'">
<link rel="canonical" href="https://wcook04.github.io/all.html"><meta name="robots" content="index, follow">
<link rel="stylesheet" href="assets/hub.css"><link rel="stylesheet" href="assets/explorer.css"><link rel="stylesheet" href="assets/door-art.css"></head><body class="question-studio static-index"><a class="studio-skip" href="#main">Skip to the catalogue</a><header class="studio-header"><a class="studio-brand" href="index.html">← Explore the work</a><nav aria-label="Catalogue"><a href="#projects">Projects</a><a href="#films">Videos</a><a href="#terms">Terms</a><a href="#about">Contact</a></nav></header><main id="main"><h1>All the work, in one place.</h1>{topics}<section id="projects">{''.join(projects)}</section><section id="films"><h2>Every video</h2><span id="introductions"></span>{''.join(film(f) for f in registry['films'])}</section><section><h2>Contributions</h2><ul>{contributions}</ul><h2>Earlier work</h2><ul>{older}</ul></section><section id="terms"><h2>Terms</h2>{terms}</section><section id="about"><h2>Will Cook</h2><p>{e(registry['owner']['lede'])}</p><p>{e(registry['owner']['availability'])}</p><p>{contacts}</p></section></main></body></html>'''
