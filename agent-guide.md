# Explore Will Cook's public websites with an agent

Start with the website that owns your question. Each entry below is plain text and links to public source data; a browser or JavaScript is not required. Follow the smaller index before downloading a complete corpus. This directory is navigation, not evidence that a research claim is true.

## Choose a website

| Question | Website | Agent entry | Source repository |
| --- | --- | --- | --- |
| What is Plectis, and what research, papers and tools can I inspect? | [Plectis](https://wcook04.github.io/plectis/) | [Plectis agent entry](https://wcook04.github.io/plectis/llms.txt) | [Toolkit](https://github.com/wcook04/plectis), [Erdős research](https://github.com/wcook04/plectis-erdos) and [Lean source](https://github.com/wcook04/plectis-erdos-lean) |
| What did OpenAI's mathematics release contain, and what did outside readers find? | [Plectis Atlas](https://wcook04.github.io/plectis-atlas/) | [Atlas agent entry](https://wcook04.github.io/plectis-atlas/llms.txt) | [Atlas source](https://github.com/wcook04/plectis-atlas) |
| What do the executable-investigation experiments and research graph show? | [Plectis Zenith](https://wcook04.github.io/plectis-zenith/) | [Zenith agent entry](https://wcook04.github.io/plectis-zenith/llms.txt) | [Zenith source](https://github.com/wcook04/plectis-zenith) |

```sh
curl -fsSL https://wcook04.github.io/llms.txt
curl -fsSL https://wcook04.github.io/plectis-atlas/llms.txt
```

## Navigate maps without rendering them

The website-specific entries link to their own graph, index and record interfaces. Fetch that site's index, choose an object by its published identifier or title, then follow its relation and source URLs. Preserve the record's attribution, scope and revision when reporting what you found. An edge in a map is a navigation relationship; it does not establish a theorem, review or endorsement.

The root homepage's [reading-map JSON](https://wcook04.github.io/data/absolute-frontier.json) contains `systems` with paper identifiers and `href` destinations, and `items` with `problem`, `paper_href`, `page_href` and `long_records`. Its `source_hashes` identify the snapshot's inputs. It is historical: follow the destination site's current entry before describing present research status. This host-root page is not the current Plectis introduction.

## Retained and related routes

[Microcosm](https://wcook04.github.io/microcosm-substrate/) is the retired name and its website forwards to Plectis. The [compatibility manifest](https://wcook04.github.io/microcosm-substrate/legacy-route-manifest.json) preserves old published URLs.

[Safety Core](https://github.com/wcook04/safety-core) and [One Checkout](https://github.com/wcook04/one-checkout) are repository projects with their own README and agent instructions. They have no separate website in this directory.

The published files are static and fetched only when requested. These agent routes add no JavaScript, background data fetches or rendering work to the human-facing homepage.
