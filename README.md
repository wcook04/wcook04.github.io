# Redirect to Plectis

The old Will Cook homepage has been removed. The current website is **[Plectis](https://wcook04.github.io/practical-formal-verification/)**.

This repository keeps the root address `wcook04.github.io` forwarding to Plectis. It contains no portfolio, research snapshots, artwork or page-generation tools. Git history retains the removed source.

## Introduction

| Film | Watch |
|---|---|
| Plectis introduction | [YouTube](https://www.youtube.com/watch?v=uO2lbstEH9M) |

## Read with an agent

Plectis is agent navigable. Its [plain-text entry](https://wcook04.github.io/practical-formal-verification/llms.txt) links papers, proof files, machine-readable maps and the records needed to follow their relationships.

```sh
curl -fsSL https://wcook04.github.io/practical-formal-verification/llms.txt
```

The small [root entry](llms.txt) and [project pointers](agent-guide.md) preserve existing discovery addresses. They direct agents to the current websites.

## Repository map

| Path | Purpose |
|---|---|
| `index.html` | Immediate static redirect, canonical URL and ordinary link to Plectis; no JavaScript required. |
| `404.html` | Gives old or unknown root addresses the same route to Plectis. |
| `llms.txt`, `agent-guide.md` | Text pointers to the current websites. |
| `robots.txt`, `sitemap.xml` | Host-wide crawling rules and the current Plectis sitemap. |
| `.nojekyll` | Serves static files and raw Markdown directly. |
| `scripts/check_redirect_site.py` | Validates the redirects, discovery files and retired repository layout. |
| `tests/test_redirect_site.py` | Tests missing routes, stale content and staged-file validation. |
| `.github/workflows/public-site.yml` | Runs the validation in CI. |

## Maintain the redirect

Edit the redirect files directly. Do not restore the old homepage, its assets, its data snapshots or its generators. Make website changes in the owning project repository instead.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/check_redirect_site.py
# Validate the files actually staged for a commit:
python3 scripts/check_redirect_site.py --index
```

Pushing `main` publishes these static files through GitHub Pages. Keep Pages enabled. The project paths `/plectis/`, `/plectis-atlas/`, `/plectis-zenith/` and the historical `/microcosm-substrate/` are deployed by their own repositories. This repository must not create directories at those paths or add rules that block them.

## Removed addresses

`/` and `/index.html` now point to Plectis. The former site had no other authored HTML pages beyond its error page. Its `assets/`, `data/`, favicon and web manifest have been removed; they have no replacement snapshot at this root. The root sitemap no longer lists the retired homepage.

The HTML uses an immediate meta refresh because GitHub Pages does not provide repository-level HTTP redirect rules. Its canonical URL and ordinary link also work for readers that do not follow the refresh. Both HTML pages request `noindex, follow`; the host-wide robots file continues to allow the project websites.
