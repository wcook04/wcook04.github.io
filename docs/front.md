# The home page and the project pages

How the front of the site is designed and the rules it follows. The builder is
[`scripts/front.py`](../scripts/front.py). Its words and order are in
[`front.json`](../front.json); addresses and video lengths come from `sites.json`.
Its look and behaviour are `assets/front.css`, `assets/front.js` and
`assets/front-init.js`. Change the data or the builder, then run
`python3 scripts/build_hub.py`. Never edit `index.html` or `work/*/index.html` by hand.

## The idea

The full introduction video draws a map of the work: fifteen projects in five
numbered groups. The home page is that map. Every project has its own page, and
every project page opens the same way: a strip of levels, from a short video on
the left down to the proof or the code on the right. A visitor chooses how deep
to go. The strip is the one control the site uses, so it is learned once.

The videos' ground colour is the page's ground colour, so a frame from a video
sits on the page with no edge.

## Two ways to arrive

- **On the home page.** One sentence, the short introduction (it plays in the
  page from a file in this repository), a quiet link to the full introduction,
  and the top of the map.
- **From a video's description.** Each video links to its project's page with a
  fragment naming the video: `/work/agent-trace/#short`. The stop the visitor
  watched carries a "You watched this" flag and the next stop is marked "Next".
  This is CSS `:target`, so it works without JavaScript. The map of all fifteen
  projects is under the strip. `front.json` `videos` holds the 24 addresses and
  the checker fails the build if any of them stops resolving.

## Pages

- `/`: header; stage (sentence, introduction); map (`#map`); about (`#about`); footer.
- `/work/<slug>/`: header; stage (group, name, claim, stated limit, credit, the
  video's own loop); the strip of levels; the map with this project marked; footer.
- `all.html`: every link in one table, a row per project under the five groups and columns in the strip's order;
  then earlier videos, contributions, contact and the glossary. `404.html`: says the address has no page and shows
  the map. Both are written by [`scripts/register.py`](../scripts/register.py) with `assets/register.css`, on this
  page's header, footer and tokens, and keep every id the earlier pages had.

A stop is one of: short video, full video, website, paper, proof, code, study,
issue. A project lists only the kinds it has, ordered from the quickest look to
the most detail. A stop may carry up to three small extra links.

## Data

`front.json`:

- `intro`: the home page's sentence, lede, the two introduction videos and the idle clip.
- `bands`: the five groups, numbered as the full introduction numbers them.
- `entries`: one per project. `slug`, `name`, `band`, `line` (the tile's line),
  `claim`, `limit`, optional `credit`, `loop` (the stem of its pictures and
  clips), `aliases` (ids the earlier home page used) and `stops`.
- A stop has `id` (its fragment), `kind`, and either `res` (a resource id in
  `sites.json`; the address and length are read from there) or `href`. Optional
  `label`, `detail`, `plate` (a picture in `assets/front/plates/`), `fallback`
  (an older picture) and `more`.
- `videos`: each of the 24 videos and the address its description links to.

## Pictures and clips

All under `assets/front/`, all this repository's own files:

- `posters/<stem>-480|960|1600.webp`: a still from the video.
- `loops/<stem>-s.mp4` (480 wide) and `-l.mp4` (1280 wide): a silent clip of
  five or six seconds from the video. A tile plays its clip while the pointer or
  the keyboard is on it. A project page plays its clip while it is in view.
- `loops/hero-l.mp4` and `hero-n.mp4`: the two-ideas scene of the short introduction (19.6 s to 27.95 s), cut
  to leave out the caption strip. It plays once and rests on its last frame, which is also the poster. `hero-n` and
  `posters/hero-n-*.webp` are the same scene cropped to its four cards, used below 1180px so the labels can be read.
- `cards/<slug>.png`: the 1200 by 630 picture a link to each page unfurls with (PNG, because some readers refuse WebP).
- `plates/<name>-640|1280.webp`: the first page of a paper, or the real website,
  proof file or repository page a stop opens.
- `intro/short-introduction.mp4`: the short introduction, with its captions in the picture.

The checker fails the build if a page names a file that is missing, or if a file
in these folders is used by no page.

## Rules

- Every number, result and credit is as the video's captions, the paper or the
  site states it, with its stated limit beside it. The limit is always visible
  text, marked with a brick rule.
- Words, never symbols: a stop says "Short video, 1:41" or "Paper, PDF, 26 pages".
- Nothing loads from another host and no page holds a frame. Only the short
  introduction plays in the page; every other video opens on YouTube.
- The static pages hold no `<video>` element. The script creates one where it is
  needed and removes it afterwards, so at most one clip is loaded.
- Complete without JavaScript: every tile and stop is a link.
- Colour is state, never category: cream is the thing to press and "you are
  here"; steel is a link; brick is a stated limit.
- Motion has a purpose and stops: the idle clip plays once; a tile's clip plays
  only under the pointer or focus; the picture travels between the map and a
  project page (cross-document view transition); the strip's line draws once.
  Under reduced motion or Save-Data nothing moves and posters remain. Anything
  that moves by itself has a Pause button.
- A stage frame is blended into the page with `mix-blend-mode: lighten` on the whole frame. The videos' encoded
  ground is a shade darker than `#1c1526`, so the page's ground shows wherever the frame is darker and the frame has
  no edge. Blend the frame, never the picture and the clip separately, or a clip doubles over its poster.
- A stop's picture is 16:9 and shows the whole capture, so no thumbnail's words are cut by the frame.
- A still must not show private file names. The first seconds of the short
  introduction do, so no still or idle clip is cut from them.

## Old addresses

The earlier home page used `#p-<id>` anchors and `#p=<id>`, `#d=<group>`,
`#t=<topic>` and `#intro` fragments. Every old project id is still an anchor on
the home page (on the matching tile), and the script forwards the other forms.
