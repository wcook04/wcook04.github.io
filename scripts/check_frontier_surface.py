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
OG_FRONTIER = ROOT / "assets" / "og-frontier.svg"
SNAPSHOT = "11a318711096671ce1c00257a55fe5d7b9963864"
PROBLEMS = ("68", "243", "249", "251", "257", "269", "1041", "1049")
FRONTIER_LABELS = {
    "68": "exact cofinal-divisibility equivalence",
    "243": "exact tail-state defect identity",
    "249": "conditional cofinal 9/10 prime-tail escape",
    "251": "prime/gap summation-by-parts identity",
    "257": "hereditary strict Mersenne-tail inequality",
    "269": "three-prime running-LCM structure",
    "1041": "ray-separation obstruction",
    "1049": "rational-base cleared-tail recurrence",
}
PROBLEM_TOPICS = {
    "68": "Factorial denominator.",
    "243": "Reciprocal tails.",
    "249": "Binary totient series.",
    "251": "Prime-gap dyadic series.",
    "257": "Infinite exponent supports.",
    "269": "Three-prime running LCMs.",
    "1041": "Short lemniscate connections.",
    "1049": "Lambert series at rational bases.",
}
OG_FRONTIER_LABELS = (
    "cofinal divisibility",
    "tail-state defect",
    "prime-tail escape",
    "prime-gap summation",
    "strict Mersenne tail",
    "running-LCM structure",
    "ray separation",
    "rational-base tail",
)
OG_IMAGE_ALT = (
    "Eight open Erdős problems: factorial denominators, reciprocal tails, "
    "binary totient, prime-gap dyadics, Mersenne supports, running LCMs, "
    "lemniscate paths, and rational Lambert. All eight remain open."
)
UNFURL_DESCRIPTION = (
    "Eight open Erdős problems: factorial denominators; reciprocal tails; "
    "binary totient; prime-gap dyadics; Mersenne supports; running LCMs; "
    "lemniscate paths; rational Lambert. All remain open."
)
FRONTIER_SHEET_ANCHORS = {
    "68": (
        "ErdosProblems.Erdos68.irrational_factorialGapSeries_iff_cofinal_strictFacTopRat_misses",
        "Irrationality of the factorial-denominator series.",
    ),
    "243": (
        "ErdosProblems.Erdos243.nextTailState_eq_sub_centered",
        "The unrestricted problem.",
    ),
    "249": (
        "ErdosProblems.Erdos249.irrational_totient_series_of_naturalPrimeTailOrbitStrictGap",
        "The strict prime-tail orbit gap.",
    ),
    "251": (
        "ErdosProblems.Erdos251.dyadicPartialSumQ_eq_start_add_differences",
        "The target irrationality.",
    ),
    "257": (
        "ErdosProblems.Erdos257.selectedMersenneTail_lt_weight",
        "Universal irrationality, or irrationality for any new infinite support.",
    ),
    "269": (
        "ErdosProblems.Erdos269.smoothPrefixLcm_eq_threePrimeHeight",
        "Irrationality or transcendence in any three-prime case.",
    ),
    "1041": (
        "ErdosProblems.Erdos1041.newtonFlow_value_hasDerivAt",
        "Erdős Problem 1041 in unrestricted degree.",
    ),
    "1049": (
        "ErdosProblems.Erdos1049.rationalBaseClearedTailQ_succ",
        "Irrationality at 3/2, or for any rational base.",
    ),
}


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


def frontier_plate(text: str) -> str:
    start = text.find('<span class="shot__frontier"')
    end = text.find('<!-- One portrait sheet per public problem.', start)
    require(start >= 0 and end >= 0, "missing or unterminated desktop frontier plate")
    return text[start:end]


def main() -> int:
    text = INDEX.read_text(encoding="utf-8")
    og_frontier = OG_FRONTIER.read_text(encoding="utf-8")
    plate = frontier_plate(text)
    require("<h1>Eight open<br>Erd&#337;s problems</h1>" in text, "masthead no longer leads with the mathematical programme")
    require("Will Cook &middot; checkable frontier" in text, "masthead lost authorship")
    require(">Eight-problem frontier<" in text, "primary entry label lost the portfolio")
    primary_route = (
        "https://github.com/wcook04/plectis-lean-erdos249-257/"
        f"blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md"
    )
    require(primary_route in text, "primary frontier entry no longer opens the programme map")
    require(" / snapshot 11a3187 · docs/EXTERNAL_VERIFICATION.md" in text, "destination plate no longer discloses its evidence snapshot")
    require('<template id="archived-plate">' in text, "archived plate regained a live delivery path")
    require("Eight formally checked frontiers" in text, "opening lost the frontier")
    require("Hover or focus a number for its question, cleared frontier, and exact open boundary." in text, "desktop portrait cue missing")
    require("Open a number for its question and evidence record." in text, "narrow-screen frontier route missing")
    require("none is a solution claim" in text, "open-problem boundary missing")
    require("not human mathematical peer review" in text, "review boundary missing")
    require("Plectis is the public site for the private work system behind it." in text, "public/private hierarchy missing from the opening")
    require("The public site for the private work system:" in text, "Plectis route no longer distinguishes public site from private system")
    require("Comparator rechecks selected propositions" in text, "Comparator scope missing")
    require("it does not assess papers, citations, intended meaning, novelty or significance" in text, "Comparator limit missing")
    require("not universal #257" in text, "representative-check boundary missing")
    require("It returns the statement, exact declaration, Comparator interface, paper, and boundary:" in text, "representative replay no longer explains its evidence route")
    require('frame.setAttribute("data-view", view);' in text, "destination frame no longer switches its view")
    require('if (view === "problem") frame.setAttribute("data-problem", d.problem);' in text, "destination frame no longer selects a portrait sheet")
    require('document.addEventListener("focusin", function (ev) {' in text, "frontier sheets no longer have a keyboard route")
    require("ALL EIGHT REMAIN OPEN" in og_frontier, "share card lost the open-problem boundary")
    require("EIGHT CHECKED FRONTIERS" in og_frontier, "share card lost its frontier heading")
    for label in OG_FRONTIER_LABELS:
        require(label in og_frontier, f"share card no longer names {label}")
    require(OG_IMAGE_ALT in text, "share-image alt text lost the eight-subject programme")
    require(UNFURL_DESCRIPTION in text, "link-unfurl description lost the eight-subject programme")

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
        require(
            FRONTIER_LABELS[number].lower() in route.group(1).lower(),
            f"#{number} visible frontier heading drifted",
        )
        require(
            PROBLEM_TOPICS[number] in route.group(1),
            f"#{number} visible entry no longer names its mathematical subject",
        )
        require(
            FRONTIER_LABELS[number].lower() in plate.lower(),
            f"#{number} desktop frontier heading drifted",
        )
        following = PROBLEMS[index + 1] if index + 1 < len(PROBLEMS) else None
        sheet = problem_sheet(text, number, following)
        require("problem-sheet__question" in sheet, f"#{number} sheet lacks a question")
        require("problem-sheet__section--open" in sheet, f"#{number} sheet lacks its open boundary")
        require('problem-sheet__status">Open<' in sheet, f"#{number} sheet lost open status")
        if number in FRONTIER_SHEET_ANCHORS:
            declaration, boundary = FRONTIER_SHEET_ANCHORS[number]
            require(declaration in sheet, f"#{number} sheet no longer names its cleared declaration")
            require(boundary in sheet, f"#{number} sheet no longer preserves its exact open boundary")

    paper_sentence = "Eight problem papers &mdash; " + ", ".join(
        f"#{number}" for number in PROBLEMS[:-1]
    ) + f" and #{PROBLEMS[-1]} &mdash;"
    require(paper_sentence in text, "paper route no longer names all eight problems")
    require("sit inside Plectis&rsquo;s 13-paper catalogue" in text, "paper route lost its catalogue context")
    print("frontier surface: 8 pinned routes, 8 portrait sheets, and all-eight paper route: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"frontier surface: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
