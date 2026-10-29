#!/usr/bin/env python3
"""Validate the home page repository, including the Git index when requested.

The home page maps every website, film and repository from sites.json. This
check holds the promises the page makes: the committed pages are what
sites.json produces, nothing loads from another host (the map's script
included), no player is embedded, every website, released film and repository
is linked, a film in preparation has no link, and this repository never claims
the paths the project websites are served from.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOME = "https://wcook04.github.io/"
SPEC = importlib.util.spec_from_file_location("build_hub", ROOT / "scripts/build_hub.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)

REQUIRED = {
    ".github/workflows/public-site.yml", ".gitignore", ".nojekyll", "README.md",
    "index.html", "404.html", "sites.json", "llms.txt", "agent-guide.md",
    "robots.txt", "sitemap.xml", "sitemap-home.xml", "favicon.ico",
    "assets/hub.css", "assets/hub.js", "assets/hub-map.js", "assets/theme-init.js", "assets/redirect.js",
    "assets/family/family.css", "assets/favicon.svg", "assets/favicon-32.png",
    "assets/apple-touch-icon.png", "docs/family.md",
    "scripts/build_hub.py", "scripts/check_hub_site.py", "tests/test_hub_site.py",
}
# Folders whose files are part of the page: fonts with their licences, film
# stills and website pictures. Anything else outside REQUIRED is unexpected.
ASSET_DIRS = ("assets/fonts/", "assets/films/", "assets/sites/", "assets/family/marks/")
# Project websites are served from these paths by their own repositories.
PROJECT_PATHS = ("plectis/", "plectis-atlas/", "plectis-zenith/", "practical-formal-verification/",
                 "lean-exposition-site/", "microcosm-substrate/")


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def snapshot(root: Path, *, index: bool = False) -> dict[str, bytes]:
    args = ["ls-files", "--cached"]
    if not index:
        args += ["--others", "--exclude-standard"]
    paths = set(git(root, *args, "-z").decode().split("\0")) - {""}
    if index:
        return {path: git(root, "show", ":" + path) for path in paths}
    return {path: (root / path).read_bytes() for path in paths if (root / path).is_file()}


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.tags: list[str] = []
        self.attrs: list[tuple[str, dict]] = []
        self.link_texts: list[str] = []
        self._open: list[list[str]] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))
        if tag == "a":
            self._open.append([])

    def handle_endtag(self, tag):
        if tag == "a" and self._open:
            self.link_texts.append(" ".join("".join(self._open.pop()).split()))

    def handle_data(self, data):
        for parts in self._open:
            parts.append(data)

    def all(self, tag: str) -> list[dict]:
        return [a for t, a in self.attrs if t == tag]


def same_origin(url: str) -> bool:
    return not url.startswith(("http://", "https://", "//"))


def validate_page(name: str, text: str, *, home: bool) -> list[str]:
    errors = []
    page = Page(text)
    for tag in ("iframe", "object", "embed", "video", "audio", "frame"):
        if tag in page.tags:
            errors.append(f"{name}: no embedded player or frame ({tag})")
    for tag, key in (("img", "src"), ("script", "src"), ("link", "href"), ("source", "src")):
        for attrs in page.all(tag):
            if tag == "link" and attrs.get("rel") in {"canonical"}:
                continue
            url = attrs.get(key)
            if url and not same_origin(url):
                errors.append(f"{name}: {tag} loads from another host: {url}")
    for attrs in page.all("img"):
        for candidate in (attrs.get("srcset") or "").split(","):
            url = candidate.strip().split(" ")[0]
            if url and not same_origin(url):
                errors.append(f"{name}: img srcset loads from another host: {url}")
    csp = [m.get("content", "") for m in page.all("meta") if m.get("http-equiv", "").lower() == "content-security-policy"]
    if len(csp) != 1 or "frame-src 'none'" not in csp[0] or "connect-src 'none'" not in csp[0] or "script-src 'self'" not in csp[0]:
        errors.append(f"{name}: content security policy must keep frames, connections and other hosts' scripts out")
    if page.tags.count("h1") != 1:
        errors.append(f"{name}: exactly one h1")
    anchors = page.all("a")
    if not anchors or anchors[0].get("href") != "#main" or "skip-link" not in anchors[0].get("class", ""):
        errors.append(f"{name}: the skip link comes first")
    robots = [m.get("content", "") for m in page.all("meta") if m.get("name") == "robots"]
    expected = "index, follow" if home else "noindex, follow"
    if robots != [expected]:
        errors.append(f"{name}: robots must be {expected}")
    if home:
        canonical = [link.get("href") for link in page.all("link") if link.get("rel") == "canonical"]
        if canonical != [HOME]:
            errors.append(f"{name}: canonical must be {HOME}")
    else:
        if "/assets/redirect.js" not in [(s.get("src") or "").split("?")[0] for s in page.all("script")]:
            errors.append(f"{name}: old Plectis addresses must forward through /assets/redirect.js")
        if "/" not in [a.get("href") for a in anchors]:
            errors.append(f"{name}: a missing page links home")
    for attrs in anchors:
        href = attrs.get("href", "")
        if "youtube.com/watch" in href and (attrs.get("target") != "_blank" or "noopener" not in attrs.get("rel", "")):
            errors.append(f"{name}: film links open in a new tab with rel=noopener: {href}")
    return errors


def validate(files: dict[str, bytes]) -> list[str]:
    errors = []
    missing = REQUIRED - files.keys()
    if missing:
        errors.append("missing maintained files: " + ", ".join(sorted(missing)))
    extra = sorted(p for p in files.keys() - REQUIRED if not p.startswith(ASSET_DIRS))
    if extra:
        errors.append("files outside the home page's roles: " + ", ".join(extra))
    claimed = sorted(p for p in files if p.startswith(PROJECT_PATHS))
    if claimed:
        errors.append("project websites are served from these paths by their own repositories: " + ", ".join(claimed))
    if "sites.json" not in files:
        return errors
    registry = json.loads(files["sites.json"])
    problems = BUILD.validate_registry(registry, exists=lambda rel: rel in files)
    errors += ["sites.json: " + p for p in problems]
    if problems:
        return errors
    BUILD.ASSET_READER = lambda rel: files.get(rel, b"")
    try:
        rendered = BUILD.outputs(registry)
    finally:
        BUILD.ASSET_READER = BUILD.read_asset
    for name, text in rendered.items():
        if files.get(name, b"").decode() != text:
            errors.append(f"{name}: out of date with sites.json (run python3 scripts/build_hub.py)")
    if "index.html" in files:
        index = files["index.html"].decode()
        errors += validate_page("index.html", index, home=True)
        page = Page(index)
        hrefs = {a.get("href") for a in page.all("a")}
        for site in registry["sites"]:
            if site["url"] not in hrefs:
                errors.append(f"index.html: website not linked: {site['name']}")
        for site in registry["sites"]:
            for route in site.get("routes", []):
                if route["href"] not in hrefs:
                    errors.append(f"index.html: {site['name']} route not linked: {route['label']}")
        for film in registry["films"]:
            if film.get("youtube") and film["youtube"] not in hrefs:
                errors.append(f"index.html: released film not linked: {film['title']}")
            if not film.get("youtube"):
                names = {film["title"], film["short"]}
                if any(name in text for text in page.link_texts for name in names):
                    errors.append(f"index.html: a film in preparation has no link: {film['title']}")
        for repo in registry["repos"]:
            if repo["href"] not in hrefs:
                errors.append(f"index.html: repository not linked: {repo['name']}")
        scripts = [attrs for attrs in page.all("script") if attrs.get("src")]
        if not any((attrs.get("src") or "").split("?")[0] == "/assets/hub-map.js" and "defer" in attrs for attrs in scripts):
            errors.append("index.html: the map's lines come from the same-origin /assets/hub-map.js, deferred")
    if "404.html" in files:
        errors += validate_page("404.html", files["404.html"].decode(), home=False)
    if "robots.txt" in files:
        lines = [line.strip().lower() for line in files["robots.txt"].decode().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        if lines != ["user-agent: *", "allow: /", "sitemap: https://wcook04.github.io/sitemap.xml"]:
            errors.append("robots.txt: preserve host-wide project crawling and the root sitemap")
    if "sitemap.xml" in files:
        try:
            tree = ET.fromstring(files["sitemap.xml"])
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            locs = [node.text for node in tree.iter(ns + "loc")]
            if tree.tag != ns + "sitemapindex" or HOME + "sitemap-home.xml" not in locs:
                errors.append("sitemap.xml: index the home page's own sitemap and the project sitemaps")
        except ET.ParseError:
            errors.append("sitemap.xml: invalid XML")
    workflow = files.get(".github/workflows/public-site.yml", b"")
    for command in (b"python3 scripts/check_hub_site.py", b"python3 -m unittest"):
        if command not in workflow:
            errors.append("CI must run " + command.decode())
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", action="store_true", help="validate staged paths and staged file contents")
    args = parser.parse_args()
    errors = validate(snapshot(ROOT, index=args.index))
    if errors:
        raise SystemExit("\n".join(errors))
    print("Home page: pages match sites.json, same-origin assets and map script, linked websites, films and repositories, project paths left free")


if __name__ == "__main__":
    main()
