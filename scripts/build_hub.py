#!/usr/bin/env python3
"""Build the home page of wcook04.github.io from sites.json.

The home page maps every website, film and repository: one row per project,
its videos on the left, its website or tool in the middle and its code on
GitHub on the right. It is static HTML: no script is needed to read it or to
follow any link (assets/hub-map.js only draws the lines between the columns),
and nothing is loaded from another host. Run
with no arguments to write the pages, or with --check to fail when the
committed pages differ from what sites.json now produces.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = "https://wcook04.github.io/"
GITHUB = "https://github.com/wcook04/"
YOUTUBE = re.compile(r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$")
OLD_PLECTIS = "/plectis/"
NEW_PLECTIS = "/practical-formal-verification/"

e = html.escape


# ---------------------------------------------------------------- registry

def load_registry(root: Path = ROOT) -> dict:
    registry = json.loads((root / "sites.json").read_text(encoding="utf-8"))
    problems = validate_registry(registry, root)
    if problems:
        raise SystemExit("sites.json:\n  " + "\n  ".join(problems))
    return registry


def validate_registry(registry: dict, root: Path = ROOT, exists=None) -> list[str]:
    """Everything the pages rely on, said once, so a bad edit fails here.

    ``exists`` answers whether a repository path is present; the default reads
    the working tree, and the repository check passes one for staged files.
    """
    if exists is None:
        exists = lambda rel: (root / rel).is_file()  # noqa: E731
    problems: list[str] = []
    films = {film["id"]: film for film in registry["films"]}
    if len(films) != len(registry["films"]):
        problems.append("film ids repeat")
    sites = {site["id"]: site for site in registry["sites"]}
    if len(sites) != len(registry["sites"]):
        problems.append("site ids repeat")
    for film in registry["films"]:
        link, still, seconds = film.get("youtube"), film.get("still"), film.get("duration_seconds")
        if link is None:
            if still or seconds:
                problems.append(f"{film['id']}: a film in preparation has no still or running time")
            continue
        if not YOUTUBE.match(link):
            problems.append(f"{film['id']}: youtube must be https://www.youtube.com/watch?v=<id>")
        if not isinstance(seconds, int) or seconds <= 0:
            problems.append(f"{film['id']}: a released film needs its running time in seconds")
        for width in (640, 1280):
            if not still or not exists(f"{still}-{width}.webp"):
                problems.append(f"{film['id']}: missing {still}-{width}.webp")
    placed: list[str] = []
    repos = {repo["id"]: repo for repo in registry.get("repos", [])}
    if len(repos) != len(registry.get("repos", [])):
        problems.append("repository ids repeat")
    for repo in registry.get("repos", []):
        if not repo.get("name") or not repo.get("description"):
            problems.append(f"{repo['id']}: a repository needs its name and a description")
        if repo.get("href") != GITHUB + repo["id"]:
            problems.append(f"{repo['id']}: href must be {GITHUB}{repo['id']}")
    referenced: list[str] = []
    for owner in registry["sites"] + registry["projects"]:
        for film_id in owner.get("films", []):
            if film_id not in films:
                problems.append(f"{owner['id']}: unknown film {film_id}")
            placed.append(film_id)
        for repo_id in owner.get("repos", []):
            if not isinstance(repo_id, str) or repo_id not in repos:
                problems.append(f"{owner['id']}: unknown repository {repo_id}")
            referenced.append(repo_id)
    unplaced = set(repos) - set(referenced)
    if unplaced:
        problems.append("repositories on no website or tool: " + ", ".join(sorted(unplaced)))
    for site in registry["sites"]:
        hrefs = [r["href"] for r in site.get("routes", [])]
        if len(hrefs) != len(set(hrefs)) or any(not h.startswith(HOME) or not r.get("label") for h, r in zip(hrefs, site.get("routes", []))):
            problems.append(f"{site['id']}: each route needs a label and an address on {HOME}, once")
        if not site["url"].startswith(HOME):
            problems.append(f"{site['id']}: websites live under {HOME}")
        for scheme in ("light", "dark"):
            for width in (720, 1440):
                capture = f"{site['capture']}-{scheme}-{width}.webp"
                if not exists(capture):
                    problems.append(f"{site['id']}: missing {capture}")
    grouped: list[str] = []
    for group in registry["film_groups"]:
        if "site" in group:
            if group["site"] not in sites:
                problems.append(f"film group names unknown site {group['site']}")
            else:
                grouped += sites[group["site"]]["films"]
        else:
            grouped += group["films"]
    missing = set(films) - set(grouped)
    if missing:
        problems.append("films in no group: " + ", ".join(sorted(missing)))
    return problems


NUMBER_WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"]


def count_words(n: int, singular: str, plural: str, *, capital: bool = False) -> str:
    """Counts under thirteen in words, as the sites' prose has them ("Nine films")."""
    word = NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)
    text = f"{word} {singular if n == 1 else plural}"
    return text[0].upper() + text[1:] if capital else text


def read_asset(rel: str) -> bytes:
    return (ROOT / rel).read_bytes()


# The repository check swaps this for a reader over the files it is checking
# (the staged files with --index), so hashes come from what is committed.
ASSET_READER = read_asset


def versioned(path: str) -> str:
    """A same-origin asset with its content's hash, so a new build is never paired
    with a stylesheet or script a browser kept from the last one."""
    data = ASSET_READER(path.lstrip("/"))
    return f"{path}?v={hashlib.sha256(data).hexdigest()[:12]}"


def clock(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def spoken(seconds: int) -> str:
    minutes, rest = divmod(seconds, 60)
    parts = [f"{minutes} minute{'s' if minutes != 1 else ''}"] if minutes else []
    if rest:
        parts.append(f"{rest} second{'s' if rest != 1 else ''}")
    return " ".join(parts)


def repos_of(registry: dict, owner: dict) -> list[dict]:
    """The repositories a website or tool names, in its own order."""
    repos = {repo["id"]: repo for repo in registry["repos"]}
    return [repos[repo_id] for repo_id in owner.get("repos", [])]


def film_groups(registry: dict) -> list[dict]:
    """Each group of the Videos band: its title, its site (if any) and its films."""
    films = {film["id"]: film for film in registry["films"]}
    sites = {site["id"]: site for site in registry["sites"]}
    groups = []
    for group in registry["film_groups"]:
        if "site" in group:
            site = sites[group["site"]]
            groups.append({"id": site["id"], "title": site["name"], "site": site,
                           "films": [films[f] for f in site["films"]]})
        else:
            groups.append({"id": group["id"], "title": group["title"], "site": None,
                           "films": [films[f] for f in group["films"]]})
    return groups


# ---------------------------------------------------------------- markup

def still_img(still: str, *, sizes: str, loading: str = "lazy") -> str:
    return (f'<img src="{e(still)}-640.webp" srcset="{e(still)}-640.webp 640w, {e(still)}-1280.webp 1280w" '
            f'sizes="{e(sizes)}" alt="" width="1280" height="720" loading="{loading}" decoding="async">')


def film_slot(film: dict, *, series: str, size: str = "", with_text: bool = True,
              sizes: str = "(min-width: 1180px) 360px, (min-width: 720px) 45vw, 100vw",
              pending_meta: str = "Video in preparation") -> str:
    """The family's film slot (docs/family.md): a still that opens YouTube, or a held frame."""
    classes = "film-slot" + (f" film-slot--{size}" if size else "")
    title = e(film["title"])
    text = f'<p class="film-slot__text">{e(film["description"])}</p>' if with_text else ""
    if film.get("youtube"):
        link = e(film["youtube"])
        seconds = film["duration_seconds"]
        return (f'<figure class="{classes}">'
                f'<a class="film-slot__frame" href="{link}" target="_blank" rel="noopener noreferrer" aria-hidden="true" tabindex="-1">'
                f'{still_img(film["still"], sizes=sizes)}'
                f'<span class="film-slot__play"></span><span class="film-slot__time">{clock(seconds)}</span></a>'
                f'<figcaption class="film-slot__caption">'
                f'<p class="film-slot__title"><a href="{link}" target="_blank" rel="noopener noreferrer">{title}'
                f'<span class="sr-only">, video on YouTube, {spoken(seconds)}</span></a></p>'
                f'{text}</figcaption></figure>')
    return (f'<figure class="{classes} film-slot--pending">'
            f'<div class="film-slot__frame film-slot__frame--pending" aria-hidden="true">'
            f'<span class="film-slot__series">{e(series)}</span>'
            f'<span class="film-slot__name">{e(film["short"])}</span>'
            f'<span class="film-slot__status">In preparation</span></div>'
            f'<figcaption class="film-slot__caption">'
            f'<p class="film-slot__title">{title}</p>'
            f'<p class="film-slot__meta">{e(pending_meta)}</p>'
            f'{text}</figcaption></figure>')


def capture_img(site: dict, scheme: str, *, sizes: str) -> str:
    base = e(site["capture"])
    return (f'<img class="site-shot site-shot--{scheme}" src="{base}-{scheme}-720.webp" '
            f'srcset="{base}-{scheme}-720.webp 720w, {base}-{scheme}-1440.webp 1440w" '
            f'sizes="{e(sizes)}" alt="" width="1440" height="790" loading="lazy" decoding="async">')


# ---------------------------------------------------------------- the map
# One row per project. The middle cell names the row and comes first in the
# markup, so a screen reader and a phone read each row as a website, then its
# videos, then its code; at laptop widths the grid sets the videos to its left.

MAP_STILL_SIZES = "(min-width: 900px) 160px, 120px"
MAP_SHOT_SIZES = "(min-width: 900px) 152px, 104px"
COLUMNS = ("Videos", "Websites and tools", "Code on GitHub")


def map_films(films: list[dict], *, series: str) -> str:
    count = "one" if len(films) == 1 else "many"
    items = "".join(f'<li class="map-film">{film_slot(film, series=series, size="inline", with_text=False, sizes=MAP_STILL_SIZES, pending_meta="In preparation")}</li>'
                    for film in films)
    return (f'<div class="map-cell map-cell--videos"><p class="map-cell__label">{COLUMNS[0]}</p>'
            f'<ul class="map-films map-films--{count}" role="list">{items}</ul></div>')


def map_repo(name: str, href: str, text: str) -> str:
    return (f'<li class="map-repo"><p class="map-repo__name"><a href="{e(href)}" rel="noopener">{e(name)}'
            f'<span class="sr-only">, on GitHub</span></a></p>'
            f'<p class="map-repo__text">{e(text)}</p></li>')


def map_code(items: str) -> str:
    return (f'<div class="map-cell map-cell--code"><p class="map-cell__label">{COLUMNS[2]}</p>'
            f'{items}</div>')


def map_site(site: dict) -> str:
    """A website: a small picture of its first screen, its name and its purpose."""
    url = e(site["url"])
    return (f'<div class="map-cell map-cell--site"><div class="map-site">'
            f'<a class="map-site__shot" href="{url}" aria-hidden="true" tabindex="-1">'
            f'{capture_img(site, "light", sizes=MAP_SHOT_SIZES)}{capture_img(site, "dark", sizes=MAP_SHOT_SIZES)}</a>'
            f'<div class="map-site__body"><h3 class="map-site__name"><a href="{url}">{e(site["name"])}</a></h3>'
            f'<p class="map-site__purpose">{e(site["purpose"])}</p>{site_routes(site)}</div></div></div>')


def site_routes(site: dict) -> str:
    """Straight to a website's main places: its full-screen map, its papers, its paper's PDF."""
    links = "".join(f'<a href="{e(r["href"])}">{e(r["label"])}<span class="sr-only">, on {e(site["name"])}</span></a>'
                    for r in site.get("routes", []))
    return f'<p class="map-site__routes">{links}</p>' if links else ""


def map_tool(project: dict, repos: list[dict]) -> str:
    """A tool without a website: its name opens its code, when its code is public."""
    name = e(project["name"])
    if repos:
        name = f'<a href="{e(repos[0]["href"])}" rel="noopener">{name}<span class="sr-only">, code on GitHub</span></a>'
    return (f'<div class="map-cell map-cell--site"><div class="map-site map-site--tool">'
            f'<div class="map-site__body"><h3 class="map-site__name">{name}</h3>'
            f'<p class="map-site__purpose">{e(project["purpose"])}</p></div></div></div>')


def map_row(row_id: str, middle: str, videos: str, code: str, *, extra: str = "") -> str:
    return (f'<li class="map-row{extra}" data-row="{e(row_id)}">{middle}{videos}{code}</li>')


def render_map(registry: dict) -> str:
    films = {film["id"]: film for film in registry["films"]}
    profile = next(c["href"] for c in registry["owner"]["contact"] if c["href"].startswith("https://github.com/"))
    overview = next(g for g in registry["film_groups"] if g.get("id") == "overview")
    rows = [map_row(
        "start",
        '<div class="map-cell map-cell--site"><div class="map-site map-site--here">'
        '<div class="map-site__body"><h3 class="map-site__name">Start here</h3>'
        '<p class="map-site__purpose">Two introductions to how the projects below fit together.</p></div></div></div>',
        map_films([films[f] for f in overview["films"]], series="Will Cook"),
        map_code(f'<ul class="map-repos" role="list">{map_repo(profile.rsplit("/", 1)[1], profile, "All public repositories")}</ul>'),
        extra=" map-row--start")]
    for site in registry["sites"]:
        repos = "".join(map_repo(r["name"], r["href"], r["description"]) for r in repos_of(registry, site))
        rows.append(map_row(site["id"], map_site(site),
                            map_films([films[f] for f in site["films"]], series=site["name"]),
                            map_code(f'<ul class="map-repos" role="list">{repos}</ul>')))
    tools = registry["projects"]
    rows.append('<li class="map-rows__group"><h3 class="map-rows__group-title">Tools for working with AI agents</h3>'
                '<p class="map-rows__group-text">These have no website of their own. Their code is on GitHub.</p></li>')
    for project in tools:
        repos = repos_of(registry, project)
        if repos:
            code = f'<ul class="map-repos" role="list">{"".join(map_repo(r["name"], r["href"], r["description"]) for r in repos)}</ul>'
        else:
            code = f'<p class="map-repo map-repo--none">No public repository. {e(project.get("status") or "")}</p>'
        rows.append(map_row(project["id"], map_tool(project, repos),
                            map_films([films[f] for f in project["films"]], series=project["name"]),
                            map_code(code), extra=" map-row--tool"))
    heads = "".join(f'<p class="map-cols__head map-cols__head--{i}">{e(c)}</p>' for i, c in enumerate(COLUMNS))
    return (f'<div class="map" data-hub-map>'
            f'<div class="map-cols" aria-hidden="true">{heads}</div>'
            f'<ul class="map-rows" role="list">{"".join(rows)}</ul></div>')


def page_head(*, title: str, description: str, canonical: str | None, robots: str, map_script: bool = False) -> str:
    canonical_link = f'\n  <link rel="canonical" href="{e(canonical)}">' if canonical else ""
    map_tag = f'\n  <script src="{versioned("/assets/hub-map.js")}" defer></script>' if map_script else ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="format-detection" content="telephone=no">
  <!-- Films open on YouTube; no player is embedded and nothing loads from another host. -->
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-src 'none'; child-src 'none'">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="{robots}">{canonical_link}
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f8f0e2" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#1c1526" media="(prefers-color-scheme: dark)">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="preload" href="/assets/fonts/plectis-serif.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/plectis-sans.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="help" href="/llms.txt" type="text/plain" title="Guide for agents">
  <script src="{versioned("/assets/theme-init.js")}"></script>
  <link rel="stylesheet" href="{versioned("/assets/hub.css")}">
  <link rel="stylesheet" href="{versioned("/assets/family/family.css")}">
  <script src="{versioned("/assets/hub.js")}" defer></script>{map_tag}'''


def header(*, current: bool) -> str:
    current_attr = ' aria-current="page"' if current else ""
    return f'''<a class="skip-link" href="#main">Skip to content</a>
  <header class="hub-header">
    <div class="wrap hub-header__inner">
      <a class="hub-wordmark" href="/"{current_attr}><img class="hub-wordmark__mark" src="/assets/favicon.svg" alt="" width="26" height="26" decoding="async">Will Cook</a>
      <nav class="hub-nav" aria-label="Primary">
        <a href="/#websites">Websites</a>
        <a href="/#videos">Videos</a>
        <a href="/#contact">Contact</a>
      </nav>
    </div>
  </header>'''


def structured_data(registry: dict) -> str:
    owner = registry["owner"]
    same_as = [c["href"] for c in owner["contact"] if c["href"].startswith("https://")]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Person", "@id": HOME + "#person", "name": owner["name"], "url": HOME, "sameAs": same_as},
            {"@type": "WebSite", "@id": HOME + "#website", "url": HOME, "name": "Will Cook",
             "author": {"@id": HOME + "#person"}},
            {"@type": "ItemList", "name": "Websites by Will Cook", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": site["url"], "name": site["name"]}
                for i, site in enumerate(registry["sites"])]},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")


def render_index(registry: dict) -> str:
    owner = registry["owner"]
    films = {film["id"]: film for film in registry["films"]}
    released = [f for f in registry["films"] if f.get("youtube")]
    pending = [f for f in registry["films"] if not f.get("youtube")]
    intro = films["introduction"]

    groups_html = []
    for group in film_groups(registry):
        site = group["site"]
        series = site["name"] if site else "Will Cook"
        slots = []
        for index, film in enumerate(group["films"]):
            size = "large" if (group["id"] == "overview" and index == 0) else ""
            sizes = "(min-width: 1180px) 760px, (min-width: 720px) 90vw, 100vw" if size else \
                    "(min-width: 1180px) 360px, (min-width: 720px) 45vw, 100vw"
            item_class = "film-grid__item film-grid__item--lead" if size else "film-grid__item"
            slots.append(f'<li class="{item_class}">{film_slot(film, series=series, size=size, sizes=sizes)}</li>')
        if site:
            repos = "".join(f'<a class="film-group__repo" href="{e(r["href"])}" rel="noopener">{e(r["name"])}<span class="sr-only"> on GitHub</span></a>'
                            for r in repos_of(registry, site))
            head = (f'<div class="film-group__head"><h3 class="film-group__title" id="films-{e(group["id"])}-title">{e(group["title"])}</h3>'
                    f'<p class="film-group__links"><a class="film-group__site" href="{e(site["url"])}">Open the website</a>{repos}</p></div>')
        else:
            head = (f'<div class="film-group__head"><h3 class="film-group__title" id="films-{e(group["id"])}-title">{e(group["title"])}</h3></div>')
        # Each group fills its row: one film is a wide card, two share the
        # row, three take thirds, and the introduction leads its own row.
        grid = "film-grid--lead" if group["id"] == "overview" else f"film-grid--count-{min(len(group['films']), 3)}"
        groups_html.append(f'<section class="film-group" id="films-{e(group["id"])}" aria-labelledby="films-{e(group["id"])}-title">'
                           f'{head}<ul class="film-grid {grid}" role="list">{"".join(slots)}</ul></section>')

    contact = "".join(f'<li><a href="{e(c["href"])}"{"" if c["href"].startswith("mailto:") else " rel=\"me noopener\""}>{e(c["label"])}</a></li>'
                      for c in owner["contact"])
    count_line = (f"{count_words(len(released), 'film is', 'films are', capital=True)} on YouTube and "
                  f"{count_words(len(pending), 'is', 'are')} in preparation. Each opens on YouTube in a new tab.")
    description = ("Will Cook’s websites and videos: research on Erdős problems and the SK model with AI, "
                   "Plectis Atlas, practical formal verification and Zenith.")
    head = page_head(title="Will Cook: websites and videos", description=description, canonical=HOME,
                     robots="index, follow", map_script=True)
    return f'''{head}
  <meta property="og:title" content="Will Cook: websites and videos">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{HOME}">
  <script type="application/ld+json">{structured_data(registry)}</script>
</head>
<body class="hub">
  {header(current=True)}

  <main id="main">
    <section class="hub-intro" aria-labelledby="hub-title">
      <div class="wrap">
        <div class="hub-intro__top">
          <div class="hub-intro__copy">
            <h1 class="hub-title" id="hub-title">{e(owner["name"])}</h1>
            <p class="hub-lede">{e(owner["lede"])}</p>
            <p class="hub-orient">Each project has its own website, and every one is on the map below with its videos and its code. New here? Start with the introduction, which explains how they fit together.</p>
          </div>
          <div class="hub-intro__film">{film_slot(intro, series="Will Cook", size="inline", with_text=False, sizes="(min-width: 1024px) 240px, 100vw")}</div>
        </div>
      </div>
    </section>

    <section class="hub-map" id="websites" aria-labelledby="map-title">
      <div class="wrap">
        <div class="hub-map__head">
          <h2 class="hub-section-title" id="map-title">Websites, videos and code</h2>
          <p class="hub-map__lede"><span class="hub-map__wide">Each line joins a video to the website it explains, and a website to its code on GitHub. Point at anything to see what it connects to.</span><span class="hub-map__narrow">Each website with its videos and its code on GitHub.</span></p>
        </div>
        {render_map(registry)}
      </div>
    </section>

    <section class="hub-films" id="videos" aria-labelledby="videos-title">
      <div class="wrap">
        <div class="hub-films__head">
          <h2 class="hub-section-title" id="videos-title">Videos</h2>
          <p class="hub-films__lede">{e(count_line)}</p>
        </div>
        {"".join(groups_html)}
      </div>
    </section>

    <section class="hub-contact" id="contact" aria-labelledby="contact-title">
      <div class="wrap hub-contact__grid">
        <h2 class="hub-section-title" id="contact-title">Get in touch</h2>
        <div class="hub-contact__text">
          {"".join(f"<p>{e(p)}</p>" for p in owner["invitation"])}
          <ul class="hub-contact__links" role="list">{contact}</ul>
        </div>
      </div>
    </section>
  </main>

  <footer class="hub-footer">
    <div class="wrap hub-footer__inner">
      <p>This page lists every website, film and repository. Each website links back here from its header.</p>
      <p><a href="https://github.com/wcook04/wcook04.github.io">Source of this page</a> <a href="/sites.json">The list as data</a></p>
    </div>
  </footer>
</body>
</html>
'''


def render_404(registry: dict) -> str:
    rows = "".join(f'<li><a href="{e(site["url"])}">{e(site["name"])}</a></li>' for site in registry["sites"])
    head = page_head(title="Page not found: Will Cook", description="This address has no page.",
                     canonical=None, robots="noindex, follow")
    return f'''{head}
  <script src="{versioned("/assets/redirect.js")}"></script>
</head>
<body class="hub hub--missing">
  {header(current=False)}

  <main id="main">
    <section class="hub-missing">
      <div class="wrap">
        <h1 class="hub-title hub-title--small">This address has no page</h1>
        <p class="hub-lede">The Plectis website moved from <code>/plectis/</code> to <a href="{HOME}practical-formal-verification/">/practical-formal-verification/</a>. Old addresses that start with <code>/plectis/</code> forward there by themselves.</p>
        <p class="hub-orient">Or go to one of the websites:</p>
        <ul class="hub-missing__list" role="list">{rows}<li><a href="/">All websites and films</a></li></ul>
      </div>
    </section>
  </main>
</body>
</html>
'''


def render_llms(registry: dict) -> str:
    lines = ["# Will Cook's websites", "",
             "This host's root page lists Will Cook's websites and films. Each website is its own project with its own source and its own agent entry where one exists.", ""]
    entries = {
        "maths": "https://wcook04.github.io/practical-formal-verification/llms.txt",
        "formal-verification": "https://wcook04.github.io/practical-formal-verification/llms.txt",
        "atlas": "https://wcook04.github.io/plectis-atlas/llms.txt",
        "zenith": "https://wcook04.github.io/plectis-zenith/llms.txt",
    }
    for site in registry["sites"]:
        entry = entries.get(site["id"])
        tail = f" Agent entry: {entry}" if entry else ""
        lines.append(f"- [{site['name']}]({site['url']}): {site['purpose']}{tail}")
    lines += ["", "Films, with their YouTube addresses and the website each belongs to, are listed in https://wcook04.github.io/sites.json.",
              "Use each site's own source links and stated limits when describing its findings.", ""]
    return "\n".join(lines)


def render_agent_guide(registry: dict) -> str:
    lines = ["# Will Cook's websites", "",
             "Start at the [home page](https://wcook04.github.io/) or read [sites.json](https://wcook04.github.io/sites.json), which lists every website, film and repository.", ""]
    for site in registry["sites"]:
        repos = ", ".join(f"[{r['name']}]({r['href']})" for r in repos_of(registry, site))
        lines.append(f"- [{site['name']}]({site['url']}). Source: {repos}.")
    lines += ["", "Use each site's own source links and stated limits when describing its findings.", ""]
    return "\n".join(lines)


def render_sitemap() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{HOME}sitemap-home.xml</loc>
  </sitemap>
  <sitemap>
    <loc>{HOME}practical-formal-verification/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>{HOME}plectis-atlas/sitemap.xml</loc>
  </sitemap>
</sitemapindex>
'''


def render_sitemap_home(registry: dict) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{HOME}</loc>
    <lastmod>{registry["updated"]}</lastmod>
  </url>
</urlset>
'''


def outputs(registry: dict) -> dict[str, str]:
    return {
        "index.html": render_index(registry),
        "404.html": render_404(registry),
        "llms.txt": render_llms(registry),
        "agent-guide.md": render_agent_guide(registry),
        "sitemap.xml": render_sitemap(),
        "sitemap-home.xml": render_sitemap_home(registry),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed pages are out of date")
    args = parser.parse_args(argv)
    registry = load_registry()
    stale = []
    for name, text in outputs(registry).items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            path.write_text(text, encoding="utf-8")
    if stale:
        print("out of date (run python3 scripts/build_hub.py): " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
