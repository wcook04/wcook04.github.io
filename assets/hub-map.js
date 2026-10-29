/* The home page's map: the lines between its columns (28 October 2026).

   Each row of the map is one opened project: its videos, its website or
   tool, its code on GitHub. A project opens beneath its line in the index
   (hub.js), and only open rows are drawn. This script draws a line from each video to the website it
   explains and from the website to each of its repositories, and lights the
   row a reader points at or tabs into while the other rows step back. Without
   it the grid alone groups each row and every link works; nothing here is
   needed to read the page or follow a link, and nothing is fetched or stored.

   Adapted, not new: the cables of the Plectis film map, the "video graph" on
   the Plectis landing (ai_workflow sites/microcosm/assets/film-map.js, the
   cables, about lines 316 to 520, and their ink rules in film-map.css). That
   code is itself adapted from Magic UI's AnimatedBeam (MIT License, Copyright
   (c) Magic UI; magicuidesign/magicui@85f97fd27b05,
   apps/www/registry/magicui/animated-beam.tsx): an SVG laid over the
   container, each path measured from two elements' boxes relative to the
   container and measured again by a ResizeObserver. Kept from the film map:
   strand(), a run with rounded orthogonal turns of radius R whose turns stand
   in the open gutter between the columns, ordered so that no two strands
   cross; the end dot; the lit route in full ink with the rest stepped back;
   and the one-off bead of light along the lit route, for a pointer only,
   never for keys, with reduced motion, Save-Data or in a hidden tab. Changed:
   the map is rows of three columns instead of a tree from one introduction,
   so each row has its own two fans (videos into the website, the website out
   to its code); a turn's run never leaves its row; and there is no first-visit
   drawing, because the lines are navigation, not a figure. The lines are
   measured again when the map resizes, when the fonts arrive and when the
   theme switches. The MIT notice is at the end of this file. */
(function () {
  'use strict';

  var doc = document;
  var map = doc.querySelector && doc.querySelector('[data-hub-map]');
  if (!map || !doc.createElementNS || !window.matchMedia) return;
  // The rows are the open projects' maps (index.html, "Projects"); a closed
  // project's row is not displayed, so it has no box and draws no line.
  var list = map;

  var NS = 'http://www.w3.org/2000/svg';
  var R = 10;             // the radius of a turn
  var SP = 6;             // between the strands where they meet one node
  var VS = 7;             // between the turns of strands that run the same way
  var svg = null, lineLayer = null, beadLayer = null;
  var shape = null;       // the geometry the drawing was made for
  var linesOf = {};       // row id -> { films: [{ el, line }], repos: [{ el, line }] }
  var lit = null;         // the lit row

  function wide() {
    try { return window.matchMedia('(min-width: 960px)').matches; } catch (e) { return false; }
  }
  function quietMotion() {
    try { if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return true; } catch (e) {}
    try { if (navigator.connection && navigator.connection.saveData) return true; } catch (e) {}
    return false;
  }
  function rowsOf() { return Array.prototype.slice.call(list.querySelectorAll('.map-row[data-row]')); }

  function root() {
    if (!svg) {
      svg = doc.createElementNS(NS, 'svg');
      svg.setAttribute('class', 'map__lines');
      svg.setAttribute('aria-hidden', 'true');
      svg.setAttribute('focusable', 'false');
      lineLayer = doc.createElementNS(NS, 'g');
      beadLayer = doc.createElementNS(NS, 'g');
      beadLayer.setAttribute('class', 'map__bead');
      beadLayer.setAttribute('opacity', '0');
      for (var i = 0; i < 4; i++) beadLayer.appendChild(doc.createElementNS(NS, 'circle'));
      svg.appendChild(lineLayer);
      svg.appendChild(beadLayer);
      map.insertBefore(svg, map.firstChild);
    }
    return svg;
  }

  // A node's box relative to the map. A video is joined at the middle of its
  // still, so the line meets the picture, not the words beside it.
  function boxOf(el, base) {
    if (!el || !el.getClientRects().length) return null;
    var r = el.getBoundingClientRect();
    return { l: r.left - base.left, r: r.right - base.left, t: r.top - base.top, b: r.bottom - base.top,
             y: r.top - base.top + r.height / 2 };
  }
  function filmBox(li, base) {
    var b = boxOf(li, base);
    var frame = boxOf(li.querySelector('.film-slot__frame'), base);
    if (b && frame) b.y = frame.y;
    return b;
  }

  function arc(x, y, sweep) { return ' A ' + R + ' ' + R + ' 0 0 ' + sweep + ' ' + x + ' ' + y; }
  // One strand (film-map.js strand()): along, a turn, down or up its own run,
  // a turn, and on into its node. A strand level with its node runs on in one
  // easy curve.
  function strand(x0, y0, turn, ex, ey) {
    var dy = ey - y0;
    if (Math.abs(dy) < 2 * R + 1) {
      var k = (ex - x0) / 2;
      return 'M ' + x0 + ' ' + y0 + ' C ' + (x0 + k) + ' ' + y0 + ' ' + (ex - k) + ' ' + ey + ' ' + ex + ' ' + ey;
    }
    var down = dy > 0, s = down ? 1 : -1;
    return 'M ' + x0 + ' ' + y0 + ' H ' + (turn - R) + arc(turn, y0 + s * R, down ? 1 : 0) +
      ' V ' + (ey - s * R) + arc(turn + R, ey, down ? 0 : 1) + ' H ' + ex;
  }
  // The turns for a set of strands crossing one gutter from xa to xb. Strands
  // running the same way take turns VS apart, the inner one first, so none
  // crosses another; the set is centred in the gutter.
  function turns(strands, xa, xb) {
    var downs = strands.filter(function (t) { return t.y1 - t.y0 >= 2 * R + 1; })
      .sort(function (a, b) { return (b.y0 + b.y1) - (a.y0 + a.y1); });
    var ups = strands.filter(function (t) { return t.y0 - t.y1 >= 2 * R + 1; })
      .sort(function (a, b) { return (a.y0 + a.y1) - (b.y0 + b.y1); });
    var room = Math.max(downs.length, ups.length, 1);
    var mid = (xa + xb) / 2;
    var first = Math.max(xa + R + 2, mid - (room - 1) * VS / 2);
    downs.forEach(function (t, i) { t.turn = Math.min(xb - R - 2, first + i * VS); });
    ups.forEach(function (t, i) { t.turn = Math.min(xb - R - 2, first + i * VS); });
    strands.forEach(function (t) { if (t.turn === undefined) t.turn = mid; });
  }
  // Where several strands meet one node, they meet it a few pixels apart, in
  // the order of the nodes at their other ends.
  function spread(i, n) { return (i - (n - 1) / 2) * SP; }

  function add(row, d, end) {
    var g = doc.createElementNS(NS, 'g');
    g.setAttribute('class', 'map__line');
    g.setAttribute('data-row', row);
    var path = doc.createElementNS(NS, 'path');
    path.setAttribute('d', d);
    g.appendChild(path);
    var dot = doc.createElementNS(NS, 'circle');
    dot.setAttribute('cx', end.x); dot.setAttribute('cy', end.y); dot.setAttribute('r', '2.5');
    g.appendChild(dot);
    lineLayer.appendChild(g);
    var length = 0;
    try { length = path.getTotalLength(); } catch (e) {}
    return { g: g, path: path, length: length };
  }

  function draw(force) {
    if (!wide()) {
      if (svg) svg.setAttribute('hidden', '');
      shape = null; light(null); return;
    }
    var base = map.getBoundingClientRect();
    var rows = rowsOf();
    var measured = rows.map(function (row) {
      var site = row.querySelector('.map-site');
      return {
        id: row.getAttribute('data-row'),
        site: boxOf(site, base),
        films: Array.prototype.map.call(row.querySelectorAll('.map-film'), function (li) { return { el: li, box: filmBox(li, base) }; }),
        repos: Array.prototype.map.call(row.querySelectorAll('.map-repo'), function (li) {
          // A cell that says there is no repository is not joined.
          return li.querySelector('a') ? { el: li, box: boxOf(li, base) } : null;
        }).filter(Boolean)
      };
    });
    // A notice that moved nothing keeps the drawing.
    var sig = [Math.round(base.width)].concat(measured.map(function (m) {
      var parts = [m.site].concat(m.films.map(function (f) { return f.box; }), m.repos.map(function (r) { return r.box; }));
      return parts.map(function (b) { return b ? Math.round(b.l) + ',' + Math.round(b.r) + ',' + Math.round(b.y) : '-'; }).join(';');
    })).join(' ');
    if (sig === shape && !force) return;
    root().removeAttribute('hidden');
    while (lineLayer.firstChild) lineLayer.removeChild(lineLayer.firstChild);
    linesOf = {};
    measured.forEach(function (m) {
      if (!m.site) return;
      var entry = { films: [], repos: [] };
      linesOf[m.id] = entry;
      // Videos into the website: from each still's right edge, across the
      // gutter, into the website's left edge.
      var films = m.films.filter(function (f) { return f.box; });
      if (films.length) {
        var xa = Math.max.apply(null, films.map(function (f) { return f.box.r; })) + 4;
        var ex = m.site.l - 6;
        var ins = films.map(function (f, i) { return { f: f, y0: f.box.y, y1: m.site.y + spread(i, films.length) }; });
        turns(ins, xa, ex);
        ins.forEach(function (t) {
          entry.films.push({ el: t.f.el, line: add(m.id, strand(xa, t.y0, t.turn, ex, t.y1), { x: ex, y: t.y1 }) });
        });
      }
      // The website out to its code: from its right edge to each repository.
      var repos = m.repos.filter(function (r) { return r.box; });
      if (repos.length) {
        var xb = m.site.r + 4;
        var rx = Math.min.apply(null, repos.map(function (r) { return r.box.l; })) - 6;
        var outs = repos.map(function (r, i) { return { r: r, y0: m.site.y + spread(i, repos.length), y1: r.box.y }; });
        turns(outs, xb, rx);
        outs.forEach(function (t) {
          entry.repos.push({ el: t.r.el, line: add(m.id, strand(xb, t.y0, t.turn, rx, t.y1), { x: rx, y: t.y1 }) });
        });
      }
    });
    shape = sig;
    light(lit);
  }

  // The lit row's lines and nodes come up to the accent ink; the rest step
  // back (.is-tracing in hub.css).
  function light(row) {
    lit = row;
    var id = row ? row.getAttribute('data-row') : null;
    rowsOf().forEach(function (r) { r.classList.toggle('is-lit', r === row); });
    if (lineLayer) {
      Array.prototype.forEach.call(lineLayer.childNodes, function (g) {
        g.classList.toggle('is-lit', g.getAttribute('data-row') === id);
      });
    }
    map.classList.toggle('is-tracing', !!row);
  }

  /* A light runs once along the row the reader points at, from a video
     through the website to its code (the pointed video and repository, or
     the row's first), so the row reads as one route. It waits a tenth of a
     second, so a pointer sweeping across the map leaves no trail, then
     travels in about half a second and is gone. Never for a key press, never
     with reduced motion or Save-Data, never in a hidden tab. */
  var beadTimer = 0, beadFrame = 0;
  function stopBead() {
    if (beadTimer) { window.clearTimeout(beadTimer); beadTimer = 0; }
    if (beadFrame) { window.cancelAnimationFrame(beadFrame); beadFrame = 0; }
    if (beadLayer) beadLayer.setAttribute('opacity', '0');
  }
  function pick(items, target) {
    for (var i = 0; i < items.length; i++) if (target && items[i].el.contains(target)) return items[i];
    return items[0] || null;
  }
  function runBead(row, target) {
    stopBead();
    if (!svg || !wide() || quietMotion() || doc.hidden || !window.requestAnimationFrame) return;
    var entry = linesOf[row.getAttribute('data-row')];
    if (!entry) return;
    var legs = [pick(entry.films, target), pick(entry.repos, target)]
      .filter(function (x) { return x && x.line.length > 0; }).map(function (x) { return x.line; });
    if (!legs.length) return;
    var total = legs.reduce(function (sum, c) { return sum + c.length; }, 0);
    var ms = Math.max(460, Math.min(700, 380 + total * 0.6));
    beadTimer = window.setTimeout(function () {
      beadTimer = 0;
      var dots = beadLayer.childNodes;
      var at = function (d) {
        d = Math.max(0, Math.min(total, d));
        for (var i = 0; i < legs.length; i++) {
          if (d <= legs[i].length || i === legs.length - 1) return legs[i].path.getPointAtLength(Math.min(d, legs[i].length));
          d -= legs[i].length;
        }
        return null;
      };
      var t0 = null;
      var step = function (now) {
        if (doc.hidden) { stopBead(); return; }
        if (t0 === null) t0 = now;
        var t = Math.min(1, (now - t0) / ms);
        var q = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        beadLayer.setAttribute('opacity', String(Math.min(1, t * 6, (1 - t) * 6)));
        for (var i = 0; i < dots.length; i++) {
          var p = at((q - i * 0.035) * total);
          if (!p) continue;
          dots[i].setAttribute('cx', p.x); dots[i].setAttribute('cy', p.y);
          dots[i].setAttribute('r', String(i ? 2.7 - i * 0.45 : 3.4));
        }
        beadFrame = t < 1 ? window.requestAnimationFrame(step) : 0;
        if (!beadFrame) beadLayer.setAttribute('opacity', '0');
      };
      beadFrame = window.requestAnimationFrame(step);
    }, 110);
  }

  // Pointing: a fine pointer only, so a tap never leaves a row lit.
  var finePointer = false;
  try { finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches; } catch (e) {}
  if (finePointer) {
    map.addEventListener('pointerover', function (event) {
      if (event.pointerType && event.pointerType !== 'mouse' && event.pointerType !== 'pen') return;
      if (!wide()) return;
      var row = event.target.closest ? event.target.closest('.map-row[data-row]') : null;
      if (row === lit) return;
      light(row);
      if (row) runBead(row, event.target); else stopBead();
    });
    map.addEventListener('pointerleave', function () {
      stopBead();
      if (!map.contains(doc.activeElement)) light(null);
    });
  }
  // Keys: focus lights its row, with no bead.
  map.addEventListener('focusin', function (event) {
    if (!wide()) return;
    stopBead();
    light(event.target.closest ? event.target.closest('.map-row[data-row]') : null);
  });
  map.addEventListener('focusout', function (event) {
    if (!event.relatedTarget || !map.contains(event.relatedTarget)) { stopBead(); light(null); }
  });
  doc.addEventListener('visibilitychange', function () { if (doc.hidden) stopBead(); });

  // Measured again when the map resizes, when the fonts arrive, when the
  // layout crosses the three-column width and when the theme switches.
  if ('ResizeObserver' in window) {
    // Opening or closing a project changes the map's height, so this hears it.
    try { new ResizeObserver(function () { draw(false); }).observe(list); } catch (e) {}
  } else {
    window.addEventListener('resize', function () { draw(false); });
  }
  try {
    var mq = window.matchMedia('(min-width: 960px)');
    if (mq.addEventListener) mq.addEventListener('change', function () { draw(true); });
  } catch (e) {}
  try { if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { draw(false); }); } catch (e) {}
  if ('MutationObserver' in window) {
    try {
      new MutationObserver(function () { draw(true); })
        .observe(doc.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    } catch (e) {}
  }
  draw(true);
})();

/* Third-party notice for the AnimatedBeam geometry adapted above.
MIT License

Copyright (c) Magic UI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
