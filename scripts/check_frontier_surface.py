#!/usr/bin/env python3
"""Keep the root front door legible as an eight-problem programme.

This is deliberately a cheap, static release guard.  It checks the root page's
own promises and its immutable source links; it neither proves mathematics nor
substitutes for the Lean repository's release checks.
"""

from __future__ import annotations

import re
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
OG_FRONTIER = ROOT / "assets" / "og-frontier.svg"
SITEMAP = ROOT / "sitemap.xml"
ROBOTS = ROOT / "robots.txt"
ABSOLUTE_FRONTIER_SOURCE = ROOT / "data" / "absolute-frontier.json"
TERM_ANCHOR = re.compile(
    r'<a class="term(?: is-again)?" data-term="[^"]*" href="[^"]*">(?P<label>.*?)</a>',
    re.DOTALL,
)
SNAPSHOT = json.loads(ABSOLUTE_FRONTIER_SOURCE.read_text(encoding="utf-8"))[
    "public_source_commit"
]
if not isinstance(SNAPSHOT, str) or re.fullmatch(r"[0-9a-f]{40}", SNAPSHOT) is None:
    raise ValueError("absolute-frontier public_source_commit must be a full commit")
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
    "68": "Factorial denominator",
    "243": "Reciprocal tails",
    "249": "Binary totient series",
    "251": "Prime-gap dyadic series",
    "257": "Infinite exponent supports",
    "269": "Three-prime running LCMs",
    "1041": "Short lemniscate connections",
    "1049": "Lambert series at rational bases",
}
PROBLEM_PAPERS = {
    "68": "erdos-68-factorial-denominator-irrationality.pdf",
    "243": "erdos-243-reciprocal-tail-rigidity.pdf",
    "249": "erdos-249-binary-totient-series.pdf",
    "251": "erdos-251-prime-gap-dyadic-series.pdf",
    "257": "erdos-257-mersenne-support-subseries.pdf",
    "269": "erdos-269-three-prime-running-lcm.pdf",
    "1041": "erdos-1041-lemniscate-newton-flow.pdf",
    "1049": "erdos-1049-rational-base-lambert.pdf",
}
ACCESSIBLE_QUESTION_MARKERS = {
    "1049": "For which rational t &gt; 1 is F(t)",
}
OG_FRONTIER_LABELS = (
    "cofinal divisibility",
    "tail-state defect",
    "conditional escape",
    "prime-gap summation",
    "strict Mersenne tail",
    "three-prime LCMs",
    "ray separation",
    "rational-base tail",
)
OG_IMAGE_ALT = (
    "Eight open Erdős problems: factorial denominators, reciprocal tails, "
    "binary totient, prime-gap dyadics, Mersenne supports, three-prime LCMs, "
    "lemniscate paths, and rational Lambert. All eight remain open."
)
UNFURL_DESCRIPTION = (
    "Mathematics written with AI and checked by Lean, on eight open Erdős problems. "
    "All eight problems remain open."
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


PAPER_PDF_FOR = {
    "68": "https://wcook04.github.io/plectis/papers/erdos-68-factorial-denominator-irrationality.pdf",
    "243": "https://wcook04.github.io/plectis/papers/erdos-243-reciprocal-tail-rigidity.pdf",
    "249": "https://wcook04.github.io/plectis/papers/erdos-249-binary-totient-series.pdf",
    "251": "https://wcook04.github.io/plectis/papers/erdos-251-prime-gap-dyadic-series.pdf",
    "257": "https://wcook04.github.io/plectis/papers/erdos-257-mersenne-support-subseries.pdf",
    "269": "https://wcook04.github.io/plectis/papers/erdos-269-three-prime-running-lcm.pdf",
    "1041": "https://wcook04.github.io/plectis/papers/erdos-1041-lemniscate-newton-flow.pdf",
    "1049": "https://wcook04.github.io/plectis/papers/erdos-1049-rational-base-lambert.pdf",
}


def main() -> int:
    markup = INDEX.read_text(encoding="utf-8")
    # Every prose promise below is a promise about what the page SAYS, so it is
    # checked against the page with its glossary anchors unwrapped. The term
    # layer is derived from the vocabulary now rather than typed in, which means
    # any sentence can gain a link between one build and the next; a check that
    # reads the raw markup would fail on "Plectis writes mathematics with AI"
    # for no reason except that "mathematics" became hoverable. The marks
    # themselves are checked separately, against `markup`.
    text = TERM_ANCHOR.sub(lambda m: m.group("label"), markup)
    og_frontier = OG_FRONTIER.read_text(encoding="utf-8")
    sitemap = SITEMAP.read_text(encoding="utf-8")
    robots = ROBOTS.read_text(encoding="utf-8")
    plate = frontier_plate(text)
    absolute_frontier = json.loads(ABSOLUTE_FRONTIER_SOURCE.read_text(encoding="utf-8"))
    selection_authority = absolute_frontier.get("selection_authority", {})
    require(len(selection_authority.get("commit", "")) == 40, "absolute-frontier selection authority is not pinned")
    require("not external significance or acceptance authority" in selection_authority.get("posture", ""), "absolute-frontier selection authority overclaims internal triage")
    require(
        '<h1><a href="https://wcook04.github.io/plectis/" data-dest="plectis-site">Plectis</a></h1>' in text,
        "masthead no longer leads with Plectis, or the wordmark lost its route to the Plectis site",
    )
    require('<link rel="canonical" href="https://wcook04.github.io/">' in text, "front door lost its canonical public URL")
    require('<meta property="og:url" content="https://wcook04.github.io/">' in text, "social preview lost its canonical public URL")
    require('https://wcook04.github.io/assets/og-frontier.png' in text, "social preview lost the eight-problem share image")
    require('<loc>https://wcook04.github.io/</loc>' in sitemap, "root front door is absent from the host sitemap")
    require('Sitemap: https://wcook04.github.io/sitemap.xml' in robots, "host robots policy no longer exposes the root sitemap")
    require(
        "Will Cook &middot; checkable mathematical research" in text,
        "masthead lost Plectis or authorship",
    )
    require(">Eight programme map<" in text, "primary entry label lost the portfolio")
    require(
        "#249/#257" not in text,
        "front door reintroduced the two-problem historical core as its programme identity",
    )
    primary_route = (
        "https://github.com/wcook04/plectis-lean-erdos249-257/"
        f"blob/{SNAPSHOT}/README.md#eight-programme-map"
    )
    require(primary_route in text, "primary frontier entry no longer opens the programme map")
    require(
        f" / snapshot {SNAPSHOT[:7]} · README.md" in text,
        "destination plate no longer discloses its evidence snapshot",
    )
    require('<picture>\n      <source type="image/avif"' in text, "art plate is no longer delivered on the front door")
    require(
        "filter: saturate(.9) contrast(.92) brightness(.76)" not in text,
        "sticky art wrapper regained the Chrome first-paint filter regression",
    )
    # The first screen is where a cold reader meets the vocabulary, and it was
    # the one place the glossary was never applied: zero data-term marks in the
    # intro and zero in the shortlist above the fold. Naming a term and leaving
    # a stranger no way to find out what it means is the same omission as
    # naming a paper and not linking it.
    for term in ("machine_checked", "lean", "proof", "open_problem"):
        require(
            f'data-term="{term}"' in markup,
            f"opening prose no longer defines {term} for a cold reader",
        )
    # The layer is derived, so the thing worth guarding is no longer which words
    # are marked but whether every mark still names something. The four ids
    # above were once written "machine-checked" and "open-problem", which are
    # not glossary rows; they raised a card anyway because the payload beside
    # them was typed by the same hand with the same two invented keys. A
    # hand-maintained layer is consistent with itself and with nothing else,
    # and only a check that reads the source can tell the difference.
    snapshot_terms = set(
        json.loads((ROOT / "data" / "glossary-terms.json").read_text(encoding="utf-8"))["terms"]
    )
    marked = set(re.findall(r'data-term="([^"]+)"', markup))
    require(
        bool(marked), "the root page carries no glossary term marks at all"
    )
    unknown = sorted(marked - snapshot_terms)
    require(
        not unknown,
        f"term marks name no glossary row: {unknown}",
    )
    payload = re.search(
        r"/\* BEGIN generated glossary terms \*/(.*?)/\* END generated glossary terms \*/",
        markup,
        re.DOTALL,
    )
    require(payload is not None, "the generated term payload is missing")
    uncarded = sorted(t for t in marked if f'"{t}": {{' not in payload.group(1))
    require(
        not uncarded,
        f"terms are marked on the page but raise no card: {uncarded}",
    )
    require(
        "Plectis writes mathematics with AI and has it" in text,
        "opening lost the Plectis system thesis",
    )
    require(
        "eight" in text and "posed by Erd&#337;s" in text,
        "opening lost the all-programme frontier",
    )
    require(
        '<a class="skip-frontier" href="#eight-problem-frontier">Skip to eight-problem frontier</a>' in text,
        "keyboard route no longer skips directly to the eight-problem frontier",
    )
    require(
        '<nav id="eight-problem-frontier" tabindex="-1" aria-label="Public routes"' in text,
        "skip-frontier target is missing",
    )
    require("all eight remain open" in text.lower(), "front door lost its explicit open-problem boundary")
    require(
        "Hover or tab to a number for the question, what was checked, and what is still unproved." in text, "desktop portrait cue missing")
    require(
        "Open a number for the question, what was checked, and what is still unproved." in text, "narrow-screen frontier route missing")
    require("all eight remain open" in text.lower(), "open-problem boundary missing")
    require("not peer review" in text, "review boundary missing")
    require(
        "The results worth reading first" in text,
        "absolute frontier is missing from first contact",
    )
    thesis_at = text.find('id="absolute-frontier-title"')
    programmes_at = text.find('id="eight-problem-frontier"')
    require(0 < thesis_at < programmes_at, "cold-reader order must be thesis, flagships, then eight programmes")
    require(3 <= len(absolute_frontier["items"]) <= 5, "absolute-frontier shortlist must contain three to five items")
    public_flagships = [item for item in absolute_frontier["items"] if item.get("publication_state", "public") == "public"]
    require(3 <= len(public_flagships) <= 5, "absolute frontier must expose three to five public items")
    require(text.count('class="flagship"') == len(public_flagships), "absolute-frontier projection count drifted")
    require("not peer review, community acceptance, priority or a claim of canonical status" in text, "internal shortlist is missing its external-review boundary")
    tao_receipt = absolute_frontier.get("tao_pipeline_receipt", {})
    for field in (
        "input_stage", "output_stage", "artifact", "human_understanding_delta",
        "verification_state", "publication_or_review_state",
        "canonicalization_state", "unresolved_downstream_bottleneck",
        "next_stage_owner",
    ):
        require(tao_receipt.get(field), f"absolute frontier Tao receipt lacks {field}")
    for item in absolute_frontier["items"]:
        for field in ("why", "evidence", "hard_step", "attribution", "boundary", "handle", "href"):
            require(item.get(field), f"absolute-frontier #{item.get('problem')} lacks {field}")
        if item.get("publication_state", "public") == "public":
            require(item["title"] in text, f"absolute-frontier #{item['problem']} is stale")
            require(
                f'data-dest="problem-{item["problem"]}"' in text,
                f"absolute-frontier #{item['problem']} lost its problem-sheet route",
            )
            require(
                item["handle"].strip(),
                f"absolute-frontier #{item['problem']} lost its proof handle in authority",
            )
        else:
            require(item["title"] not in text, f"withheld absolute-frontier #{item['problem']} leaked publicly")
    require("The public site for the private work system:" in text, "Plectis route no longer distinguishes public site from private system")
    require("a second Lean file states the theorem again without its proof" in text, "formal checking scope missing")
    require("This does not review the papers, citations, meaning, novelty or significance" in text, "formal checking limit missing")
    require("How checking works" in text, "formal checking reader exit missing")
    require("Reproduce the checks" in text, "verification replay reader exit missing")
    require("Trace one classical benchmark after reading the programme and papers." in text, "representative-check boundary missing")
    require("The route returns the statement, exact declaration, Comparator interface, paper and boundary:" in text, "representative replay no longer explains its evidence route")
    require(
        '<a href="https://wcook04.github.io/plectis/docs/updates.html">Follow updates</a>' in text,
        "public updates exit missing",
    )
    require(
        '<a href="https://wcook04.github.io/plectis/#contact">Contact</a>' in text,
        "public contact exit missing",
    )
    require(
        f'<a data-to="repo" aria-label="Citation metadata for the reviewed-core release; portfolio-wide citation metadata is pending" href="https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/CITATION.cff">Citation metadata</a>' in text,
        "public citation route no longer discloses its reviewed-core boundary",
    )
    require('frame.setAttribute("data-view", view);' in text, "destination frame no longer switches its view")
    require('if (view === "problem") frame.setAttribute("data-problem", d.problem);' in text, "destination frame no longer selects a portrait sheet")
    require('document.addEventListener("focusin", function (ev) {' in text, "frontier sheets no longer have a keyboard route")
    require("function routeFocusIsHeld()" in text, "focus-held portrait route missing")
    require("if (!routeFocusIsHeld()) release();" in text, "focus-driven scroll can erase portrait route")
    require(
        ".dest__frame[data-view=\"problem\"] .shot__frontier {\n      opacity: 0;\n      visibility: hidden;" in text,
        "selected portrait can bleed the eight-problem overview through its resting state",
    )
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
    allowed_source_commits = {SNAPSHOT}
    for link in lean_links:
        require(
            any(f"/{commit}" in link for commit in allowed_source_commits),
            f"floating or mismatched Lean evidence link: {link}",
        )

    # The page carries exactly one list of problem numbers, at the foot of the
    # shortlist. The five shortlisted problems are reached through their
    # flagship rows (title, dest route, readable paper in the row's exits);
    # the other three keep the compact accessible entry with its topic and
    # portrait-sheet cue. Both forms end at the same sheets and papers.
    flagship_problems = frozenset({"68", "249", "251", "257", "1041"})
    for index, number in enumerate(PROBLEMS):
        selector = (
            f'.dest__frame[data-view="problem"][data-problem="{number}"] '
            f'.shot__problem[data-problem="{number}"]'
        )
        require(selector in text, f"#{number} portrait is not selected by its frontier route")
        expected_url = (
            "https://wcook04.github.io/plectis/papers/"
            f"{PROBLEM_PAPERS[number]}"
        )
        if number in flagship_problems:
            require(
                f'data-dest="problem-{number}"' in text,
                f"#{number} flagship row lost its problem-sheet route",
            )
            require(
                expected_url in text,
                f"#{number} no longer opens its readable paper",
            )
        else:
            route = re.search(
                rf'<p role="listitem" data-dest="problem-{number}">(.*?)</p>', text
            )
            require(route is not None, f"missing accessible frontier entry for #{number}")
            require(expected_url in route.group(1), f"#{number} does not open its readable paper")
            require(
                "Hover or focus for the question, checked object and open boundary." in route.group(1),
                f"#{number} compact route no longer points to its portrait sheet",
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
        if number in ACCESSIBLE_QUESTION_MARKERS:
            require(
                ACCESSIBLE_QUESTION_MARKERS[number] in sheet,
                f"#{number} sheet no longer states its mathematical question",
            )
        require("problem-sheet__section--open" in sheet, f"#{number} sheet lacks its open boundary")
        require('problem-sheet__status">Open<' in sheet, f"#{number} sheet lost open status")
        if number in FRONTIER_SHEET_ANCHORS:
            declaration, boundary = FRONTIER_SHEET_ANCHORS[number]
            require(declaration in sheet, f"#{number} sheet no longer names its cleared declaration")
            require(boundary in sheet, f"#{number} sheet no longer preserves its exact open boundary")

    # The eight numbers in the paper sentence are now routes, so the old
    # contiguous-string test could not survive the markup and would have been
    # the wrong test anyway: it proved the page NAMED all eight, not that a
    # reader could REACH all eight. Assert the reachable form instead, which is
    # strictly stronger: the sentence still opens the same way, and every one
    # of the eight numbers still carries a link to its own paper.
    require(
        "Eight problem papers, for " in text,
        "paper route no longer opens on all eight problem papers",
    )
    for number in PROBLEMS:
        # Attribute order is not the contract; the three facts are. The link
        # exists, it points at that problem's own paper, and hovering it puts
        # that paper in the destination window rather than a catalogue page.
        require(
            f'href="{PAPER_PDF_FOR[number]}"' in text,
            f"paper route no longer links #{number} to its own paper",
        )
        require(
            f'data-dest="paper-{number}"' in text,
            f"paper #{number} no longer previews itself in the window",
        )
        require(
            f'"paper-{number}":' in text and f"paper-{number}-640.jpg" in text,
            f"paper #{number} lost its first-page still",
        )
        require(
            f'>#{number}</a>' in text,
            f"paper route no longer names #{number} as a reachable number",
        )
    require("sit inside Plectis&rsquo;s 13-paper catalogue" in text, "paper route lost its catalogue context")
    print("frontier surface: 8 pinned routes, 8 portrait sheets, and all-eight paper route: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"frontier surface: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
