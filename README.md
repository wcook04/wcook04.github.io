# Will Cook's home page

**[wcook04.github.io](https://wcook04.github.io/)** is a map of my websites,
the videos that explain them and the repositories that hold their code. Each
website is its own project with its own repository; this page links to all of
them, and each of them links back here. Start with the introduction video or
open a project directly; its details link to the papers, maps, videos and code.

[![Will Cook’s home page: an introduction video and routes into the projects](assets/sites/home-light-1440.webp)](https://wcook04.github.io/)

- **[Plectis Mathematics](https://wcook04.github.io/practical-formal-verification/map/)**. Eight Erdős problems researched with AI: papers, computer-checked proofs of partial results and the approaches that failed.
  Source: [plectis-erdos](https://github.com/wcook04/plectis-erdos), [plectis-erdos-lean](https://github.com/wcook04/plectis-erdos-lean).

- **[Lean Exposition](https://wcook04.github.io/lean-exposition-site/)**. One result about the Sherrington–Kirkpatrick model of magnets, explained three ways and linked to a map of the argument.
  Source: [lean-exposition](https://github.com/wcook04/lean-exposition).

- **[Proof Reader](https://wcook04.github.io/proof-reader/)**. A published paper with its Lean proof beside it.
  Source: [proof-reader](https://github.com/wcook04/proof-reader).

- **[Plectis Atlas](https://wcook04.github.io/plectis-atlas/)**. OpenAI's maths papers beside the reports that outside groups wrote about them.
  Source: [plectis-atlas](https://github.com/wcook04/plectis-atlas).

- **[Practical Formal Verification](https://wcook04.github.io/practical-formal-verification/explorer/)**. 88 Python components; for twelve, proofs that particular calculations follow their written requirements.
  Source: [practical-formal-verification](https://github.com/wcook04/practical-formal-verification).

- **[Zenith](https://wcook04.github.io/plectis-zenith/)**. Experiments on whether records of past mistakes help AI models test and repair code.
  Source: [plectis-zenith](https://github.com/wcook04/plectis-zenith).

The page also links to [Safety Core](https://github.com/wcook04/safety-core)
and [One Checkout](https://github.com/wcook04/one-checkout), two tools for
working with coding agents. Code Map has a demonstration video; its source is
private.

## Preview and check locally

The build and checks need Python 3 and use only its standard library:

```sh
python3 scripts/build_hub.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_hub_site.py
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [localhost:8000](http://127.0.0.1:8000/) to browse the page. Project links
open the published websites. Edit `sites.json` and rebuild to change the list;
`index.html` is generated.

## Old Plectis addresses

The Plectis website moved from `/plectis/` to `/practical-formal-verification/`
when its repository was renamed, and GitHub Pages does not forward a renamed
repository's pages. This repository answers the old addresses instead. Every
page listed in [`plectis-paths.txt`](plectis-paths.txt) has a small page at its
old address under `plectis/` that forwards to the same page at the new address
(the old front door, `/plectis/`, opens this home page). They answer 200, so
links already sent in emails and film descriptions keep working without a
script; [`assets/redirect.js`](assets/redirect.js) keeps the query and
fragment. Any other old address, such as a PDF, gets the 404 page, whose same
script forwards it. After the Plectis website adds pages, run
`python3 scripts/build_hub.py --refresh-plectis-paths`.

## How the page is made

[`sites.json`](sites.json) is the one list of websites, tools, repositories
and films. Each website and tool names its repositories by id from the
top-level `repos` list, and the build refuses a repository that is unknown or
on no website or tool. The page is static HTML built from it by
`scripts/build_hub.py`; it needs no script to read and loads nothing from
another host. Films open on YouTube in a new tab. A film that is not out yet
shows a frame marked "In preparation" and has no link.

The page opens with the introduction film, then lists the projects in two
groups (`index_groups` in `sites.json`): one line each, with a picture, its
name, one sentence and the way in (the website, or the code). Each line opens
beneath itself into that project's own small map: its videos, the website's
main places, its code on GitHub. "Show all details" opens every line,
which is the whole map. Without a script every line is open.
[`assets/hub-map.js`](assets/hub-map.js) draws the lines inside an open
project and lights the one a reader points at or tabs into. It is adapted from
the Plectis film map's cables (and through them from Magic UI's AnimatedBeam,
MIT; the notice is in the file). Below the map's width an open project reads
as a list. A link to `/#zenith` (any project's id) arrives with that project
open. The Videos band shows the current videos first, labelled with their
projects. Earlier introductions have their own section below; videos still
being made are listed by title.

[`docs/family.md`](docs/family.md) describes what every website shares: the
linked Plectis mark and site name in its header, the film slots, and the list
of sister sites in its footer. The shared styles are
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
| [`index.html`](index.html), [`404.html`](404.html) | Built from `sites.json`; do not edit by hand. The 404 page forwards old `/plectis/...` addresses to the same page under `/practical-formal-verification/`. |
| [`sites.json`](sites.json) | Websites, tools, repositories and films: the source for this page and for every site's film slots. |
| [`assets/hub.css`](assets/hub.css), [`assets/hub.js`](assets/hub.js), [`assets/theme-init.js`](assets/theme-init.js) | The page's styles and its day and night switch. The theme script and the tokens are the Plectis site's. |
| [`assets/hub-map.js`](assets/hub-map.js) | The lines inside an open project between its videos, website and repositories, and the lit row. |
| [`assets/family/family.css`](assets/family/family.css), [`docs/family.md`](docs/family.md) | What every website shares, and how to use it. |
| [`assets/films/`](assets/films/), [`assets/sites/`](assets/sites/) | Film stills and pictures of each website's first screen. `home-light-1440.webp` is the home page's README and sharing preview. |
| [`assets/fonts/`](assets/fonts/) | Plectis Serif (STIX Two Text) and Plectis Sans (Source Sans 3) subsets, with their licences. |
| [`llms.txt`](llms.txt), [`agent-guide.md`](agent-guide.md), [`robots.txt`](robots.txt), [`sitemap.xml`](sitemap.xml), [`sitemap-home.xml`](sitemap-home.xml) | Entries for agents and crawlers. |
| [`scripts/check_hub_site.py`](scripts/check_hub_site.py), [`tests/`](tests/) | Checks run by `.github/workflows/public-site.yml`. |

Pushing `main` publishes the page through GitHub Pages. Keep Pages enabled.
The project paths `/practical-formal-verification/`, `/plectis-atlas/`,
`/plectis-zenith/`, `/lean-exposition-site/` and `/proof-reader/` are served by their own
repositories; this repository must not create folders at those paths, and the
check refuses them.

Refresh a website's picture by capturing its first screen at 1440×900 in both
schemes and converting it with `cwebp -q 80 -m 6 -resize 720 0` and
`-resize 1440 0` into `assets/sites/<id>-<light|dark>-<720|1440>.webp`.
