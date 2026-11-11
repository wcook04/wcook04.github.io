"""Bounded regressions for the v3 catalogue/explorer integration.

These checks protect source identity, live states, complete static access,
the important branching routes and staged-snapshot semantics. Visual layout
and motion are checked in the browser, not duplicated as DOM-shape tests.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hub_check", ROOT / "scripts/check_hub_site.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class HubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = CHECK.snapshot(ROOT)
        cls.canonical = json.loads(cls.files["sites.json"])
        cls.glossary = json.loads(cls.files["glossary.json"])
        cls.registry = CHECK.BUILD.load_registry(ROOT)
        cls.view = CHECK.site_view(ROOT)

    def test_v3_load_retains_the_canonical_record(self):
        self.assertEqual(self.registry["_canonical_v3"], self.canonical)
        self.assertEqual(self.registry["schema"], "will_cook_site_family_v2")
        self.assertEqual(len(self.registry["films"]), 38)
        self.assertEqual(len(self.registry["sites"]) + len(self.registry["projects"]), 14)

    def test_graph_and_structured_data_do_not_publish_preview_films(self):
        before = CHECK.BUILD.render_catalogue(self.registry, self.glossary)
        structured = CHECK.BUILD.structured_data(self.registry)
        old = CHECK.BUILD.PREVIEW
        try:
            CHECK.BUILD.PREVIEW = True
            self.assertEqual(CHECK.BUILD.render_catalogue(self.registry, self.glossary), before)
            self.assertEqual(CHECK.BUILD.structured_data(self.registry), structured)
        finally:
            CHECK.BUILD.PREVIEW = old
        videos = [n for n in json.loads(before)["nodes"] if n["type"] == "video"]
        canonical_videos = [r for r in self.canonical["resources"] if r["type"] == "video"]
        published = sum(bool(CHECK.CATALOGUE.public_location(r, "youtube")) for r in canonical_videos)
        self.assertEqual(sum(n["publicly_available"] for n in videos), published)
        self.assertEqual(len(videos), len(canonical_videos))

    def test_the_portable_package_matches_its_sources_and_links(self):
        self.assertEqual(CHECK.validate(self.files, prototype=True), [])

    def test_outputs_include_the_full_static_catalogue_and_metadata(self):
        outputs = CHECK.BUILD.outputs(self.registry, self.glossary, include_redirects=False)
        self.assertTrue({"index.html", "all.html", "catalogue.json", "structured-data.jsonld"}.issubset(outputs))
        static = CHECK.Page(outputs["all.html"])
        # One row per project page, and every project id the earlier page used is still an anchor.
        self.assertTrue({"project-" + p["slug"] for p in self.canonical["projects"]} <= set(static.ids))
        self.assertTrue({"project-" + e["slug"] for e in json.loads(self.files["front.json"])["entries"]} <= set(static.ids))
        self.assertEqual(sum(x.startswith("film-") for x in static.ids), 38)
        self.assertEqual(sum(x.startswith("term-") for x in static.ids), 61)
        self.assertFalse(any(path.startswith("plectis/") for path in outputs))

    def test_six_doors_cover_known_projects_and_all_nine_topic_aliases(self):
        self.assertEqual(len(self.view["config"]["doors"]), 6)
        self.assertEqual(len(self.view["config"]["topic_aliases"]), 9)
        self.assertEqual(CHECK.validate_projection(self.view, self.canonical), [])
        bad = deepcopy(self.view)
        bad["config"]["doors"][0]["projects"].append("missing-project")
        self.assertTrue(any("unknown project" in error for error in CHECK.validate_projection(bad, self.canonical)))

    def test_every_video_website_and_repository_is_reached_from_a_question(self):
        # A question page links each project; a project page lists every video,
        # website route and repository the project has (explore.js everything()).
        doors = self.view["config"]["doors"]
        reached = {pid for d in doors for pid in d["projects"]}
        self.assertEqual(reached, set(self.view["projects"]))
        films = {fid for pid in reached for fid in self.view["projects"][pid]["films"]}
        intro = set(self.registry["intro"]["films"])
        self.assertEqual(films | intro, set(self.view["films"]))
        repos = {r["id"] for pid in reached for r in self.view["projects"][pid]["repo_records"]}
        contributed = {c["repo"] for c in self.registry["contributions"]}
        listed = {r["id"] for r in self.registry["repos"]}
        self.assertEqual(listed - repos - contributed, set())
        for pid in reached:
            p = self.view["projects"][pid]
            if pid in {"agent-trace", "one-checkout", "safety-core", "codemap", "funnel", "narration-ir"}:
                continue
            self.assertTrue(p.get("url"), pid + " has no website address")
        # Each card's short video comes first and leads to a full video.
        for d in doors:
            for pid in d["projects"]:
                shorts = [self.view["films"][f] for f in self.view["projects"][pid]["films"]
                          if self.view["films"][f]["format"] == "short"]
                self.assertTrue(shorts, pid + " has no short video")
                self.assertTrue(any(s.get("leads_to") for s in shorts), pid + ": no short video leads to a full video")

    def test_a_planned_video_cannot_gain_a_fake_playable_url_in_the_view(self):
        bad = deepcopy(self.view)
        canonical = deepcopy(self.canonical)
        planned = next(r for r in canonical["resources"] if r["id"] == "film:short-quartic")
        youtube = next(p for p in planned["publications"] if p["platform"] == "youtube")
        youtube.update(state="in_preparation", url=None)
        bad["films"]["short-quartic"]["youtube"] = "https://www.youtube.com/watch?v=AAAAAAAAAAA"
        self.assertTrue(any("invented or changed public video URL" in error
                            for error in CHECK.validate_projection(bad, canonical)))

    def test_a_dropped_continuation_is_detected(self):
        bad = deepcopy(self.view)
        bad["films"]["short-quartic"]["leads_to"] = []
        self.assertTrue(any("omitted or changed continuation" in error
                            for error in CHECK.validate_projection(bad, self.canonical)))

    def test_static_access_cannot_drop_a_public_resource(self):
        files = dict(self.files)
        resource = next(r for r in self.canonical["resources"] if r["id"] == "paper:quartic-original")
        url = CHECK.CATALOGUE.public_location(resource)["url"]
        files["all.html"] = files["all.html"].replace(('href="' + url + '"').encode(), b'href="#removed"')
        self.assertTrue(any("public resource not linked: paper:quartic-original" in error
                            for error in CHECK.validate(files, prototype=True, check_generated=False)))

    def test_remote_assets_and_embedded_players_are_rejected(self):
        page = self.files["index.html"].decode().replace("</main>", '<iframe src="https://example.org/player"></iframe></main>')
        self.assertIn('src="/assets/front.js?', page)
        page = page.replace('src="/assets/front.js?', 'src="https://example.org/front.js?')
        errors = CHECK.validate_page("index.html", page, prototype=True)
        self.assertTrue(any("embedded player" in error for error in errors))
        self.assertTrue(any("another host" in error for error in errors))

    def test_no_page_frames_a_player(self):
        page = self.files["index.html"].decode()
        self.assertEqual(CHECK.validate_page("index.html", page, prototype=True), [])
        for name in ("index.html", "all.html", "work/zenith/index.html"):
            framed = self.files[name].decode().replace("frame-src 'none'", "frame-src https://www.youtube.com")
            self.assertTrue(any("frame-src 'none'" in error
                                for error in CHECK.validate_page(name, framed, prototype=True)))

    def test_home_and_project_pages_reach_every_current_video_website_and_repository(self):
        self.assertEqual(CHECK.validate_landing(self.files, self.view), [])
        short = self.view["films"]["short-quartic"]["youtube"].encode()
        broken = {name: (data.replace(short, b"#gone") if name.endswith(".html") else data) for name, data in self.files.items()}
        self.assertTrue(any("current video not linked: short-quartic" in error for error in CHECK.validate_landing(broken, self.view)))
        extra = dict(self.files)
        extra["assets/front/loops/unused-s.mp4"] = b""
        self.assertTrue(any("no page uses" in error for error in CHECK.validate_landing(extra, self.view)))
        # The map is a list of links without its script: fifteen tiles, each to a project page that exists,
        # and no picture depends on YouTube (posters, plates and loops are this repository's own files).
        page = self.files["index.html"].decode()
        parsed = CHECK.Page(page)
        tiles = [a.get("href") for a in parsed.all("a") if a.get("class") == "tile"]
        self.assertEqual(len(tiles), 15)
        self.assertTrue(all(href.lstrip("/") + "index.html" in self.files for href in tiles))
        self.assertNotIn("ytimg", page)
        self.assertNotIn("youtube.com/embed", page)

    def test_every_video_has_a_page_and_a_stop_to_arrive_at(self):
        front = json.loads(self.files["front.json"])
        self.assertEqual(len(front["videos"]), 24)
        missing = dict(self.files)
        del missing["work/agent-trace/index.html"]
        self.assertTrue(any("page that does not exist" in error for error in CHECK.validate_landing(missing, self.view)))
        moved = dict(self.files)
        moved["work/funnel/index.html"] = moved["work/funnel/index.html"].replace(b'id="long"', b'id="elsewhere"')
        self.assertTrue(any("missing stop" in error for error in CHECK.validate_landing(moved, self.view)))
        # Old addresses still land: every project the earlier page listed keeps its anchor on the home page.
        home = CHECK.Page(self.files["index.html"].decode())
        for pid in self.view["projects"]:
            self.assertIn("p-" + pid, home.ids)

    def test_a_stray_brace_in_the_stylesheet_is_caught(self):
        sheet = self.files["assets/front.css"].decode()
        self.assertEqual(CHECK.stylesheet_errors("assets/front.css", sheet), [])
        # A stray closing brace once made browsers drop the rule after it: the page-to-page transition.
        broken = sheet.replace("@view-transition { navigation: auto; }", "}\n@view-transition { navigation: auto; }", 1)
        self.assertTrue(any("never opened" in error for error in CHECK.stylesheet_errors("assets/front.css", broken)))
        self.assertTrue(any("@view-transition" in error
                            for error in CHECK.stylesheet_errors("assets/front.css", sheet.replace("@view-transition { navigation: auto; }", "", 1))))

    def test_host_wide_crawling_and_project_ownership_are_preserved(self):
        files = dict(self.files)
        files["robots.txt"] += b"Disallow: /plectis-atlas/\n"
        files["plectis-atlas/index.html"] = b"<h1>Wrong repository</h1>"
        errors = CHECK.validate(files, prototype=True, check_generated=False)
        self.assertTrue(any("project crawling" in error for error in errors))
        self.assertTrue(any("own repositories" in error for error in errors))

    def test_index_reads_staged_bytes_and_staged_deletions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "sites.json").write_text("staged catalogue")
            (root / "removed.txt").write_text("staged then removed")
            CHECK.git(root, "add", "sites.json", "removed.txt")
            (root / "sites.json").write_text("unstaged repair")
            CHECK.git(root, "rm", "--cached", "--", "removed.txt")
            staged = CHECK.snapshot(root, index=True)
            working = CHECK.snapshot(root)
            self.assertEqual(staged["sites.json"], b"staged catalogue")
            self.assertEqual(working["sites.json"], b"unstaged repair")
            self.assertNotIn("removed.txt", staged)
            self.assertIn("removed.txt", working)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "Git checkout"):
                CHECK.snapshot(Path(temporary), index=True)

    @unittest.skipUnless(shutil.which("node"), "Node is optional; needed for pure navigation checks")
    def test_navigation_preserves_reader_result_shared_and_deep_routes(self):
        script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const M = require(process.argv[1]);
const d = JSON.parse(fs.readFileSync(0,'utf8'));
for (const id of ['short-sk-website','short-quartic-reader','short-proof-reader']) {
  assert.deepEqual(M.onward(d,d.films[id]).map(f=>f.id),['long-lean-readers']);
}
assert.equal(Object.values(d.films).reduce((n,f)=>n+M.onward(d,f).length,0),18);
const multiple=JSON.parse(JSON.stringify(d));
multiple.films['short-quartic'].leads_to.push('long-funnel');
assert.equal(M.onward(multiple,multiple.films['short-quartic']).length,2);
assert.equal(M.lead(d,M.resolve(d,'#p=quartic&film=short-quartic')).id,'short-quartic');
assert.equal(M.lead(d,M.resolve(d,'#p=quartic&via=proofs')).id,'short-quartic-reader');
for (const [pid,expected] of [['quartic','short-quartic-reader'],['lean-exposition','short-sk-website'],['proof-reader','short-proof-reader']]) {
  const state=M.resolve(d,M.routeForFilm(d,pid,'long-lean-readers'));
  assert.equal(state.id,pid); assert.equal(state.via,'proofs'); assert.equal(M.lead(d,state).id,expected);
}
for (const [pid,fid,taster] of [['quartic','quartic-query','short-quartic'],['lean-exposition','sk-no-gap','short-sk-no-gap']]) {
  const state=M.resolve(d,M.routeForFilm(d,pid,fid));
  assert.equal(state.via,'proofs'); assert.equal(M.lead(d,state).id,taster);
}
assert.equal(M.resolve(d,'#t=quantum').id,'quartic');
assert.equal(M.resolve(d,'#d=testing').view,'door'); assert.equal(M.resolve(d,'#d=research').id,'maths');
for (const alias of Object.keys(d.config.topic_aliases)) assert.notEqual(M.resolve(d,'#t='+alias).view,'home');
for (const [name,id] of [['Proof Reader','proof-reader'],['Lean Exposition','lean-exposition'],['Plectis Mathematics','maths'],['Code Map','codemap']]) {
  assert(M.search(d,name).some(p=>p.id===id));
}
assert.equal(M.published(d.films['short-quartic']),true);
assert.equal(M.earlier(d,d.films['introduction']),true);
assert.equal(M.earlier(d,d.films['introduction-v2']),true);
process.stdout.write('shared/result/deep routes, all continuations, aliases and live states passed\n');
'''
        result = subprocess.run(["node", "-e", script, str(ROOT / "assets/explore-model.js")],
                                input=json.dumps(self.view), text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
