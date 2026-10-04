#!/usr/bin/env python3
"""Regression tests for public snapshot identity and route validation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_absolute_frontier import NUMBERS, corpus_revision, snapshot
from check_public_routes import BASE, destinations, group_destinations, read_destination, validate_body


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

    def orientation_snapshot(self, system_ids):
        papers = [{'paper_id': f'erdos{n}', 'title': f'Problem {n}',
                   'public_pdf_url': f'{BASE}papers/erdos{n}.pdf',
                   'source_embedded': True, 'body': 'Manuscript'} for n in NUMBERS]
        papers += [{'paper_id': name, 'title': name,
                    'public_pdf_url': f'{BASE}papers/{name}.pdf',
                    'source_embedded': True, 'body': 'Manuscript'} for name in system_ids]
        packet = {'scholarly_corpus': {'papers': papers, 'repository_maps': [
            {'repository': 'plectis-erdos', 'revision': 'current'}]}}
        problems = {'problems': [{'erdos_number': n, 'short_title': str(n),
                    'question': 'Question', 'status': 'open',
                    'paper': {'paper_id': f'erdos{n}'}} for n in NUMBERS]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'lean').mkdir()
            (root / 'plectis-ai-reader-complete.json').write_text(json.dumps(packet))
            (root / 'lean/problems.json').write_text(json.dumps(problems))
            return snapshot(root)

    def test_retired_orientation_paper_is_not_required_or_republished(self):
        current = 'claim-faithful-publication-systems'
        for names in ([current], [current, 'open-source-mathematics-strategy']):
            with self.subTest(names=names):
                payload = self.orientation_snapshot(names)
                self.assertEqual([row['paper_id'] for row in payload['systems']], [current])
                self.assertEqual([row['problem'] for row in payload['items']], NUMBERS)

    def test_current_orientation_paper_remains_required(self):
        with self.assertRaisesRegex(ValueError, 'missing current orientation papers'):
            self.orientation_snapshot(['open-source-mathematics-strategy'])

    def test_front_page_links_retain_fragments_and_fetch_documents_once(self):
        urls = destinations({'systems': [], 'items': []},
                            f'<a href="{BASE}docs/contact.html#email">Contact</a>'
                            f'<a href="{BASE}docs/contact.html#funding">Funding</a>')
        grouped = group_destinations(urls)
        self.assertEqual(grouped[BASE + 'docs/contact.html'], {'email', 'funding'})
        self.assertIn(BASE + 'plectis-reviewer-brief.json', urls)

    def test_empty_and_non_html_documents_are_rejected(self):
        for body in (b'', b' ', b'not found', b'{}', b'<html><head></head></html>'):
            with self.subTest(body=body), self.assertRaisesRegex(ValueError, 'HTML document'):
                validate_body(BASE + 'docs/papers.html', body, {})

    def test_html_fragments_require_ids_or_legacy_named_anchors(self):
        body = b'<html><body><h1 id="a b">Heading</h1><a name="legacy"></a></body></html>'
        validate_body(BASE + '#a%20b', body, {}, fragments={'legacy'})
        validate_body(BASE + '#:~:text=Heading', body, {})
        with self.assertRaisesRegex(ValueError, 'missing HTML anchors: absent'):
            validate_body(BASE, body, {}, fragments={'legacy', 'absent'})

    def test_reviewer_brief_requires_real_reading_sections(self):
        packet = {'schema': 'plectis_reviewer_source_hologram_v3',
                  'artifact_kind': 'plectis_reviewer_decision_brief',
                  'read_in_this_order': ['execution_boundary'],
                  'execution_boundary': {'meaning': 'Reading does not run checks'}}
        url = BASE + 'plectis-reviewer-brief.json'
        validate_body(url, json.dumps(packet).encode(), {})
        for invalid in ({}, [], {**packet, 'read_in_this_order': []},
                        {**packet, 'execution_boundary': {}},
                        {**packet, 'read_in_this_order': ['missing']}):
            with self.subTest(packet=invalid), self.assertRaises(ValueError):
                validate_body(url, json.dumps(invalid).encode(), {})

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
