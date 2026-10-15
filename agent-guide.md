# Explore Will Cook's public websites with an agent

An AI agent can read these websites by downloading their text and data files. It does not need to control a browser. The entry files below list the papers, programs and map data available on each site. Download the smaller index first, then the files needed to answer your question. The links help you find evidence; they do not establish whether a research result is correct.

## Choose a website

| Question | Website | Agent entry | Source repository |
| --- | --- | --- | --- |
| What is Plectis, and what research, papers and tools can I inspect? | [Plectis](https://wcook04.github.io/plectis/) | [Plectis agent entry](https://wcook04.github.io/plectis/llms.txt) | [Toolkit](https://github.com/wcook04/plectis), [Erdős research](https://github.com/wcook04/plectis-erdos) and [Lean source](https://github.com/wcook04/plectis-erdos-lean) |
| What did OpenAI's mathematics release contain, and what did outside readers find? | [Plectis Atlas](https://wcook04.github.io/plectis-atlas/) | [Atlas agent entry](https://wcook04.github.io/plectis-atlas/llms.txt) | [Atlas source](https://github.com/wcook04/plectis-atlas) |
| How does Zenith use experiments to investigate software and repair errors? | [Plectis Zenith](https://wcook04.github.io/plectis-zenith/) | [Zenith agent entry](https://wcook04.github.io/plectis-zenith/llms.txt) | [Zenith source](https://github.com/wcook04/plectis-zenith) |

```sh
curl -fsSL https://wcook04.github.io/llms.txt
curl -fsSL https://wcook04.github.io/plectis-atlas/llms.txt
```

## Navigate maps without rendering them

Each website publishes its map as JSON, a text format that programs can read. A map contains records for papers, results or programs, and links between those records. Download the index, find a record by its identifier or title, and follow its links to the original source. Read what each link means: a citation, a dependency and membership in a group describe different relationships. When reporting a result, name its author, source version, stated result and remaining uncertainty.

The root homepage's [reading-map JSON](https://wcook04.github.io/data/absolute-frontier.json) contains `systems` with paper identifiers and `href` destinations, and `items` with `problem`, `paper_href`, `page_href` and `long_records`. Its `source_hashes` identify the versions of the source files used to build that snapshot. This is historical data: follow the destination site's current entry before describing present research status. The homepage at this address is an older introduction to Plectis.

## Retained and related routes

Microcosm was the project's earlier name. Its [old website](https://wcook04.github.io/microcosm-substrate/) forwards to Plectis. The [old-to-new address list](https://wcook04.github.io/microcosm-substrate/legacy-route-manifest.json) lets an agent find the current destination of a published link.

[Safety Core](https://github.com/wcook04/safety-core) and [One Checkout](https://github.com/wcook04/one-checkout) are repository projects with their own README and agent instructions. They have no separate website in this directory.

These files are downloaded only when someone requests them. Adding them does not make the homepage run more JavaScript or download extra data in the background.
