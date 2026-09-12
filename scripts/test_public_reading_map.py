#!/usr/bin/env python3
"""Regression tests for public snapshot identity and route validation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_absolute_frontier import corpus_revision
from check_public_routes import BASE, destinations, read_destination, validate_body


class PublicReadingMapTests(unittest.TestCase):
    def test_current_and_historical_repository_names(self):
        for name in ('plectis-erdos', 'plectis-lean-erdos249-257'):
            with self.subTest(name=name):
                self.assertEqual(corpus_revision({'repository_maps': [
                    {'repository': name, 'revision': 'public-revision'},
                ]}), 'public-revision')

    def test_current_identity_wins_over_compatibility_map(self):
        self.assertEqual(corpus_revision({'repository_maps': [
            {'repository': 'plectis-lean-erdos249-257', 'revision': 'old'},
            {'repository': 'plectis-erdos', 'revision': 'current'},
        ]}), 'current')

    def test_missing_duplicate_and_empty_revisions_fail_clearly(self):
        for maps in ([], [{'repository': 'plectis-erdos'}], [
            {'repository': 'plectis-erdos', 'revision': 'one'},
            {'repository': 'plectis-erdos', 'revision': 'two'},
        ]):
            with self.subTest(maps=maps), self.assertRaises(ValueError):
                corpus_revision({'repository_maps': maps})

    def test_front_page_links_are_included_and_fragments_deduplicated(self):
        urls = destinations({'systems': [], 'items': []},
                            f'<a href="{BASE}docs/contact.html#email">Contact</a>'
                            f'<a href="{BASE}docs/contact.html#funding">Funding</a>')
        self.assertEqual(urls.count(BASE + 'docs/contact.html'), 1)
        self.assertIn(BASE + 'plectis-reviewer-brief.json', urls)

    def test_offline_directory_routes_and_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'index.html').write_text('front door')
            self.assertEqual(read_destination(BASE, BASE, root), b'front door')
            with self.assertRaises(FileNotFoundError):
                read_destination(BASE + 'missing.html', BASE, root)
            with self.assertRaises(ValueError):
                read_destination(BASE + '%2e%2e/outside', BASE, root)

    def test_pdf_and_json_error_documents_are_rejected(self):
        for url in ('papers/paper.pdf', 'plectis-reviewer-brief.json'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_body(BASE + url, b'<html>Not found</html>', {})

    def test_reading_graph_json_pointer_escapes(self):
        packet = {'a/b': {'~key': 'target'}, 'scholarly_corpus': {
            'papers': [{'paper_id': 'paper', 'source_embedded': True, 'body': 'text'}],
            'reading_graph': {'nodes': [{'pointer': '/a~1b/~0key'}]},
        }}
        raw = json.dumps(packet).encode()
        data = {'source_hashes': {'plectis-ai-reader-complete.json': hashlib.sha256(raw).hexdigest()},
                'systems': [{'paper_id': 'paper'}]}
        validate_body(BASE + 'plectis-ai-reader-complete.json', raw, data)
        with self.assertRaisesRegex(ValueError, 'handoff changed'):
            validate_body(BASE + 'plectis-ai-reader-complete.json', raw + b' ', data)


if __name__ == '__main__':
    unittest.main()
