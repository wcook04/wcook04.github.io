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

- `/`: header; stage (sentence, introduction); map (`#map`): three places to start (`#start`), then all fifteen
  by group (`#all`, each group at `#band-<id>`); about (`#about`); footer.
- `/work/<slug>/`: header; where the page is (All projects, the group, and the previous and next project);
  stage (name, claim, stated limit, credit, one filled control that opens the thing itself, the video's own loop);
  the strip of levels; the previous and next project with pictures; the site in one sentence with links home;
  all fifteen projects as words with this one marked (`#map`); footer.
- `all.html`: every link in one table, a row per project under the five groups and columns in the strip's order;
  then earlier videos, contributions, contact and the glossary. `404.html`: says the address has no page and shows
  the map. Both are written by [`scripts/register.py`](../scripts/register.py) with `assets/register.css`, on this
  page's header, footer and tokens, and keep every id the earlier pages had.

A stop is one of: short video, full video, website, paper, proof, code, study,
issue. A project lists only the kinds it has, ordered from the quickest look to
the most detail, and the axis above the strip ends over the last stop. A stop
may carry up to three small extra links. A video stop says it opens on YouTube.
A paper's first page is printed on the page's bone colour, never pure white. A
repository or an issue is shown by its own name, because every GitHub page looks
the same at this size.

## Finding the way

Most visitors arrive on one project page, from a video's description or an email, so every page answers three
questions the same way.

- **Whose site is this, and how do I get back?** The header is the same on every page and stays at the top of the
  window. Projects always opens the map on the home page, so the word means one thing everywhere. On a project page
  it is underlined, and the line under the header reads All projects, then the group, each a link.
- **What is next to this?** Previous and Next step through the fifteen in the map's order: as words at the top of a
  project page (wider than a phone) and as two pictures under the strip.
- **What else is there?** Three sizes say what leads. The home page shows three places to start with large pictures
  (the three projects the introduction uses as its examples, marked `start` in `front.json`), then every project in
  its group with a small picture and one sentence about the group. Under a project page the same fifteen are words
  only. No single project is given a larger place than the other two starts.

A project page has one filled control. It opens the thing itself (the website, the study or the repository), named
in `front.json` as `primary`: a stop's id and the control's words. The address is read from that stop, so the two
cannot differ. Reader websites and CodeMap have none: the first is three websites of equal standing, and CodeMap's
code is private.

## Data

`front.json`:

- `intro`: the home page's sentence, lede, the two introduction videos and the idle clip.
- `terms`: one plain sentence for each word a newcomer may not know (Lean,
  Dafny). A project page that uses the word prints the sentence under its credit.
- `bands`: the five groups, numbered as the full introduction numbers them. Each has `about`, one sentence on
  what the group is, printed beside it on the home page. A group may carry a `note`, printed under that sentence.
- `entries`: one per project. `slug`, `name`, `band`, `line` (the tile's line),
  `claim`, `limit`, optional `credit`, optional `start` and `primary` (see Finding the way), `loop` (the stem of its pictures and
  clips), `aliases` (ids the earlier home page used) and `stops`.
- A stop has `id` (its fragment), `kind`, and either `res` (a resource id in
  `sites.json`; the address and length are read from there) or `href`. Optional
  `label`, `detail`, `plate` (a picture in `assets/front/plates/`), `fallback`
  (an older picture) and `more`.
- `videos`: each of the 24 videos and the address its description links to.

## Pictures and clips

All under `assets/front/`, all this repository's own files:

- `posters/<stem>-480|960|1600.webp`: a still from the video, chosen and cropped
  to read at tile size with no words cut by the frame.
- `loops/<stem>-s.mp4` (480 wide) and `-l.mp4` (1280 wide): a silent clip of a
  few seconds from the video. Every clip opens on the still and ends on it, so
  starting or stopping one never makes the picture jump. A tile plays its clip
  while the pointer or the keyboard rests on it; a project page's large picture
  plays its clip while the pointer is on it. No clip on a project page starts by
  itself, because several count up to the number the sentence beside them states.
- `loops/hero-l.mp4`: the two-ideas scene of the short introduction (19.6 s to 27.95 s), cut
  to leave out the caption strip. It plays once, only where the whole scene is shown (wider than 1180px), and rests on its last frame, which is also the poster.
  `posters/hero-n-*.webp` is that last frame cropped to its four cards, shown still at 1180px and narrower so the labels can be read.
- `cards/<slug>.png`: the 1200 by 630 picture a link to each page unfurls with (PNG, because some readers refuse WebP).
- `plates/<name>-640|1280.webp`: the first page of a paper, or the real website,
  proof file or repository page a stop opens.

The checker fails the build if a page names a file that is missing, or if a file
in these folders is used by no page.

## Rules

- Every number, result and credit is as the video's captions, the paper or the
  site states it, with its stated limit beside it. The limit is always visible
  text, marked with a brick rule.
- Words, never symbols: a stop says "Short video, 1:41" or "Paper, PDF, 26 pages".
- Nothing loads from another host, with one exception: when Play is pressed, the home page's script
  puts the short introduction in YouTube's own player where the scene was.
  Every other video opens on YouTube.
- The static pages hold no `<video>` element. The script creates one where it is
  needed and removes it afterwards, so at most one clip is loaded.
- Complete without JavaScript: every tile and stop is a link.
- Colour is state, never category: cream is the thing to press and "you are
  here"; steel is a link; brick is a stated limit.
- Motion has a purpose and stops: the home page's scene plays once, building
  from nothing (the visitors who get it are not first shown its finished still);
  a clip plays only under the pointer or focus, after a short dwell; the picture
  travels between the map and a project page (cross-document view transition),
  opaque, while the old page leaves before the new one arrives; the strip's line
  draws once. Under reduced motion or Save-Data nothing moves and the stills
  remain. The one thing that moves by itself has a Pause button, which leaves
  when the motion stops. Pressing Play changes the layout in one step.
- Arriving from a video on a phone, the watched stop and the next one are on the
  first screen: the large picture and the credit are left out for that arrival,
  since the visitor has just watched the picture.
- A stage frame is blended into the page with `mix-blend-mode: lighten` on the whole frame. The videos' encoded
  ground is a shade darker than `#1c1526`, so the page's ground shows wherever the frame is darker and the frame has
  no edge. Blend the frame, never the picture and the clip separately, or a clip doubles over its poster.
- A stop's picture is 16:9 and shows the whole capture, so no thumbnail's words are cut by the frame.
- A still must not show private file names. The first seconds of the short
  introduction do, so no still or idle clip is cut from them.

## Old addresses

The earlier home page used `#p-<id>` anchors and `#p=<id>`, `#d=<group>`,
`#t=<topic>` and `#intro` fragments. Every old project id is still an anchor on
the home page (on the matching tile), and the script forwards the other forms,
including `#h-<id>`, `#t-<term>`, `#terms` and `#more`, which now live on
`all.html`.
