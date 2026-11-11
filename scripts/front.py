"""The home page and the project pages.

The home page is the map the full introduction draws: fifteen projects in five
groups. Every project has its own page at work/<slug>/, and every project page
opens the same way: a strip of levels from a short video on the left down to
the proof or the code on the right.

Words and order come from front.json. Addresses and video lengths come from
sites.json through each stop's `res`, so the two files cannot drift. Pictures
are this repository's own files under assets/front/. Nothing is embedded from
another host; the short introduction plays from a file in this repository.
The pages are complete without JavaScript: every stop and tile is a link, and
the stop a visitor arrived from is marked with CSS `:target`. See docs/front.md.
"""
from __future__ import annotations

import json
import re
from html import escape as e
from pathlib import Path

HOME = "https://wcook04.github.io/"
CSP = ("default-src 'self'; base-uri 'none'; object-src 'none'; form-action 'none'; script-src 'self'; "
       "style-src 'self'; img-src 'self' data:; media-src 'self'; font-src 'self'; connect-src 'none'; "
       "frame-src 'none'; child-src 'none'")
# The home page frames one thing: the introduction, in YouTube's own player, once the visitor presses Play.
CSP_HOME = CSP.replace("frame-src 'none'; child-src 'none'", "frame-src https://www.youtube.com; child-src https://www.youtube.com")
VIDEO_KINDS = ("short", "long")
NAMED_KINDS = ("code", "issue")   # shown by the repository's own name, since every GitHub page looks alike at this size


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


WORDS = {"title", "description", "h1", "lede", "second", "label", "alt", "map_title", "map_note", "name", "line", "names",
         "claim", "limit", "credit", "detail", "detail_prefix", "page_title", "card_alt"}


def typeset(value, key: str = ""):
    """front.json is typed with straight apostrophes; the pages print typographic ones."""
    if isinstance(value, dict):
        return {k: typeset(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [typeset(v, key) for v in value]
    if isinstance(value, str) and (key in WORDS or key in {"short", "long", "site", "paper", "proof", "code", "study", "issue"}):
        return value.replace("'", "\u2019")
    return value


def load(root: Path) -> dict:
    return typeset(json.loads((root / "front.json").read_text(encoding="utf-8")))


class Book:
    """Addresses and lengths from sites.json, pictures from this repository."""

    def __init__(self, canonical: dict, root: Path):
        self.resources = {r["id"]: r for r in canonical["resources"]}
        self.root = root

    def has(self, rel: str) -> bool:
        return (self.root / rel).is_file()

    def place(self, rid: str) -> dict:
        r = self.resources[rid]
        pubs = [p for p in r.get("publications", []) if p.get("state") == "published" and p.get("url")]
        pub = next((p for p in pubs if p.get("preferred")), pubs[0])
        return {"href": pub["url"], "seconds": pub.get("duration_seconds"), "title": r.get("title", ""),
                "type": r["type"], "slug": r.get("slug", ""), "stem": pub.get("thumbnail_stem") or r.get("poster")}

    def poster(self, slug: str, stem: str | None = None) -> dict | None:
        """A video's still: the picture cut for this page, else the catalogue's thumbnail."""
        base = f"assets/front/posters/{slug}"
        if self.has(base + "-480.webp"):
            sizes = [(w, f"{base}-{w}.webp") for w in (480, 960, 1600) if self.has(f"{base}-{w}.webp")]
            return {"src": sizes[0][1], "set": sizes}
        if stem and self.has(stem + "-640.webp"):
            sizes = [(w, f"{stem}-{w}.webp") for w in (640, 1280) if self.has(f"{stem}-{w}.webp")]
            return {"src": sizes[0][1], "set": sizes}
        return None

    def plate(self, name: str | None, fallback: str | None = None) -> dict | None:
        """A website, paper, proof or repository as a picture of the real page."""
        base = f"assets/front/plates/{name}" if name else None
        if base and self.has(base + "-640.webp"):
            sizes = [(w, f"{base}-{w}.webp") for w in (640, 1280) if self.has(f"{base}-{w}.webp")]
            return {"src": sizes[0][1], "set": sizes}
        if fallback and self.has(fallback):
            return {"src": fallback, "set": [(720, fallback)]}
        return None

    def loop(self, slug: str) -> dict | None:
        small, large = f"assets/front/loops/{slug}-s.mp4", f"assets/front/loops/{slug}-l.mp4"
        return {"s": small, "l": large} if self.has(small) and self.has(large) else None


def resolve(front: dict, book: Book) -> dict:
    """front.json with every stop's address, length, label and picture filled in."""
    kinds = front["kinds"]
    bands = {b["id"]: b for b in front["bands"]}

    def link(item: dict) -> dict:
        if item.get("res"):
            place = book.place(item["res"])
            label = item["label"]
            if place["type"] == "video" and place["seconds"]:
                label = f"{label}, {clock(place['seconds'])}"
            return {"label": label, "href": place["href"], "res": item["res"]}
        return {"label": item["label"], "href": item["href"], "res": None}

    entries = []
    for entry in front["entries"]:
        stops = []
        for stop in entry["stops"]:
            place = book.place(stop["res"]) if stop.get("res") else None
            kind = stop["kind"]
            label = stop.get("label") or kinds[kind]
            detail = stop.get("detail", "")
            picture = None
            if kind in VIDEO_KINDS:
                detail = stop.get("detail_prefix", "") + clock(place["seconds"])
                picture = book.poster(place["slug"], place["stem"])
            elif kind not in NAMED_KINDS:
                picture = book.plate(stop.get("plate"), stop.get("fallback"))
            href = place["href"] if place else stop["href"]
            stops.append({"id": stop["id"], "kind": kind, "label": label, "detail": detail, "href": href,
                          "res": stop.get("res"), "picture": picture, "video": kind in VIDEO_KINDS,
                          "watched": stop.get("watched"), "named": named(href) if kind in NAMED_KINDS else None,
                          "more": [link(m) for m in stop.get("more", [])]})
        lead = next((s for s in stops if s["video"]), None)
        entries.append({**entry, "stops": stops, "band_name": bands[entry["band"]]["name"], "band_n": bands[entry["band"]]["n"],
                        "poster": book.poster(entry["loop"]), "loops": book.loop(entry["loop"]),
                        "path": f"work/{entry['slug']}/", "lead": lead})
    intro = dict(front["intro"])
    for key in ("short", "long"):
        intro[key] = {**intro[key], **book.place(intro[key]["res"])}
    intro["poster"] = book.poster(intro["idle"]["loop"])
    return {"intro": intro, "bands": front["bands"], "entries": entries, "videos": front["videos"],
            "terms": front.get("terms", {})}


def named(href: str) -> tuple[str, str]:
    """A repository or issue is shown by its own name: ("wcook04/", "safety-core") or ("NVIDIA/auto-ontology", "#431")."""
    parts = href.split("github.com/", 1)[-1].strip("/").split("/")
    if len(parts) >= 4 and parts[2] == "issues":
        return f"{parts[0]}/{parts[1]}", "#" + parts[3]
    return parts[0] + "/", parts[1] if len(parts) > 1 else ""


def glosses(entry: dict, terms: dict) -> list[str]:
    """One plain sentence for each term this page uses and a newcomer may not know."""
    words = " ".join([entry["claim"], entry["limit"], entry.get("credit", "")] +
                     [f'{s["label"]} {s["detail"]}' for s in entry["stops"]])
    return [text for term, text in terms.items() if re.search(rf"\b{re.escape(term)}\b", words)]


# ------------------------------------------------------------------ markup

def whole(text: str) -> str:
    """Escaped text in which a hyphenated word never breaks across lines."""
    return re.sub(r"\b[\w']+(?:-[\w']+)+\b", lambda m: f'<span class="nb">{m.group(0)}</span>', e(text))


def off(href: str) -> str:
    """Links that leave this host open in a new tab; this host's own pages do not."""
    return ' target="_blank" rel="noopener noreferrer"' if href.startswith("http") and not href.startswith(HOME) else ""


def img(picture: dict | None, *, sizes: str, alt: str = "", eager: bool = False, soon: bool = False, cls: str = "") -> str:
    """eager: the page's main picture. soon: on the first screen, so not lazy. Otherwise loaded when scrolled to."""
    if not picture:
        return ""
    srcset = ", ".join(f"/{path} {width}w" for width, path in picture["set"])
    lazy = (' decoding="sync" fetchpriority="high"' if eager else ' decoding="async"' if soon
            else ' decoding="async" loading="lazy"')
    klass = f' class="{cls}"' if cls else ""
    return (f'<img{klass} src="/{e(picture["src"])}" srcset="{e(srcset)}" sizes="{e(sizes)}" alt="{e(alt)}" '
            f'width="16" height="9"{lazy}>')


def head(hub, *, title: str, description: str, canonical: str, picture: str | None, alt: str = "", structured: str = "", frames: bool = False) -> str:
    v = hub.versioned
    card = (f'\n  <meta property="og:image" content="{e(HOME + picture)}">'
            f'\n  <meta property="og:image:width" content="1200">\n  <meta property="og:image:height" content="630">'
            f'\n  <meta property="og:image:alt" content="{e(alt)}">'
            f'\n  <meta name="twitter:card" content="summary_large_image">'
            f'\n  <meta name="twitter:image" content="{e(HOME + picture)}">') if picture else ""
    data = f'\n  <script type="application/ld+json">{structured}</script>' if structured else ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="format-detection" content="telephone=no">
  <!-- Nothing loads from another host, except the introduction on the home page, which plays in YouTube's player. -->
  <meta http-equiv="Content-Security-Policy" content="{CSP_HOME if frames else CSP}">
  <title>{e(title)}</title>
  <meta name="description" content="{e(description)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{e(canonical)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Will Cook">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:url" content="{e(canonical)}">{card}
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#1c1526">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="preload" href="/assets/fonts/front-serif.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/barlow-condensed-700.woff" as="font" type="font/woff" crossorigin>
  <link rel="preload" href="/assets/fonts/barlow-400.woff" as="font" type="font/woff" crossorigin>
  <link rel="help" href="/llms.txt" type="text/plain" title="Guide for agents">
  <link rel="alternate" href="/catalogue.json" type="application/json" title="Catalogue as a graph">
  <script src="{v("/assets/front-init.js")}"></script>
  <link rel="stylesheet" href="{v("/assets/front.css")}">
  <script src="{v("/assets/front.js")}" defer></script>{data}
</head>'''


def header(*, home: bool) -> str:
    current = ' aria-current="page"' if home else ""
    about = "#about" if home else "/#about"
    return f'''<a class="skip" href="#main">Skip to the content</a>
  <header class="top">
    <div class="wrap top__in">
      <a class="brand" href="/"{current}><img src="/assets/favicon.svg" alt="" width="28" height="28"><span translate="no">Will Cook</span></a>
      <nav class="top__nav" aria-label="Main">
        <a href="#map">Projects</a>
        <a href="{about}">About</a>
        <a href="/all.html">Every link</a>
      </nav>
    </div>
  </header>'''


def footer() -> str:
    return '''<footer class="foot wrap">
    <a href="/all.html">Every video, paper, website and repository on one page</a>
    <a href="/all.html#terms">Glossary</a>
    <a href="https://github.com/wcook04/wcook04.github.io" target="_blank" rel="noopener noreferrer">This site’s source</a>
  </footer>'''


def tile(entry: dict, *, here: bool, home: bool) -> str:
    ids = "".join(f'<span class="anchor" id="p-{e(a)}"></span>' for a in entry.get("aliases", [])) if home else ""
    loop = f' data-loop="/{e(entry["loops"]["s"])}"' if entry.get("loops") else ""
    current = ' aria-current="page"' if here else ""
    mark = '<span class="tile__here">You are here</span>' if here else ""
    names = f'<span class="tile__names">{e(entry["names"])}</span>' if entry.get("names") else ""
    return (f'<li class="tiles__item">{ids}<a class="tile" href="/{e(entry["path"])}"{current}{loop} data-entry="{e(entry["slug"])}">'
            f'<span class="tile__pic">{img(entry["poster"], sizes="(min-width: 900px) 16vw, 46vw")}{mark}</span>'
            f'<span class="tile__name">{e(entry["name"])}</span><span class="vh">: </span>'
            f'<span class="tile__line">{e(entry["line"])}</span>{names}</a></li>')


def project_map(model: dict, *, current: str | None, title: str, note: str) -> str:
    home = current is None
    bands = []
    for band in model["bands"]:
        tiles = "".join(tile(x, here=x["slug"] == current, home=home) for x in model["entries"] if x["band"] == band["id"])
        aside = f'<p class="band__note">{e(band["note"])}</p>' if band.get("note") else ""
        bands.append(f'<section class="band band--{e(band["id"])}" aria-labelledby="band-{e(band["id"])}">'
                     f'<div class="band__head"><h3 class="band__name" id="band-{e(band["id"])}"><span class="band__n">{band["n"]}</span> {e(band["name"])}</h3>{aside}</div>'
                     f'<ul class="tiles" role="list">{tiles}</ul></section>')
    lead = f'<p class="map__note">{e(note)}</p>' if note else ""
    old = '<span class="anchor" id="projects"></span><span class="anchor" id="explore"></span><span class="anchor" id="films"></span>' if home else ""
    return (f'<section class="map wrap" id="map" aria-labelledby="map-title">{old}'
            f'<div class="map__head"><h2 class="map__title" id="map-title">{e(title)}</h2>{lead}</div>'
            f'<div class="bands">{"".join(bands)}</div></section>')


def stop_markup(stop: dict) -> str:
    kind = stop["kind"]
    if stop.get("named"):
        owner, name = stop["named"]
        picture = f'<span class="stop__named"><span class="stop__owner">{e(owner)}</span><span class="stop__repo">{e(name)}</span></span>'
    elif stop["picture"]:
        picture = img(stop["picture"], sizes="(min-width: 900px) 15vw, 30vw", soon=True)
    else:
        picture = f'<span class="stop__named"><span class="stop__repo">{e(stop["label"])}</span></span>'
    play = '<span class="stop__play" aria-hidden="true"></span>' if stop["video"] else ""
    more = ""
    if stop["more"]:
        more = '<ul class="stop__more" role="list">' + "".join(
            f'<li><a href="{e(m["href"])}"{off(m["href"])}>{e(m["label"])}</a></li>' for m in stop["more"]) + "</ul>"
    flag = "You watched this" if stop["video"] else "The video showed this"
    return (f'<li class="stop stop--{e(kind)}{" stop--video" if stop["video"] else ""}" id="{e(stop["id"])}">'
            f'<span class="stop__flag stop__flag--here">{flag}</span><span class="stop__flag stop__flag--next">Next</span>'
            f'<a class="stop__main" href="{e(stop["href"])}"{off(stop["href"])}>'
            f'<span class="stop__pic">{picture}{play}</span>'
            f'<span class="stop__kind">{e(stop["label"])}</span><span class="vh">, </span>'
            f'<span class="stop__detail">{e(stop["detail"])}{" on YouTube" if stop["video"] else ""}</span></a>{more}</li>')


def card_of(slug: str, book: Book) -> str | None:
    """The picture a link to this page unfurls with: 1200 by 630, PNG (some readers refuse WebP)."""
    path = f"assets/front/cards/{slug}.png"
    return path if book.has(path) else None


def render_home(model: dict, registry: dict, hub, structured: str, book: Book) -> str:
    intro = model["intro"]
    owner = registry["owner"]
    short, long = intro["short"], intro["long"]
    found = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", short["href"])
    if not found:
        raise ValueError("the short introduction has no YouTube address to embed")
    embed = f"https://www.youtube.com/embed/{found.group(1)}?autoplay=1&rel=0"
    idle_clip = "assets/front/loops/hero-l.mp4"
    loop_attrs = f' data-idle="/{idle_clip}"' if book.has(idle_clip) else ""
    narrow = "".join(f'<source media="(max-width: 1180px)" srcset="/assets/front/posters/hero-n-480.webp 480w, /assets/front/posters/hero-n-960.webp 960w" sizes="(min-width: 861px) 56vw, 100vw">'
                     for _ in [0] if book.has("assets/front/posters/hero-n-480.webp") and book.has("assets/front/posters/hero-n-960.webp"))
    contact = "".join(f'<li><a href="{e(c["href"])}"{off(c["href"])}>{e(c["label"])}</a></li>' for c in owner["contact"])
    # The hero has already said what he does; this part says what he is looking for and how to reach him.
    asks = [typeset(text, "lede") for text in owner.get("invitation", [])]
    lead = e(asks[0]) if asks else ""
    invitation = "".join(f"<p>{e(text)}</p>" for text in asks[1:])
    aliases = '<span class="anchor" id="p-intro"></span><span class="anchor" id="work"></span>'
    return f'''{head(hub, title=intro["title"], description=intro["description"], canonical=HOME, picture=card_of("home", book), alt=intro.get("card_alt", ""), structured=structured, frames=True)}
<body class="home">
  {header(home=True)}
  <main id="main">
    <section class="stage stage--home wrap" aria-labelledby="say">
      <div class="stage__text">{aliases}
        <h1 class="say" id="say">{whole(intro["h1"])}</h1>
        <p class="lede">{e(intro["lede"])}</p>
        <p class="lede lede--second">{e(intro["second"])}</p>
      </div>
      <div class="stage__show">
        <div class="player" id="player" data-embed="{e(embed)}" data-embed-title="{e(short["label"])}, {e(clock(short["seconds"]))}"{loop_attrs}>
          <div class="player__screen"><picture>{narrow}{img(intro.get("poster"), sizes="(min-width: 900px) 58vw, 100vw", alt=intro["idle"]["alt"], eager=True, cls="player__poster")}</picture></div>
          <div class="player__bar">
            <a class="play" href="{e(short["href"])}"{off(short["href"])} data-play><span class="play__mark" aria-hidden="true"></span><span class="play__what">Play {e(short["label"])}</span><span class="play__len">{e(clock(short["seconds"]))}</span></a>
            <a class="quiet" href="{e(long["href"])}"{off(long["href"])}>{e(long["label"])}, {e(clock(long["seconds"]))}</a>
            <a class="quiet" href="{e(short["href"])}"{off(short["href"])} data-youtube>Watch on YouTube</a>
          </div>
        </div>
      </div>
    </section>
    {project_map(model, current=None, title=intro["map_title"], note=intro["map_note"])}
    <section class="about wrap" id="about" aria-labelledby="about-title">
      <span class="anchor" id="contact"></span>
      <h2 class="about__title" id="about-title">About</h2>
      <div class="about__body">
        <div class="about__words">
          <p class="say say--small">{lead}</p>
          {invitation}
        </div>
        <div class="about__reach">
          <ul class="about__contact" role="list">{contact}</ul>
          <p class="about__more"><a href="/all.html#about">Contributions to other people’s projects, and earlier work</a></p>
        </div>
      </div>
    </section>
  </main>
  {footer()}
</body>
</html>
'''


def render_entry(model: dict, entry: dict, hub, book: Book) -> str:
    stops = "".join(stop_markup(s) for s in entry["stops"])
    credit = f'<p class="credit">{e(entry["credit"])}</p>' if entry.get("credit") else ""
    gloss = "".join(f'<p class="credit credit--term">{e(text)}</p>' for text in glosses(entry, model["terms"]))
    loops = entry.get("loops") or {}
    loop_attrs = f' data-loop-l="/{e(loops["l"])}"' if loops else ""
    count = len(entry["stops"])
    return f'''{head(hub, title=entry["page_title"] + " | Will Cook", description=entry["description"], canonical=HOME + entry["path"], picture=card_of(entry["slug"], book), alt=entry.get("card_alt", ""))}
<body class="work" data-entry="{e(entry["slug"])}">
  {header(home=False)}
  <main id="main">
    <article class="stage stage--work wrap" aria-labelledby="name">
      <div class="stage__text">
        <p class="stage__band"><a href="#map">Projects</a><span aria-hidden="true">/</span>{e(entry["band_name"])}</p>
        <h1 class="name" id="name">{e(entry["name"])}</h1>
        <p class="say say--claim">{e(entry["claim"])}</p>
        <p class="limit"><strong class="limit__label">Limits:</strong> {e(entry["limit"])}</p>
        {credit}{gloss}
      </div>
      <div class="stage__show">
        <div class="screen" id="screen"{loop_attrs}>{img(entry["poster"], sizes="(min-width: 900px) 58vw, 100vw", eager=True)}</div>
      </div>
    </article>
    <nav class="levels levels--{count} wrap" aria-labelledby="levels-title">
      <h2 class="levels__title" id="levels-title">{e(entry["name"])}, from the quickest look to the most detail</h2>
      <p class="levels__axis" aria-hidden="true"><span>Quickest</span><span>Most detail</span></p>
      <ol class="strip strip--{count}" role="list">{stops}</ol>
    </nav>
    {project_map(model, current=entry["slug"], title="All fifteen projects", note="")}
  </main>
  {footer()}
</body>
</html>
'''


def pages(registry: dict, root: Path, structured: str, hub) -> dict[str, str]:
    """Every page this module owns, by path."""
    book = Book(registry["_canonical_v3"], root)
    model = resolve(load(root), book)
    out = {"index.html": render_home(model, registry, hub, structured, book)}
    for entry in model["entries"]:
        out[entry["path"] + "index.html"] = render_entry(model, entry, hub, book)
    return out


def addresses(root: Path) -> list[str]:
    """The pages' public addresses, for the sitemap."""
    return [HOME] + [f"{HOME}work/{x['slug']}/" for x in load(root)["entries"]]
