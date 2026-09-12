#!/usr/bin/env python3
"""Structural regression tests for required front-door projection owners."""
import json
import unittest

from build_absolute_frontier import INDEX, SOURCE, project


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


if __name__ == '__main__':
    unittest.main()
