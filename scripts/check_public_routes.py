#!/usr/bin/env python3
"""Smoke-check the public records named by the root exhibition.

This deliberately checks only destinations outside the unpublished root-site
working tree.  It therefore catches a broken reader hand-off without claiming
that local root edits have been deployed.
"""

from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SNAPSHOT = "11a318711096671ce1c00257a55fe5d7b9963864"
ROUTES = (
    ("Plectis public site", "https://wcook04.github.io/plectis/"),
    ("13-paper catalogue", "https://wcook04.github.io/plectis/docs/papers.html"),
    ("pinned Lean snapshot", f"https://github.com/wcook04/plectis-lean-erdos249-257/tree/{SNAPSHOT}"),
    ("eight-problem verification packet", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md"),
    ("Comparator appendix", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION.md#comparator-interface-appendix"),
    ("reviewer replay", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/docs/EXTERNAL_VERIFICATION_REPLAY.md"),
    ("citation record", f"https://github.com/wcook04/plectis-lean-erdos249-257/blob/{SNAPSHOT}/CITATION.cff"),
    ("updates route", "https://wcook04.github.io/plectis/docs/updates.html"),
)


def status(url: str) -> int:
    request = Request(url, headers={"User-Agent": "PlectisPublicRouteCheck/1.0"})
    with urlopen(request, timeout=20) as response:  # nosec B310: fixed public URLs
        return response.status


def main() -> int:
    failures: list[str] = []
    for label, url in ROUTES:
        try:
            code = status(url)
        except (HTTPError, URLError, TimeoutError) as error:
            failures.append(f"{label}: {error}")
            continue
        if code != 200:
            failures.append(f"{label}: HTTP {code}")

    if failures:
        raise SystemExit("public routes: FAIL\n" + "\n".join(failures))
    print(f"public routes: {len(ROUTES)} reader hand-offs reachable at pinned snapshot {SNAPSHOT[:7]}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
