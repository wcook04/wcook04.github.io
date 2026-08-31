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
            # One clear control for the band: the same five results, and the
            # other three programmes, rendered as readable pages with the
            # checked statements and their boundaries. The card exits keep
            # the per-result Paper and Lean routes; this names the room.
            '        <p class="absolute-frontier__act"><a class="btn btn--quiet" '
            'data-dest="maths-pages" '
            'href="https://wcook04.github.io/plectis/maths/">Read all eight as pages</a></p>',
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
