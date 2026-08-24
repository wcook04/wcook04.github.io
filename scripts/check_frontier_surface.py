#!/usr/bin/env python3
"""Keep the root front door legible as an eight-problem programme.

This is deliberately a cheap, static release guard.  It checks the root page's
own promises and its immutable source links; it neither proves mathematics nor
substitutes for the Lean repository's release checks.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SNAPSHOT = "11a318711096671ce1c00257a55fe5d7b9963864"
PROBLEMS = ("68", "243", "249", "251", "257", "269", "1041", "1049")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def problem_sheet(text: str, number: str, following: str | None) -> str:
    start = text.find(f'<span class="shot__problem" data-problem="{number}"')
    require(start >= 0, f"missing portrait sheet for #{number}")
    end = text.find(
        f'<span class="shot__problem" data-problem="{following}"', start
    ) if following else text.find('<p class="dest__hint">', start)
    require(end >= 0, f"unterminated portrait sheet for #{number}")
    return text[start:end]


def main() -> int:
    text = INDEX.read_text(encoding="utf-8")
    require("Eight open Erd&#337;s problems" in text, "masthead lost the programme")
    require(">Eight-problem frontier<" in text, "primary entry label lost the portfolio")
    primary_route = (
        "https://github.com/wcook04/plectis-lean-erdos249-257/"
        f"blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md"
    )
    require(primary_route in text, "primary frontier entry no longer opens the programme map")
    require("main.fold > picture { display: none; }" in text, "decorative plate returned to the reading surface")
    require("<picture hidden>" in text and 'loading="lazy"' in text, "archived plate regained eager delivery")
    require("Eight formally checked frontiers" in text, "opening lost the frontier")
    require("none is a solution claim" in text, "open-problem boundary missing")
    require("not human mathematical peer review" in text, "review boundary missing")
    require("Comparator rechecks selected propositions" in text, "Comparator scope missing")
    require("it does not assess papers, citations, intended meaning, novelty or significance" in text, "Comparator limit missing")
    require("not universal #257" in text, "representative-check boundary missing")
    require("conditional cofinal 9/10 prime-tail escape" in text, "#249 heading drifted from the pinned frontier")
    require("prime/gap summation-by-parts identity" in text, "#251 heading drifted from the pinned frontier")
    require("hereditary strict Mersenne-tail inequality" in text, "#257 heading drifted from the pinned frontier")

    lean_links = re.findall(
        r'https://github\.com/wcook04/plectis-lean-erdos249-257/(?:tree|blob)/[^"\s<]+',
        text,
    )
    require(lean_links, "front door has no Lean evidence links")
    for link in lean_links:
        require(
            f"/{SNAPSHOT}" in link,
            f"floating or mismatched Lean evidence link: {link}",
        )

    for index, number in enumerate(PROBLEMS):
        expected_url = (
            "https://github.com/wcook04/plectis-lean-erdos249-257/"
            f"blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md#programme-{number}"
        )
        route = re.search(
            rf'<p role="listitem" data-dest="problem-{number}">(.*?)</p>', text
        )
        require(route is not None, f"missing accessible frontier entry for #{number}")
        require(expected_url in route.group(1), f"#{number} does not use the pinned packet")
        following = PROBLEMS[index + 1] if index + 1 < len(PROBLEMS) else None
        sheet = problem_sheet(text, number, following)
        require("problem-sheet__question" in sheet, f"#{number} sheet lacks a question")
        require("problem-sheet__section--open" in sheet, f"#{number} sheet lacks its open boundary")
        require('problem-sheet__status">Open<' in sheet, f"#{number} sheet lost open status")

    paper_sentence = "Eight problem papers &mdash; " + ", ".join(
        f"#{number}" for number in PROBLEMS[:-1]
    ) + f" and #{PROBLEMS[-1]} &mdash;"
    require(paper_sentence in text, "paper route no longer names all eight problems")
    print("frontier surface: 8 pinned routes, 8 portrait sheets, and all-eight paper route: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"frontier surface: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
