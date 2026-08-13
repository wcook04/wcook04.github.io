# wcook04.github.io

The page served at the root of `https://wcook04.github.io/`.

It exists for two reasons.

The first is ordinary: it is a front door for anyone who trims a link back to
the host, and a place to point at the published work.

The second is the reason it was written. Google resolves a site's favicon and
its displayed site name **per host, not per directory**. Everything published
here lives under a path — `/plectis/` — so before this page existed, the crawler
fetched `https://wcook04.github.io/` and got GitHub's own error page:

```
GET /             → 404, <title>Site not found · GitHub Pages</title>
GET /favicon.ico  → 404
```

Google attributed that page to the whole host. Search results for `/plectis/`
were shown with a generic globe and the site name "GitHub Pages documentation",
and no amount of correct metadata *inside* `/plectis/` could override it — the
markup there was already right, and was simply never consulted.

`/robots.txt` was a 404 for the same reason. Crawlers only ever read robots.txt
at the host root, so the copy at `/plectis/robots.txt` had never been fetched by
anything, and the sitemap it declared had never been discovered by that route.

## Contents

| Path | Purpose |
|---|---|
| `index.html` | The root page. Self-contained; no build step, no dependencies. |
| `404.html` | Served by GitHub Pages for unmatched paths under the host root. |
| `robots.txt` | The host-root robots.txt. Declares the Plectis sitemap. |
| `site.webmanifest` | Root-scoped manifest. |
| `favicon.ico`, `assets/` | The Plectis mark and its rasters. |

## The mark

`assets/favicon.svg` is a copy, not a fork. The source of truth lives in the
Plectis repository, where `tools/brand/plectis_favicon.py` renders the rasters
and the pinned day/night siblings from it. If the mark changes there, recopy it
here; do not edit it in place.

None of the icons in `site.webmanifest` is declared `maskable`, and none should
be. A maskable icon is cropped to a circle inscribed in the middle 80% of the
canvas, and the braid runs the full height of every raster we have — declaring
it maskable cuts the top and bottom strands off on Android. A real maskable
variant would need its own padded render from the Plectis tool, not a flag
here. Until that exists, the plain `any` purpose is the honest one: the
launcher then supplies its own container rather than cutting into the mark.

## Licence

The mark and page content are © Will Cook.
