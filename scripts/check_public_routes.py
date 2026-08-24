#!/usr/bin/env python3
"""Smoke-check the public records named by the root exhibition.

This deliberately checks only destinations outside the unpublished root-site
working tree.  It therefore catches a broken reader hand-off without claiming
that local root edits have been deployed.
"""

from __future__ import annotations

from html import unescape
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SNAPSHOT = "11a318711096671ce1c00257a55fe5d7b9963864"
PROGRAMME_MARKERS = (
    "#68 — Factorial-denominator series",
    "#243 — Reciprocal-tail rigidity near the Sylvester recurrence",
    "#249 — Binary totient series",
    "#251 — Prime-gap dyadic series",
    "#257 — Reciprocal sums over infinite exponent supports",
    "#269 — Three-prime running least common multiples",
    "#1041 — Short connections inside polynomial lemniscates",
    "#1049 — Lambert-type series at rational bases",
)
PAPER_CATALOGUE_MARKERS = (
    "Erdős #68",
    "Erdős #243",
    "Erdős #249",
    "Erdős #251",
    "Erdős #257",
    "Erdős #269",
    "Erdős #1041",
    "Erdős #1049",
)
PAPER_PDF_LINKS = (
    "https://wcook04.github.io/plectis/papers/erdos-68-factorial-denominator-irrationality.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-243-reciprocal-tail-rigidity.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-249-binary-totient-series.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-251-prime-gap-dyadic-series.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-257-mersenne-support-subseries.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-269-three-prime-running-lcm.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-1041-lemniscate-newton-flow.pdf",
    "https://wcook04.github.io/plectis/papers/erdos-1049-rational-base-lambert.pdf",
)
ROUTES = (
    ("Plectis public site", "https://wcook04.github.io/plectis/", None),
    (
        "public contact route",
        "https://wcook04.github.io/plectis/#contact",
        'id="contact"',
    ),
    (
        "13-paper catalogue",
        "https://wcook04.github.io/plectis/docs/papers.html",
        ("The 13 papers",) + PAPER_CATALOGUE_MARKERS + PAPER_PDF_LINKS,
    ),
    ("pinned Lean snapshot", f"https://github.com/wcook04/plectis-lean-erdos249-257/tree/{SNAPSHOT}", None),
    (
        "representative claim route",
        f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/README.md#read-or-run-it",
        (
            "Check one of those claims before you read any of this.",
            "python3 scripts/verify_claims.py --claim eb_full_support",
        ),
    ),
    ("eight-problem verification packet", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md", PROGRAMME_MARKERS),
    ("Comparator appendix", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md#comparator-interface-appendix", "comparator-interface-appendix"),
    ("reviewer replay", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION_REPLAY.md", None),
    ("citation record", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/CITATION.cff", None),
    ("updates route", "https://wcook04.github.io/plectis/docs/updates.html", "Follow updates"),
)


def fetch(url: str) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "PlectisPublicRouteCheck/1.0"})
    with urlopen(request, timeout=20) as response:  # nosec B310: fixed public URLs
        return response.status, response.read().decode("utf-8", errors="replace")


def visible_text(body: str) -> str:
    """Give text markers a stable surface across harmless HTML wrappers."""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", body)))


def main() -> int:
    failures: list[str] = []
    for label, url, expected_text in ROUTES:
        try:
            code, body = fetch(url)
        except (HTTPError, URLError, TimeoutError) as error:
            failures.append(f"{label}: {error}")
            continue
        if code != 200:
            failures.append(f"{label}: HTTP {code}")
        elif expected_text:
            markers = (expected_text,) if isinstance(expected_text, str) else expected_text
            text = visible_text(body)
            missing = [marker for marker in markers if marker not in text and marker not in body]
            if missing:
                failures.append(f"{label}: expected public marker missing: {missing[0]}")

    if failures:
        raise SystemExit("public routes: FAIL\n" + "\n".join(failures))
    print(f"public routes: {len(ROUTES)} reader hand-offs reachable at pinned snapshot {SNAPSHOT[:7]}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
