#!/usr/bin/env python3
"""Structural regression tests for required front-door projection owners."""
import json
import re
import unittest

from build_absolute_frontier import INDEX, NUMBERS, SOURCE, project, render
from build_glossary_term_layer import link_terms


class AbsoluteFrontierStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.markup = INDEX.read_text()
        cls.payload = json.loads(SOURCE.read_text())

    def test_current_front_door_has_one_owner_for_every_projection(self):
        project(self.markup, self.payload)

    def test_missing_destination_is_rejected(self):
        broken = self.markup.replace('"lean-github":', '"lean-github-missing":', 1)
        with self.assertRaisesRegex(ValueError, 'lean-github destination'):
            project(broken, self.payload)

    def test_duplicate_destination_is_rejected(self):
        route = '"math-frontier": { to: "page", view: "frontier", host: "wcook04.github.io", path: "/plectis/maths/", href: "https://wcook04.github.io/plectis/maths/" }'
        broken = self.markup.replace(route, route + ',\n      ' + route, 1)
        with self.assertRaisesRegex(ValueError, 'expected 1 math-frontier destination, found 2'):
            project(broken, self.payload)

    def test_missing_frontier_boundary_is_rejected(self):
        broken = self.markup.replace('<span class="frontier-plate__boundary">', '<span class="frontier-plate__boundary-missing">', 1)
        with self.assertRaisesRegex(ValueError, 'expected 8 frontier plate boundaries, found 7'):
            project(broken, self.payload)

    def test_generated_reading_section_links_every_problem_preview(self):
        rendered = render(self.payload)
        links = re.findall(
            r'<a href="([^"]+)" data-dest="problem-(\d+)">Erdős #(\d+)</a>',
            rendered,
        )
        self.assertEqual(len(links), len(NUMBERS))
        self.assertEqual([int(dest) for _, dest, _ in links], NUMBERS)
        self.assertTrue(all(dest == label for _, dest, label in links))
        expected_hrefs = {str(row['problem']): row['page_href'] for row in self.payload['items']}
        self.assertTrue(all(href == expected_hrefs[dest] for href, dest, _ in links))

    def test_problem_controls_are_outside_the_decorative_preview(self):
        rendered = render(self.payload)
        self.assertNotIn('dest__frame', rendered)
        self.assertEqual(rendered.count('class="frontier"'), 1)
        for number in NUMBERS:
            self.assertEqual(rendered.count(f'<p data-dest="problem-{number}">'), 1)
            self.assertEqual(rendered.count(f'<a href="https://wcook04.github.io/plectis/maths/problems/erdos_{number}.html" data-dest="problem-{number}">'), 1)

    def test_mathematical_description_has_help_beside_its_unchanged_problem_link(self):
        problem = '<a href="maths/problems/erdos_1041.html" data-dest="problem-1041">Erdős #1041</a>'
        markup = ('<body><p>' + problem + ' <span class="frontier-topic">A lemniscate</span></p>'
                  '<span class="frontier-plate__handle">A lemniscate</span></body>')
        linked = link_terms(markup, [('lemniscate', 'lemniscate')],
                            {'lemniscate': 'glossary.html#glossary-lemniscate'})
        self.assertIn(problem, linked)
        self.assertIn('<span class="frontier-topic">A <a class="term" data-term="lemniscate"', linked)
        self.assertEqual(linked.count('data-term="lemniscate"'), 1)
        self.assertIn('<span class="frontier-plate__handle">A lemniscate</span>', linked)


if __name__ == '__main__':
    unittest.main()
