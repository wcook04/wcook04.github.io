"""Every link on one page (all.html), and the page for an address that has none (404.html).

all.html is the register: one row for each of the fifteen projects, in the five
groups of the full introduction, and one column for each kind of thing, in the
order of the strip of levels on a project page (Short video, Full video,
Website, Paper, Proof, Code, Study). Under it: earlier videos, contributions to
other people's projects, earlier work, contact and the glossary.

Rows come from front.json through front.resolve(), so a project page and its
row cannot drift. Addresses, video lengths, repository names, contributions and
earlier work come from sites.json. Any published resource in sites.json that no
row names is still placed (in its project's row, in the column for its type),
so nothing can drop off the page. Every id the earlier all.html had is kept:
project-*, film-*, term-*, topic-*, projects, films, introductions, terms, about.

Both pages use front.py's head, header and footer and load assets/register.css
after assets/front.css. Neither needs JavaScript.
"""
from __future__ import annotations

import re
from html import escape as e
from pathlib import Path

import front

HOME = front.HOME
GITHUB = "https://github.com/"

# The strip's order: the quickest look on the left, the most detail on the right.
COLUMNS = (("short", "Short video"), ("long", "Full video"), ("site", "Website"), ("paper", "Paper"),
           ("proof", "Proof"), ("code", "Code"), ("study", "Study"))
COLUMN_OF_KIND = {"short": "short", "long": "long", "site": "site", "paper": "paper", "proof": "proof",
                  "code": "code", "study": "study", "issue": "study"}
COLUMN_OF_TYPE = {"website": "site", "link": "site", "paper": "paper", "repository": "code"}
# A resource no project page names, and the column it belongs in when its type alone would misplace it.
COLUMN_OF_RESOURCE = {"link:zenith-held-out-study-unmerged-revision": "study", "link:zenith-study-pull-request-13": "study"}
# The earlier page grouped projects under six questions. Their ids stay, on the nearest group.
OLD_TOPICS = {"research": "maths", "proofs": "maths", "explaining": "videos", "assistants": "assistants",
              "code": "code", "testing": "checks"}
INTRO_LINE = "How the projects fit together, and where to start"


def cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def curl(text: str) -> str:
    """Typographic apostrophes in words this module prints: OpenAI's, people's."""
    return re.sub(r"(?<=\w)'(?=\w)", "’", text)


def t(text: str) -> str:
    return e(curl(text))


class Ids:
    """Hands out each HTML id once; a second request for the same id gets none."""

    def __init__(self):
        self.seen: set[str] = set()

    def attr(self, value: str) -> str:
        if value in self.seen:
            return ""
        self.seen.add(value)
        return f' id="{e(value)}"'

    def anchor(self, value: str) -> str:
        attr = self.attr(value)
        return f'<span class="anchor"{attr}></span>' if attr else ""


# ------------------------------------------------------------------ the rows

def video_item(resource: dict, place: dict, *, owner: str, sub: str = "") -> dict:
    return {"video": True, "format": resource.get("format", "short"), "seconds": place["seconds"], "href": place["href"],
            "slug": resource["slug"], "owner": owner, "sub": sub, "more": []}


def stop_item(stop: dict, resources: dict, kinds: dict) -> dict:
    """The words for one stop in its cell: what it is, then a quieter detail."""
    kind, label, detail = stop["kind"], stop["label"], stop["detail"]
    resource = resources.get(stop.get("res") or "")
    if kind == "code" and resource and resource["type"] == "repository":
        named = label if label != kinds.get("code") else ""
        note = ", ".join(x for x in (named[:1].lower() + named[1:], detail) if x)
        what, detail = resource["title"], ("" if note == "on GitHub" else note)
    elif kind == "site" and label == kinds.get("site") and detail:
        what, detail = cap(detail), ""
    else:
        what = label
    return {"video": False, "what": what, "detail": detail, "href": stop["href"], "more": []}


def build_rows(model: dict, book: front.Book, canonical: dict, kinds: dict) -> tuple[list[dict], set[str]]:
    resources = book.resources
    rows, linked = [], set()
    for entry in model["entries"]:
        cells = {key: [] for key, _ in COLUMNS}
        for stop in entry["stops"]:
            resource = resources.get(stop.get("res") or "")
            if stop["video"] and resource:
                # "all three, 4:58" keeps its "all three"; a bare length keeps nothing.
                sub = stop["detail"].replace(front.clock(book.place(stop["res"])["seconds"]), "").strip(" ,")
                item = video_item(resource, book.place(stop["res"]), owner=entry["name"], sub=sub)
            else:
                item = stop_item(stop, resources, kinds)
            cells[COLUMN_OF_KIND.get(stop["kind"], "site")].append(item)
            linked.add(stop["href"])
            for extra in stop["more"]:
                linked.add(extra["href"])
                other = resources.get(extra.get("res") or "")
                if other and other["type"] == "video":
                    cells["long" if other.get("format") == "long" else "short"].append(
                        video_item(other, book.place(extra["res"]), owner=entry["name"], sub=stop["label"]))
                else:
                    label = extra["label"]
                    if other and other["type"] == "repository":
                        label = other["title"] if label == kinds.get("code") else label
                    item["more"].append({"what": label, "href": extra["href"]})
        rows.append({"entry": entry, "cells": cells})

    # Anything published in sites.json that belongs to a project and that no stop names.
    project_of = {}
    for entry in model["entries"]:
        for alias in [entry["slug"], *entry.get("aliases", [])]:
            project_of["project:" + alias] = entry["slug"]
    by_slug = {row["entry"]["slug"]: row for row in rows}
    homes = {}
    for rel in canonical["relationships"]:
        if rel["type"] == "resource_for" and rel["to"] in project_of:
            homes.setdefault(rel["from"], project_of[rel["to"]])
    for resource in canonical["resources"]:
        rid = resource["id"]
        if rid == "home" or rid not in homes or is_earlier(resource, canonical):
            continue
        place = book.place(rid)
        if place["href"] in linked:
            continue
        row = by_slug[homes[rid]]
        if resource["type"] == "video":
            column = "long" if resource.get("format") == "long" else "short"
            row["cells"][column].append(video_item(resource, place, owner=row["entry"]["name"]))
        else:
            column = COLUMN_OF_RESOURCE.get(rid) or COLUMN_OF_TYPE.get(resource["type"], "site")
            row["cells"][column].append({"video": False, "what": resource["title"], "detail": "", "href": place["href"], "more": []})
        linked.add(place["href"])
    return rows, linked


def is_earlier(resource: dict, canonical: dict) -> bool:
    """A video kept for the record: marked as an earlier edition, or replaced by a newer one."""
    if resource["type"] != "video":
        return False
    if resource.get("edition") == "earlier":
        return True
    return any(rel["type"] == "superseded_by" and rel["from"] == resource["id"] for rel in canonical["relationships"])


# ------------------------------------------------------------------ markup

def link(href: str, inner: str, *, cls: str = "", attrs: str = "") -> str:
    klass = f' class="{cls}"' if cls else ""
    return f'<a{klass}{attrs} href="{e(href)}"{front.off(href)}>{inner}</a>'


def item_markup(item: dict, label: str, ids: Ids) -> str:
    if item["video"]:
        said = f'{item["owner"]}, {label.lower()}' + (f', {item["sub"]}' if item["sub"] else "") + ", "
        sub = f'<span class="reg__sub">{t(item["sub"])}</span>' if item["sub"] else ""
        inner = f'<span class="vh">{t(said)}</span><span class="reg__time">{e(front.clock(item["seconds"]))}</span>'
        return f'<li>{link(item["href"], inner, cls="reg__play", attrs=ids.attr("film-" + item["slug"]))}{sub}</li>'
    detail = f' <span class="reg__detail">{t(item["detail"])}</span>' if item["detail"] else ""
    out = f'<li>{link(item["href"], f"""<span class="reg__what">{t(item["what"])}</span>{detail}""")}</li>'
    for extra in item["more"]:
        out += f'<li class="reg__extra">{link(extra["href"], t(extra["what"]))}</li>'
    return out


def cell_markup(key: str, label: str, items: list[dict], ids: Ids) -> str:
    if not items:
        return f'<td class="reg__cell reg__cell--{key} is-empty" role="cell"></td>'
    body = "".join(item_markup(item, label, ids) for item in items)
    return (f'<td class="reg__cell reg__cell--{key}" role="cell"><span class="reg__kind">{e(label)}</span>'
            f'<ul role="list">{body}</ul></td>')


def row_markup(row: dict, ids: Ids) -> str:
    entry = row["entry"]
    aliases = "".join(ids.anchor("project-" + a) for a in entry.get("aliases", []) if a != entry["slug"])
    cells = "".join(cell_markup(key, label, row["cells"][key], ids) for key, label in COLUMNS)
    return (f'<tr class="reg__row" role="row"{ids.attr("project-" + entry["slug"])}>'
            f'<th class="reg__name" scope="row" role="rowheader">{aliases}'
            f'<a href="/{e(entry["path"])}">{t(entry["name"])}</a>'
            f'<span class="reg__line">{t(entry["line"])}</span></th>{cells}</tr>')


def table_markup(model: dict, rows: list[dict], book: front.Book, canonical: dict, ids: Ids) -> str:
    span = len(COLUMNS) + 1
    head = "".join(f'<th class="reg__col reg__col--{key}" scope="col" role="columnheader">{e(label)}</th>' for key, label in COLUMNS)
    cols = '<col class="reg__w reg__w--name">' + "".join(f'<col class="reg__w reg__w--{key}">' for key, _ in COLUMNS)

    intro = model["intro"]
    resources = book.resources
    intro_cells = {key: [] for key, _ in COLUMNS}
    for key in ("short", "long"):
        res = intro[key]["res"]
        intro_cells[key].append(video_item(resources[res], book.place(res), owner="Introduction"))
    intro_row = (f'<tr class="reg__row" role="row"{ids.attr("introductions")}>'
                 f'<th class="reg__name" scope="row" role="rowheader"><a href="/">Introduction</a>'
                 f'<span class="reg__line">{t(INTRO_LINE)}</span></th>'
                 + "".join(cell_markup(key, label, intro_cells[key], ids) for key, label in COLUMNS) + "</tr>")
    groups = [f'<tbody class="reg__group reg__group--intro" role="rowgroup">{intro_row}</tbody>']

    topics = {}
    for topic, band in OLD_TOPICS.items():
        topics.setdefault(band, []).append(topic)
    for band in model["bands"]:
        body = "".join(row_markup(row, ids) for row in rows if row["entry"]["band"] == band["id"])
        old = "".join(ids.anchor("topic-" + topic) for topic in topics.get(band["id"], []))
        groups.append(
            f'<tbody class="reg__group" role="rowgroup"><tr class="reg__band" role="row">'
            f'<th colspan="{span}" scope="rowgroup" role="rowheader" aria-colspan="{span}">{old}'
            f'<h2 class="reg__bandname" id="group-{e(band["id"])}"><span class="band__n">{band["n"]}</span> {t(band["name"])}</h2>'
            f'</th></tr>{body}</tbody>')

    # A project in sites.json that no row carries would lose its old address: keep the id on the table.
    covered = {"project-" + a for row in rows for a in [row["entry"]["slug"], *row["entry"].get("aliases", [])]}
    loose = "".join(ids.anchor("project-" + p["slug"]) for p in canonical["projects"] if "project-" + p["slug"] not in covered)
    loose += "".join(ids.anchor("topic-" + topic) for topic in OLD_TOPICS)

    return (f'<p class="levels__axis reg__axis" aria-hidden="true"><span>Quickest</span><span>Most detail</span></p>'
            f'{loose}<table class="reg__table" role="table" aria-labelledby="reg-title"><colgroup>{cols}</colgroup>'
            f'<thead role="rowgroup"><tr role="row"><th class="reg__col reg__col--name" scope="col" role="columnheader">Project</th>{head}</tr></thead>'
            f'{"".join(groups)}</table>')


def earlier_markup(book: front.Book, canonical: dict, linked: set[str], ids: Ids) -> str:
    items = []
    for resource in canonical["resources"]:
        if not is_earlier(resource, canonical):
            continue
        place = book.place(resource["id"])
        linked.add(place["href"])
        length = f' <span class="reg__detail">{e(front.clock(place["seconds"]))}</span>' if place["seconds"] else ""
        items.append(f'<li>{link(place["href"], t(resource["title"]), attrs=ids.attr("film-" + resource["slug"]))}{length}</li>')
    if not items:
        return ""
    return (f'<section class="reg-sec wrap" id="earlier" aria-labelledby="earlier-title">'
            f'<h2 class="reg-sec__title" id="earlier-title">Earlier videos</h2>'
            f'<p class="reg-sec__note">Older versions, each replaced by a newer video in the table above.</p>'
            f'<ul class="reg-list reg-list--plain" role="list">{"".join(items)}</ul></section>')


def about_markup(registry: dict, linked: set[str]) -> str:
    gifts = []
    for c in registry.get("contributions", []):
        fork = GITHUB + "wcook04/" + c["repo"]
        linked.add(fork)
        name = c["upstream"].split("/")[-1]
        proof = ""
        if c.get("evidence"):
            linked.add(c["evidence"]["href"])
            proof = f'<li>{link(c["evidence"]["href"], t(c["evidence"]["label"]))}</li>'
        gifts.append(
            f'<li class="reg-item"><p class="reg-item__name">{link(GITHUB + c["upstream"], t(c["upstream"]))}</p>'
            f'<p class="reg-item__what">{t(c["what"])}</p>'
            f'<ul class="reg-item__links" role="list"><li>{link(fork, f"""My fork<span class="vh"> of {t(name)}</span>""")}</li>{proof}</ul></li>')
    older = []
    for x in registry.get("earlier", []):
        linked.add(x["href"])
        older.append(f'<li class="reg-item"><p class="reg-item__name">{link(x["href"], t(x["name"]))}</p>'
                     f'<p class="reg-item__what">{t(x["note"])}</p></li>')
    contact = "".join(f'<li><a href="{e(c["href"])}" rel="noopener">{t(c["label"])}</a></li>' for c in registry["owner"]["contact"])
    parts = []
    if gifts:
        parts.append(f'<h2 class="reg-sec__title" id="about-title">Contributions to other people’s projects</h2>'
                     f'<ul class="reg-list" role="list">{"".join(gifts)}</ul>')
    if older:
        parts.append(f'<h2 class="reg-sec__title reg-sec__title--next">Earlier work</h2>'
                     f'<ul class="reg-list" role="list">{"".join(older)}</ul>')
    parts.append(f'<h2 class="reg-sec__title reg-sec__title--next">Contact</h2>'
                 f'<ul class="about__contact" role="list">{contact}</ul>')
    return f'<section class="reg-sec wrap" id="about" aria-labelledby="about-title">{"".join(parts)}</section>'


def terms_markup(glossary: dict, ids: Ids) -> str:
    terms = sorted(glossary.get("terms", []), key=lambda x: x["term"].lower())
    if not terms:
        return ""
    items = "".join(
        f'<div class="reg-term"{ids.attr("term-" + x["id"])}><dt>{t(x["term"])}</dt>'
        f'<dd><p class="reg-term__short">{t(x["preview"])}</p><p class="reg-term__more">{t(x["detail"])}</p></dd></div>'
        for x in terms)
    return (f'<section class="reg-sec wrap" id="terms" aria-labelledby="terms-title">'
            f'<h2 class="reg-sec__title" id="terms-title">Glossary</h2>'
            f'<p class="reg-sec__note">{len(terms)} terms used on these pages and in the videos.</p>'
            f'<dl class="reg-terms">{items}</dl></section>')


def with_sheet(head: str, hub) -> str:
    """front.py's head, with this module's stylesheet after front.css."""
    sheet = f'  <link rel="stylesheet" href="{hub.versioned("/assets/register.css")}">\n'
    if "</head>" not in head:
        raise ValueError("front.head() no longer ends with </head>")
    return head.replace("</head>", sheet + "</head>")


def header() -> str:
    """front.py's header, with Every link marked as this page."""
    top = front.header(home=False)
    return top.replace('<a href="/all.html">', '<a href="/all.html" aria-current="page">')


# ------------------------------------------------------------------ pages

def render(registry: dict, glossary: dict, root: Path, hub) -> str:
    """all.html. `registry` is build_hub.load_registry()'s view; `hub` supplies versioned()."""
    canonical = registry["_canonical_v3"]
    data = front.load(root)
    book = front.Book(canonical, root)
    model = front.resolve(data, book)
    rows, linked = build_rows(model, book, canonical, data["kinds"])
    ids = Ids()
    ids.seen.update({"main", "map", "projects", "films", "reg-title", "about", "terms", "earlier",
                     "about-title", "terms-title", "earlier-title"})
    table = table_markup(model, rows, book, canonical, ids)
    linked.update(model["intro"][key]["href"] for key in ("short", "long"))
    earlier = earlier_markup(book, canonical, linked, ids)
    about = about_markup(registry, linked)
    terms = terms_markup(glossary, ids)

    # Nothing published may be missing from this page.
    missing = []
    for resource in canonical["resources"]:
        if resource["id"] == "home":
            continue
        pubs = [p for p in resource.get("publications", []) if p.get("state") == "published" and p.get("url")]
        if pubs and next((p for p in pubs if p.get("preferred")), pubs[0])["url"] not in linked:
            missing.append(resource["id"])
    if missing:
        raise ValueError("all.html: no place for " + ", ".join(missing))

    jump = "".join(f'<a class="quiet" href="#{target}">{label}</a>' for target, label in
                   ((("earlier", "Earlier videos"),) if earlier else ()) + (("about", "Contributions"), ("terms", "Glossary")))
    head = with_sheet(front.head(
        hub, title="Every link: videos, websites, papers, proofs and code | Will Cook",
        description="Every video, website, paper, proof and repository from Will Cook’s fifteen projects on one page, with a glossary.",
        canonical=HOME + "all.html", picture=None), hub)
    return f'''{head}
<body class="register">
  {header()}
  <main id="main">
    <section class="reg wrap" id="map" aria-labelledby="reg-title">
      <span class="anchor" id="projects"></span><span class="anchor" id="films"></span>
      <div class="reg__head">
        <h1 class="reg__title" id="reg-title">Every link</h1>
        <p class="reg__note">Every video, website, paper, proof and repository, project by project, from the quickest look to the most detail.</p>
        <nav class="reg__jump" aria-label="Further down this page">{jump}</nav>
      </div>
      {table}
    </section>
    {earlier}
    {about}
    {terms}
  </main>
  {front.footer()}
</body>
</html>
'''


def render_404(registry: dict, root: Path, hub) -> str:
    """404.html: one sentence, the map of fifteen, the way home. Old /plectis/ addresses still forward."""
    canonical = registry["_canonical_v3"]
    model = front.resolve(front.load(root), front.Book(canonical, root))
    head = with_sheet(front.head(hub, title="Page not found | Will Cook", description="This address has no page.",
                                 canonical=HOME, picture=None), hub)
    # This page answers for any address: no canonical address, no social card, and search engines skip it.
    swaps = (
        (r'<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, follow">'),
        (r'\n\s*<link rel="canonical" href="[^"]*">', ""),
        (r'\n\s*<meta property="og:url" content="[^"]*">', ""),
    )
    for pattern, new in swaps:
        head, count = re.subn(pattern, new, head)
        if count != 1:
            raise ValueError("404.html: front.head() changed; could not rewrite " + pattern)
    head = head.replace("</head>", f'  <script src="{hub.versioned("/assets/redirect.js")}"></script>\n</head>')
    moved = HOME + "practical-formal-verification/"
    return f'''{head}
<body class="missing">
  {front.header(home=False)}
  <main id="main">
    <section class="lost wrap" aria-labelledby="lost-title">
      <h1 class="lost__say" id="lost-title">This address has no page.</h1>
      <p class="lost__ways"><a class="lost__home" href="/">Go to the home page</a><a class="quiet" href="/all.html">Every link on one page</a></p>
      <p class="lost__note">Addresses that start with /plectis/ now live at <a href="{e(moved)}">/practical-formal-verification/</a> and forward there by themselves.</p>
    </section>
    {front.project_map(model, current=None, title="The projects", note="")}
  </main>
  {front.footer()}
</body>
</html>
'''
