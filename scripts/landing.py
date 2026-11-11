"""The home page: the weave and the stage.

The page draws the catalogue as it is. Every project is a row (a thread); every
thing a visitor can open is a mark on that thread, placed in a column by its
kind: short film, full film, website, paper, code. The row a visitor selects
shows what its marks lead to in the stage beside it: the film's own poster and
a silent loop cut from it, the website's first screen, the repository page.

Rows and marks are derived from sites.json (through the same view the tests
check) and from explorer.json, which names the groups, the plain-words row
labels and the two rows that stand above the groups. Nothing here is typed by
hand per project. The page works without JavaScript: the weave is a list of
real links and every article is visible. assets/landing.js selects one row at a
time, plays the loops and runs the tour. See docs/landing.md.
"""
from __future__ import annotations

import json
from html import escape as e
from pathlib import Path

COLUMNS = ("short", "full", "site", "paper", "code")
PAPER_ROLES = ("original", "exposition", "paper_index", "earlier_study")


def clock(seconds: int | None) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}" if seconds else ""


def spoken(seconds: int | None) -> str:
    if not seconds:
        return ""
    minutes, rest = divmod(seconds, 60)
    parts = [f"{minutes} minute{'s' if minutes != 1 else ''}"] if minutes else []
    if rest:
        parts.append(f"{rest} second{'s' if rest != 1 else ''}")
    return " ".join(parts)


def current_films(view: dict, ids: list[str]) -> list[dict]:
    films, out = view["films"], []
    for fid in ids:
        f = films.get(fid)
        if not f or not f.get("youtube") or f.get("edition") == "earlier":
            continue
        newer = f.get("superseded_by")
        if newer and films.get(newer, {}).get("youtube"):
            continue
        out.append(f)
    return out


def film_resource(f: dict, root: Path, shared: bool = False) -> dict:
    short = f["format"] == "short"
    stem = f.get("still") or f.get("poster")
    loop = f"assets/films/loops/{f['id']}.mp4"
    kind = "Short film" if short else "Full film"
    seconds = f.get("duration_seconds")
    return {
        "key": f["id"], "col": "short" if short else "full", "kind": kind,
        "detail": clock(seconds), "title": f["title"], "href": f["youtube"],
        "aria": f"{f['title']}: {kind.lower()} on YouTube" + (f", {spoken(seconds)}" if seconds else ""),
        "img": f"{stem}-640.webp" if stem else None, "img2": f"{stem}-1280.webp" if stem else None,
        "loop": loop if (root / loop).exists() else None, "shared": shared, "external": True,
    }


def papers_of(canonical: dict, pid: str) -> list[dict]:
    """A project's papers and paper indexes, in the catalogue's order."""
    resources = {r["id"]: r for r in canonical.get("resources", [])}
    found = []
    for rel in canonical.get("relationships", []):
        if rel["type"] != "resource_for" or rel["to"] != "project:" + pid:
            continue
        r = resources.get(rel["from"])
        if not r or not (r["type"] == "paper" or rel.get("role") == "paper_index"):
            continue
        url = next((p.get("url") for p in r.get("publications", []) if p.get("state") == "published" and p.get("url")), None)
        if url:
            found.append({"label": rel.get("label") or r["title"], "href": url, "order": rel.get("order", 0)})
    return sorted(found, key=lambda x: x["order"])


def build_rows(view: dict, canonical: dict, root: Path) -> list[dict]:
    """The rows of the weave, top to bottom, each with its resources by column."""
    config = view["config"]
    films = view["films"]
    owners_of_film: dict[str, set] = {}
    for pid, p in view["projects"].items():
        for fid in p.get("films", []):
            owners_of_film.setdefault(fid, set()).add(pid)
    shared = {fid for fid, owners in owners_of_film.items() if len(owners) > 1}

    def project_row(pid: str, group: dict, ink: str) -> dict:
        p = view["projects"][pid]
        res = []
        for f in current_films(view, p.get("films", [])):
            is_shared = f["id"] in shared
            leads_shared = any(t in shared for t in f.get("leads_to", []))
            r = film_resource(f, root, shared=is_shared)
            r["slot"] = 1 if (is_shared or leads_shared) else 0
            res.append(r)
        # Two films of one kind that are both a project's own take slots A then B.
        for col in ("short", "full"):
            own = [r for r in res if r["col"] == col]
            if len(own) == 2 and own[0]["slot"] == own[1]["slot"]:
                own[0]["slot"], own[1]["slot"] = 0, 1
        capture = p.get("capture")
        site_img = (f"{capture}-dark-720.webp", f"{capture}-dark-1440.webp") if capture else (None, None)
        if p.get("url"):
            res.append({"key": "site", "col": "site", "slot": 0, "kind": "Website", "detail": "", "title": p["name"],
                        "href": p["url"], "aria": f"{p['name']}: the website", "img": site_img[0], "img2": site_img[1],
                        "loop": None, "external": False, "caption": p.get("capture_caption")})
        papers = papers_of(canonical, pid)
        if papers:
            res.append({"key": "paper", "col": "paper", "slot": 0, "kind": "Paper", "detail": "", "title": papers[0]["label"],
                        "href": papers[0]["href"], "aria": f"{p['name']}: {papers[0]['label']}", "img": site_img[0],
                        "img2": site_img[1], "loop": None, "external": False})
        repos = p.get("repo_records", [])
        if repos:
            stem = f"assets/sites/repo-{pid}"
            if not (root / f"{stem}-720.webp").exists():
                stem = f"assets/sites/repo-{repos[0]['id']}"
            has = (root / f"{stem}-720.webp").exists()
            res.append({"key": "code", "col": "code", "slot": 0, "kind": "Code", "detail": "", "title": repos[0]["name"],
                        "href": repos[0]["href"], "aria": f"{repos[0]['name']}: the code on GitHub",
                        "img": f"{stem}-720.webp" if has else None, "img2": f"{stem}-1440.webp" if has else None,
                        "loop": None, "external": False, "note": repos[0].get("description")})
        order = {c: i for i, c in enumerate(COLUMNS)}
        res.sort(key=lambda r: (order[r["col"]], r["slot"]))
        used = {papers[0]["href"]} if papers else set()
        extra = [x for x in papers[1:]] + [x for x in p.get("routes", []) if x["href"] not in {y["href"] for y in papers}]
        extra += [{"label": r["name"] + " on GitHub", "href": r["href"]} for r in repos[1:]]
        return {"id": pid, "group": group["id"], "heading": group["heading"], "ink": ink,
                "label": config["row_labels"][pid], "name": p["name"], "question": p["question"],
                "line": p["line"], "credit": p.get("credit"), "resources": res,
                "extra": [x for x in extra if x["href"] not in used]}

    rows = []
    root_cfg = config["root"]
    root_group = {"id": "root", "heading": root_cfg["heading"]}
    root_projects = set()
    for item in root_cfg["rows"]:
        if item.get("project"):
            root_projects.add(item["project"])
            rows.append(project_row(item["project"], root_group, "root"))
        else:
            res = [dict(film_resource(films[fid], root), slot=0) for fid in item["films"] if films.get(fid, {}).get("youtube")]
            rows.append({"id": item["id"], "group": "root", "heading": root_cfg["heading"], "ink": "root",
                         "label": item["label"], "name": item["name"], "question": item["question"],
                         "line": item["line"], "credit": None, "resources": res, "extra": []})
    for door in config["doors"]:
        for pid in door["projects"]:
            if pid not in root_projects:
                rows.append(project_row(pid, door, door.get("ink", "code")))
    # The shared film ties the rows it belongs to: mark where the tie starts and ends.
    for fid in shared:
        holders = [i for i, row in enumerate(rows) if any(r["key"] == fid for r in row["resources"])]
        if len(holders) > 1 and holders == list(range(holders[0], holders[-1] + 1)):
            for i in holders:
                rows[i]["tie"] = "start" if i == holders[0] else "end" if i == holders[-1] else "mid"
    return rows


# ------------------------------------------------------------------ markup

def slots(columns: list) -> list[tuple[str, int]]:
    return [(col, s) for col, _, _, width in columns for s in range(width)]


def link_tail(r: dict) -> str:
    return ' target="_blank" rel="noopener noreferrer"' if r.get("external") else ' rel="noopener"'


def data_attrs(r: dict) -> str:
    chip = r["kind"] + (f", {r['detail']}" if r["detail"] else "")
    out = f' data-res="{e(r["key"])}" data-col="{e(r["col"])}" data-chip="{e(chip)}"'
    for key in ("img", "img2", "loop"):
        if r.get(key):
            out += f' data-{key}="{e(r[key])}"'
    return out


def weave(rows: list[dict], config: dict) -> str:
    landing = config["landing"]
    cols = landing["columns"]
    all_slots = slots(cols)
    head = "".join(f'<span class="col col--{width}"><span class="col__wide">{e(wide)}</span><span class="col__tight">{e(tight)}</span></span>'
                   for _, wide, tight, width in cols)
    out = [f'<li class="row row--head" aria-hidden="true"><span class="row__label"></span><span class="row__knots">{head}</span></li>']
    previous = None
    for row in rows:
        by_slot = {(r["col"], r["slot"]): r for r in row["resources"]}
        last = max((i for i, s in enumerate(all_slots) if s in by_slot), default=0)
        knots = []
        for col, s in all_slots:
            r = by_slot.get((col, s))
            if not r:
                knots.append('<span class="slot"></span>')
                continue
            tie = f' knot--tie-{row["tie"]}' if r.get("shared") and row.get("tie") else ""
            knots.append(f'<a class="slot knot knot--{col}{tie}" href="{e(r["href"])}"{link_tail(r)} aria-label="{e(r["aria"])}" '
                         f'title="{e(r["kind"] + (", " + r["detail"] if r["detail"] else "") + ": " + r["title"])}" data-knot="{e(r["key"])}"><i></i></a>')
        first = row["group"] != previous
        previous = row["group"]
        group = f'<span class="row__group">{e(row["heading"])}</span>' if first else ""
        name = f' <span class="row__name">{e(row["name"])}</span>' if row["name"] != row["label"] else ""
        out.append(
            f'<li class="row{" row--first" if first else ""}" data-row="{e(row["id"])}" data-group="{e(row["group"])}" data-ink="{e(row["ink"])}" data-last="{last}">{group}'
            f'<a class="row__label" href="#p-{e(row["id"])}"><span class="row__what">{e(row["label"])}</span>{name}</a>'
            f'<span class="row__knots">{"".join(knots)}</span></li>')
    key = landing["key"].split(". ")
    return (f'<nav class="weave" aria-labelledby="weave-title"><h2 class="weave__title" id="weave-title">Every project, at every level of detail</h2>'
            f'<ol class="weave__rows" role="list">{"".join(out)}</ol>'
            f'<p class="weave__note">{e(landing["weave_note"])} '
            f'<span class="weave__key"><span class="key key--maths"></span>{e(key[0])}. <span class="key key--code"></span>{e(key[1])}</span></p></nav>')


def picture(r: dict, *, sizes: str, eager: bool = False, cls: str = "") -> str:
    if not r.get("img"):
        return f'<span class="blank{(" " + cls) if cls else ""}"><span class="blank__name">{e(r["title"])}</span><span class="blank__note">{e(r.get("note") or "")}</span></span>'
    high = ' fetchpriority="high"' if eager else ""
    return (f'<img{(" class=" + chr(34) + cls + chr(34)) if cls else ""} src="{e(r["img"])}" srcset="{e(r["img"])} 720w, {e(r["img2"])} 1440w" sizes="{e(sizes)}" '
            f'alt="" width="1280" height="720" loading="{"eager" if eager else "lazy"}" decoding="async"{high}>')


def article(row: dict, terms, *, first: bool) -> str:
    res = row["resources"]
    lead = res[0]
    chip = lead["kind"] + (f", {lead['detail']}" if lead["detail"] else "")
    frame = (f'<a class="frame" href="{e(lead["href"])}"{link_tail(lead)} aria-label="{e(lead["aria"])}"{data_attrs(lead)}>'
             f'{picture(lead, sizes="(min-width: 1100px) 760px, 100vw", eager=first)}'
             f'<span class="frame__chip">{e(chip)}</span></a>')
    tiles = "".join(
        f'<li><a class="tile" href="{e(r["href"])}"{link_tail(r)} aria-label="{e(r["aria"])}"{data_attrs(r)}>'
        f'<span class="tile__pic">{picture(r, sizes="160px")}</span>'
        f'<span class="tile__kind">{e(r["kind"])}</span><span class="tile__detail">{e(r["detail"] or r["title"])}</span></a></li>'
        for r in res)
    extra = ""
    if row["extra"]:
        links = ", ".join(f'<a href="{e(x["href"])}" rel="noopener">{e(x["label"])}</a>' for x in row["extra"])
        extra = f'<p class="proj__more">Also here: {links}.</p>'
    credit = f'<p class="proj__credit">{terms.link(row["credit"])}</p>' if row.get("credit") else ""
    name = f'<p class="proj__name">{e(row["name"])}</p>' if row["name"] != row["question"] else ""
    return (f'<article class="proj" id="p-{e(row["id"])}" data-row="{e(row["id"])}" data-ink="{e(row["ink"])}" aria-labelledby="h-{e(row["id"])}">'
            f'{frame}<div class="proj__text">{name}<h3 class="proj__q" id="h-{e(row["id"])}">{e(row["question"])}</h3>'
            f'<p class="proj__line">{terms.link(row["line"])}</p>{credit}</div>'
            f'<ol class="strip" role="list" aria-label="{e(row["name"])}, from the short film to the source">{tiles}</ol>{extra}</article>')


def render(registry: dict, glossary: dict, root: Path, structured: str, hub) -> str:
    """index.html. `hub` is the build_hub module (versioned assets, Terms, shared sections)."""
    from explorer_v3 import build_view
    view = build_view(registry, glossary, root)
    config = view["config"]
    rows = build_rows(view, registry.get("_canonical_v3", {}), root)
    protect = [p["name"] for p in view["projects"].values()] + [r["name"] for r in registry["repos"]]
    terms = hub.Terms(glossary, protect=protect)
    articles, previous = [], None
    for i, row in enumerate(rows):
        if row["group"] != previous:
            articles.append(f'<h2 class="stage__group" data-group="{e(row["group"])}">{e(row["heading"])}</h2>')
            previous = row["group"]
        articles.append(article(row, terms, first=i == 0))
    doors = {d["id"]: d for d in config["doors"]}
    in_root = {r.get("project") for r in config["root"]["rows"]}
    topics = {}
    for alias, door in config.get("topic_aliases", {}).items():
        target = config.get("direct_topics", {}).get(alias) or next((p for p in doors[door]["projects"] if p not in in_root), None)
        if target:
            topics[alias] = target
    topic_attr = e(json.dumps(topics, separators=(",", ":")))
    owner = registry["owner"]
    principles = config["title"].split(". ", 1)
    contact = "".join(f'<li><a href="{e(c["href"])}" rel="noopener">{e(c["label"])}</a></li>' for c in owner["contact"])
    invitation = "".join(f"<p>{e(text)}</p>" for text in owner.get("invitation", []))
    v = hub.versioned
    description = ("Will Cook uses AI to make AI-written mathematics and code easier to understand: Lean proofs, papers, "
                   "reader websites and films, shown project by project.")
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="format-detection" content="telephone=no">
  <!-- Films open on YouTube; no player is embedded and nothing loads from another host. -->
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; font-src 'self'; connect-src 'none'; frame-src 'none'; child-src 'none'">
  <title>Will Cook: AI-written maths and code, made easier to understand</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://wcook04.github.io/">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#1c1526">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="preload" href="/assets/fonts/barlow-condensed-700.woff" as="font" type="font/woff" crossorigin>
  <link rel="preload" href="/assets/fonts/barlow-400.woff" as="font" type="font/woff" crossorigin>
  <link rel="help" href="/llms.txt" type="text/plain" title="Guide for agents">
  <link rel="describedby" href="/llms.txt" type="text/plain">
  <link rel="alternate" href="/catalogue.json" type="application/json" title="Catalogue as a graph">
  <script src="{v("/assets/landing-init.js")}"></script>
  <link rel="stylesheet" href="{v("/assets/landing.css")}">
  <script src="{v("/assets/landing.js")}" defer></script>
  <script type="application/ld+json">{structured}</script>
</head>
<body>
  <a class="skip" href="#main">Skip to the projects</a>
  <header class="top">
    <div class="wrap top__in">
      <a class="brand" href="/" aria-current="page"><img src="/assets/favicon.svg" alt="" width="26" height="26"><span translate="no">Will Cook</span></a>
      <nav class="top__nav" aria-label="Main">
        <a href="#work">Projects</a>
        <a href="all.html#films">Every video</a>
        <a href="all.html">Every link</a>
        <a href="#about">About and contact</a>
      </nav>
    </div>
  </header>
  <main id="main">
    <section class="hero wrap" aria-labelledby="hero-title">
      <h1 id="hero-title">{e(principles[0])}.</h1>
      <p class="hero__second">{e(principles[1])}</p>
      <p class="hero__note">AI now writes more mathematics and code than anyone has time to read. Each project below takes some of that output and shows it at several levels: a film of about 90&nbsp;seconds, a full film, a website, a paper and the source.</p>
    </section>
    <section class="work wrap" id="work" aria-label="Projects" data-topics="{topic_attr}">
      {weave(rows, config)}
      <div class="stage" id="stage">
        {"".join(articles)}
        <div class="stage__tour" aria-hidden="true"><i></i></div>
      </div>
    </section>
    <section class="about wrap" id="about" aria-labelledby="about-title">
      <div class="about__lead">
        <h2 id="about-title">About and contact</h2>
        <p class="about__lede">{e(owner["lede"])}</p>
        <p>{e(owner["orient"])}</p>
        {invitation}
        <ul class="about__contact" role="list">{contact}</ul>
        <p><a href="all.html#about">More about me and what I have contributed</a></p>
      </div>
      {hub.render_more(registry)}
    </section>
    {hub.render_terms(glossary, terms)}
  </main>
  <footer class="foot wrap">
    <p><a href="all.html">Every project, video, paper and repository on one page</a></p>
    <p><a href="all.html#films">Earlier videos and introductions</a></p>
    <p><a href="https://github.com/wcook04/wcook04.github.io" rel="noopener">This page’s source</a></p>
  </footer>
  <div class="termcard" id="termcard" role="tooltip" hidden></div>
</body>
</html>
'''
