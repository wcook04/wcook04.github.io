"""Regression checks for retiring the root site without blocking its projects."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("redirect_check", ROOT / "scripts/check_redirect_site.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class RedirectTests(unittest.TestCase):
    def setUp(self):
        self.files = {name: (ROOT / name).read_bytes() for name in CHECK.REQUIRED}

    def test_current_site_contract(self):
        self.assertEqual(CHECK.validate(self.files), [])

    def test_retired_assets_cannot_return(self):
        self.files["assets/old-homepage.jpg"] = b"old"
        self.assertTrue(any("outside" in error for error in CHECK.validate(self.files)))

    def test_redirect_cannot_become_a_portfolio_again(self):
        self.files["index.html"] = self.files["index.html"].replace(b"<main>", b"<main><canvas></canvas>")
        self.assertTrue(any("old page content" in error for error in CHECK.validate(self.files)))

    def test_no_javascript_fallback_link_is_required(self):
        self.files["index.html"] = self.files["index.html"].replace(
            b'href="https://wcook04.github.io/practical-formal-verification/">Open',
            b'href="/old-homepage.html">Open')
        self.assertTrue(any("ordinary link" in error for error in CHECK.validate(self.files)))

    def test_host_rules_cannot_block_project_sites(self):
        self.files["robots.txt"] += b"Disallow: /plectis-atlas/\n"
        self.assertTrue(any("project crawling" in error for error in CHECK.validate(self.files)))

    def test_sitemap_cannot_advertise_retired_homepage(self):
        self.files["sitemap.xml"] = self.files["sitemap.xml"].replace(
            b"https://wcook04.github.io/practical-formal-verification/sitemap.xml", b"https://wcook04.github.io/")
        self.assertTrue(any("retired page" in error for error in CHECK.validate(self.files)))

    def test_index_uses_staged_contents_and_honours_deletions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            for name, content in self.files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            CHECK.git(root, "add", ".")
            CHECK.git(root, "-c", "user.name=Redirect test", "-c", "user.email=redirect@example.invalid", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
            broken = self.files["index.html"].replace(b"noindex, follow", b"index, follow")
            (root / "index.html").write_bytes(broken)
            CHECK.git(root, "add", "index.html")
            (root / "index.html").write_bytes(self.files["index.html"])
            self.assertEqual(CHECK.validate(CHECK.snapshot(root)), [])
            self.assertTrue(any("noindex" in error for error in CHECK.validate(CHECK.snapshot(root, index=True))))
            CHECK.git(root, "add", "index.html")
            CHECK.git(root, "rm", "llms.txt")
            (root / "llms.txt").write_bytes(self.files["llms.txt"])
            self.assertEqual(CHECK.validate(CHECK.snapshot(root)), [])
            self.assertTrue(any("llms.txt" in error for error in CHECK.validate(CHECK.snapshot(root, index=True))))
            (root / "assets").mkdir()
            (root / "assets/old-homepage.jpg").write_bytes(b"old")
            CHECK.git(root, "add", "assets/old-homepage.jpg")
            self.assertTrue(any("outside" in error for error in CHECK.validate(CHECK.snapshot(root, index=True))))
            (root / "__pycache__").mkdir()
            (root / "__pycache__/ignored.pyc").write_bytes(b"cache")
            self.assertNotIn("__pycache__/ignored.pyc", CHECK.snapshot(root))


if __name__ == "__main__":
    unittest.main()
