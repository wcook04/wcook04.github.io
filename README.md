# wcook04.github.io

The page served at the root of <https://wcook04.github.io/>.

It is the top of a two-level public presence. This page is the index; everything
it lists lives one directory down or in its own repository.

| | |
|---|---|
| **Front door** | <https://wcook04.github.io/>: this repository |
| **Plectis, the site** | <https://wcook04.github.io/plectis/> · [docs](https://wcook04.github.io/plectis/docs/) · [papers](https://wcook04.github.io/plectis/docs/papers.html) |
| **Plectis, the repository** | <https://github.com/wcook04/plectis> |
| **Lean research repository** | <https://github.com/wcook04/plectis-lean-erdos249-257> |
| **Videos** | [1 min](https://youtu.be/R_--vExxWyk) · [5 min](https://youtu.be/VoWByIOIuBE) · [29 min](https://youtu.be/jA_xC8gmdSs) |

The Plectis site is a separate GitHub Pages deployment: the `gh-pages` branch
of `wcook04/plectis`, served under a path on this host.
Nothing here builds it, and nothing in it builds this. The reading-map builder imports the source snapshot from the Plectis site; the return links are described under [The pair](#the-pair).

It exists for two reasons.

The first is ordinary: it is a front door for anyone who trims a link back to
the host, and a place to point at the published work.

The second is the reason it was written. Google resolves a site's favicon and
its displayed site name **per host, not per directory**. Everything published
here lives under the `/plectis/` path, so before this page existed, the crawler
fetched `https://wcook04.github.io/` and got GitHub's own error page:

```
GET /             → 404, <title>Site not found · GitHub Pages</title>
GET /favicon.ico  → 404
```

Google attributed that page to the whole host. Search results for `/plectis/`
were shown with a generic globe and the site name "GitHub Pages documentation",
and no amount of correct metadata *inside* `/plectis/` could override it. The
markup there was already right, and was simply never consulted.

`/robots.txt` was a 404 for the same reason. Crawlers only ever read robots.txt
at the host root, so the copy at `/plectis/robots.txt` had never been fetched by
anything, and the sitemap it declared had never been discovered by that route.

## Contents

| Path | Purpose |
|---|---|
| `index.html` | The root page. Served as-is; two generated regions are spliced into it by the scripts below. |
| `404.html` | Served by GitHub Pages for unmatched paths under the host root. |
| `robots.txt` | The host-root robots.txt. Declares the Plectis sitemap. |
| `site.webmanifest` | Root-scoped manifest. |
| `favicon.ico`, `assets/` | The Plectis mark and its rasters. |
| `assets/plate-01*` | Archived artwork retained locally; it is not part of the reading surface. |
| `assets/previews/` | Screenshots of each public destination, used as stills on the front door. |
| `assets/og-frontier.svg` / `.png` | The claim-bounded eight-problem social preview and its PNG delivery file. |
| `data/glossary-terms.json` | The governed public vocabulary, exported from the Plectis substrate: 486 terms with their reader cards, and the 2,354 surface forms that are safe to resolve on a bare word. |
| `scripts/build_glossary_term_layer.py` | Links every governed term the page actually uses and regenerates the preview payload. Re-runnable: it unwraps its own anchors before it writes. |
| `scripts/check_frontier_surface.py` | Static release guard for the all-eight programme map and immutable verification links. |
| `scripts/check_public_routes.py` | Live smoke check for the public Plectis, paper, Lean, verification, Comparator, replay, citation, and updates hand-offs. |

## Refresh and check

The Lean repository is the primary research destination. The separate Plectis
repository publishes reusable software components. The system and open-source
papers introduce the research; all eight problems have the same presentation
and appear in numerical order. The full JSON handoff embeds all published short
notes, long working records and system papers.

Refresh the source snapshot from a validated Plectis site build:

```sh
python3 scripts/build_absolute_frontier.py --site-root /path/to/ai_workflow/sites/microcosm --refresh-previews
```

The historical script and data filenames remain stable. The script reads the
complete handoff and source-owned problem index, records their hashes, and
rebuilds both the visible reading map and the problem previews. Do not edit
`data/absolute-frontier.json` or its generated HTML regions by hand. Publication
order is Plectis first, then this root page, so new paper links exist when the
front door points at them.

Refresh the glossary from the same site build with the Plectis owner:

```sh
./repo-python tools/meta/dissemination/export_public_glossary_snapshot.py --out /path/to/wcook04.github.io/data/glossary-terms.json
```

Then, in this repository:

```sh
python3 scripts/build_glossary_term_layer.py
python3 scripts/build_absolute_frontier.py --check
python3 scripts/check_frontier_surface.py
python3 scripts/check_public_routes.py
```

The static check verifies equal problem coverage, paper and page destinations,
source projection parity and glossary identifiers. The live route check verifies
published destinations. Neither establishes mathematical truth or peer review.

## Destination kinds

The route index colours each link by what it lands you on, so a reader knows
before clicking whether a word takes them to a page, a repository, or a video.

| Kind | Attribute | Colour | Mark |
|---|---|---|---|
| a page on this host | *(none)* | bone, lifting to the blue accent | none |
| a repository | `data-to="repo"` | `--to-repo` `#e6b264` | `↗` |
| a video | `data-to="video"` | `--to-video` `#d47fac` | `↗` |
| an account | `data-to="profile"` | inherits the colophon's `--faint` | `↗` |

Neither colour is invented here. The gold is the value the Plectis stylesheet
already uses for every link that leaves it (`--link-ext`, dark scheme); the rose
is the magenta flare from the thread across the top of this page, lifted until
it clears AA on the plum. That makes the thread the key to the list beneath it.

Two rules are load-bearing, and both are easy to break by accident:

- **Set only `data-to`.** The colour and the mark both hang off that one
  attribute, so a kind cannot be half-applied. Do not hand-type a `↗`; the
  stylesheet generates it. The colophon used to carry typed ones and they drifted
  out of step with everything else.
- **Colour is never the only signal.** The kind column, the route name and the
  exit text each say the same thing in words: `Watch` / `Videos` / `29 min`,
  `Check` / `Eight-problem frontier` / `GitHub`. A reader who sees no hue loses a shortcut,
  not a fact. Where the visible word does not name its own destination, an
  `aria-label` supplies the row it belongs to.

## Destination stills

A name like "Plectis" does not say whether it is a website, a repository, or
a word. The index now names the first row **Plectis website**, and each route
carries a screenshot of the page that link actually opens.

- Below 1280px, the still sits under the row it belongs to.
- At 1280px and up, the stills occupy a quiet panel on the right. Hover or
  focus a route (or an exit inside it) and the panel swaps to that landing.
  Hovering a problem number switches the panel to its 7:9 question sheet.

The files in `assets/previews/` are captures of the live URLs, not drawings.
If a destination page changes enough that the still lies, recapture it:

```sh
# hero 1280w JPEG, thumb 640w JPEG, from a live screenshot
sips -Z 1280 -s format jpeg -s formatOptions 72 \
     --out assets/previews/<id>.jpg /tmp/<id>.png
sips -Z 640 -s format jpeg -s formatOptions 68 \
     --out assets/previews/<id>-640.jpg /tmp/<id>.png
```

Do not invent browser chrome around the still. The screenshot is the picture
of the landing; the caption names it.

## Social preview

The share card is a separate object from the destination stills. It has to
communicate the mathematical first contact before a reader opens the page, so
`assets/og-frontier.svg` is the source of truth for the eight-problem
composition. `index.html` points Open Graph and Twitter at the 1200 by 630 PNG
because social crawlers do not reliably render SVG.

The card names the open-source mathematics project and the eight problem
subjects. These are topic labels, not a ranking of results or a claim that any
problem has been solved. The checked results and remaining work live on the
current problem pages.

After changing the SVG, regenerate and inspect the PNG before changing the
metadata:

```sh
sips -s format png assets/og-frontier.svg --out assets/og-frontier.png
sips -g pixelWidth -g pixelHeight -g format assets/og-frontier.png
```

The expected delivery format is a 1200 by 630 PNG. Keep the `og:image`,
`og:image:width`, `og:image:height`, `og:image:alt`, `twitter:card`, and
`twitter:image` fields in `index.html` synchronized with that file.

## The pair

This page and the Plectis site each name the other, and neither has a build step
that could check it.

- Down: the `Run` row of the route index points at `/plectis/`.
- Up: the Plectis header carries `Will Cook / Plectis` beside its wordmark, and
  its colophon carries a `Front door` row reading *Will Cook: public work*.

Those labels preserve the cross-site return route: `Will Cook` is this page's
`<h1>`, and *public work* describes the front door in the Plectis colophon. They
must not be used as a paraphrase of the programme line, which is now **Eight
open Erdős problems**. If you change either return label, change the Plectis
header, its colophon, and `PARENT_SITE_LABEL` in that site's builder in the same
pass.

## Archived plate

`assets/plate-01.jpg` is former artwork: Wet Proof, plate 01, seed 5 at
2560x1600, made by `assets/plate-01.lab.py`. It is retained for provenance in
an inert HTML template, not shown or loaded by the root front door. The
programme index and portrait problem sheets now carry the visual hierarchy.

The ladder below is archival source material. Do not restore it to the reading
surface as incidental polish: decoration must not compete with the programme.

```sh
# JPEG rungs. sips ships with macOS and writes progressive JPEG by default,
# which is what the lab wrote; formatOptions 75 is also its default, stated
# here so the files do not move if that default ever does.
for W in 960 1280; do
  sips -Z $W -s format jpeg -s formatOptions 75 \
       --out assets/plate-01-$W.jpg assets/plate-01.jpg
done

# AVIF rungs, via a lossless PNG so the resize is not encoded twice.
# avifenc comes from libavif (brew install libavif).
for W in 960 1280 1920 2560; do
  sips -s format png -Z $W --out /tmp/plate-$W.png assets/plate-01.jpg
  avifenc -q 66 -s 2 -y 444 -j all /tmp/plate-$W.png assets/plate-01-$W.avif
done
```

| Rung | AVIF | JPEG |
|---|---|---|
| 960w | 29,252 B | 79,662 B |
| 1280w | 44,641 B | 129,922 B |
| 1920w | 72,397 B | none |
| 2560w | 123,399 B | 246,660 B (`plate-01.jpg`) |

Three of those choices are worth a sentence, since they are the ones a later
pass would otherwise have to rediscover. `-q 66` is where AVIF comes level with
the JPEG rung on SSIM against the same reference, at about a third of its size;
the dark plum ground is where loss would show first on this plate, so that is
the region to look at if the quality is ever lowered. `-y 444` keeps full chroma
resolution, because the one hard edge in the picture is a thin saturated blue
membrane against orange, and 4:2:0 blurs exactly that. The JPEG ladder stops at
1280 because a 1920 rung would encode larger than the 2560 original below it.

AVIF is offered and WebP is not. WebP came out slightly smaller here but
measurably worse at the same size, and the browsers that read WebP but not AVIF
are a narrow band that the JPEG already serves correctly. Two formats is the
most this page should carry.

Any intentional return of the artwork requires a fresh visual and performance
review; do not reinstate it as an eager decorative hero.

## The mark

`assets/favicon.svg` is a copy, not a fork. The source of truth lives in the
Plectis repository, where `tools/brand/plectis_favicon.py` renders the rasters
and the pinned day/night siblings from it. If the mark changes there, recopy it
here; do not edit it in place.

None of the icons in `site.webmanifest` is declared `maskable`, and none should
be. A maskable icon is cropped to a circle inscribed in the middle 80% of the
canvas, and the braid runs the full height of every raster we have. Declaring
it maskable cuts the top and bottom strands off on Android. A real maskable
variant would need its own padded render from the Plectis tool, not a flag
here. Until that exists, the plain `any` purpose is the honest one: the
launcher then supplies its own container rather than cutting into the mark.

## Licence

The mark and page content are © Will Cook.
