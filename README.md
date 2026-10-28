# Will Cook's home page

**[wcook04.github.io](https://wcook04.github.io/)** is a map of my websites,
the films that explain them and the repositories that hold their code. Each
website is its own project with its own repository; this page links to all of
them, and each of them links back here.

| Website | What it is for | Source |
|---|---|---|
| [Plectis Mathematics](https://wcook04.github.io/practical-formal-verification/maths/) | Eight Erdős problems researched with AI: papers, computer-checked proofs of partial results and the approaches that failed. | [plectis-erdos](https://github.com/wcook04/plectis-erdos), [plectis-erdos-lean](https://github.com/wcook04/plectis-erdos-lean) |
| [Lean Exposition](https://wcook04.github.io/lean-exposition-site/) | One result about the Sherrington–Kirkpatrick model of magnets, explained three ways and linked to a map of the argument. | [lean-exposition](https://github.com/wcook04/lean-exposition) |
| [Plectis Atlas](https://wcook04.github.io/plectis-atlas/) | OpenAI's maths papers beside the reports that outside groups wrote about them. | [plectis-atlas](https://github.com/wcook04/plectis-atlas) |
| [Practical Formal Verification](https://wcook04.github.io/practical-formal-verification/docs/) | 88 Python components; for twelve, proofs that particular calculations follow their written requirements. | [practical-formal-verification](https://github.com/wcook04/practical-formal-verification) |
| [Zenith](https://wcook04.github.io/plectis-zenith/) | Experiments on whether records of past mistakes help AI models test and repair code. | [plectis-zenith](https://github.com/wcook04/plectis-zenith) |

## How the page is made

[`sites.json`](sites.json) is the one list of websites, tools, repositories
and films. Each website and tool names its repositories by id from the
top-level `repos` list, and the build refuses a repository that is unknown or
on no website or tool. The page is static HTML built from it by
`scripts/build_hub.py`; it needs no script to read and loads nothing from
another host. Films open on YouTube in a new tab. A film that is not out yet
shows a frame marked "In preparation" and has no link.

The map near the top has one row per project: its videos, its website or
tool, its code on GitHub. Without a script the grid alone groups each row;
[`assets/hub-map.js`](assets/hub-map.js) draws the lines between the columns
and lights the row a reader points at or tabs into. It is adapted from the
Plectis film map's cables (and through them from Magic UI's AnimatedBeam, MIT;
the notice is in the file). Below the full map's width each row reads as a
list: the website, then its videos, then its code. The Videos band under the
map gives each film's description.

[`docs/family.md`](docs/family.md) describes what every website shares: the
"Will Cook / site" ladder at the start of its header, the film slots, and the
list of sister sites in its footer. The shared styles are
[`assets/family/family.css`](assets/family/family.css), adapted from the
Plectis site's film and header components. Each website keeps a copy of
`sites.json` and that stylesheet beside its own source.

## Add a released film

1. In `sites.json`, give the film its `youtube` address, `duration_seconds`
   and `still` (for example `"assets/films/sk-no-gap"`), and its published
   title and description.
2. Make the still's two page-sized copies from the uploaded thumbnail:

   ```sh
   cwebp -q 80 -m 6 -resize 640 0 thumbnail.png -o assets/films/<id>-640.webp
   cwebp -q 80 -m 6 -resize 1280 0 thumbnail.png -o assets/films/<id>-1280.webp
   ```

3. Rebuild and check, then commit and push `main`, which publishes the page:

   ```sh
   python3 scripts/build_hub.py
   python3 -m unittest discover -s tests -p 'test_*.py'
   python3 scripts/check_hub_site.py
   ```

4. Copy `sites.json` and the two stills to the website the film belongs to
   (its `family.json`), rebuild that site and publish it, so its film slot
   shows the film too.

## Repository map

| Path | Purpose |
|---|---|
| `index.html`, `404.html` | Built from `sites.json`; do not edit by hand. The 404 page forwards old `/plectis/...` addresses to the same page under `/practical-formal-verification/`. |
| `sites.json` | Websites, tools, repositories and films: the source for this page and for every site's film slots. |
| `assets/hub.css`, `assets/hub.js`, `assets/theme-init.js` | The page's styles and its day and night switch. The theme script and the tokens are the Plectis site's. |
| `assets/hub-map.js` | The map's lines between videos, websites and repositories, and the lit row. |
| `assets/family/family.css`, `docs/family.md` | What every website shares, and how to use it. |
| `assets/films/`, `assets/sites/` | Film stills (the uploaded thumbnails) and pictures of each website's first screen, in both schemes. |
| `assets/fonts/` | Plectis Serif (STIX Two Text) and Plectis Sans (Source Sans 3) subsets, with their licences. |
| `llms.txt`, `agent-guide.md`, `robots.txt`, `sitemap.xml`, `sitemap-home.xml` | Entries for agents and crawlers. |
| `scripts/check_hub_site.py`, `tests/` | Checks run by `.github/workflows/public-site.yml`. |

Pushing `main` publishes the page through GitHub Pages. Keep Pages enabled.
The project paths `/practical-formal-verification/`, `/plectis-atlas/`,
`/plectis-zenith/` and `/lean-exposition-site/` are served by their own
repositories; this repository must not create folders at those paths, and the
check refuses them.

Refresh a website's picture by capturing its first screen at 1440×900 in both
schemes and converting it with `cwebp -q 80 -m 6 -resize 720 0` and
`-resize 1440 0` into `assets/sites/<id>-<light|dark>-<720|1440>.webp`.
