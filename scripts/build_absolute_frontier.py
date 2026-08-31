#!/usr/bin/env python3
"""Render the governed absolute-frontier shortlist into the root page."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "absolute-frontier.json"
INDEX = ROOT / "index.html"
BEGIN = "      <!-- BEGIN generated absolute frontier -->"
END = "      <!-- END generated absolute frontier -->"

# The question is the only field allowed to carry markup, because a reader
# meeting the problem for the first time needs the series itself and not a
# transliteration of it. Nothing but sub, sup and character entities gets
# through; the builder refuses anything else rather than trusting the file.
SAFE_QUESTION = re.compile(r"\A(?:[^<>&]|</?su[bp]>|&[a-zA-Z]+;|&#\d+;)*\Z")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def question(value: str) -> str:
    if not SAFE_QUESTION.fullmatch(value):
        raise ValueError(
            f"question_html carries markup that is not sub, sup or an entity: {value!r}"
        )
    return value


# A shortlisted result has to be legible where it is listed. These fields are
# what a reader needs before deciding whether to open anything, so a card that
# is missing one is a build failure and not a thinner card: the section used to
# render a bare title and an outbound link, and the mathematics that was
# already sitting in this file went unrendered.
REQUIRED = ("title", "kind", "question_html", "why", "evidence", "hard_step",
            "attribution", "paper_href")


def check_row(row: dict) -> None:
    for field in REQUIRED:
        if not str(row.get(field, "")).strip():
            raise ValueError(f"absolute-frontier #{row.get('problem')} has no {field}")


def card(row: dict) -> str:
    check_row(row)
    # data-dest still raises the destination window on hover and on focus, but
    # the card no longer depends on it for its content. Everything a reader
    # needs in order to judge the result is in the article itself: the
    # question, what the reduction buys, the evidence class, and the step
    # nobody has. A hover is an extra. On a phone there is no hover at all.
    exits = ['<a href="{}">Paper</a>'.format(esc(row["paper_href"]))]
    if row.get("lean_href"):
        exits.append('<a href="{}">Lean statement</a>'.format(esc(row["lean_href"])))
    exit_html = '<span class="sep" aria-hidden="true">&middot;</span>'.join(exits)
    caveat = row.get("paper_caveat")
    caveat_html = (
        '\n              <p class="flagship__caveat">{}</p>'.format(esc(caveat))
        if caveat
        else ""
    )
    return "\n".join(
        [
            '          <article class="flagship" tabindex="0" data-dest="problem-{}">'.format(
                esc(row["problem"])
            ),
            '            <p class="flagship__line"><span class="flagship__number">#{}</span>'
            '<span class="flagship__kind">{}</span></p>'.format(
                esc(row["problem"]), esc(row["kind"])
            ),
            '            <div class="flagship__body">',
            "              <h3>{}</h3>".format(esc(row["title"])),
            '              <p class="flagship__question">'
            '<span class="flagship__tag">Question</span>{}</p>'.format(
                question(row["question_html"])
            ),
            '              <p class="flagship__why">{}</p>'.format(esc(row["why"])),
            '              <p class="flagship__fact">'
            '<span class="flagship__tag">Evidence</span>{}</p>'.format(esc(row["evidence"])),
            '              <p class="flagship__fact flagship__fact--open">'
            '<span class="flagship__tag">Still open</span>{}</p>'.format(esc(row["hard_step"])),
            '              <p class="flagship__attribution">{}</p>'.format(
                esc(row["attribution"])
            ),
            '              <p class="flagship__exits">{}</p>{}'.format(exit_html, caveat_html),
            "            </div>",
            "          </article>",
        ]
    )


# The three programmes without a shortlisted headline result. They live here,
# at the foot of the shortlist, so the page carries exactly one list of
# problem numbers: same row grammar as the shortlist's hover routes, same
# portrait sheets, same readable-paper links. The Check band beneath names
# the programme map without repeating the numbers.
OTHER_PROGRAMMES = (
    ("243", "Reciprocal tails", "erdos-243-reciprocal-tail-rigidity.pdf"),
    ("269", "Three-prime running LCMs", "erdos-269-three-prime-running-lcm.pdf"),
    ("1049", "Lambert series at rational bases", "erdos-1049-rational-base-lambert.pdf"),
)


def other_row(number: str, topic: str, paper: str) -> str:
    return (
        '            <p role="listitem" data-dest="problem-{n}">'
        '<a data-to="repo" data-dest="problem-{n}" aria-label="#{n}: {t}. '
        'Hover or focus for the question, checked object and open boundary." '
        'href="https://wcook04.github.io/plectis/papers/{p}">#{n}</a> '
        '<span class="frontier-topic">{t}</span></p>'
    ).format(n=esc(number), t=esc(topic), p=esc(paper))


def paper_number_links() -> str:
    parts = []
    for number, _topic, paper in (
        ("68", "factorial denominator irrationality", "erdos-68-factorial-denominator-irrationality.pdf"),
        ("243", "reciprocal tail rigidity", "erdos-243-reciprocal-tail-rigidity.pdf"),
        ("249", "the binary totient series", "erdos-249-binary-totient-series.pdf"),
        ("251", "the prime-gap dyadic series", "erdos-251-prime-gap-dyadic-series.pdf"),
        ("257", "Mersenne support subseries", "erdos-257-mersenne-support-subseries.pdf"),
        ("269", "three-prime running LCMs", "erdos-269-three-prime-running-lcm.pdf"),
        ("1041", "the lemniscate Newton flow", "erdos-1041-lemniscate-newton-flow.pdf"),
        ("1049", "rational-base Lambert series", "erdos-1049-rational-base-lambert.pdf"),
    ):
        parts.append(
            '<a class="paper" data-dest="paper-{n}" '
            'href="https://wcook04.github.io/plectis/papers/{p}" '
            'aria-label="Paper, PDF: Erd&#337;s #{n}, {t}">#{n}</a>'.format(
                n=number, p=paper, t=_topic
            )
        )
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def combined_routes(snapshot: str) -> list[str]:
    """The checked map, the papers, and the deep-check tail, inside the one
    mathematics band. These moved here from the separate Check and Read route
    rows so the page states the programme once; the wording of every promise
    and boundary is unchanged and stays pinned by check_frontier_surface."""
    repo = "https://github.com/wcook04/plectis-lean-erdos249-257"
    blob = f"{repo}/blob/{snapshot}"
    return [
        '        <p class="af-route">One machine-checked statement for each problem, '
        "and the exact thing that is still unproved: the "
        f'<a data-to="repo" data-dest="math-frontier" href="{blob}/README.md#eight-programme-map">'
        "Eight programme map</a>.</p>",
        '        <p class="af-route">Eight problem papers, for '
        + paper_number_links()
        + ", <a data-dest=\"papers-catalogue\" "
        'href="https://wcook04.github.io/plectis/docs/papers.html">'
        "sit inside Plectis&rsquo;s 13-paper catalogue</a> with the reasoning "
        "surfaces and the system papers. They are written for someone reading cold.</p>",
        '        <p class="absolute-frontier__acts">'
        '<a class="btn btn--quiet" data-dest="maths-pages" '
        'href="https://wcook04.github.io/plectis/maths/">Read all eight as pages</a>'
        '<a class="btn btn--quiet" data-to="repo" data-dest="math-frontier" '
        f'href="{blob}/README.md#eight-programme-map">Open the programme map</a>'
        '<a class="btn btn--quiet" data-dest="papers-catalogue" '
        'href="https://wcook04.github.io/plectis/docs/papers.html">Open the papers catalogue</a>'
        "</p>",
        '        <details class="route-more">',
        "          <summary>More ways to check it</summary>",
        '          <p class="exits frontier-exits">',
        f'            <a data-to="repo" data-dest="lean-github" aria-label="Open the pinned Lean source" href="{repo}/tree/{snapshot}">Lean source</a><span class="sep" aria-hidden="true">&middot;</span>'
        f'<a data-to="repo" aria-label="Check one theorem without building Lean" href="{blob}/README.md#read-or-run-it">Check one theorem</a><span class="sep" aria-hidden="true">&middot;</span>'
        f'<a data-to="repo" aria-label="Read the programme map for all eight open problems" href="{blob}/docs/EXTERNAL_VERIFICATION.md">Read all eight</a><span class="sep" aria-hidden="true">&middot;</span>'
        f'<a data-to="repo" aria-label="See how selected formal statements are checked" href="{blob}/docs/EXTERNAL_VERIFICATION.md#comparator-interface-appendix">How checking works</a><span class="sep" aria-hidden="true">&middot;</span>'
        f'<a data-to="repo" aria-label="Reproduce the public verification checks" href="{blob}/docs/EXTERNAL_VERIFICATION_REPLAY.md">Reproduce the checks</a><span class="sep" aria-hidden="true">&middot;</span>'
        f'<a data-to="repo" aria-label="Cite the eight-problem Lean corpus" href="{blob}/CITATION.cff">Cite the corpus</a>',
        "          </p>",
        '          <p class="frontier-comparator">For selected propositions, a second Lean '
        "file states the theorem again without its proof. The build checks that the "
        "original proof has exactly that type and stays within a fixed axiom budget. "
        "This does not review the papers, citations, meaning, novelty or significance.</p>",
        '          <p class="frontier-proof"><span>Trace one classical benchmark after '
        "reading the programme and papers. No Lean build is needed. The route returns "
        "the statement, exact declaration, Comparator interface, paper and boundary:"
        "</span>"
        f'<a data-to="repo" aria-label="Trace the classical full-support benchmark without a Lean build" href="{blob}/README.md#read-or-run-it">'
        "<code>python3 scripts/verify_claims.py --claim eb_full_support</code></a></p>",
        "        </details>",
    ]


def render(payload: dict) -> str:
    items = [
        row for row in payload["items"]
        if row.get("publication_state", "public") == "public"
    ]
    if not 3 <= len(items) <= 5:
        raise ValueError("absolute frontier must contain three to five items")
    cards = "\n".join(card(row) for row in items)
    others = "\n".join(other_row(*row) for row in OTHER_PROGRAMMES)
    return "\n".join(
        [
            BEGIN,
            '      <section class="absolute-frontier" aria-labelledby="absolute-frontier-title">',
            '        <p class="absolute-frontier__eyebrow">Start here</p>',
            '        <h2 id="absolute-frontier-title">The results worth reading first</h2>',
            '        <p class="absolute-frontier__thesis">{}</p>'.format(esc(payload["thesis"])),
            '        <p class="frontier-instruction"><span class="frontier-instruction__wide">'
            "Hover or tab to a number for the question, what was checked, and what is still "
            "unproved.</span><span class=\"frontier-instruction__narrow\">Open a number for "
            "the question, what was checked, and what is still unproved.</span></p>",
            '        <div class="flagships">',
            cards,
            "        </div>",
            '        <p class="frontier-label">The other three programmes</p>',
            '        <div class="frontier frontier--others" role="list" '
            'aria-label="The other three programmes: one checked frontier and one open '
            'boundary each">',
            others,
            "        </div>",
            '        <p class="absolute-frontier__note">{}</p>'.format(
                esc(payload["selection_note"])
            ),
            *combined_routes(payload["public_source_commit"]),
            "      </section>",
            END,
        ]
    )


def replace_region(text: str, region: str) -> str:
    start = text.find(BEGIN)
    end = text.find(END)
    if start < 0 or end < 0 or end < start:
        raise ValueError("absolute-frontier generated region is missing")
    end += len(END)
    return text[:start] + region + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    current = INDEX.read_text(encoding="utf-8")
    expected = replace_region(current, render(payload))
    if args.check:
        if expected != current:
            raise SystemExit("absolute frontier: generated region is stale")
        # Verified against the page and not only against the renderer, so a
        # hand-edit of index.html that strips a result back to a headline is
        # caught here rather than shipping.
        region = current[current.find(BEGIN):current.find(END)]
        for row in payload["items"]:
            if row.get("publication_state", "public") != "public":
                continue
            for field in ("why", "evidence", "hard_step"):
                if esc(row[field]) not in region:
                    raise SystemExit(
                        f"absolute frontier: #{row['problem']} no longer states its {field}"
                    )
        print("absolute frontier: source, ordering, stated results and generated region: ok")
        return 0
    INDEX.write_text(expected, encoding="utf-8")
    public_count = sum(
        row.get("publication_state", "public") == "public"
        for row in payload["items"]
    )
    print(f"absolute frontier: rendered {public_count} public items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
