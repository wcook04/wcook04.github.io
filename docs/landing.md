# The home page: the weave and the stage

How the home page is designed and the rules it follows. The builder is
[`scripts/landing.py`](../scripts/landing.py); its data is `sites.json` and
`explorer.json`; its look and behaviour are `assets/landing.css` and
`assets/landing.js`. Change the data or the builder, then run
`python3 scripts/build_hub.py`; never edit `index.html` by hand.

## Design read

A front door for a body of work, for a stranger with one minute (lab staff from an email link, mathematicians,
lay visitors), in the register of the films themselves: flat night ground, lit paper, steel and brick.
One aesthetic risk: the page's index is a drawing of the real graph (the weave), and the selected row lights
up as a cream paper band set in Barlow Condensed, the films' own title band. Everything else stays quiet.

The one idea the page must carry: AI is used to make AI output understandable at every level of detail, and
it gets better as models do. The page shows that idea as its horizontal axis: every project is a thread that
runs from a 90-second film on the left to the source on the right.

## Structure (DOM order is the no-JavaScript reading order)

1. Skip link. Header, one line, 60px: logo mark + "Will Cook"; nav "Projects" (#work), "Every video" (all.html#films),
   "Every link" (all.html), "About and contact" (#about). No theme switch: this page has one scheme, the films' night ground
   (`color-scheme: dark`). Dropped on purpose: the page is the films' stage.
2. Hero, left-aligned on the container's left edge, with two text elements (the sentence about
   the levels sits under the weave, where the marks are):
   - h1 (Will's first principle, verbatim): "Use AI to make what AI produces easier to understand, at every level of detail."
   - lede, large (his second principle): "Build things that get better as AI models get better."
   - direct links to the short V4 introduction and then the full V4 introduction, with their runtimes.
3. The instrument `#work`: the weave (a `<nav>`) and the stage (one `<article>` per row). Described below.
4. `#about`: Will's lede, availability, invitation and contact links from `sites.json` `owner` (reuse the
   existing text and fields), the earlier introductions, contributions to other repositories and earlier work
   (existing `render_more` content), the glossary list (existing `render_terms`; glossary hover stays on every
   project line). Plain, one column, measure 70 characters.
5. Footer: "Every link on one page" (all.html), llms.txt, source repository.

## The weave (left; the index and the picture of the graph)

A ledger. Columns: group name | row label | Short film | Full film | Website | Paper | Code.
Rows, top to bottom:

- Start here (root, above every group): "Introduction V4" (short-introduction, long-introduction) and
  "The funnel" (short-funnel, long-funnel, code: lean-exposition repo).
- Then the six groups of `explorer.json` `doors`, in file order, each door's new `heading` in the group column
  spanning its rows: research "Erdős problems" (maths); proofs "Papers beside Lean proofs" (quartic,
  lean-exposition, proof-reader, atlas); explaining "Making the films" (narration-ir; funnel is a root
  row and is skipped here); assistants "AI coding assistants" (agent-trace, one-checkout, safety-core); code
  "Reading AI-written code" (codemap, code-ontology-bridge); testing "Tests and proofs of code" (zenith,
  formal-verification). Mathematics first.
- Row label: a plain-words label from `explorer.json` `row_labels` (never the opaque project name alone):
  maths "Eight Erdős problems"; quartic "Quantum query complexity"; lean-exposition "Spin glasses";
  proof-reader "A paper beside its Lean proof"; atlas "Reports on OpenAI's maths"; narration-ir "Pictures
  timed to speech"; agent-trace "Claude Code and Codex sessions"; one-checkout "Several agents, one checkout";
  safety-core "Rules and command checks"; codemap "A map of a codebase"; code-ontology-bridge "NVIDIA Auto
  Ontology"; zenith "AI-written tests"; formal-verification "Dafny proofs in a toolkit". The project name
  (Quartic Reader, Zenith) follows in muted ink where the width allows (>= 1680px) and always in the stage.
- Knots: one mark per thing that can be opened, each a real `<a href>` to the film, site, paper or repo.
  The two film columns have two slots each (slot A: the result film or the only film; slot B: the second
  film). Shapes carry the type so colour is never the only signal: short film a small disc, full film a
  larger disc, website a rounded square outline, paper a page outline with a folded corner, code a diamond
  outline. The one shared film ("Three maths websites", long-lean-readers) is drawn once, as one capsule in
  slot B of Full film spanning the three reader rows (quartic, lean-exposition, proof-reader, kept adjacent).
- Thread: a 1px horizontal line per row from the label through its last knot, in the row's ink at low
  strength: brick for mathematics doors (`ink: maths`), steel for software doors (`ink: code`), cream ink for
  the two root rows. A one-line key under the weave says so.
- Selected row: its label cell becomes a cream paper band (`--paper`, text `--ground`, Barlow Condensed 700),
  the thread goes to full ink, and one bead runs along the thread left to right once (600ms).
- A sentence under the weave explains it, with the key: "Each row is one project. Each mark opens something: a 90-second
  film on the left, then the full film, the website, the paper and the source."

## The stage (right; what the selected thing leads to)

One `<article id="p-<slug>">` per row (`p-intro` for the introduction). With JavaScript only the selected
article shows and the stage is sticky under the header. Each article:

- Frame, 16:9, one link to the featured resource. Shows that resource's real preview: for a film its poster
  (`assets/films/next/<slug>-1280.webp` or the older stems) and, with JavaScript, its silent loop
  (`assets/films/loops/<slug>.mp4`, 640x360, about 6 s, muted, playsinline, loop) laid over the poster; for a
  website or paper the site capture (`assets/sites/<slug>-dark-*.webp`); for code the repo capture
  (`assets/sites/repo-<name>-*.webp`) where one exists. A cream chip in the frame's lower-left names it and
  its length: "Short film, 1:50", "Website", "Code on GitHub". Nothing here depends on YouTube: posters and
  loops are local, so a private video breaks nothing; the link is the only thing that needs YouTube.
- Under the frame: the project name as a small label; h2 = the project's question from `explorer.json`
  `project_questions` (root rows: "What is this body of work?" and "How does one Lean proof become papers and
  a video?"); one paragraph = `sites.json` project `line` with glossary links; `credit` in muted small text
  where the project has one (attribution and limits stay beside the claim).
- Depth strip: the row's resources in column order as small tiles (thumbnail + "Short film, 1:50" / "Full
  film, 34:02" / "Website" / the paper's label / "Code"), joined by a thin line so the row reads as one
  thread going deeper. Each tile is a link; hovering or focusing a tile puts it in the frame; the tile shown
  in the frame is marked current. All papers and extra project routes are listed as text links after the tiles.

## States and interaction

- Load: the Introduction row is selected; its loop plays in the frame.
- Select a row: pointer rests on a row 120ms, a row label is focused or clicked, or Up/Down while focus is in
  the weave. Selecting swaps the article (180ms cross-fade of the frame only; text swaps at once), moves the
  paper band and the bead, and writes `#p=<slug>` with `history.replaceState`.
- Hover or focus a knot: selects its row and puts that resource in the frame. Click opens it (new tab for
  off-site links, as today).
- Keyboard: Tab reaches each row label (a link to `#p-<slug>`), then the stage's frame and strip links. With
  JavaScript the knots take `tabindex=-1` (the strip repeats them); without it they are ordinary links.
  Enter on a row label moves focus to that article's frame link. Visible `:focus-visible` outline in steel.
- Tour (the page feels alive without input): 5 s after load, if the reader has not touched the instrument,
  the selection advances one row every 6 s, with a thin progress line under the frame. Any pointer move over
  the instrument, key press, touch or focus ends the tour for the session. Never under
  `prefers-reduced-motion` or Save-Data; paused in a hidden tab or when the instrument is off screen.
- Deep links kept: `#p=<slug>` selects a project; `#d=<door>` selects that door's first row; `#intro` and
  `#t=<topic alias>` map through `explorer.json` `topic_aliases`/`direct_topics`.
- One orchestrated entrance, once per session, not under reduced motion: the threads draw left to right,
  25ms apart per row, about 700ms in all, knots appearing as the line reaches them. No scroll reveals.
- Without JavaScript: the weave is a table of working links; every article is visible, stacked in the right
  column, each with its poster, text and strip. Nothing is hidden.

## Layout at three widths

- 1440 (primary; first screen 1440x790): container 1360 (40px gutters). Hero about 170px tall. Instrument:
  weave 628 (group 140 | label 250 | 7 knot slots of 34), gap 48, stage 684 (frame 684x385). Rows 32px, so
  the whole weave (15 rows + header) is about 520px and fits the first screen under the hero.
- 1920: container 1560. Weave 760 (adds a muted project-name column), stage 740 to 760. Type one step up.
- 390 (first-class): one column, 16px gutters. Order: hero, the Introduction article, the weave, the other
  articles under their group headings. The weave keeps its form: group heading on its own line, then rows of
  label (wraps to two lines) + seven 26px knot slots; tapping a label scrolls to its article; knots are
  direct links (hit area 26x40). Articles are all open; a loop plays only while its frame is at least 60% in
  view, one at a time. Strip tiles wrap three to a line. No sideways scroll at 320.
- Between 900 and 1180 the two columns stay, the group column folds into heading lines.

## Type, colour, motion

- Faces (the films' own): Barlow Condensed 700 for h1, group names, the paper band and chips; Barlow 400/600
  for everything else (`assets/fonts/barlow-*.woff`, OFL, subset). Numbers tabular. No monospace, no tracked
  uppercase, no middle dots, no em dashes.
- Sizes: h1 clamp(38px, 4.4vw, 68px) / 1.02; lede 22 to 26px; body 17/1.5; row label 15/600; small 13.
- Tokens (from `house_identity.json`): `--ground #1c1526` flat everywhere; `--raise #272033` for the frame
  edge and tiles; `--line #3b3249`; `--ink #f2e6d4`; `--muted #bcb8c6`; `--paper #fffdf7`;
  `--steel #97c1df`; `--brick #e18a79`. No gradients, glows or shadows. Radius 6 on frames and tiles, 3 on chips.
- Motion: arrivals `cubic-bezier(0.16,1,0.3,1)`; hover 120ms; frame cross-fade 180ms; bead 600ms; entrance
  700ms once. Transform and opacity only. Everything stops under reduced motion.

## Data and build

- `explorer.json`: add `heading` to each door, `row_labels`, and `root` (the two root rows); bump `version`.
- `scripts/landing.py`: `build_rows(registry, explorer, root)` derives rows and knots from `sites.json`
  relationships (`resource_for` roles, `leads_to`, `superseded_by`, `in_area`); `render(...)` writes
  `index.html`. `build_hub.outputs()` uses it for `index.html`; `all.html`, `catalogue.json`, `family.json`,
  `llms.txt` unchanged. Loops attach by convention when `assets/films/loops/<film-slug>.mp4` exists.
- `assets/landing.css`, `assets/landing.js`, `assets/landing-init.js` (adds `html.js` before paint).
- `scripts/check_hub_site.py` and `tests/test_hub_site.py` updated with the design: the home page has no
  iframe, loads nothing from other hosts, reaches every current film, website and repository from a row,
  and every loop file on disk is used.
- `scripts/cut_loops.py` (kept in the repo) records how the loops were cut.

## Rules learned while building it

- The page must look the same whether or not a video is public: posters and clips are this repository's
  files, no player is embedded, and the checker fails a page that frames anything.
- The static page holds no `<video>` element; the script creates one for the frame on show and removes it
  when the frame changes, so only one clip is ever loaded.
- Inline `style` attributes are blocked by the page's content security policy. Per-row values (thread
  length, entrance order) are set by attribute and class selectors in the stylesheet.
- The whole weave fits the first screen at 1440x790. Re-capture that screen after adding a row or a group.
- A clip whose chosen moment is mostly empty ground is cut again from a hand-picked second
  (`scripts/loop_starts.json`); look at the contact sheet the cutter writes before committing clips.
- The tour stops for good at the first pointer move, key press, touch or focus inside the instrument.
