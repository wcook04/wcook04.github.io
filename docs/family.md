# One family of websites

Will Cook's websites are separate projects with separate repositories, but a
reader moving between them should always know where they are and how to get
back. Every site carries the same three elements, implemented in its own code:

1. **A shared header**: the woven logo links to Will's home page,
   <https://wcook04.github.io/>, which lists his projects and videos. Next to
   it, the site's own name and symbol link to that site's front page.
2. **Video cards** for recordings about that site: a thumbnail, play symbol
   and running time once the video is on YouTube, and a card marked "In
   preparation" until then.
3. **Links to the other sites** in its footer: the websites by name, and
   "All projects and videos" back to the home page.

The list of websites, videos and repositories is [`sites.json`](../sites.json)
in this repository. A website's `repos` names repositories by id from its
top-level `repos` list (name, address and a one-sentence description). Each site keeps a copy beside its own source (`family.json`) and
renders from it at build time, so no page requests anything from another host
or depends on JavaScript to show its videos.

The home page features the current introduction. Earlier introductions stay in
the final `earlier-introductions` group, below the current videos, with the
version and "older version" near the start of each title so they remain clear
when a title is shortened on screen.

The shared styles are [`assets/family/family.css`](../assets/family/family.css).
Copy the file unchanged and map the site's tokens onto its `--fam-*` names:

```css
:root {
  --fam-page: var(--ground);     /* the site's page colour */
  --fam-surface: var(--surface);
  --fam-ink: var(--ink);
  --fam-ink-soft: var(--ink-2);
  --fam-muted: var(--ink-2);
  --fam-faint: var(--ink-3);
  --fam-rule: var(--rule);
  --fam-rule-strong: var(--rule-strong);
  --fam-accent: var(--accent);   /* links and focus */
  --fam-serif: var(--font-serif);
  --fam-sans: var(--font-sans);
}
```

## The lockup (29 October 2026)

The start of every site's header is the **lockup**, which replaces the older
"Will Cook / site" ladder:

    [Plectis plait] | [site mark] Site name

- The **Plectis plait** links to the home page, <https://wcook04.github.io/>,
  which lists every project and video. Its accessible name is "Will Cook: all
  projects and videos". Copy [`assets/family/marks/plectis.svg`](../assets/family/marks/plectis.svg)
  beside the site and show it as an `<img>`; it carries its own day and night
  palettes.
- A short upright **rule** separates the two links.
- The **site mark and name** link to that site's own front page. The mark is
  inline SVG drawn from the site's inks, so it follows the theme switch.

Marks: Lean Exposition keeps its rising graph with its dot, Plectis Atlas its
tiles. New marks, in [`assets/family/marks/`](../assets/family/marks/):
`zenith.svg` (the sun at its highest point on its arc), `mathematics.svg`
(dots closing on a limit, for Plectis Mathematics) and `verification.svg`
(the explorer's proof flower, for Practical Formal Verification). Paste their
`<svg>` inline. [`assets/family/marks/preview.html`](../assets/family/marks/preview.html)
previews every mark and lockup in both themes.

```html
<span class="fam-lockup">
  <a class="fam-lockup__home" href="https://wcook04.github.io/" rel="author" title="All of Will Cook's projects and videos">
    <img src="assets/plectis.svg" alt="Will Cook: all projects and videos" width="26" height="26">
  </a>
  <span class="fam-lockup__rule" aria-hidden="true"></span>
  <a class="fam-lockup__site" href="./">
    <!-- the site mark, inline, aria-hidden="true" -->
    <span class="fam-lockup__name" translate="no">Zenith</span>
  </a>
</span>
```

Map two more tokens for the marks: `--fam-mark-warm` (the Plectis brick red:
`#9a322c` by day, `#e67b6d` by night) and `--fam-mark-cool` (the steel azure:
`#2a5982` by day, `#93c5e6` by night), and `--fam-page` for the flower's
centre ring.

## Markup

Older headers used the markup below. New pages use the shared header shown above:

```html
<span class="fam-ladder">
  <a class="fam-ladder__up" href="https://wcook04.github.io/" rel="author">Will Cook</a>
  <span class="fam-ladder__sep" aria-hidden="true">/</span>
  <!-- the site's own wordmark, linking to its home page -->
</span>
```

A published video. The thumbnail and the title open the same video, so only the
title is in the Tab order, and it says the running time in words:

```html
<figure class="film-slot">
  <a class="film-slot__frame" href="https://www.youtube.com/watch?v=ID" target="_blank"
     rel="noopener noreferrer" aria-hidden="true" tabindex="-1">
    <img src="assets/films/atlas-v3-640.webp"
         srcset="assets/films/atlas-v3-640.webp 640w, assets/films/atlas-v3-1280.webp 1280w"
         sizes="(min-width: 960px) 480px, 100vw"
         alt="" width="1280" height="720" loading="lazy" decoding="async">
    <span class="film-slot__play"></span>
    <span class="film-slot__time">5:27</span>
  </a>
  <figcaption class="film-slot__caption">
    <p class="film-slot__title"><a href="https://www.youtube.com/watch?v=ID" target="_blank"
       rel="noopener noreferrer">Plectis Atlas: compare maths papers with the reports that check them<span
       class="sr-only">, video on YouTube, 5 minutes 27 seconds</span></a></p>
    <p class="film-slot__text">One or two sentences from the video's description.</p>
  </figcaption>
</figure>
```

A video in preparation. It has no link, because there is nothing to open yet:

Tests for this state must create a fixture with `youtube`, `still` and
`duration_seconds` set to `null`. The real registry may have no videos left in
preparation after a release.

```html
<figure class="film-slot film-slot--pending">
  <div class="film-slot__frame film-slot__frame--pending" aria-hidden="true">
    <span class="film-slot__series">Lean Exposition</span>
    <span class="film-slot__name">SK reading interface</span>
    <span class="film-slot__status">In preparation</span>
  </div>
  <figcaption class="film-slot__caption">
    <p class="film-slot__title">SK reading interface</p>
    <p class="film-slot__meta">Video in preparation</p>
    <p class="film-slot__text">One sentence on what the video will show.</p>
  </figcaption>
</figure>
```

On the Plectis pages the figure also carries `data-term-auto="off"`, so the
glossary linker leaves a video's title and description as written.

`film-slot--small` and `film-slot--large` change only the play chip and the
title size. `film-slot--inline` sets a small still beside its title, for a
video about a tool on a page whose main subject is something else (the Maths
Map video beside the map of results). The sister sites:

```html
<nav class="fam-sites" aria-label="Will Cook's websites">
  <p class="fam-sites__title">More from Will Cook</p>
  <ul class="fam-sites__list">
    <li><a href="https://wcook04.github.io/practical-formal-verification/maths/">Mathematics</a></li>
    <li><a href="https://wcook04.github.io/lean-exposition-site/" aria-current="page">SK exposition</a></li>
    <!-- … every site in sites.json order, then: -->
    <li><a href="https://wcook04.github.io/">All projects and videos</a></li>
  </ul>
</nav>
```

On the site being read, its own entry keeps `aria-current="page"` and is
shown, not removed, so the list reads the same everywhere.

## Rules

- **No embedded players.** A video opens on YouTube in a new tab. Pages load
  nothing from YouTube or any other host, and a site's content security
  policy needs no change.
- **Never invent a link.** A video without a `youtube` value is shown in
  preparation. Its title is the working title, and its description says what
  it will show, taken from its script.
- **Stills are the uploaded thumbnails**, served as 640 and 1280 px WebP
  copies made with `cwebp -q 80 -m 6 -resize <width> 0`, the settings of the
  Plectis site's `plectis_thumbnail_cards.py web`. They live in this
  repository's `assets/films/`; a site copies the ones it shows.
- **Words.** British spelling, sentence case, no em dashes. Name things by
  what they are: "PDF, 26 pages", not "Download". Call the recordings videos
  or walkthroughs. Keep technical names such as the `films` registry key,
  `film-slot` CSS class and existing asset paths unchanged.
- **Colour.** The family's ground is the warm paper of the Plectis sites
  (`#f8f0e2` by day, `#1c1526` at night) with ink `#191520` / `#f2e6d4`. A
  site keeps its own meaning-carrying colours (a map's categories, a check's
  outcome) on that ground.

## Add a published video

Follow the [home page’s release steps](../README.md#add-a-published-video) to
update the registry and thumbnail pair, run the checks, and publish the page.
That procedure also covers copying the registry and stills to the sites that
show the video. Keep one set of release instructions there; this document owns
the shared components and their markup.
