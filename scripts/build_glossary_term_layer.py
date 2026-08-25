#!/usr/bin/env python3
"""Link every governed glossary term the root page actually uses.

The page used to carry nine terms, chosen by hand, with their preview cards
retyped into the file beside them. The glossary those nine came from has 486
entries, and this page is where most readers meet the vocabulary first: a
reader who hovered "cofinal", "lemniscate", "Mersenne", "radix", "Erdos" or
"irrational" — every one of them defined, every one of them on this page — got
nothing back, because a hand-maintained list only ever holds the words someone
remembered to add.

So the list is derived instead. ``data/glossary-terms.json`` is exported from
the same vocabulary the Plectis glossary page renders, and it arrives already
compiled: the decision about which surface forms are safe to resolve on a bare
occurrence — distinctive, collision-free, not ordinary English whose card
teaches a reader nothing — was made upstream by the governed policy, so this
script owns no opinion about vocabulary. It owns where on the page a link may
go, which is a question about this page's own markup.

The pass is re-runnable rather than merely idempotent. It unwraps every anchor
it previously wrote before it writes any, so a term retired from the glossary
leaves the page rather than accumulating in it, and it regenerates the preview
payload from the same snapshot, so a card can no longer say something the
glossary does not.

Usage::

    python3 scripts/build_glossary_term_layer.py          # rewrite index.html
    python3 scripts/build_glossary_term_layer.py --check   # fail if stale
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "glossary-terms.json"
INDEX = ROOT / "index.html"

TERMS_BEGIN = "    /* BEGIN generated glossary terms */"
TERMS_END = "    /* END generated glossary terms */"

# Where a term link is structurally wrong rather than merely unwanted. Nested
# anchors are invalid, a literal inside code is not prose, and splicing an
# anchor into a button or label manufactures interactive content inside a
# control. h1 is refused for its own reason: the masthead is the page's subject,
# not a word the page can send you elsewhere to look up.
SKIP_TAGS = frozenset(
    {
        "a", "button", "code", "h1", "kbd", "label", "noscript", "option",
        "pre", "samp", "script", "select", "style", "svg", "textarea", "th",
        "title",
    }
)

# Void elements never close. Counting one as an open region strands the counter
# and silently kills term links for the whole rest of the document.
VOID_TAGS = frozenset(
    {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    }
)

# Crossing one of these starts a new link budget, because it starts a new thing
# to read.
BLOCK_TAGS = frozenset(
    {
        "address", "article", "aside", "blockquote", "body", "caption", "dd",
        "details", "div", "dl", "dt", "figcaption", "figure", "footer", "form",
        "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "main", "nav", "ol",
        "p", "section", "summary", "table", "tbody", "td", "tfoot", "thead",
        "tr", "ul",
    }
)

# Labels, not prose. A micro-label opening a row ("Question", "Evidence",
# "Still open"), a kicker over a heading, a status chip, the fake browser chrome
# in a screenshot frame, the numbers down the side of the programme map. Linking
# inside one is wrong three ways at once: the label stops reading as a label
# because the anchor brings its own type, the click leaves the very thing the
# label describes, and the destination is often a term whose name is not the
# word on screen. Matching on class rather than on each emission site means a
# label added later is covered without anyone remembering to mark it.
CHROME_CLASSES = frozenset(
    {
        "eyebrow",
        "flagship__kind",
        "flagship__line",
        "flagship__number",
        "flagship__tag",
        "frontier-plate__handle",
        "frontier-plate__number",
        # The eight programme names beside their numbers. A row label is a
        # name for the thing the row opens, so a link inside it retypes the
        # name and offers a second click that leaves the map. Every one of
        # these words is defined again in the prose below, where a reader has
        # a sentence to hang the definition on.
        "frontier-topic",
        "kind",
        "map__k",
        "name",
        "problem-sheet__handle",
        "problem-sheet__label",
        "problem-sheet__number",
        "problem-sheet__status",
        "problem-sheet__topline",
        "profile-card__status",
        "profile-card__topline",
        "role",
        "shot__bar",
        "shot__host",
        "shot__path",
        "shot__problem",
        "sr-only",
        "tag",
    }
)

# How many distinct terms one block may link before the pass stops. The cap
# exists to keep a paragraph from becoming a texture; it is not a claim that the
# rest of its vocabulary is undefined, since a word skipped here is still on the
# glossary page.
BLOCK_BUDGET = 8

TAG_OR_COMMENT = re.compile(r"<!--.*?-->|<[^>]*>", re.DOTALL)
TAG_NAME = re.compile(r"^<\s*(/?)\s*([a-zA-Z][-a-zA-Z0-9]*)")
CLASS_ATTR = re.compile(r'\bclass=(?P<q>["\'])(?P<value>.*?)(?P=q)', re.DOTALL)
OPT_OUT = re.compile(r'\bdata-term-auto=(?P<q>["\'])off(?P=q)', re.IGNORECASE)
CHAR_REF = re.compile(r"&(?:#[xX][0-9a-fA-F]+|#[0-9]+|[a-zA-Z][a-zA-Z0-9]+);")
# Every term anchor on the page is written by this script, so unwrapping is the
# whole recovery story: no hand-typed anchor has to be told apart from a
# generated one, and none can drift away from the glossary behind its back.
TERM_ANCHOR = re.compile(
    r'<a class="term(?: is-again)?" data-term="[^"]*" href="[^"]*">(?P<label>.*?)</a>',
    re.DOTALL,
)


def phrase_re(phrase: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)


class Budget:
    """One block's remaining allowance, one link per concept."""

    def __init__(self) -> None:
        self.spent: set[str] = set()

    def reset(self) -> None:
        self.spent = set()

    def blocks(self, term_id: str) -> bool:
        return term_id in self.spent or len(self.spent) >= BLOCK_BUDGET

    def spend(self, term_id: str) -> None:
        self.spent.add(term_id)


def decoded_view(text: str) -> tuple[str, list[tuple[int, int]] | None]:
    """Decode character references while remembering the span each came from.

    The page spells the same visible word two ways — ``Erdős`` and
    ``Erd&#337;s`` — and the resolver matches what a reader sees. The anchor
    still has to wrap the source bytes exactly, so every decoded character
    carries the source span that produced it.
    """
    if "&" not in text or CHAR_REF.search(text) is None:
        return text, None
    out: list[str] = []
    spans: list[tuple[int, int]] = []
    pos = 0

    def literal(start: int, end: int) -> None:
        out.extend(text[start:end])
        spans.extend((i, i + 1) for i in range(start, end))

    for match in CHAR_REF.finditer(text):
        literal(pos, match.start())
        source = match.group(0)
        visible = html.unescape(source)
        if visible == source:
            literal(match.start(), match.end())
        else:
            out.extend(visible)
            spans.extend((match.start(), match.end()) for _ in visible)
        pos = match.end()
    literal(pos, len(text))
    return "".join(out), spans


def iter_matches(text: str, phrases: list[tuple[str, str]]):
    """Longest-first, word-boundary, non-overlapping matches, in reading order.

    ``phrases`` arrives sorted longest-first from the snapshot, so a character
    consumed by a longer phrase is never reused by a shorter one and one span
    maps to exactly one concept.
    """
    lowered = text.lower()
    taken = bytearray(len(text))
    found: list[tuple[int, int, str, str]] = []
    for phrase, term_id in phrases:
        if phrase not in lowered:
            continue
        for match in phrase_re(phrase).finditer(text):
            start, end = match.span()
            if any(taken[start:end]):
                continue
            taken[start:end] = b"\x01" * (end - start)
            found.append((start, end, term_id, match.group(0)))
    found.sort(key=lambda hit: hit[0])
    return found


def link_run(
    text: str,
    phrases: list[tuple[str, str]],
    anchors: dict[str, str],
    budget: Budget,
    seen: set[str],
) -> str:
    """Splice anchors over the governed phrases in one run of page text."""
    match_text, spans = decoded_view(text)
    pieces: list[str] = []
    pos = 0
    for start, end, term_id, matched in iter_matches(match_text, phrases):
        if budget.blocks(term_id):
            continue
        source_start, source_end, label = start, end, matched
        if spans is not None:
            # Never wrap part of a multi-codepoint reference: the phrase has to
            # align with the reference's own source boundaries.
            if start > 0 and spans[start - 1] == spans[start]:
                continue
            if end < len(spans) and spans[end - 1] == spans[end]:
                continue
            source_start, source_end = spans[start][0], spans[end - 1][1]
            label = text[source_start:source_end]
        # First mention keeps the dotted rule; later ones render as plain ink
        # and stay hoverable. Graded here rather than only in the runtime,
        # because with 200 anchors the ungraded first paint is a page of
        # underline, and the runtime re-applies the same class harmlessly.
        grade = " is-again" if term_id in seen else ""
        seen.add(term_id)
        pieces.append(text[pos:source_start])
        pieces.append(
            f'<a class="term{grade}" data-term="{html.escape(term_id, quote=True)}" '
            f'href="{html.escape(anchors[term_id], quote=True)}">{label}</a>'
        )
        pos = source_end
        budget.spend(term_id)
    if not pieces:
        return text
    pieces.append(text[pos:])
    return "".join(pieces)


def is_chrome(tag: str) -> bool:
    """True when an opening tag carries a label class.

    Token comparison, not substring, so ``class="tag-list"`` is not mistaken for
    ``class="tag"``.
    """
    match = CLASS_ATTR.search(tag)
    if match is None:
        return False
    return any(token in CHROME_CLASSES for token in match.group("value").split())


def link_terms(page: str, phrases: list[tuple[str, str]], anchors: dict[str, str]) -> str:
    """Walk the finished page and link governed terms in its prose only."""
    page = TERM_ANCHOR.sub(lambda m: m.group("label"), page)
    body = page.find("<body")
    if body == -1:
        raise ValueError("index.html has no <body>")

    out: list[str] = [page[:body]]
    depth: dict[str, int] = {}
    budget = Budget()
    seen: set[str] = set()
    pos = body
    for tag_match in TAG_OR_COMMENT.finditer(page, body):
        run = page[pos : tag_match.start()]
        if run:
            out.append(
                run
                if any(depth.values())
                else link_run(run, phrases, anchors, budget, seen)
            )
        tag = tag_match.group(0)
        name_match = TAG_NAME.match(tag)
        if name_match and not tag.startswith("<!--"):
            closing, name = name_match.group(1), name_match.group(2).lower()
            if name in BLOCK_TAGS:
                budget.reset()
            if name in VOID_TAGS or tag.endswith("/>"):
                pass  # no close tag will arrive; touching a counter strands it
            elif name in SKIP_TAGS:
                depth[name] = (
                    max(0, depth.get(name, 0) - 1) if closing else depth.get(name, 0) + 1
                )
            else:
                # Keyed by tag name so an unmarked close finds its own open. An
                # unmarked element of the same name nested inside a marked one is
                # tracked separately, or its close would release the outer
                # opt-out early and leak links into the rest of the chrome.
                key, nested = f"opt-out:{name}", f"opt-out-nested:{name}"
                if closing:
                    if depth.get(nested):
                        depth[nested] -= 1
                    elif depth.get(key):
                        depth[key] -= 1
                elif OPT_OUT.search(tag) or is_chrome(tag):
                    depth[key] = depth.get(key, 0) + 1
                elif depth.get(key):
                    depth[nested] = depth.get(nested, 0) + 1
        out.append(tag)
        pos = tag_match.end()
    tail = page[pos:]
    out.append(tail if any(depth.values()) else link_run(tail, phrases, anchors, budget, seen))
    return "".join(out)


def render_terms_block(snapshot: dict, used: list[str]) -> str:
    """The preview payload, carrying only the terms the page actually links."""
    terms = snapshot["terms"]
    payload = {}
    for term_id in used:
        row = terms[term_id]
        entry = {"preferred_label": row["label"]}
        for name, key in (
            ("preview", "reader_preview"),
            ("card", "reader_card"),
            ("rule", "reader_rule"),
            ("deep", "reader_deep"),
        ):
            if row.get(name):
                entry[key] = row[name]
        payload[term_id] = entry
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    body = "\n".join("    " + line for line in body.splitlines())
    return f"{TERMS_BEGIN}\n    var TERMS =\n{body};\n{TERMS_END}"


def build(page: str, snapshot: dict) -> str:
    phrases = [(phrase, term_id) for phrase, term_id in snapshot["phrases"]]
    glossary = snapshot["glossary_href"]
    anchors = {
        term_id: f"{glossary}#{row['anchor']}" for term_id, row in snapshot["terms"].items()
    }
    linked = link_terms(page, phrases, anchors)

    used = sorted(set(re.findall(r'<a class="term(?: is-again)?" data-term="([^"]+)"', linked)))
    missing = [term_id for term_id in used if term_id not in snapshot["terms"]]
    if missing:
        raise ValueError(f"linked terms absent from the snapshot: {missing}")

    start = linked.find(TERMS_BEGIN)
    end = linked.find(TERMS_END)
    if start == -1 or end == -1:
        raise ValueError(
            f"index.html carries no generated-terms markers ({TERMS_BEGIN!r})"
        )
    return linked[:start] + render_terms_block(snapshot, used) + linked[end + len(TERMS_END):]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if index.html is not what this script would write",
    )
    args = parser.parse_args(argv)

    snapshot = json.loads(SOURCE.read_text(encoding="utf-8"))
    page = INDEX.read_text(encoding="utf-8")
    built = build(page, snapshot)
    count = len(re.findall(r'<a class="term', built))
    distinct = len(set(re.findall(r'data-term="([^"]+)"', built)))

    if args.check:
        if built != page:
            print(
                "index.html is stale: run scripts/build_glossary_term_layer.py",
                file=sys.stderr,
            )
            return 1
        print(f"term layer current — {count} anchors over {distinct} terms")
        return 0

    if built == page:
        print(f"term layer unchanged — {count} anchors over {distinct} terms")
        return 0
    INDEX.write_text(built, encoding="utf-8")
    print(
        f"wrote index.html — {count} anchors over {distinct} terms "
        f"(from {snapshot['term_count']} defined, {snapshot['phrase_count']} surface forms)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
