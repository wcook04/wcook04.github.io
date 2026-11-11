#!/usr/bin/env python3
"""Check canonical v3 and its generated static/explorer views.

--prototype checks an unpacked review ZIP without production CI or legacy
forwarding pages. --index reads actual staged paths and bytes, including
staged deletions, and never substitutes working-tree content.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOME = "https://wcook04.github.io/"
sys.path.insert(0, str(ROOT / "scripts"))
import catalogue_v3 as CATALOGUE

SPEC = importlib.util.spec_from_file_location("build_hub", ROOT / "scripts/build_hub.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)

REQUIRED = {
    ".nojekyll", "README.md", "index.html", "all.html", "404.html", "sites.json",
    "glossary.json", "catalogue.json", "family.json", "structured-data.jsonld", "explorer.json",
    "llms.txt", "agent-guide.md", "plectis-paths.txt", "robots.txt", "sitemap.xml",
    "sitemap-home.xml", "favicon.ico", "assets/hub.css", "assets/explorer.css",
    "assets/explore.js", "assets/explore-model.js", "assets/redirect.js", "assets/door-art.css",
    "front.json", "assets/front.css", "assets/front.js", "assets/front-init.js", "scripts/front.py",
    "assets/favicon.svg", "scripts/build_hub.py", "scripts/check_hub_site.py",
    "scripts/catalogue_v3.py", "scripts/explorer_v3.py", "scripts/door_art.py", "scripts/sites.schema.json",
    "scripts/glossary.schema.json", "tests/test_hub_site.py",
}
PRODUCTION_REQUIRED = {".github/workflows/public-site.yml", ".gitignore"}
ALLOWED = REQUIRED | PRODUCTION_REQUIRED | {
    "assets/hub.js", "assets/theme-init.js", "assets/family/family.css",
    "assets/favicon-32.png", "assets/apple-touch-icon.png", "scripts/capture_cards.py",
    "scripts/check_explorer_model.js", "scripts/build_portable.py", "tests/__init__.py", "requirements.txt",
}
ALLOWED_DIRS = ("assets/fonts/", "assets/films/", "assets/sites/", "assets/logos/", "assets/family/marks/",
                "assets/front/", "content/transcripts/", "docs/", "work/")
FRONT_MEDIA = ("assets/front/loops/", "assets/front/posters/", "assets/front/plates/", "assets/front/intro/", "assets/front/cards/")
PROJECT_PATHS = ("plectis-atlas/", "plectis-zenith/", "practical-formal-verification/",
                 "lean-exposition-site/", "proof-reader/", "microcosm-substrate/",
                 "quartic-query-lean/", "plectis-erdos/")


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)


def snapshot(root: Path, *, index: bool = False) -> dict[str, bytes]:
    root = root.resolve()
    try:
        checkout = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root
    except (subprocess.CalledProcessError, FileNotFoundError):
        checkout = False
    if index and not checkout:
        raise ValueError("--index requires this directory to be the root of a Git checkout")
    if checkout:
        args = ["ls-files", "--cached"] + ([] if index else ["--others", "--exclude-standard"])
        paths = set(git(root, *args, "-z").decode().split("\0")) - {""}
        if index:
            return {name: git(root, "show", ":" + name) for name in paths}
        return {name: (root / name).read_bytes() for name in paths if (root / name).is_file()}
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*")
            if path.is_file() and not any(part in {".git", "__pycache__", ".pytest_cache"}
                                          for part in path.relative_to(root).parts)
            and path.suffix != ".pyc"}


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.tags = []
        self.attrs = []
        self.scripts = []
        self._script = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        self.attrs.append((tag, attrs))
        if tag == "script": self._script = {"attrs": attrs, "text": ""}

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            self.scripts.append(self._script)
            self._script = None

    def handle_data(self, data):
        if self._script is not None: self._script["text"] += data

    def all(self, tag):
        return [attrs for name, attrs in self.attrs if name == tag]

    @property
    def ids(self):
        return [attrs["id"] for _, attrs in self.attrs if attrs.get("id")]


def site_view(root: Path) -> dict:
    """The view both pages are rendered from, rebuilt from the files under root."""
    import explorer_v3
    glossary = json.loads((root / "glossary.json").read_text(encoding="utf-8"))
    return explorer_v3.build_view(BUILD.load_registry(root), glossary, root)


def front_pages(files) -> dict[str, str]:
    """The home page and the project pages, as text, by path."""
    return {name: files[name].decode() for name in sorted(files)
            if name == "index.html" or (name.startswith("work/") and name.endswith("/index.html"))}


def named_files(text: str) -> set[str]:
    """Every file of this repository that a page names, in any attribute."""
    page = Page(text)
    found = set()
    for _, attrs in page.attrs:
        for key, value in attrs.items():
            if not value:
                continue
            parts = [part.strip().split(" ")[0] for part in value.split(",")] if key == "srcset" else [value]
            for part in parts:
                if part.startswith(HOME): part = part[len(HOME) - 1:]
                if part.startswith("/assets/"): found.add(part.split("?")[0].split("#")[0].lstrip("/"))
    return found


def validate_landing(files, view: dict) -> list[str]:
    """The home page and the project pages together reach every current video,
    website and first repository; every project page a tile or a video's link
    names exists; and every picture and clip shipped for them is used."""
    pages = front_pages(files)
    if "index.html" not in pages: return ["index.html: missing"]
    parsed = {name: Page(text) for name, text in pages.items()}
    hrefs = {a.get("href") for page in parsed.values() for a in page.all("a")}
    home = parsed["index.html"]
    errors = []
    films = view["films"]
    for fid, film in films.items():
        newer = film.get("superseded_by")
        earlier = film.get("edition") == "earlier" or bool(newer and films.get(newer, {}).get("youtube"))
        if film.get("youtube") and not earlier and film["youtube"] not in hrefs:
            errors.append("home and project pages: current video not linked: " + fid)
    for pid, project in view["projects"].items():
        if "p-" + pid not in home.ids: errors.append("index.html: project has no anchor: " + pid)
        if project.get("url") and project["url"] not in hrefs: errors.append("home and project pages: website not linked: " + pid)
        for repo in project.get("repo_records", [])[:1]:
            if repo["href"] not in hrefs: errors.append("home and project pages: repository not linked: " + repo["id"])
    try:
        front = json.loads(files["front.json"])
    except (KeyError, ValueError) as exc:
        return errors + ["front.json: " + str(exc)]
    tiles = [a.get("href") for a in home.all("a") if a.get("class") == "tile"]
    expected = ["/work/" + entry["slug"] + "/" for entry in front["entries"]]
    if tiles != expected: errors.append("index.html: the map must hold one tile per project, in front.json's order")
    for address in expected:
        if address.lstrip("/") + "index.html" not in pages: errors.append("missing project page: " + address)
    for video, address in front.get("videos", {}).items():
        path, _, fragment = address.partition("#")
        name = (path.lstrip("/") + "index.html") if path != "/" else "index.html"
        if name not in parsed: errors.append(f"front.json: {video} points at a page that does not exist: {address}")
        elif fragment and fragment not in parsed[name].ids: errors.append(f"front.json: {video} points at a missing stop: {address}")
    named = set().union(*(named_files(text) for text in pages.values()))
    shipped = {name for name in files if name.startswith(FRONT_MEDIA)}
    for name in sorted(n for n in named if n.startswith("assets/") and n not in files): errors.append("a page names a file that is not in the repository: " + name)
    for name in sorted(shipped - named): errors.append("picture or clip no page uses: " + name)
    return errors


def same_origin(url: str) -> bool:
    return not url.startswith(("http://", "https://", "//"))


def validate_page(name: str, text: str, *, prototype: bool = False, redirect: bool = False) -> list[str]:
    page = Page(text)
    errors = []
    for tag in ("iframe", "object", "embed", "video", "audio", "frame"):
        if tag in page.tags: errors.append(f"{name}: no embedded player or frame ({tag})")
    for tag, key in (("img", "src"), ("script", "src"), ("link", "href"), ("source", "src")):
        for attrs in page.all(tag):
            if tag == "link" and attrs.get("rel") == "canonical": continue
            url = attrs.get(key, "")
            if url and not same_origin(url): errors.append(f"{name}: {tag} loads from another host: {url}")
    for attrs in page.all("img") + page.all("source"):
        for part in attrs.get("srcset", "").split(","):
            url = part.strip().split(" ")[0]
            if url and not same_origin(url): errors.append(f"{name}: image source loads from another host: {url}")
    csp = [m.get("content", "") for m in page.all("meta") if m.get("http-equiv", "").lower() == "content-security-policy"]
    # No page frames anything: films open on YouTube, and the home page's previews are its own files.
    frames = "frame-src 'none'"
    rules = [r.strip() for r in csp[0].split(";")] if len(csp) == 1 else []
    if any(rule not in rules for rule in (frames, "connect-src 'none'", "script-src 'self'")):
        errors.append(f"{name}: preserve the same-origin content security policy ({frames})")
    if page.tags.count("h1") != 1: errors.append(f"{name}: exactly one h1 is required")
    if len(page.ids) != len(set(page.ids)): errors.append(f"{name}: HTML ids must be unique")
    anchors = page.all("a")
    if not redirect and ("main" not in page.ids or not anchors or anchors[0].get("href") != "#main"):
        errors.append(f"{name}: first link must skip to the main landmark")
    if not prototype:
        robots = [m.get("content", "") for m in page.all("meta") if m.get("name") == "robots"]
        expected = "noindex, follow" if redirect else "index, follow"
        if robots != [expected]: errors.append(f"{name}: robots must be {expected}")
        if name == "index.html" or name.startswith("work/"):
            canonical = [a.get("href") for a in page.all("link") if a.get("rel") == "canonical"]
            expected_url = HOME if name == "index.html" else HOME + name[: -len("index.html")]
            if canonical != [expected_url]: errors.append(name + ": canonical must identify the page's real URL")
    if redirect:
        scripts = [(a.get("src") or "").split("?")[0] for a in page.all("script")]
        if "/assets/redirect.js" not in scripts: errors.append(f"{name}: legacy routes must use /assets/redirect.js")
    return errors


def validate_projection(view: dict, canonical: dict) -> list[str]:
    errors = []
    projects = {p["slug"] for p in canonical["projects"]}
    films = {r["slug"]: r for r in canonical["resources"] if r["type"] == "video"}
    config = view.get("config", {})
    doors = config.get("doors", [])
    door_ids = [d["id"] for d in doors]
    if not doors or len(door_ids) != len(set(door_ids)): errors.append("explorer: door IDs must be nonempty and unique")
    reached = set()
    for door in doors:
        for pid in door.get("projects", []):
            if pid not in projects: errors.append("explorer: unknown project " + pid)
            reached.add(pid)
        for shortcut in door.get("shortcuts", []):
            if shortcut["project"] not in door.get("projects", []): errors.append("explorer: shortcut leaves its owning door")
    if projects - reached: errors.append("explorer: unreachable projects " + ", ".join(sorted(projects - reached)))
    for key in ("project_questions", "project_choices", "project_objects"):
        if set(config.get(key, {})) != projects: errors.append("explorer: " + key + " must cover exactly the project IDs")
    for bridge in config.get("bridges", []):
        if bridge.get("from") not in door_ids or bridge.get("to") not in door_ids: errors.append("explorer: bridge has an unknown door")
    topics = {t["slug"] for t in canonical["topics"]}
    if set(config.get("topic_aliases", {})) != topics: errors.append("explorer: preserve every canonical topic alias")
    if any(d not in door_ids for d in config.get("topic_aliases", {}).values()): errors.append("explorer: topic alias targets an unknown door")
    if any(t not in topics or p not in projects for t, p in config.get("direct_topics", {}).items()): errors.append("explorer: direct topic targets an unknown project")
    if set(view.get("projects", {})) != projects or set(view.get("films", {})) != set(films): errors.append("explorer: embedded view lost a project or video")
    expected_films = {f["id"]: f for f in CATALOGUE.adapt_v3_to_v2(canonical)["films"]}
    for fid, displayed in view.get("films", {}).items():
        if fid not in films: continue
        expected = expected_films[fid]
        if displayed.get("youtube") != expected.get("youtube"): errors.append("explorer: invented or changed public video URL for " + fid)
        if displayed.get("leads_to", []) != expected.get("leads_to", []): errors.append("explorer: omitted or changed continuation for " + fid)
        if displayed.get("term_refs", []) != films[fid].get("term_refs", []): errors.append("explorer: stale video glossary references for " + fid)
    return errors


def validate(files: dict[str, bytes], *, prototype: bool = False, check_generated: bool = True) -> list[str]:
    """Validate one immutable snapshot, including renderer inputs and outputs."""
    errors = []
    view = None
    required = REQUIRED | (set() if prototype else PRODUCTION_REQUIRED)
    missing = required - files.keys()
    if missing: errors.append("missing maintained files: " + ", ".join(sorted(missing)))
    forwards = {"plectis/" + p for p in BUILD.plectis_paths_from(files.get("plectis-paths.txt", b""))}
    extra = sorted(p for p in files if p not in ALLOWED and p not in forwards and not p.startswith(ALLOWED_DIRS))
    if extra: errors.append("files outside the home page's roles: " + ", ".join(extra))
    claimed = sorted(p for p in files if p.startswith(PROJECT_PATHS))
    if claimed: errors.append("project websites belong to their own repositories: " + ", ".join(claimed))
    if any(Path(p).is_absolute() or ".." in Path(p).parts for p in files): return errors + ["snapshot paths must stay inside the repository"]
    if any(name not in files for name in ("sites.json", "glossary.json", "scripts/sites.schema.json", "scripts/glossary.schema.json")): return errors
    try:
        canonical = json.loads(files["sites.json"])
        glossary = json.loads(files["glossary.json"])
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return errors + ["catalogue JSON: " + str(exc)]
    with tempfile.TemporaryDirectory(prefix="plectis-check-") as temporary:
        root = Path(temporary)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        shape = CATALOGUE.validate(canonical, glossary,
            schema_path=root / "scripts/sites.schema.json",
            glossary_schema_path=root / "scripts/glossary.schema.json", asset_root=root)
        if shape: return errors + ["sites.json: " + item for item in shape]
        legacy = BUILD.validate_registry(CATALOGUE.adapt_v3_to_v2(canonical), exists=lambda p: p in files)
        if legacy: return errors + ["rendering view: " + item for item in legacy]
        try:
            view = site_view(root)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append("explorer data: " + str(exc))
        if check_generated and "scripts/build_hub.py" in files:
            # Builder, modules, config, transcripts, glossary and assets all
            # come from this snapshot, including when it is the Git index.
            command = [sys.executable, str(root / "scripts/build_hub.py"), "--check"]
            if prototype: command.append("--prototype")
            result = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=45)
            if result.returncode: errors.append("generated outputs: " + (result.stderr or result.stdout).strip())
    for name in ["all.html"] + list(front_pages(files)):
        if name in files: errors += validate_page(name, files[name].decode(), prototype=prototype)
    if "404.html" in files: errors += validate_page("404.html", files["404.html"].decode(), prototype=prototype, redirect=True)
    if "index.html" in files and view is not None:
        errors += validate_projection(view, canonical)
        if {t["id"] for t in view.get("terms", [])} != {t["id"] for t in glossary["terms"]}: errors.append("explorer: the view lost a glossary definition")
        errors += validate_landing(files, view)
        scripts = Page(files["index.html"].decode()).all("script")
        if not any((s.get("src") or "").split("?")[0].lstrip("/") == "assets/front.js" and "defer" in s for s in scripts): errors.append("index.html: load the deferred same-origin assets/front.js")
    if "all.html" in files:
        page = Page(files["all.html"].decode())
        hrefs = {a.get("href") for a in page.all("a")}
        for entity in canonical["projects"]:
            if "project-" + entity["slug"] not in page.ids: errors.append("all.html: missing project " + entity["slug"])
        for resource in canonical["resources"]:
            if resource["type"] == "video" and "film-" + resource["slug"] not in page.ids: errors.append("all.html: missing video " + resource["slug"])
            location = CATALOGUE.public_location(resource)
            if resource["id"] != "home" and location and location["url"] not in hrefs: errors.append("all.html: public resource not linked: " + resource["id"])
        for term in glossary["terms"]:
            if "term-" + term["id"] not in page.ids: errors.append("all.html: missing glossary term " + term["id"])
    for name, expected in (("catalogue.json", CATALOGUE.build_graph(canonical, glossary)), ("structured-data.jsonld", CATALOGUE.jsonld(canonical))):
        if name in files:
            try:
                if json.loads(files[name]) != expected: errors.append(name + ": out of date with canonical data")
            except ValueError: errors.append(name + ": invalid JSON")
    if not prototype:
        for name in sorted(forwards):
            if name not in files:
                errors.append(name + ": missing legacy forwarding page")
                continue
            page = Page(files[name].decode())
            refresh = [m for m in page.all("meta") if m.get("http-equiv", "").lower() == "refresh"]
            scripts = [(s.get("src") or "").split("?")[0] for s in page.all("script")]
            if len(refresh) != 1 or "/assets/redirect.js" not in scripts: errors.append(name + ": old Plectis routes must forward by refresh and redirect script")
        workflow = files.get(".github/workflows/public-site.yml", b"")
        for command in (b"python3 scripts/check_hub_site.py", b"python3 -m unittest"):
            if command not in workflow: errors.append("CI must run " + command.decode())
    if "robots.txt" in files:
        lines = [line.strip().lower() for line in files["robots.txt"].decode().splitlines() if line.strip() and not line.lstrip().startswith("#")]
        if lines != ["user-agent: *", "allow: /", "sitemap: https://wcook04.github.io/sitemap.xml"]: errors.append("robots.txt: preserve host-wide project crawling and the root sitemap")
    if "sitemap.xml" in files:
        try:
            tree = ET.fromstring(files["sitemap.xml"])
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            if tree.tag != ns + "sitemapindex" or HOME + "sitemap-home.xml" not in [n.text for n in tree.iter(ns + "loc")]: errors.append("sitemap.xml: preserve the home and project sitemap index")
        except ET.ParseError: errors.append("sitemap.xml: invalid XML")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", action="store_true", help="check staged paths and staged contents")
    parser.add_argument("--prototype", action="store_true", help="check the portable ZIP without production forwarding/CI files")
    args = parser.parse_args()
    try:
        errors = validate(snapshot(ROOT, index=args.index), prototype=args.prototype)
    except (ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(str(exc))
    if errors: raise SystemExit("\n".join(errors))
    print("Home page: canonical v3, complete static resources, valid explorer projection, generated outputs and hosting boundaries verified")


if __name__ == "__main__":
    main()
