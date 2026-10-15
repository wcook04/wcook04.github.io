#!/usr/bin/env python3
"""Validate the retired host root, including the Git index when requested."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "https://wcook04.github.io/plectis/"
REQUIRED = {
    ".github/workflows/public-site.yml", ".gitignore", ".nojekyll",
    "index.html", "404.html", "README.md", "llms.txt", "agent-guide.md",
    "robots.txt", "sitemap.xml", "scripts/check_redirect_site.py",
    "tests/test_redirect_site.py",
}


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


class RedirectDocument(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.tags: list[str] = []
        self.meta: list[dict] = []
        self.links: list[dict] = []
        self.anchors: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attributes = dict(attrs)
        if tag == "meta":
            self.meta.append(attributes)
        elif tag == "link":
            self.links.append(attributes)
        elif tag == "a":
            self.anchors.append(attributes.get("href", ""))


def validate(files: dict[str, bytes]) -> list[str]:
    errors = []
    missing, extra = REQUIRED - files.keys(), files.keys() - REQUIRED
    if missing:
        errors.append("missing maintained files: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("files outside the retired-site roles: " + ", ".join(sorted(extra)))
    for name in ("index.html", "404.html"):
        if name not in files:
            continue
        page = RedirectDocument(files[name].decode())
        if not {"html", "head", "body", "main", "h1"} <= set(page.tags):
            errors.append(name + ": incomplete redirect document")
        if any(tag in page.tags for tag in ("script", "style", "img", "canvas", "video", "audio", "iframe", "object", "section")):
            errors.append(name + ": old page content or runtime assets must not return")
        canonical = [link.get("href") for link in page.links if link.get("rel") == "canonical"]
        if canonical != [CANONICAL] or page.anchors != [CANONICAL]:
            errors.append(name + ": canonical and ordinary link must point only to Plectis")
        if any(link.get("rel") not in {"canonical", "help"} for link in page.links):
            errors.append(name + ": redirect must not load external assets")
        refresh = [meta.get("content") for meta in page.meta if meta.get("http-equiv", "").lower() == "refresh"]
        if refresh != ["0; url=" + CANONICAL]:
            errors.append(name + ": immediate Plectis redirect required")
        robots = [meta.get("content", "") for meta in page.meta if meta.get("name") == "robots"]
        if len(robots) != 1 or set(robots[0].replace(" ", "").split(",")) != {"noindex", "follow"}:
            errors.append(name + ": noindex, follow required")
    if "robots.txt" in files:
        lines = [line.strip().lower() for line in files["robots.txt"].decode().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        if lines != ["user-agent: *", "allow: /", "sitemap: https://wcook04.github.io/sitemap.xml"]:
            errors.append("robots.txt: preserve host-wide project crawling and the root sitemap")
    if "sitemap.xml" in files:
        try:
            tree = ET.fromstring(files["sitemap.xml"])
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            if tree.tag != ns + "sitemapindex" or [node.text for node in tree.iter(ns + "loc")] != [CANONICAL + "sitemap.xml"]:
                errors.append("sitemap.xml: index the current Plectis sitemap, not the retired page")
        except ET.ParseError:
            errors.append("sitemap.xml: invalid XML")
    for name in ("llms.txt", "agent-guide.md", "README.md"):
        if name in files and (CANONICAL + "llms.txt").encode() not in files[name]:
            errors.append(name + ": current agent entry missing")
    if "agent-guide.md" in files:
        for project in ("plectis-atlas", "plectis-zenith"):
            if f"https://wcook04.github.io/{project}/llms.txt".encode() not in files["agent-guide.md"]:
                errors.append("agent-guide.md: separate project entry missing: " + project)
    workflow = files.get(".github/workflows/public-site.yml", b"")
    if b"python3 scripts/check_redirect_site.py" not in workflow:
        errors.append("CI must run the redirect and repository check")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", action="store_true", help="validate staged paths and staged file contents")
    args = parser.parse_args()
    errors = validate(snapshot(ROOT, index=args.index))
    if errors:
        raise SystemExit("\n".join(errors))
    print("Retired homepage: redirect, agent pointers, project crawl access and repository roles verified")


if __name__ == "__main__":
    main()
