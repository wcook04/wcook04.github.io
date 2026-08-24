#!/usr/bin/env python3
"""Render the governed absolute-frontier shortlist into the root page."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "absolute-frontier.json"
INDEX = ROOT / "index.html"
BEGIN = "      <!-- BEGIN generated absolute frontier -->"
END = "      <!-- END generated absolute frontier -->"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def render(payload: dict) -> str:
    items = [
        row for row in payload["items"]
        if row.get("publication_state", "public") == "public"
    ]
    if not 3 <= len(items) <= 5:
        raise ValueError("absolute frontier must contain three to five items")
    cards = []
    for row in items:
        # The card raises the destination window rather than a card of its own.
        # There is already one instrument on this page that answers "what is
        # this problem", it is pinned to the right of the column at every
        # desktop width, and it holds a sheet for all eight problems. A second
        # hover surface for the same gesture meant the reader got two answers
        # at once, one of them covering the column it was hovering over, while
        # the dedicated window sat there showing something else. data-dest is
        # the page's own contract for this: the runtime reads it off the
        # nearest ancestor on hover and on focus, so the article needs the
        # attribute and nothing else. tabindex stays, because that is what
        # makes the keyboard raise the window too.
        cards.append(
            f'''          <article class="flagship" tabindex="0" data-dest="problem-{esc(row["problem"])}">
            <p class="flagship__line"><span class="flagship__number">#{esc(row["problem"])}</span><span class="flagship__kind">{esc(row["kind"])}</span></p>
            <h3><a href="{esc(row["href"])}">{esc(row["title"])}</a></h3>
          </article>'''
        )
    return f'''{BEGIN}
      <section class="absolute-frontier" aria-labelledby="absolute-frontier-title">
        <p class="absolute-frontier__eyebrow">Start here</p>
        <h2 id="absolute-frontier-title">The results worth reading first</h2>
        <p class="absolute-frontier__thesis">{esc(payload["thesis"])}</p>
        <div class="flagships">
{chr(10).join(cards)}
        </div>
        <p class="absolute-frontier__note">{esc(payload["selection_note"])}</p>
      </section>
{END}'''


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
        print("absolute frontier: source, ordering and generated region: ok")
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
