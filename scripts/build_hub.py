#!/usr/bin/env python3
"""Build the home page of wcook04.github.io from sites.json and glossary.json.

sites.json is the catalogue: every website, tool, film and repository, the
three areas they sit in, and how they connect (typed links and collections).
glossary.json defines the technical words the page uses. From them this writes:

  index.html     the home page: an introduction, a map of how the work
                 connects, one card per project led by its short film, every
                 film in pairs (short film, then the full version), other work
                 and contributions, and the terms;
  catalogue.json the same catalogue as a graph (nodes and typed edges) for
                 agents and other tools;
  llms.txt, agent-guide.md, the sitemaps, 404.html and the forwarding pages
                 at old /plectis/ addresses.

Everything is static HTML. No script is needed to read the page or follow a
link; assets/explore.js runs the explorer on the first screen and assets/hub.js adds the
theme switch and the glossary cards. Nothing loads from another host. Run with
no arguments to write the pages, with --check to fail when the committed pages
differ from what the data now produces, or with --preview DIR to write a copy
in which every film in preparation is drawn as if it were out (for review).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = "https://wcook04.github.io/"
GITHUB = "https://github.com/wcook04/"
YOUTUBE = re.compile(r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$")
OLD_PLECTIS = "/plectis/"
NEW_PLECTIS = "/practical-formal-verification/"
PLECTIS_PATHS = "plectis-paths.txt"
PLECTIS_TREE = "https://api.github.com/repos/wcook04/practical-formal-verification/git/trees/gh-pages?recursive=1"
PLECTIS_SKIP = ("404.html", "google")
PREVIEW = False   # --preview: films in preparation are drawn as if they were out

e = html.escape


# ---------------------------------------------------------------- registry

def load_registry(root: Path = ROOT) -> dict:
    registry = json.loads((root / "sites.json").read_text(encoding="utf-8"))
    problems = validate_registry(registry, root)
    if problems:
        raise SystemExit("sites.json:\n  " + "\n  ".join(problems))
    return registry


def load_glossary(root: Path = ROOT) -> dict:
    path = root / "glossary.json"
    if not path.is_file():
        return {"terms": []}
    return json.loads(path.read_text(encoding="utf-8"))


def owners_of(registry: dict) -> dict[str, dict]:
    """Every website and tool by id, each stamped with its kind."""
    out = {}
    for site in registry["sites"]:
        out[site["id"]] = dict(site, kind="site")
    for project in registry["projects"]:
        out[project["id"]] = dict(project, kind="tool")
    return out


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
        if film.get("format") not in ("short", "long"):
            problems.append(f"{film['id']}: format must be short or long")
        for target in film.get("leads_to", []):
            if target not in films:
                problems.append(f"{film['id']}: leads to unknown film {target}")
        if film.get("superseded_by") and film["superseded_by"] not in films:
            problems.append(f"{film['id']}: superseded by unknown film {film['superseded_by']}")
        if link is None:
            if still or seconds:
                problems.append(f"{film['id']}: a film in preparation has no still or running time")
            poster = film.get("poster")
            if poster:
                for width in (640, 1280):
                    if not exists(f"{poster}-{width}.webp"):
                        problems.append(f"{film['id']}: missing {poster}-{width}.webp")
            continue
        if not YOUTUBE.match(link):
            problems.append(f"{film['id']}: youtube must be https://www.youtube.com/watch?v=<id>")
        if not isinstance(seconds, int) or seconds <= 0:
            problems.append(f"{film['id']}: a released film needs its running time in seconds")
        for width in (640, 1280):
            if not still or not exists(f"{still}-{width}.webp"):
                problems.append(f"{film['id']}: missing {still}-{width}.webp")
    placed: list[str] = list(registry.get("intro", {}).get("films", []))
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
        if not owner.get("label"):
            problems.append(f"{owner['id']}: a website or tool needs its short label")
        thumbnail = owner.get("thumbnail")
        if thumbnail and (not thumbnail.startswith("assets/") or ".." in Path(thumbnail).parts or not exists(thumbnail)):
            problems.append(f"{owner['id']}: thumbnail must name an existing local asset")
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
        # Evidence may live at a fixed revision in this project's repository.
        route_roots = (HOME,) + tuple(GITHUB + rid + "/" for rid in site.get("repos", []) if rid in repos)
        if len(hrefs) != len(set(hrefs)) or any(not h.startswith(route_roots) or not r.get("label") for h, r in zip(hrefs, site.get("routes", []))):
            problems.append(f"{site['id']}: each route needs a label and a unique address on the home host or an attached repository")
        if not site["url"].startswith(HOME):
            problems.append(f"{site['id']}: websites live under {HOME}")
        for scheme in ("light", "dark"):
            for width in (720, 1440):
                capture = f"{site['capture']}-{scheme}-{width}.webp"
                if not exists(capture):
                    problems.append(f"{site['id']}: missing {capture}")
    owners = [owner["id"] for owner in registry["sites"] + registry["projects"]]
    indexed = [item for area in registry.get("areas", []) for item in area["items"]]
    if sorted(indexed) != sorted(owners):
        problems.append("areas must list every website and tool once")
    for link in registry.get("links", []):
        for end in (link["from"], link["to"]):
            if end not in owners:
                problems.append(f"link names unknown project {end}")
        if not link.get("label"):
            problems.append(f"link {link['from']} -> {link['to']} needs a label")
    for group in registry.get("collections", []):
        if len(group["members"]) < 2 or any(m not in owners for m in group["members"]):
            problems.append(f"collection {group['id']} needs two or more known members")
        if group.get("film") and group["film"] not in films:
            problems.append(f"collection {group['id']} names unknown film {group['film']}")
    for item in registry.get("contributions", []):
        if not item.get("repo") or not item.get("upstream") or not item.get("what"):
            problems.append("a contribution needs its fork, its upstream project and what it holds")
    for topic in registry.get("topics", []):
        for item in topic["items"]:
            if item not in owners:
                problems.append(f"topic {topic['id']} names unknown project {item}")
    in_topics = {i for t in registry.get("topics", []) for i in t["items"]}
    if registry.get("topics") and set(owners) - in_topics:
        problems.append("projects in no topic: " + ", ".join(sorted(set(owners) - in_topics)))
    missing = set(films) - set(placed)
    if missing:
        problems.append("films on no project: " + ", ".join(sorted(missing)))
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


# ---------------------------------------------------------------- films

def is_out(film: dict) -> bool:
    return bool(film.get("youtube")) or (PREVIEW and bool(film.get("poster")))


def film_href(film: dict) -> str:
    return film.get("youtube") or "#preview-not-published"


def film_seconds(film: dict) -> int | None:
    return film.get("duration_seconds") or (film.get("cut_seconds") if PREVIEW else None)


def film_stem(film: dict) -> str | None:
    return film.get("still") or film.get("poster")


def is_earlier(film: dict, films: dict) -> bool:
    """An earlier edition: said so, or replaced by a newer film that is out."""
    if film.get("edition") == "earlier":
        return True
    newer = films.get(film.get("superseded_by") or "")
    return bool(newer and is_out(newer))


def role_of(film: dict) -> str:
    return "Short film" if film["format"] == "short" else "Full video"


def picture(film: dict, *, sizes: str, loading: str = "lazy") -> str:
    stem = film_stem(film)
    if not stem:
        return f'<span class="frame__blank" aria-hidden="true">{e(film["short"])}</span>'
    return (f'<img src="{e(stem)}-640.webp" srcset="{e(stem)}-640.webp 640w, {e(stem)}-1280.webp 1280w" '
            f'sizes="{e(sizes)}" alt="" width="1280" height="720" loading="{loading}" decoding="async">')


def frame(film: dict, *, sizes: str, size: str = "", loading: str = "lazy", named: bool = False) -> str:
    """A film's picture. Out: it opens the film on YouTube. Where a title link
    beside it opens the same film, the picture is hidden from the Tab order;
    where it stands alone (named), it is the link and carries the title. In
    preparation: the provisional picture, marked as such, with no link."""
    seconds = film_seconds(film)
    cls = "frame" + (f" frame--{size}" if size else "")
    time = f'<span class="frame__time">{clock(seconds)}</span>' if seconds else ""
    if is_out(film):
        access = (f'aria-label="{e(film["title"])}, {role_of(film).lower()} on YouTube{", " + spoken(seconds) if seconds else ""}"'
                  if named else 'aria-hidden="true" tabindex="-1"')
        return (f'<a class="{cls}" href="{e(film_href(film))}" target="_blank" rel="noopener noreferrer" {access}>'
                f'{picture(film, sizes=sizes, loading=loading)}<span class="frame__play"></span>{time}</a>')
    return (f'<div class="{cls} frame--pending" aria-hidden="true">{picture(film, sizes=sizes, loading=loading)}'
            f'<span class="frame__status">In preparation</span></div>')


def film_title(film: dict, text: str | None = None, cls: str = "") -> str:
    """The film's title: the link when the film is out, plain words when it is not."""
    words = e(text or film["title"])
    cls_attr = f' class="{cls}"' if cls else ""
    if is_out(film):
        seconds = film_seconds(film)
        tail = f'<span class="sr-only">, {role_of(film).lower()} on YouTube{", " + spoken(seconds) if seconds else ""}</span>'
        return f'<a{cls_attr} href="{e(film_href(film))}" target="_blank" rel="noopener noreferrer">{words}{tail}</a>'
    return f'<span{cls_attr}>{words}</span>'


def film_meta(film: dict) -> str:
    seconds = film_seconds(film)
    if is_out(film):
        return f"{role_of(film)}, {clock(seconds)}" if seconds else role_of(film)
    return f"{role_of(film)}, in preparation"


# ---------------------------------------------------------------- glossary

class Terms:
    """Links the first use of each defined term in a block of text to its
    definition at the foot of the page (#t-<id>); hub.js turns the link into a
    card on hover or focus. Longest names win, whole words only."""

    def __init__(self, glossary: dict, protect: list[str] | None = None):
        # Project and repository names are never split by a term link: the
        # "Ontology" in "Code Ontology Bridge" is a name, not the concept.
        names_kept = sorted({p for p in (protect or []) if p}, key=len, reverse=True)
        self.protect = (re.compile("|".join(re.escape(p) for p in names_kept)) if names_kept else None)
        self.terms = glossary.get("terms", [])
        self.by_id = {t["id"]: t for t in self.terms}
        names = []
        for t in self.terms:
            for name in [t["term"]] + t.get("aliases", []):
                names.append((name, t["id"]))
        names.sort(key=lambda pair: -len(pair[0]))
        self.lookup = {name.lower(): tid for name, tid in names}
        self.pattern = (re.compile(r"(?<![\w-])(" + "|".join(re.escape(n) for n, _ in names) + r")(?![\w-])", re.IGNORECASE)
                        if names else None)
        self.used: set[str] = set()

    def link(self, text: str, *, skip: set[str] | None = None) -> str:
        if not text:
            return ""
        if not self.pattern:
            return e(text)
        seen = set(skip or ())
        kept = [(p.start(), p.end()) for p in self.protect.finditer(text)] if self.protect else []
        out, last = [], 0
        for m in self.pattern.finditer(text):
            tid = self.lookup.get(m.group(1).lower())
            if not tid or tid in seen:
                continue
            if any(a < m.end() and m.start() < b for a, b in kept):
                continue
            seen.add(tid)
            self.used.add(tid)
            out.append(e(text[last:m.start()]))
            out.append(f'<a class="term" href="#t-{e(tid)}" data-term="{e(tid)}">{e(m.group(1))}</a>')
            last = m.end()
        out.append(e(text[last:]))
        return "".join(out)


# ---------------------------------------------------------------- the explorer
# The first screen: the work as topics in plain words, woven together. A night
# stage holds the topics as knots and the threads between them (a thread means
# two topics share a project, or a project in one is a worked example, a sibling
# or a related tool of a project in the other). A paper panel on the left reads
# the same thing in three levels: every topic; one topic and its projects; one
# project with its short film and where to go next. assets/explore.js moves
# the camera between the levels and blooms a topic's projects and a project's
# film, website and code on the stage. Without the script the stage is a still
# picture, the panel shows every topic, and each topic links to its projects in
# the list below.

def topic_threads(registry: dict) -> list[dict]:
    """Threads between topics, each with the reasons that join them."""
    topics = registry.get("topics", [])
    home: dict[str, list[str]] = {}
    for t in topics:
        for item in t["items"]:
            home.setdefault(item, []).append(t["id"])
    owners = owners_of(registry)
    reasons: dict[tuple[str, str], list[str]] = {}

    def join(a: str, b: str, why: str) -> None:
        if a == b:
            return
        key = tuple(sorted((a, b)))
        if why not in reasons.setdefault(key, []):
            reasons[key].append(why)

    for item, ts in home.items():
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                join(ts[i], ts[j], f"{owners[item]['label']} is in both")
    for link in registry.get("links", []):
        for a in home.get(link["from"], []):
            for b in home.get(link["to"], []):
                join(a, b, f"{owners[link['from']]['label']} and {owners[link['to']]['label']}: {lc_first(link['label'])}")
    for group in registry.get("collections", []):
        ms = group["members"]
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                for a in home.get(ms[i], []):
                    for b in home.get(ms[j], []):
                        join(a, b, group["title"])
    return [{"a": a, "b": b, "why": why} for (a, b), why in sorted(reasons.items())]


def thread_path(p: tuple, q: tuple, bend: float = 0.18) -> str:
    """A soft arc from p to q, bowed toward the centre of the loom."""
    (x1, y1), (x2, y2) = p, q
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    cx, cy = mx * (1 - bend * 2), my * (1 - bend * 2)
    return f"M {x1:.1f} {y1:.1f} Q {cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}"


def topic_radius(n: int) -> int:
    return {1: 21, 2: 25}.get(n, 29)


def render_explorer(registry: dict, owners: dict, films: dict, terms: Terms) -> str:
    topics = registry.get("topics", [])
    tmap = {t["id"]: t for t in topics}
    threads = topic_threads(registry)
    owner = registry["owner"]
    hero = registry.get("hero", {})
    intro = [films[f] for f in registry.get("intro", {}).get("films", [])]
    short = next((f for f in intro if f["format"] == "short" and is_out(f)), None)
    full = next((f for f in intro if f["format"] == "long" and is_out(f) and not is_earlier(f, films)), None)
    main = short or full
    # The stage, drawn here so it is a complete still picture without the script.
    spokes = "".join(f'<path class="ex-spoke" d="M 0 0 L {t["at"][0]} {t["at"][1]}"/>' for t in topics)
    lines = "".join(
        f'<path class="ex-thread" data-a="{e(th["a"])}" data-b="{e(th["b"])}" d="{thread_path(tmap[th["a"]]["at"], tmap[th["b"]]["at"])}"/>'
        for th in threads)
    knots = []
    for t in topics:
        x, y = t["at"]
        r = topic_radius(len(t["items"]))
        label_y = y + r + 24
        knots.append(
            f'<g class="ex-topic ex-topic--{e(t["area"])}" data-topic="{e(t["id"])}" transform="translate({x} {y})">'
            f'<circle class="ex-topic__glow" r="{r + 14}"/><circle class="ex-topic__ring" r="{r}"/>'
            f'<circle class="ex-topic__core" r="{max(6, r - 13)}"/>'
            f'<text class="ex-topic__label" y="{r + 26}" text-anchor="middle">{e(t["label"])}</text></g>')
    knot = ('<g class="ex-knot" data-knot="1"><circle r="17"/>'
            '<path d="M -8 -10 C 8 -3 -8 3 8 10 M 8 -10 C -8 -3 8 3 -8 10"/></g>')
    stage = (f'<svg class="ex-stage" viewBox="-760 -400 1400 800" preserveAspectRatio="xMidYMid meet" aria-hidden="true" data-ex-stage>'
             f'<g class="ex-world"><g class="ex-spokes">{spokes}</g><g class="ex-threads">{lines}</g>'
             f'<g class="ex-flow"></g><g class="ex-topics">{"".join(knots)}</g><g class="ex-bloom"></g>{knot}</g></svg>')
    # The panel's three levels.
    topic_rows = "".join(
        f'<li><a class="ex-row ex-row--{e(t["area"])}" href="#t={e(t["id"])}" data-go-topic="{e(t["id"])}">'
        f'<span class="ex-row__dot" aria-hidden="true"></span><span class="ex-row__name">{e(t["label"])}</span></a></li>' for t in topics)
    actions = ""
    if main:
        seconds = film_seconds(main)
        actions = (f'<a class="btn btn--primary ex-intro" href="{e(film_href(main))}" target="_blank" rel="noopener noreferrer">'
                   f'<span class="btn__play" aria-hidden="true"></span>Watch the introduction'
                   f'{f"<span class=\"btn__time\">{clock(seconds)}</span>" if seconds else ""}<span class="sr-only">, on YouTube</span></a>')
    level0 = (f'<section class="ex-level ex-level--home" data-level="home" aria-labelledby="hub-title">'
              f'<h1 class="ex-title" id="hub-title">{e(hero.get("headline") or owner["lede"])}</h1>'
              f'<p class="ex-lede">{terms.link(hero.get("summary", ""))}</p>'
              f'<div class="ex-actions">{actions}<a class="ex-work" href="#contact">Open to work</a></div>'
              f'<h2 class="ex-hint">Choose a topic</h2>'
              f'<ul class="ex-rows" role="list">{topic_rows}</ul></section>')
    levels = [level0]
    for t in topics:
        rows = "".join(
            f'<li><a class="ex-row ex-row--project ex-row--{e(t["area"])}" href="#p={e(pid)}" data-go-project="{e(pid)}" data-in="{e(t["id"])}">'
            f'<span class="ex-row__name">{e(owners[pid]["label"])}</span>'
            f'<span class="ex-row__plain">{e(owners[pid].get("plain", ""))}</span></a></li>' for pid in t["items"])
        near = []
        for th in threads:
            if t["id"] in (th["a"], th["b"]):
                other = tmap[th["b"] if th["a"] == t["id"] else th["a"]]
                near.append(f'<li><a class="ex-chip ex-chip--{e(other["area"])}" href="#t={e(other["id"])}" data-go-topic="{e(other["id"])}" '
                            f'title="{e("; ".join(th["why"]))}">{e(other["label"])}</a></li>')
        near_html = f'<h3 class="ex-sub">Connected to</h3><ul class="ex-near" role="list">{"".join(near)}</ul>' if near else ""
        levels.append(
            f'<section class="ex-level ex-level--topic ex-level--{e(t["area"])}" data-level="topic" data-topic="{e(t["id"])}" hidden>'
            f'<nav class="ex-crumbs" aria-label="Where you are"><a href="#explore" data-go-home>All topics</a></nav>'
            f'<h2 class="ex-name">{e(t["label"])}</h2><p class="ex-question">{terms.link(t["question"])}</p>'
            f'<ul class="ex-rows" role="list">{rows}</ul>{near_html}</section>')
    for t in topics:
        for pid in t["items"]:
            if any(f'data-project="{pid}"' in lv for lv in levels):
                continue
            o = owners[pid]
            lead, full_film = lead_of(o, films)
            acts = []
            if full_film and is_out(full_film):
                acts.append(f'<a class="act act--film" href="{e(film_href(full_film))}" target="_blank" rel="noopener noreferrer">Full video '
                            f'<span class="act__time">{clock(film_seconds(full_film))}</span><span class="sr-only">: {e(full_film["title"])}, on YouTube</span></a>')
            if o["kind"] == "site":
                acts.append(f'<a class="act" href="{e(o["url"])}">Website<span class="sr-only">: {e(o["name"])}</span></a>')
            repos = repos_of(registry, o)
            if repos:
                acts.append(f'<a class="act" href="{e(repos[0]["href"])}" rel="noopener">Code<span class="sr-only">: {e(repos[0]["name"])} on GitHub</span></a>')
            acts.append(f'<a class="act act--quiet" href="#{e(pid)}">All details</a>')
            homes = [x for x in topics if pid in x["items"]]
            levels.append(
                f'<section class="ex-level ex-level--project ex-level--{e(homes[0]["area"])}" data-level="project" data-project="{e(pid)}" hidden>'
                f'<nav class="ex-crumbs" aria-label="Where you are"><a href="#explore" data-go-home>All topics</a>'
                f'<a href="#t={e(homes[0]["id"])}" data-go-topic="{e(homes[0]["id"])}">{e(homes[0]["label"])}</a></nav>'
                f'<h2 class="ex-name">{e(o["label"])}</h2><p class="ex-question">{e(o.get("plain", ""))}</p>'
                f'{frame(lead, sizes="(min-width: 1000px) 400px, 90vw", named=True)}'
                f'<p class="ex-line">{terms.link(o.get("line", ""))}</p>'
                f'<p class="card__acts">{"".join(acts)}</p></section>')
    # Data for the script: positions, threads, and what each project blooms into.
    data = {"topics": [{"id": t["id"], "label": t["label"], "area": t["area"], "at": t["at"], "items": t["items"],
                        "r": topic_radius(len(t["items"]))} for t in topics],
            "threads": [{"a": th["a"], "b": th["b"]} for th in threads],
            "projects": {}}
    for t in topics:
        for pid in t["items"]:
            o = owners[pid]
            lead, full_film = lead_of(o, films)
            sats = [{"kind": "film", "label": "Short film" if lead["format"] == "short" else "Video",
                     "time": clock(film_seconds(lead)) if film_seconds(lead) else "",
                     "href": film_href(lead) if is_out(lead) else None, "img": (film_stem(lead) or "") + "-640.webp"}]
            if full_film:
                sats.append({"kind": "full", "label": "Full video", "time": clock(film_seconds(full_film)) if film_seconds(full_film) and is_out(full_film) else "",
                             "href": film_href(full_film) if is_out(full_film) else None})
            if o["kind"] == "site":
                sats.append({"kind": "site", "label": "Website", "href": o["url"]})
            for r in repos_of(registry, o)[:2]:
                sats.append({"kind": "code", "label": r["name"], "href": r["href"]})
            data["projects"][pid] = {"label": o["label"], "area": next(x["area"] for x in topics if pid in x["items"]), "sats": sats}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (f'<section class="ex" id="explore" aria-label="Explore the work by topic">'
            f'<span id="intro" class="hub-alias"></span><span id="map" class="hub-alias"></span>'
            f'<div class="ex-stagewrap">{stage}<p class="ex-tip" aria-hidden="true">Click a topic. Esc goes back.</p></div>'
            f'<div class="ex-panel" data-ex-panel>{"".join(levels)}</div>'
            f'<script type="application/json" id="ex-data">{payload}</script></section>')


# ---------------------------------------------------------------- project cards

STILL_SIZES = "(min-width: 1180px) 430px, (min-width: 720px) 45vw, 100vw"
SMALL_SIZES = "(min-width: 720px) 168px, 40vw"


def capture_img(site: dict, scheme: str, *, sizes: str) -> str:
    base = e(site["capture"])
    return (f'<img class="site-shot site-shot--{scheme}" src="{base}-{scheme}-720.webp" '
            f'srcset="{base}-{scheme}-720.webp 720w, {base}-{scheme}-1440.webp 1440w" '
            f'sizes="{e(sizes)}" alt="" width="1440" height="810" loading="lazy" decoding="async">')


def shot(owner: dict) -> str:
    """The website's own first screen (both schemes), or a tool's picture,
    linked to the place it shows."""
    sizes = "(min-width: 1180px) 430px, 45vw"
    if owner["kind"] == "site" and owner.get("capture"):
        return (f'<a class="card__shot" href="{e(owner["url"])}" aria-hidden="true" tabindex="-1">'
                f'{capture_img(owner, "light", sizes=sizes)}{capture_img(owner, "dark", sizes=sizes)}</a>')
    if owner.get("thumbnail"):
        return (f'<span class="card__shot" aria-hidden="true"><img src="{e(owner["thumbnail"])}" alt="" loading="lazy" decoding="async"></span>')
    return ""


def lead_of(owner: dict, films: dict) -> tuple[dict, dict | None]:
    """The card's film, and the full film it leads to. A project's short film
    leads when it is out; until then its full video stands in its place."""
    own = [films[f] for f in owner.get("films", [])]
    short = next((f for f in own if f["format"] == "short"), None)
    if short is None:
        first = next((f for f in own if is_out(f)), own[0] if own else None)
        return first, None
    full = films.get((short.get("leads_to") or [None])[0] or "")
    if is_out(short) or not (full and is_out(full)):
        return short, full
    return full, None


def lc_first(text: str) -> str:
    """Lower-case a label's first letter for use mid-sentence, unless the first
    word is a name (OpenAI, Lean, Erdős)."""
    first = text.split(" ", 1)[0]
    if first[:1].isupper() and (first[1:2].isupper() or first.rstrip("’'s") in ("Lean", "Erdős", "Atlas", "OpenAI", "NVIDIA") or first.startswith(("OpenAI", "NVIDIA"))):
        return text
    return text[:1].lower() + text[1:]


def link_attrs(href: str) -> str:
    if "youtube.com/watch" in href:
        return ' target="_blank" rel="noopener noreferrer"'
    return ' rel="noopener"' if href.startswith("https://github.com/") else ""


def card(owner: dict, registry: dict, owners: dict, films: dict, terms: Terms, area: str) -> str:
    pid = owner["id"]
    lead, full = lead_of(owner, films)
    shown = {lead["id"]} | ({full["id"]} if full else set())
    rows = []
    if full:
        rows.append(f'<li class="kin kin--full"><span class="kin__kind">Full video</span>'
                    f'<span class="kin__what">{film_title(full)}<span class="kin__meta">{e(clock(film_seconds(full)) if film_seconds(full) and is_out(full) else "in preparation")}</span></span></li>')
    more = [films[f] for f in owner.get("films", []) if f not in shown and not is_earlier(films[f], films)]
    for film in more:
        label = "Short film" if film["format"] == "short" else "Also"
        meta = clock(film_seconds(film)) if is_out(film) and film_seconds(film) else "in preparation"
        rows.append(f'<li class="kin"><span class="kin__kind">{label}</span>'
                    f'<span class="kin__what">{film_title(film)}<span class="kin__meta">{e(meta)}</span></span></li>')
    if owner["kind"] == "site":
        routes = "".join(f'<a href="{e(r["href"])}">{e(r["label"])}<span class="sr-only">, on {e(owner["name"])}</span></a>'
                         for r in owner.get("routes", []))
        rows.append(f'<li class="kin kin--site"><span class="kin__kind">Website</span>'
                    f'<span class="kin__what"><a class="kin__main" href="{e(owner["url"])}">{e(owner["name"])}</a>'
                    f'{f"<span class=\"kin__routes\">{routes}</span>" if routes else ""}</span></li>')
    repos = repos_of(registry, owner)
    if repos:
        names = "".join(f'<a href="{e(r["href"])}" rel="noopener" title="{e(r["description"])}">{e(r["name"])}<span class="sr-only">, on GitHub</span></a>'
                        for r in repos)
        rows.append(f'<li class="kin kin--code"><span class="kin__kind">Code</span><span class="kin__what kin__repos">{names}</span></li>')
    elif owner.get("status"):
        rows.append(f'<li class="kin kin--code"><span class="kin__kind">Code</span><span class="kin__what kin__note">{e(owner["status"])}</span></li>')
    joins = []
    for link in registry.get("links", []):
        if pid in (link["from"], link["to"]):
            other = link["to"] if link["from"] == pid else link["from"]
            joins.append(f'<a href="#{e(other)}">{e(owners[other]["label"])}</a> <span class="kin__why">({e(lc_first(link["label"]))})</span>')
    for group in registry.get("collections", []):
        if pid in group["members"]:
            others = ", ".join(f'<a href="#{e(m)}">{e(owners[m]["label"])}</a>' for m in group["members"] if m != pid)
            joins.append(f'{others} <span class="kin__why">({e(lc_first(group["title"]))})</span>')
    if joins:
        rows.append(f'<li class="kin kin--joins"><span class="kin__kind">Connected</span><span class="kin__what">{"<br>".join(joins)}</span></li>')
    takeaway = lead.get("takeaway") or lead.get("description", "")
    summary = owner.get("summary") or owner.get("purpose", "")
    credit = f'<p class="card__credit">{e(owner["credit"])}</p>' if owner.get("credit") else ""
    # The default path: the film, the name, one line, and where to go next.
    actions = []
    if full and is_out(full):
        actions.append(f'<a class="act act--film" href="{e(film_href(full))}" target="_blank" rel="noopener noreferrer">'
                       f'Full video <span class="act__time">{clock(film_seconds(full))}</span>'
                       f'<span class="sr-only">: {e(full["title"])}, on YouTube</span></a>')
    if owner["kind"] == "site":
        actions.append(f'<a class="act" href="{e(owner["url"])}">Website<span class="sr-only">: {e(owner["name"])}</span></a>')
    if repos:
        actions.append(f'<a class="act" href="{e(repos[0]["href"])}" rel="noopener">Code<span class="sr-only">: {e(repos[0]["name"])} on GitHub</span></a>')
    return (f'<article class="card card--{e(area)}" id="{e(pid)}" aria-labelledby="{e(pid)}-name">'
            f'{frame(lead, sizes=STILL_SIZES, named=True)}'
            f'<div class="card__body">'
            f'<p class="card__subject">{e(owner.get("subject", ""))}</p>'
            f'<h4 class="card__name" id="{e(pid)}-name">{e(owner["label"])}</h4>'
            f'<p class="card__line">{terms.link(owner.get("line") or takeaway)}</p>'
            f'<p class="card__acts">{"".join(actions)}</p>'
            f'<details class="card__more"><summary>More</summary>{shot(owner)}'
            f'<p class="card__film"><span class="card__role">{e(film_meta(lead))}</span> {film_title(lead, cls="card__filmtitle")}</p>'
            f'<p class="card__takeaway">{terms.link(takeaway)}</p>'
            f'<p class="card__summary">{terms.link(summary)}</p>{credit}'
            f'<ul class="kins" role="list">{"".join(rows)}</ul></details></div></article>')


def render_areas(registry: dict, owners: dict, films: dict, terms: Terms) -> str:
    out = []
    for area in registry["areas"]:
        cards = "".join(card(owners[i], registry, owners, films, terms, area["id"]) for i in area["items"])
        n = len(area["items"])
        out.append(
            f'<section class="area area--{e(area["id"])}" id="area-{e(area["id"])}" aria-labelledby="area-{e(area["id"])}-title">'
            f'<div class="area__head"><div class="area__sticky">'
            f'<span class="area__strand" aria-hidden="true"></span>'
            f'<h3 class="area__title" id="area-{e(area["id"])}-title">{e(area["title"])}</h3>'
            f'<p class="area__blurb">{terms.link(area["blurb"])}</p>'
            f'</div></div><div class="area__cards">{cards}</div></section>')
    return "".join(out)


# ---------------------------------------------------------------- every film

def film_tile(film: dict, terms: Terms, *, lead: bool = False) -> str:
    takeaway = film.get("takeaway")
    text = ""
    return (f'<div class="tile tile--{e(film["format"])}">{frame(film, sizes=SMALL_SIZES, size="small")}'
            f'<div class="tile__words"><p class="tile__meta">{e(film_meta(film))}</p>'
            f'<p class="tile__title">{film_title(film)}</p>{text}</div></div>')


def render_library(registry: dict, owners: dict, films: dict, terms: Terms) -> str:
    """Every film: each short film beside the full video it leads to, in the
    order of the areas; three short films that share one full video share one
    row. Then the films no short film leads to, and the earlier editions."""
    order = list(registry.get("intro", {}).get("films", []))
    for area in registry["areas"]:
        for pid in area["items"]:
            order += owners[pid].get("films", [])
    seen, groups = set(), {}
    for fid in order:
        film = films[fid]
        if film["format"] != "short" or fid in seen:
            continue
        seen.add(fid)
        target = (film.get("leads_to") or [None])[0]
        groups.setdefault(target, []).append(film)
    paired = set(seen) | {t for t in groups if t}
    rows = []
    for target, shorts in groups.items():
        full = films.get(target or "")
        left = "".join(f'<li>{film_tile(s, terms, lead=True)}</li>' for s in shorts)
        right = film_tile(full, terms) if full else ""
        many = " pair--many" if len(shorts) > 1 else ""
        rows.append(f'<li class="pair{many}"><ul class="pair__shorts" role="list">{left}</ul>'
                    f'<span class="pair__join" aria-hidden="true"></span><div class="pair__full">{right}</div></li>')
    others = [films[f] for f in dict.fromkeys(order) if f not in paired and not is_earlier(films[f], films)]
    earlier = [films[f] for f in dict.fromkeys(order) if f not in paired and is_earlier(films[f], films)]
    out = [f'<ol class="pairs" role="list">{"".join(rows)}</ol>']
    if others:
        out.append('<h3 class="films__sub">More films</h3><ul class="tiles" role="list">'
                   + "".join(f"<li>{film_tile(f, terms)}</li>" for f in others) + "</ul>")
    if earlier:
        out.append('<h3 class="films__sub" id="earlier-introductions">Earlier editions</h3><ul class="tiles tiles--quiet" role="list">'
                   + "".join(f"<li>{film_tile(f, terms)}</li>" for f in earlier) + "</ul>")
    return "".join(out)


# ---------------------------------------------------------------- page

def page_head(*, title: str, description: str, canonical: str | None, robots: str, map_script: bool = False) -> str:
    canonical_link = f'\n  <link rel="canonical" href="{e(canonical)}">' if canonical else ""
    map_tag = f'\n  <script src="{versioned("/assets/explore.js")}" defer></script>' if map_script else ""
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
  <link rel="alternate" href="/catalogue.json" type="application/json" title="Catalogue as a graph">
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
        <a href="/#explore">Explore</a>
        <a href="/#projects">All projects</a>
        <a href="/#films">Films</a>
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


def render_more(registry: dict) -> str:
    contributions = "".join(
        f'<li><p class="more__name"><a href="{e(GITHUB + c["repo"])}" rel="noopener">{e(c["upstream"])}</a></p>'
        f'<p class="more__what">{e(c["what"])}'
        f'{f" <a href=\"{e(c["evidence"]["href"])}\" rel=\"noopener\">{e(c["evidence"]["label"])}</a>" if c.get("evidence") else ""}</p></li>'
        for c in registry.get("contributions", []))
    earlier = "".join(
        f'<li><p class="more__name"><a href="{e(x["href"])}" rel="noopener">{e(x["name"])}</a></p><p class="more__what">{e(x["note"])}</p></li>'
        for x in registry.get("earlier", []))
    return f'''<section class="more" id="more" aria-labelledby="more-title">
      <div class="wrap more__grid">
        <div>
          <h2 class="section-title" id="more-title">Contributions to other projects</h2>
          
          <ul class="more__list" role="list">{contributions}</ul>
        </div>
        <div>
          <h3 class="section-title section-title--small">Earlier work</h3>
          <ul class="more__list" role="list">{earlier}</ul>
        </div>
      </div>
    </section>'''


def render_terms(glossary: dict, terms: Terms) -> str:
    used = [t for t in glossary.get("terms", []) if t["id"] in terms.used]
    if not used:
        return ""
    used.sort(key=lambda t: t["term"].lower())
    items = "".join(
        f'<div class="def" id="t-{e(t["id"])}"><dt>{e(t["term"])}</dt>'
        f'<dd><p class="def__preview">{e(t["preview"])}</p><p class="def__detail">{e(t["detail"])}</p></dd></div>'
        for t in used)
    return f'''<section class="terms" id="terms" aria-labelledby="terms-title">
      <div class="wrap">
        <h2 class="section-title" id="terms-title">Terms used on this page</h2>
        
        <dl class="defs">{items}</dl>
      </div>
    </section>'''


def render_index(registry: dict, glossary: dict | None = None) -> str:
    glossary = glossary if glossary is not None else load_glossary()
    owner = registry["owner"]
    films = {film["id"]: film for film in registry["films"]}
    owners = owners_of(registry)
    protect = [n for o in owners.values() for n in [o["name"], o["label"], *o.get("aka", [])]]
    protect += [r["name"] for r in registry["repos"]] + ["Plectis Mathematics", "Lean Exposition"]
    terms = Terms(glossary, protect)
    explorer = render_explorer(registry, owners, films, terms)
    areas = render_areas(registry, owners, films, terms)
    library = render_library(registry, owners, films, terms)
    more = render_more(registry)
    glossary_html = render_terms(glossary, terms)
    out_count = sum(1 for f in films.values() if is_out(f))
    pending = len(films) - out_count
    films_lede = (f"{count_words(out_count, 'film is', 'films are', capital=True)} on YouTube"
                  + (f" and {count_words(pending, 'is', 'are')} in preparation" if pending else "")
                  + ". Each short film sits beside the full video it leads to.")
    contact = "".join(
        f'<li><a class="{"hub-contact__primary" if c["href"].startswith("mailto:") else ""}" href="{e(c["href"])}"'
        f'{"" if c["href"].startswith("mailto:") else " rel=\"me noopener\""}>{e(c["label"])}</a></li>'
        for c in owner["contact"]).replace(' class=""', "")
    legend = "".join(
        f'<li class="key key--{e(a["id"])}"><span class="key__swatch" aria-hidden="true"></span>'
        f'<a href="#area-{e(a["id"])}">{e(a["title"])}</a></li>' for a in registry["areas"])
    description = ("Will Cook’s AI-assisted mathematics and software: Erdős research, OpenAI’s results beside "
                   "their Lean proofs, tools for coding agents, and the films that explain them.")
    head = page_head(title="Will Cook: mathematics, software and films", description=description, canonical=HOME,
                     robots="index, follow", map_script=True)
    return f'''{head}
  <meta property="og:title" content="Will Cook: mathematics, software and films">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{HOME}">
  <meta property="og:image" content="{HOME}assets/sites/home-light-1440.webp">
  <meta property="og:image:width" content="1440">
  <meta property="og:image:height" content="790">
  <meta property="og:image:alt" content="Will Cook’s home page, with the introduction film and a map of how the projects connect.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{HOME}assets/sites/home-light-1440.webp">
  <script type="application/ld+json">{structured_data(registry)}</script>
</head>
<body class="hub">
  {header(current=True)}

  <main id="main">
    {explorer}

    <section class="work" id="projects" aria-labelledby="projects-title">
      <span id="websites" class="hub-alias"></span><span id="work" class="hub-alias"></span>
      <div class="wrap">
        <h2 class="section-title" id="projects-title">All projects</h2>
        {areas}
      </div>
    </section>

    <section class="films" id="films" aria-labelledby="films-title">
      <span id="videos" class="hub-alias"></span>
      <div class="wrap">
        <h2 class="section-title" id="films-title">Every film</h2>
        <p class="section-lede">{e(films_lede)}</p>
        {library}
      </div>
    </section>

    {more}

    <section class="hub-contact" id="contact" aria-labelledby="contact-title">
      <div class="wrap hub-contact__grid">
        <h2 class="section-title" id="contact-title">Get in touch</h2>
        <div class="hub-contact__text">
          {"".join(f"<p>{e(p)}</p>" for p in owner["invitation"])}
          <ul class="hub-contact__links" role="list">{contact}</ul>
        </div>
      </div>
    </section>

    {glossary_html}
  </main>

  <footer class="hub-footer">
    <div class="wrap hub-footer__inner">
      <p>This page lists every website, film and repository, and how they connect. Each website links back here from its header.</p>
      <p><a href="https://github.com/wcook04/wcook04.github.io">Source of this page</a> <a href="/catalogue.json">The catalogue as a graph</a> <a href="/sites.json">The list as data</a> <a href="/glossary.json">The terms as data</a></p>
    </div>
  </footer>
</body>
</html>
'''


# ---------------------------------------------------------------- the catalogue as a graph

def render_catalogue(registry: dict, glossary: dict) -> str:
    """Nodes (areas, projects, websites, films, repositories, contributions,
    terms) and typed edges, from the same data the page is drawn from."""
    films = {f["id"]: f for f in registry["films"]}
    owners = owners_of(registry)
    nodes, edges = [], []
    for area in registry["areas"]:
        nodes.append({"id": f"area:{area['id']}", "type": "area", "title": area["title"], "summary": area["blurb"]})
        for pid in area["items"]:
            edges.append({"from": f"project:{pid}", "to": f"area:{area['id']}", "type": "in_area"})
    for pid, owner in owners.items():
        nodes.append({"id": f"project:{pid}", "type": "project", "title": owner["label"], "name": owner["name"],
                      "subject": owner.get("subject"), "plain": owner.get("plain"), "line": owner.get("line"),
                      "tagline": owner.get("tagline"),
                      "summary": owner.get("summary") or owner.get("purpose"), "anchor": f"{HOME}#{pid}",
                      "aka": owner.get("aka", [])})
        if owner["kind"] == "site":
            nodes.append({"id": f"site:{pid}", "type": "website", "title": owner["name"], "url": owner["url"],
                          "routes": owner.get("routes", [])})
            edges.append({"from": f"site:{pid}", "to": f"project:{pid}", "type": "website_of"})
        for fid in owner.get("films", []):
            edges.append({"from": f"film:{fid}", "to": f"project:{pid}", "type": "film_of"})
        for rid in owner.get("repos", []):
            edges.append({"from": f"repo:{rid}", "to": f"project:{pid}", "type": "code_of"})
    for film in registry["films"]:
        nodes.append({"id": f"film:{film['id']}", "type": "film", "format": film["format"], "title": film["title"],
                      "takeaway": film.get("takeaway"), "url": film.get("youtube"),
                      "seconds": film.get("duration_seconds") or film.get("cut_seconds"),
                      "status": "published" if film.get("youtube") else "in_preparation",
                      "edition": "earlier" if is_earlier(film, films) else "current"})
        for target in film.get("leads_to", []):
            edges.append({"from": f"film:{film['id']}", "to": f"film:{target}", "type": "leads_to"})
        if film.get("superseded_by"):
            edges.append({"from": f"film:{film['id']}", "to": f"film:{film['superseded_by']}", "type": "superseded_by"})
    for fid in registry.get("intro", {}).get("films", []):
        edges.append({"from": f"film:{fid}", "to": "home", "type": "introduces"})
    for repo in registry["repos"]:
        nodes.append({"id": f"repo:{repo['id']}", "type": "repository", "title": repo["name"], "url": repo["href"],
                      "summary": repo["description"]})
    for link in registry.get("links", []):
        edges.append({"from": f"project:{link['from']}", "to": f"project:{link['to']}", "type": "related", "label": link["label"]})
    for topic in registry.get("topics", []):
        nodes.append({"id": f"topic:{topic['id']}", "type": "topic", "title": topic["label"], "summary": topic["question"]})
        for item in topic["items"]:
            edges.append({"from": f"project:{item}", "to": f"topic:{topic['id']}", "type": "in_topic"})
    for group in registry.get("collections", []):
        nodes.append({"id": f"collection:{group['id']}", "type": "collection", "title": group["title"]})
        for m in group["members"]:
            edges.append({"from": f"project:{m}", "to": f"collection:{group['id']}", "type": "member_of"})
        if group.get("film"):
            edges.append({"from": f"film:{group['film']}", "to": f"collection:{group['id']}", "type": "film_of"})
    for c in registry.get("contributions", []):
        nodes.append({"id": f"contribution:{c['repo']}", "type": "contribution", "title": c["upstream"],
                      "url": GITHUB + c["repo"], "upstream": "https://github.com/" + c["upstream"], "summary": c["what"]})
    for t in glossary.get("terms", []):
        nodes.append({"id": f"term:{t['id']}", "type": "term", "title": t["term"], "aliases": t.get("aliases", []),
                      "preview": t["preview"], "detail": t["detail"], "anchor": f"{HOME}#t-{t['id']}"})
    nodes.append({"id": "home", "type": "website", "title": "Will Cook", "url": HOME})
    data = {"schema": "will_cook_catalogue_graph_v1", "updated": registry["updated"],
            "about": "Generated from sites.json and glossary.json by scripts/build_hub.py; edit those, not this.",
            "node_types": sorted({n["type"] for n in nodes}), "edge_types": sorted({x["type"] for x in edges}),
            "nodes": nodes, "edges": edges}
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


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
        <ul class="hub-missing__list" role="list">{rows}<li><a href="/">All projects and videos</a></li></ul>
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
        credit = f" {site['credit']}" if site.get("credit") else ""
        evidence = "".join(f" [{route['label']}]({route['href']})."
                           for route in site.get("routes", []) if route["href"].startswith(GITHUB))
        lines.append(f"- [{site['name']}]({site['url']}): {site['purpose']}{credit}{evidence}{tail}")
    lines += ["", "Every website, film, repository and term, with how they connect, is in https://wcook04.github.io/catalogue.json (a graph of typed nodes and edges, generated from https://wcook04.github.io/sites.json and https://wcook04.github.io/glossary.json).",
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


def plectis_paths_from(data: bytes) -> list[str]:
    return [line for line in data.decode("utf-8").splitlines() if line and not line.startswith("#")]


def plectis_paths() -> list[str]:
    return plectis_paths_from(ASSET_READER(PLECTIS_PATHS))


def render_plectis_forward(path: str) -> str:
    """A page at an old /plectis/ address that forwards to its new address.

    The old front door opens the home page, as assets/redirect.js does; every
    other page opens the same page under /practical-formal-verification/. The
    script keeps the query and fragment; the refresh works without it."""
    if path == "index.html":
        target = "/"
    elif path.endswith("/index.html"):
        target = NEW_PLECTIS + path[: -len("index.html")]
    else:
        target = NEW_PLECTIS + path
    url = HOME.rstrip("/") + target
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; frame-src 'none'; child-src 'none'">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url={e(target)}">
  <link rel="canonical" href="{e(url)}">
  <title>This page moved</title>
  <script src="{versioned("/assets/redirect.js")}"></script>
</head>
<body>
  <h1>This page moved</h1>
  <p>The Plectis website moved from <code>/plectis/</code> to <code>/practical-formal-verification/</code>. This page is now at <a href="{e(target)}">{e(url)}</a>.</p>
</body>
</html>
'''


def outputs(registry: dict, glossary: dict | None = None) -> dict[str, str]:
    glossary = glossary if glossary is not None else load_glossary()
    pages = {
        "index.html": render_index(registry, glossary),
        "catalogue.json": render_catalogue(registry, glossary),
        "404.html": render_404(registry),
        "llms.txt": render_llms(registry),
        "agent-guide.md": render_agent_guide(registry),
        "sitemap.xml": render_sitemap(),
        "sitemap-home.xml": render_sitemap_home(registry),
    }
    for path in plectis_paths():
        pages["plectis/" + path] = render_plectis_forward(path)
    return pages


def refresh_plectis_paths() -> None:
    with urllib.request.urlopen(PLECTIS_TREE, timeout=60) as response:
        tree = json.load(response)
    if tree.get("truncated"):
        raise SystemExit("the Plectis website tree came back truncated; list its pages another way")
    paths = sorted(item["path"] for item in tree["tree"]
                   if item["type"] == "blob" and item["path"].endswith(".html")
                   and not item["path"].split("/")[-1].startswith(PLECTIS_SKIP))
    header = ("# Pages of https://wcook04.github.io/practical-formal-verification/ that get a forwarding page\n"
              "# at their old /plectis/ address. Written by scripts/build_hub.py --refresh-plectis-paths.\n")
    (ROOT / PLECTIS_PATHS).write_text(header + "\n".join(paths) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed pages are out of date")
    parser.add_argument("--preview", metavar="DIR",
                        help="write index.html to DIR with every film in preparation drawn as if it were out")
    parser.add_argument("--refresh-plectis-paths", action="store_true",
                        help=f"rewrite {PLECTIS_PATHS} from the Plectis website's published pages first")
    args = parser.parse_args(argv)
    if args.refresh_plectis_paths:
        refresh_plectis_paths()
    registry = load_registry()
    if args.preview:
        global PREVIEW
        PREVIEW = True
        out = Path(args.preview)
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(render_index(registry), encoding="utf-8")
        for name in ("assets", "favicon.ico", "sites.json", "glossary.json"):
            link = out / name
            if not link.exists() and (ROOT / name).exists():
                link.symlink_to(ROOT / name)
        (out / "catalogue.json").write_text(render_catalogue(registry, load_glossary()), encoding="utf-8")
        print(out / "index.html")
        return 0
    stale = []
    for name, text in outputs(registry).items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    if stale:
        print("out of date (run python3 scripts/build_hub.py): " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
