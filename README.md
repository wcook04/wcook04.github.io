# Legacy host-root website

**The current website is [Plectis](https://wcook04.github.io/plectis/).**

This repository contains Will Cook's deprecated host-root homepage and host-wide files for `wcook04.github.io`. It is retained for those files and the historical source; the old reading map is not the current project introduction.

[Current website](https://wcook04.github.io/plectis/) · [Mathematics](https://wcook04.github.io/plectis/maths/) · [Papers](https://wcook04.github.io/plectis/docs/papers.html) · [Videos](https://wcook04.github.io/plectis/#videos)

## Explore with an agent

The websites are agent navigable: start with [the plain-text entry](https://wcook04.github.io/llms.txt) or [the Markdown project directory](https://wcook04.github.io/agent-guide.md), then follow a project's map and source records without running JavaScript.

```sh
curl -fsSL https://wcook04.github.io/llms.txt
```

The directory routes to Plectis, Atlas and Zenith. The root reading map is a retained snapshot; each destination owns its current claims. Agent files load only when requested and add no runtime work to the homepage.

## Repository map

| Path | Purpose |
|---|---|
| `index.html`, `404.html` | Legacy homepage and host-root error page. |
| `favicon.ico`, `site.webmanifest`, `robots.txt`, `sitemap.xml` | Host-wide identity and search-discovery files. |
| [`.nojekyll`](.nojekyll) | Serve the authored static files directly, including raw Markdown agent routes. |
| [`llms.txt`](llms.txt), [`agent-guide.md`](agent-guide.md) | Static agent entry and project directory; maintained here. |
| `assets/` | Existing brand assets, destination screenshots and archived artwork. |
| `data/` | The historical reading map and glossary snapshot. |
| `scripts/` | Builders and checks for the legacy page. |

The current Plectis site is deployed separately from the `gh-pages` branch of [wcook04/plectis](https://github.com/wcook04/plectis). Changes to this repository do not update that site. Preserve the host-wide files when maintaining or retiring the legacy page.

## Maintain the retained source

Python 3 is sufficient. From a fresh clone:

```sh
git clone https://github.com/wcook04/wcook04.github.io.git
cd wcook04.github.io
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/build_absolute_frontier.py --check
python3 scripts/build_glossary_term_layer.py --check
python3 scripts/check_frontier_surface.py
```

To inspect the historical page locally, run `python3 -m http.server 8000` and open [localhost:8000](http://localhost:8000). Update an owning script before regenerating a marked HTML region.

## Editing public wording

Write for someone who has never used this software or read about the project.
Name the person or program, what it does, and the object it reads or changes.
For “check” or “verify”, say which program compares which evidence and what its
answer establishes. For example, “Lean verifies whether the proof follows from
its assumptions” is more useful than “the work is checked”. Define technical
terms where a reader first needs them. Keep the exact mathematical statements,
assumptions, attribution and unsolved questions unchanged.

Review the complete page, its link labels, previews, error page and generated
text. Edit `scripts/build_absolute_frontier.py` for the marked reading-map and
problem-preview sections, then rebuild those sections and the glossary links.
Use the existing layout and inspect the finished page at laptop and phone sizes;
a phrase scan alone cannot show whether the explanation makes sense.

## Credit and licence

The mark and page content are © Will Cook. Linked projects retain their own authorship, licences and acknowledgements; follow the current Plectis site for those records.
