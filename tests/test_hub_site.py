"""Regression checks for the home page and the repository that serves it."""
import importlib.util
import json
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hub_check", ROOT / "scripts/check_hub_site.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def current_files() -> dict[str, bytes]:
    return CHECK.snapshot(ROOT)


class HubTests(unittest.TestCase):
    def setUp(self):
        self.files = current_files()

    def errors(self):
        return CHECK.validate(self.files)

    def test_current_site_contract(self):
        self.assertEqual(self.errors(), [])

    def test_pages_must_match_the_registry(self):
        registry = json.loads(self.files["sites.json"])
        registry["sites"][0]["purpose"] = "Changed without rebuilding."
        self.files["sites.json"] = json.dumps(registry).encode()
        self.assertTrue(any("out of date" in error for error in self.errors()))

    def test_a_film_in_preparation_gets_no_invented_link(self):
        registry = json.loads(self.files["sites.json"])
        pending = next(f for f in registry["films"] if not f["youtube"])
        pending["youtube"] = "https://www.youtube.com/watch?v=AAAAAAAAAAA"
        self.files["sites.json"] = json.dumps(registry).encode()
        self.assertTrue(any("running time" in error or "missing" in error for error in self.errors()))

    def test_no_embedded_player(self):
        self.files["index.html"] = self.files["index.html"].replace(
            b'<main id="main">', b'<main id="main"><iframe src="https://www.youtube-nocookie.com/embed/x"></iframe>')
        self.assertTrue(any("embedded player" in error for error in self.errors()))

    def test_nothing_loads_from_another_host(self):
        self.files["index.html"] = re.sub(
            rb'src="/assets/theme-init\.js(\?v=[0-9a-f]+)?"', b'src="https://cdn.example.com/theme.js"',
            self.files["index.html"])
        self.assertTrue(any("another host" in error for error in self.errors()))

    def test_assets_carry_their_content_hash(self):
        index = self.files["index.html"].decode()
        for asset in ("/assets/hub.css", "/assets/family/family.css", "/assets/hub.js", "/assets/hub-map.js"):
            self.assertRegex(index, re.escape(asset) + r"\?v=[0-9a-f]{12}")

    def test_project_paths_stay_free(self):
        self.files["plectis-atlas/index.html"] = b"<!doctype html>"
        self.assertTrue(any("own repositories" in error for error in self.errors()))

    def test_every_website_is_linked(self):
        url = json.loads(self.files["sites.json"])["sites"][2]["url"].encode()
        self.files["index.html"] = self.files["index.html"].replace(b'href="' + url + b'"', b'href="#"')
        self.assertTrue(any("website not linked" in error for error in self.errors()))

    def test_every_repository_is_linked(self):
        href = json.loads(self.files["sites.json"])["repos"][1]["href"].encode()
        self.files["index.html"] = self.files["index.html"].replace(b'href="' + href + b'"', b'href="#"')
        self.assertTrue(any("repository not linked" in error for error in self.errors()))

    def test_a_film_in_preparation_is_not_linked(self):
        registry = json.loads(self.files["sites.json"])
        pending = next(f for f in registry["films"] if not f["youtube"])
        title = pending["title"].encode()
        self.assertIn(title, self.files["index.html"])
        self.files["index.html"] = self.files["index.html"].replace(
            b'<p class="film-words__title">' + title, b'<p class="film-words__title"><a href="#">' + title + b'</a>', 1)
        self.assertTrue(any("in preparation has no link" in error for error in self.errors()))

    def test_map_script_is_same_origin(self):
        self.files["index.html"] = re.sub(
            rb'src="/assets/hub-map\.js(\?v=[0-9a-f]+)?"', b'src="https://cdn.example.com/hub-map.js"',
            self.files["index.html"])
        errors = self.errors()
        self.assertTrue(any("another host" in error for error in errors))
        self.assertTrue(any("hub-map.js" in error for error in errors))

    def test_every_repository_is_placed_and_known(self):
        registry = json.loads(self.files["sites.json"])
        registry["sites"][0]["repos"].append("no-such-repository")
        registry["repos"].append({"id": "stray", "name": "stray", "href": "https://github.com/wcook04/stray",
                                  "description": "Placed nowhere."})
        problems = CHECK.BUILD.validate_registry(registry, exists=lambda rel: rel in self.files)
        self.assertTrue(any("unknown repository no-such-repository" in p for p in problems))
        self.assertTrue(any("on no website or tool: stray" in p for p in problems))

    def test_missing_page_forwards_old_plectis_addresses(self):
        self.files["404.html"] = self.files["404.html"].replace(b"/assets/redirect.js", b"/assets/other.js")
        self.assertTrue(any("redirect.js" in error for error in self.errors()))

    def test_host_rules_cannot_block_project_sites(self):
        self.files["robots.txt"] += b"Disallow: /plectis-atlas/\n"
        self.assertTrue(any("project crawling" in error for error in self.errors()))

    def test_index_uses_staged_contents_and_honours_deletions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            for name, content in self.files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            CHECK.git(root, "add", ".")
            CHECK.git(root, "-c", "user.name=Hub test", "-c", "user.email=hub@example.invalid",
                      "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
            broken = self.files["index.html"].replace(b"index, follow", b"noindex, follow")
            (root / "index.html").write_bytes(broken)
            CHECK.git(root, "add", "index.html")
            (root / "index.html").write_bytes(self.files["index.html"])
            self.assertEqual(CHECK.validate(CHECK.snapshot(root)), [])
            self.assertTrue(any("robots" in error for error in CHECK.validate(CHECK.snapshot(root, index=True))))
            CHECK.git(root, "add", "index.html")
            CHECK.git(root, "rm", "-q", "llms.txt")
            (root / "llms.txt").write_bytes(self.files["llms.txt"])
            self.assertEqual(CHECK.validate(CHECK.snapshot(root)), [])
            self.assertTrue(any("llms.txt" in error for error in CHECK.validate(CHECK.snapshot(root, index=True))))
            (root / "__pycache__").mkdir()
            (root / "__pycache__/ignored.pyc").write_bytes(b"cache")
            self.assertNotIn("__pycache__/ignored.pyc", CHECK.snapshot(root))


if __name__ == "__main__":
    unittest.main()
