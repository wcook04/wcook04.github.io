# Legacy host-root website

**The current website is [Plectis](https://wcook04.github.io/plectis/).**

This repository contains Will Cook's deprecated host-root homepage and host-wide files for `wcook04.github.io`. It is retained for those files and the historical source; the old reading map is not the current project introduction.

[Current website](https://wcook04.github.io/plectis/) · [Mathematics](https://wcook04.github.io/plectis/maths/) · [Papers](https://wcook04.github.io/plectis/docs/papers.html) · [Videos](https://wcook04.github.io/plectis/#videos)

## Repository map

| Path | Purpose |
|---|---|
| `index.html`, `404.html` | Legacy homepage and host-root error page. |
| `favicon.ico`, `site.webmanifest`, `robots.txt` | Host-wide identity and search-discovery files. |
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

## Credit and licence

The mark and page content are © Will Cook. Linked projects retain their own authorship, licences and acknowledgements; follow the current Plectis site for those records.
