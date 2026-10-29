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
    indexed = [item for group in registry.get("index_groups", []) for item in group["items"]]
    owners = [owner["id"] for owner in registry["sites"] + registry["projects"]]
    if sorted(indexed) != sorted(owners):
        problems.append("index_groups must list every website and tool once")
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
              pending_meta: str = "Video in preparation", meta: str = "", loading: str = "lazy") -> str:
    """The family's film slot (docs/family.md): a still that opens YouTube, or a held frame."""
    classes = "film-slot" + (f" film-slot--{size}" if size else "")
    title = e(film["title"])
    text = f'<p class="film-slot__text">{e(film["description"])}</p>' if with_text else ""
    if film.get("youtube"):
        link = e(film["youtube"])
        seconds = film["duration_seconds"]
        return (f'<figure class="{classes}">'
                f'<a class="film-slot__frame" href="{link}" target="_blank" rel="noopener noreferrer" aria-hidden="true" tabindex="-1">'
                f'{still_img(film["still"], sizes=sizes, loading=loading)}'
                f'<span class="film-slot__play"></span><span class="film-slot__time">{clock(seconds)}</span></a>'
                f'<figcaption class="film-slot__caption">'
                f'<p class="film-slot__title"><a href="{link}" target="_blank" rel="noopener noreferrer">{title}'
                f'<span class="sr-only">, video on YouTube, {spoken(seconds)}</span></a></p>'
                f'{f"<p class=\"film-slot__meta\">{e(meta)}</p>" if meta else ""}'
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


# ---------------------------------------------------------------- the projects
# The work as a short index: one row per website or tool, in the groups that
# sites.json names. A closed row shows a picture, the name, one sentence and
# the way in (the website, or the code), with a summary of what it holds. It
# opens beneath itself into a small map of that project alone: its videos, the
# website's main places, its code on GitHub, joined by lines that
# assets/hub-map.js draws. "Show all details" opens every row, which is the
# whole map. A tool has no website, so its open row is its films and its code,
# with no middle node and no lines.
# html.scripting (set in the head) keeps rows closed from the first paint;
# without scripting every row is open and every link works. The middle cell
# comes first in the markup, so a screen reader and a phone read each open
# row as the website, then its videos, then its code.

MAP_STILL_SIZES = "(min-width: 960px) 144px, 112px"
THUMB_SIZES = "(min-width: 720px) 300px, 180px"
COLUMNS = ("Videos", "On the website", "Code on GitHub")
CHEVRON = ('<svg class="proj__chevron" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false">'
           '<path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def index_entries(registry: dict) -> list[dict]:
    """Each index group with its rows: a website or a tool, its films and its code."""
    films = {film["id"]: film for film in registry["films"]}
    owners = {item["id"]: ("site", item) for item in registry["sites"]}
    owners.update({item["id"]: ("tool", item) for item in registry["projects"]})
    groups = []
    for group in registry["index_groups"]:
        rows = []
        for item_id in group["items"]:
            kind, item = owners[item_id]
            rows.append({"kind": kind, "item": item, "films": [films[f] for f in item.get("films", [])],
                         "repos": repos_of(registry, item)})
        groups.append({"id": group["id"], "title": group["title"], "rows": rows})
    return groups


def plural(n: int, singular: str, many: str) -> str:
    return f"{n} {singular if n == 1 else many}"


def holds(films: list[dict], repos: list[dict]) -> list[str]:
    """What a closed row holds, in the order its open map shows it."""
    released = sum(1 for film in films if film.get("youtube"))
    pending = len(films) - released
    parts = []
    if released:
        parts.append(plural(released, "video", "videos"))
    if pending:
        parts.append(plural(pending, "video", "videos") + " in preparation")
    if repos:
        parts.append(plural(len(repos), "repository", "repositories"))
    elif films:
        parts.append("code not public")
    return parts


def film_words(film: dict) -> str:
    """A film as words: its title (the link, when it is out), when or how long, what it shows."""
    title = e(film["title"])
    if film.get("youtube"):
        seconds = film["duration_seconds"]
        head = (f'<p class="film-words__title"><a href="{e(film["youtube"])}" target="_blank" rel="noopener noreferrer">{title}'
                f'<span class="sr-only">, video on YouTube, {spoken(seconds)}</span></a></p>'
                f'<p class="film-words__meta">Video, {clock(seconds)}</p>')
    else:
        head = (f'<p class="film-words__title">{title}</p>'
                f'<p class="film-words__meta film-words__meta--pending">In preparation</p>')
    return f'<div class="film-words">{head}<p class="film-words__text">{e(film["description"])}</p></div>'


def map_films(films: list[dict], *, series: str, pictures: bool = True) -> str:
    def one(film: dict) -> str:
        if pictures and film.get("youtube"):
            return film_slot(film, series=series, size="inline", sizes=MAP_STILL_SIZES)
        return film_words(film)
    items = "".join(f'<li class="map-film">{one(film)}</li>' for film in films)
    return (f'<div class="map-cell map-cell--videos"><p class="map-cell__label">{COLUMNS[0]}</p>'
            f'<ul class="map-films" role="list">{items}</ul></div>')


def map_repo(name: str, href: str, text: str) -> str:
    return (f'<li class="map-repo"><p class="map-repo__name"><a href="{e(href)}" rel="noopener">{e(name)}'
            f'<span class="sr-only">, on GitHub</span></a></p>'
            f'<p class="map-repo__text">{e(text)}</p></li>')


def map_code(repos: list[dict], note: str = "") -> str:
    if repos:
        body = f'<ul class="map-repos" role="list">{"".join(map_repo(r["name"], r["href"], r["description"]) for r in repos)}</ul>'
    else:
        return (f'<div class="map-cell map-cell--code"><p class="map-cell__label">Code</p>'
                f'<p class="map-repo map-repo--none">No public repository. {e(note)}</p></div>')
    return f'<div class="map-cell map-cell--code"><p class="map-cell__label">{COLUMNS[2]}</p>{body}</div>'


def map_middle(row: dict) -> str:
    """A website's main places, the node its videos and code join. A tool has
    no website, so it has no middle: its open line is its films and its code."""
    item = row["item"]
    if row["kind"] != "site":
        return ""
    links = [{"label": item.get("front_label", "Front page"), "href": item["url"]}] + item.get("routes", [])
    routes = "".join(f'<li><a href="{e(r["href"])}">{e(r["label"])}<span class="sr-only">, on {e(item["name"])}</span></a></li>'
                     for r in links)
    note = f'<p class="map-node__note">{e(item["status"])}</p>' if item.get("status") else ""
    body = f'<p class="map-node__label">{COLUMNS[1]}</p><ul class="map-node__routes" role="list">{routes}</ul>{note}'
    return f'<div class="map-cell map-cell--site"><div class="map-site map-node">{body}</div></div>'


def row_thumb(row: dict) -> str:
    """A website shows its first screen; a tool shows its film's still."""
    item = row["item"]
    if row["kind"] == "site":
        href, _ = row_way_in(row)
        focus = " proj__thumb--map" if item.get("thumb_focus") == "map" else ""
        return (f'<a class="proj__thumb{focus}" href="{e(href)}"{link_attrs(href)} aria-hidden="true" tabindex="-1">'
                f'{capture_img(item, "light", sizes=THUMB_SIZES)}{capture_img(item, "dark", sizes=THUMB_SIZES)}</a>')
    film = next((f for f in row["films"] if f.get("youtube")), None)
    if not film:
        return '<span class="proj__thumb proj__thumb--empty" aria-hidden="true"></span>'
    return (f'<a class="proj__thumb proj__thumb--film film-slot__frame" href="{e(film["youtube"])}" target="_blank" '
            f'rel="noopener noreferrer" aria-hidden="true" tabindex="-1">{still_img(film["still"], sizes=THUMB_SIZES)}'
            f'<span class="film-slot__play"></span><span class="film-slot__time">{clock(film["duration_seconds"])}</span></a>')


def row_way_in(row: dict) -> tuple[str, str]:
    """The row's main link: the website, else the code, else the film. (href, label)"""
    item = row["item"]
    if row["kind"] == "site" and item.get("way_in") != "code":
        return item["url"], "Open the website"
    if row["repos"]:
        return row["repos"][0]["href"], "Code on GitHub"
    film = next(f for f in row["films"] if f.get("youtube"))
    return film["youtube"], "Watch the video"


def link_attrs(href: str) -> str:
    if "youtube.com/watch" in href:
        return ' target="_blank" rel="noopener noreferrer"'
    return ' rel="noopener"' if href.startswith("https://github.com/") else ""


def row_summary(row: dict) -> str:
    """The toggle: what it does (Show details, Hide details once open), then what
    the details hold, in words a step quieter."""
    return (f'<span class="proj__act"><span><span class="proj__verb">Show</span> details</span>{CHEVRON}</span>'
            f'<span class="proj__holds"><span class="sr-only">: </span>{e(", ".join(holds(row["films"], row["repos"])))}</span>')


def project_row(row: dict) -> str:
    item = row["item"]
    pid = e(item["id"])
    href, label = row_way_in(row)
    attrs = link_attrs(href)
    name = f'<a href="{e(href)}"{attrs}>{e(item["name"])}</a>'
    way_in = f'<a class="proj__go" href="{e(href)}"{attrs}>{e(label)}<span class="sr-only">: {e(item["name"])}</span></a>'
    series = item["name"]
    # A tool's line already shows its film's still, so its open line gives the film as words.
    films = map_films(row["films"], series=series, pictures=row["kind"] == "site")
    more = (f'<div class="proj__more" id="more-{pid}">'
            f'<div class="map-row map-row--{row["kind"]}" data-row="{pid}">{map_middle(row)}{films}'
            f'{map_code(row["repos"], item.get("status") or "")}</div></div>')
    return (f'<li class="proj proj--{row["kind"]}" id="{pid}">'
            f'<div class="proj__head">{row_thumb(row)}'
            f'<div class="proj__main"><h4 class="proj__name">{name}</h4>'
            f'<p class="proj__purpose">{e(item["purpose"])}</p><p class="proj__ways">{way_in}</p></div>'
            f'<button class="proj__toggle" type="button" aria-expanded="false" aria-controls="more-{pid}">'
            f'<span class="sr-only">{e(item["name"])}: </span>{row_summary(row)}</button>'
            f'</div>{more}</li>')


def render_projects(registry: dict) -> str:
    groups = "".join(
        f'<div class="proj-group" aria-labelledby="group-{e(g["id"])}">'
        f'<h3 class="proj-group__title" id="group-{e(g["id"])}">{e(g["title"])}</h3>'
        f'<ul class="proj-list" role="list">{"".join(project_row(r) for r in g["rows"])}</ul></div>'
        for g in index_entries(registry))
    return f'<div class="map" data-hub-map>{groups}</div>'


def video_owner_names(registry: dict) -> dict[str, str]:
    """Which project each film belongs to, as a short name for the video wall."""
    names = {}
    for group in registry["film_groups"]:
        if "site" in group:
            continue
        for film_id in group["films"]:
            names[film_id] = "Introduction" if group["id"] == "overview" else ""
    for owner in registry["sites"] + registry["projects"]:
        for film_id in owner.get("films", []):
            names[film_id] = owner["name"]
    return names


def render_videos(registry: dict) -> str:
    """Every released film as one wall of stills, then the films still being made, as text."""
    names = video_owner_names(registry)
    order = [film for group in film_groups(registry) for film in group["films"]]
    released = [f for f in order if f.get("youtube")]
    pending = [f for f in order if not f.get("youtube")]
    cards = "".join(
        f'<li class="vid">{film_slot(film, series=names[film["id"]], size="small", with_text=False, meta=names[film["id"]], sizes="(min-width: 1180px) 380px, (min-width: 820px) 31vw, (min-width: 520px) 48vw, 100vw")}</li>'
        for film in released)
    waiting = "".join(f'<li><span class="vid-pending__name">{e(film["title"])}</span>'
                      f'<span class="vid-pending__for">{e(names[film["id"]])}</span></li>' for film in pending)
    later = (f'<div class="vid-pending"><h3 class="vid-pending__title">In preparation</h3>'
             f'<ul class="vid-pending__list" role="list">{waiting}</ul></div>') if pending else ""
    return f'<ul class="vid-wall" role="list">{cards}</ul>{later}'


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
        <a href="/#projects">Projects</a>
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

    contact = "".join(
        f'<li><a class="{"hub-contact__primary" if c["href"].startswith("mailto:") else ""}" href="{e(c["href"])}"'
        f'{"" if c["href"].startswith("mailto:") else " rel=\"me noopener\""}>{e(c["label"])}</a></li>'
        for c in owner["contact"]).replace(' class=""', "")
    count_line = (f"{count_words(len(released), 'film is', 'films are', capital=True)} on YouTube and "
                  f"{count_words(len(pending), 'is', 'are')} in preparation. Each opens on YouTube in a new tab.")
    rows = sum(len(g["items"]) for g in registry["index_groups"])
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
      <div class="wrap hub-intro__top">
        <div class="hub-intro__copy">
          <h1 class="hub-title" id="hub-title">{e(owner["name"])}</h1>
          <p class="hub-lede">{e(owner["lede"])}</p>
          <p class="hub-orient">Each project has its own website or code, and its videos. New here? Start with the introduction, which explains how they fit together.</p>
          <p class="hub-intro__next"><a href="#projects">See the {count_words(rows, "project", "projects")}</a></p>
        </div>
        <div class="hub-intro__film">{film_slot(intro, series="Will Cook", size="large", with_text=False, sizes="(min-width: 1024px) 600px, 100vw", loading="eager")}</div>
      </div>
    </section>

    <section class="hub-projects" id="projects" aria-labelledby="projects-title">
      <span id="websites" class="hub-alias"></span>
      <div class="wrap">
        <div class="hub-projects__head">
          <div>
            <h2 class="hub-section-title" id="projects-title">Projects</h2>
            <p class="hub-projects__lede"><span class="hub-when-script">Visit a project directly, or choose Show details to see its videos and code here.</span><span class="hub-when-plain">Each project with its videos and its code on GitHub.</span></p>
          </div>
          <button class="hub-projects__all" type="button" data-proj-all aria-expanded="false">Show all details</button>
        </div>
        {render_projects(registry)}
      </div>
    </section>

    <section class="hub-films" id="videos" aria-labelledby="videos-title">
      <div class="wrap">
        <div class="hub-films__head">
          <h2 class="hub-section-title" id="videos-title">Videos</h2>
          <p class="hub-films__lede">{e(count_line)}</p>
        </div>
        {render_videos(registry)}
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
