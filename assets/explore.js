/* The explorer (index.html, the first screen): the work as topics woven
   together on a night stage, read in three levels by the panel beside it.

   Levels: every topic; one topic, whose projects bloom around its knot; one
   project, whose short film, full video, website and code bloom around it.
   The address names the level (#t=<topic>, #p=<project>), so a view can be
   shared and Back works; Esc or an empty click goes up a level. Pointing at a
   topic on the stage or at its row in the panel lights the same threads, so
   the two read as one instrument. Small beads travel the threads to show
   that the work is joined; they stop under reduced motion, Save-Data, in a
   hidden tab or with the stage out of view.

   The stage is static SVG written by scripts/build_hub.py, and the panel's
   levels are already in the HTML; without this script the panel shows every
   topic, each linking to its projects in the list below. Interaction model
   adapted from the Plectis maths universe map (ai_workflow
   sites/microcosm/maths/assets/universe.js: a panel in three levels, hover
   previews, a click pins, Esc goes back, an addressable view); the beads from
   this site's earlier map (the Plectis film map's cables, after Magic UI's
   AnimatedBeam, MIT). Nothing is fetched or stored but a session flag. */
(function () {
  'use strict';
  var root = document.getElementById('explore');
  var dataEl = document.getElementById('ex-data');
  if (!root || !dataEl || !window.requestAnimationFrame) return;
  var svg = root.querySelector('[data-ex-stage]');
  var panel = root.querySelector('[data-ex-panel]');
  var world = svg.querySelector('.ex-world');
  var bloomG = svg.querySelector('.ex-bloom');
  var flowG = svg.querySelector('.ex-flow');
  var data = JSON.parse(dataEl.textContent);
  var NS = 'http://www.w3.org/2000/svg';
  var topicById = {}, topicEl = {}, homeOf = {};
  data.topics.forEach(function (t) {
    topicById[t.id] = t;
    t.items.forEach(function (p) { (homeOf[p] = homeOf[p] || []).push(t.id); });
  });
  Array.prototype.forEach.call(svg.querySelectorAll('.ex-topic'), function (g) { topicEl[g.getAttribute('data-topic')] = g; });
  var threads = Array.prototype.slice.call(svg.querySelectorAll('.ex-thread'));
  var levels = Array.prototype.slice.call(panel.querySelectorAll('.ex-level'));

  function mq(q) { try { return window.matchMedia(q).matches; } catch (e) { return false; } }
  function still() {
    if (mq('(prefers-reduced-motion: reduce)')) return true;
    try { if (navigator.connection && navigator.connection.saveData) return true; } catch (e) {}
    return false;
  }
  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function ease(k) { return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; }

  root.classList.add('is-live');

  // ------------------------------------------------------------ camera
  // The graph sits in the stage to the right of the panel; a level zooms in
  // on its topic or project, keeping it in that free space.
  var GRAPH = { cx: 40, cy: -12, w: 940, h: 700 };
  var cam = null, camAnim = 0;
  function frameFor(px, py, zoom) {
    var box = svg.getBoundingClientRect();
    var W = Math.max(1, box.width), H = Math.max(1, box.height);
    var wide = W >= 900;
    var left = wide ? panel.getBoundingClientRect().right - box.left + 24 : 0;
    var free = Math.max(240, W - left);
    var scale = Math.min(free / GRAPH.w, H / GRAPH.h) * (zoom || 1);
    var w = W / scale, h = H / scale;
    var x = (px === undefined ? GRAPH.cx : px) - (left + free / 2) / scale;
    var y = (py === undefined ? GRAPH.cy : py) - h / 2;
    return { x: x, y: y, w: w, h: h };
  }
  // Semantic zoom: the camera magnifies the picture, but words and lines keep
  // their reading size (the stylesheet divides them by --z).
  function setBox(b) {
    cam = b;
    svg.setAttribute('viewBox', b.x + ' ' + b.y + ' ' + b.w + ' ' + b.h);
    var base = frameFor();
    svg.style.setProperty('--z', (base.w / b.w).toFixed(3));
  }
  function moveTo(target, instant) {
    cancelAnimationFrame(camAnim);
    if (instant || still() || !cam) { setBox(target); return; }
    var from = cam, t0 = null, dur = 760;
    function step(t) {
      if (t0 === null) t0 = t;
      var k = ease(Math.min(1, (t - t0) / dur));
      setBox({ x: from.x + (target.x - from.x) * k, y: from.y + (target.y - from.y) * k,
               w: from.w + (target.w - from.w) * k, h: from.h + (target.h - from.h) * k });
      if (k < 1) camAnim = requestAnimationFrame(step);
    }
    camAnim = requestAnimationFrame(step);
  }

  // ------------------------------------------------------------ state
  var state = { level: 'home', topic: null, project: null };

  function showLevel(match) {
    var shown = null;
    levels.forEach(function (s) {
      var on = match(s);
      s.hidden = !on;
      if (on) shown = s;
    });
    panel.scrollTop = 0;
    if (shown) {
      shown.classList.remove('is-entering'); void shown.offsetWidth; shown.classList.add('is-entering');
    }
    return shown;
  }

  function light(topicId, cls) {
    cls = cls || 'is-on';
    var near = {};
    if (topicId) near[topicId] = true;
    threads.forEach(function (p) {
      var hit = !!topicId && (p.getAttribute('data-a') === topicId || p.getAttribute('data-b') === topicId);
      p.classList.toggle(cls, hit);
      if (hit) { near[p.getAttribute('data-a')] = true; near[p.getAttribute('data-b')] = true; }
    });
    Object.keys(topicEl).forEach(function (id) { topicEl[id].classList.toggle(cls, !!near[id]); });
    svg.classList.toggle(cls === 'is-on' ? 'has-focus' : 'has-hover', !!topicId);
  }

  // A topic's projects bloom outward from its knot, away from the centre.
  function bloomTopic(t) {
    bloomG.innerHTML = '';
    var n = t.items.length, base = Math.atan2(t.at[1], t.at[0]);
    var spread = n === 1 ? 0 : Math.min(1.25, 0.62 * (n - 1));
    var R = t.r + 112;
    t.items.forEach(function (pid, i) {
      var a = n === 1 ? base : base - spread / 2 + spread * i / (n - 1);
      var x = t.at[0] + Math.cos(a) * R, y = t.at[1] + Math.sin(a) * R;
      var p = data.projects[pid];
      var stalk = el('path', { 'class': 'ex-stalk', d: 'M ' + t.at[0] + ' ' + t.at[1] + ' L ' + x + ' ' + y, pathLength: '1' }, bloomG);
      // Its other topics: a faint line from the project to each.
      (homeOf[pid] || []).forEach(function (other) {
        if (other === t.id) return;
        var o = topicById[other];
        el('path', { 'class': 'ex-also', d: 'M ' + x + ' ' + y + ' Q ' + ((x + o.at[0]) / 2) * 0.8 + ' ' + ((y + o.at[1]) / 2) * 0.8 + ' ' + o.at[0] + ' ' + o.at[1] }, bloomG);
      });
      var g = el('g', { 'class': 'ex-proj ex-proj--' + p.area, 'data-project': pid, transform: 'translate(' + t.at[0] + ' ' + t.at[1] + ')' }, bloomG);
      el('circle', { 'class': 'ex-proj__halo', r: 24 }, g);
      el('circle', { 'class': 'ex-proj__dot', r: 10 }, g);
      var right = Math.cos(a) >= -0.2;
      var lx = right ? 18 : -18, anchor = right ? 'start' : 'end';
      var name = el('text', { 'class': 'ex-proj__name', x: lx, y: -2, 'text-anchor': anchor }, g);
      name.textContent = p.label;
      g.style.opacity = '0';
      g.__to = [x, y];
      g.__from = [t.at[0], t.at[1]];
      stalk.__delay = i * 70;
      g.__delay = i * 70;
    });
    animateBloom();
  }

  function animateBloom() {
    var items = Array.prototype.slice.call(bloomG.querySelectorAll('.ex-proj, .ex-sat'));
    var stalks = Array.prototype.slice.call(bloomG.querySelectorAll('.ex-stalk, .ex-sat-stalk'));
    if (still()) {
      items.forEach(function (g) { g.setAttribute('transform', 'translate(' + g.__to[0] + ' ' + g.__to[1] + ')'); g.style.opacity = ''; });
      return;
    }
    stalks.forEach(function (s) { s.classList.add('is-growing'); });
    var t0 = null, dur = 620;
    function step(t) {
      if (t0 === null) t0 = t;
      var done = true;
      items.forEach(function (g) {
        var k = Math.max(0, Math.min(1, (t - t0 - (g.__delay || 0)) / dur));
        if (k < 1) done = false;
        var q = 1 - Math.pow(1 - k, 4);
        var x = g.__from[0] + (g.__to[0] - g.__from[0]) * q, y = g.__from[1] + (g.__to[1] - g.__from[1]) * q;
        g.setAttribute('transform', 'translate(' + x + ' ' + y + ')');
        g.style.opacity = String(Math.min(1, k * 1.6));
      });
      if (!done) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // A project's film, full video, website and code branch out beside it as a
  // short list, drawn at reading size whatever the zoom (their bodies are
  // scaled by 1 / --z in the stylesheet).
  var PROJECT_ZOOM = 1.75;
  function bloomProject(pid) {
    var holder = bloomG.querySelector('.ex-proj[data-project="' + pid + '"]');
    if (!holder) return;
    Array.prototype.forEach.call(bloomG.querySelectorAll('.ex-sat, .ex-sat-stalk'), function (n) { n.parentNode.removeChild(n); });
    Array.prototype.forEach.call(bloomG.querySelectorAll('.ex-proj'), function (g) {
      g.classList.toggle('is-on', g === holder);
      // The chosen project's name moves above its dot, clear of its branches.
      var name = g.querySelector('.ex-proj__name');
      if (!name.__home) name.__home = [name.getAttribute('x'), name.getAttribute('y'), name.getAttribute('text-anchor')];
      if (g === holder) { name.setAttribute('x', 0); name.setAttribute('y', -30); name.setAttribute('text-anchor', 'middle'); }
      else { name.setAttribute('x', name.__home[0]); name.setAttribute('y', name.__home[1]); name.setAttribute('text-anchor', name.__home[2]); }
    });
    var p = data.projects[pid];
    var cx = holder.__to[0], cy = holder.__to[1];
    var side = cx >= GRAPH.cx - 40 ? 1 : -1;
    var u = 1 / PROJECT_ZOOM;                    // one screen pixel in map units
    var FILM_W = 176, FILM_H = 99, PILL_H = 32, GAP = 10, OFF = 120;
    var heights = p.sats.map(function (s) { return s.kind === 'film' ? FILM_H + 22 : PILL_H; });
    var total = heights.reduce(function (a, b) { return a + b; }, 0) + GAP * (p.sats.length - 1);
    var y = cy - (total / 2) * u;
    p.sats.forEach(function (s, i) {
      var h = heights[i];
      var ix = cx + side * OFF * u, iy = y + (s.kind === 'film' ? FILM_H / 2 : h / 2) * u;
      y += (h + GAP) * u;
      el('path', { 'class': 'ex-sat-stalk', pathLength: '1',
        d: 'M ' + cx + ' ' + cy + ' C ' + (cx + side * 60 * u) + ' ' + cy + ' ' + (ix - side * 60 * u) + ' ' + iy + ' ' + ix + ' ' + iy }, bloomG);
      var g = el('g', { 'class': 'ex-sat ex-sat--' + s.kind + (s.href ? '' : ' is-pending'), transform: 'translate(' + cx + ' ' + cy + ')' }, bloomG);
      var body = el('g', { 'class': 'ex-sat__body' }, g);
      var x0 = side > 0 ? 0 : -1;               // left edge, or right edge on the left side
      if (s.kind === 'film') {
        var fx = side > 0 ? 0 : -FILM_W;
        var clip = 'exclip-' + pid;
        var cp = el('clipPath', { id: clip }, el('defs', {}, body));
        el('rect', { x: fx, y: -FILM_H / 2, width: FILM_W, height: FILM_H, rx: 7 }, cp);
        el('rect', { 'class': 'ex-sat__frame', x: fx - 1, y: -FILM_H / 2 - 1, width: FILM_W + 2, height: FILM_H + 2, rx: 8 }, body);
        var img = el('image', { href: s.img, x: fx, y: -FILM_H / 2, width: FILM_W, height: FILM_H, 'clip-path': 'url(#' + clip + ')', preserveAspectRatio: 'xMidYMid slice' }, body);
        img.setAttributeNS('http://www.w3.org/1999/xlink', 'href', s.img);
        if (s.href) {
          el('circle', { 'class': 'ex-sat__chip', cx: fx + FILM_W / 2, cy: 0, r: 17 }, body);
          el('path', { 'class': 'ex-sat__play', d: 'M ' + (fx + FILM_W / 2 - 5) + ' -7 L ' + (fx + FILM_W / 2 + 8) + ' 0 L ' + (fx + FILM_W / 2 - 5) + ' 7 Z' }, body);
        }
        var cap = el('text', { 'class': 'ex-sat__label', x: side > 0 ? fx : fx + FILM_W, y: FILM_H / 2 + 16, 'text-anchor': side > 0 ? 'start' : 'end' }, body);
        cap.textContent = s.label + (s.time ? ', ' + s.time : '') + (s.href ? '' : ', in preparation');
      } else {
        var t = el('text', { 'class': 'ex-sat__label ex-sat__label--pill', y: 4.5 }, body);
        t.textContent = s.label + (s.time ? '  ' + s.time : '') + (s.href ? '' : ', in preparation');
        var w = 28;
        try { w = t.getComputedTextLength() + 28; } catch (e) { w = t.textContent.length * 7 + 28; }
        var px = side > 0 ? 0 : -w;
        var r = el('rect', { 'class': 'ex-sat__pill', x: px, y: -PILL_H / 2, width: w, height: PILL_H, rx: PILL_H / 2 }, body);
        body.insertBefore(r, t);
        t.setAttribute('x', px + 14);
      }
      if (s.href) {
        g.setAttribute('data-href', s.href);
        g.setAttribute('data-out', /^https?:/.test(s.href) ? '1' : '');
      }
      g.style.opacity = '0';
      g.__from = [cx, cy]; g.__to = [ix, iy]; g.__delay = 80 + i * 55;
    });
    animateBloom();
  }

  function go(level, id, instant) {
    if (level === 'project') {
      var t = state.topic && homeOf[id] && homeOf[id].indexOf(state.topic) !== -1 ? state.topic : (homeOf[id] || [])[0];
      if (!t) return;
      if (state.topic !== t || state.level === 'home') { state.topic = t; bloomTopic(topicById[t]); }
      state.level = 'project'; state.project = id;
      light(t);
      bloomProject(id);
      var g = bloomG.querySelector('.ex-proj[data-project="' + id + '"]');
      var to = g ? g.__to : topicById[t].at;
      moveTo(frameFor(to[0] + (to[0] >= GRAPH.cx - 40 ? 1 : -1) * 90 / PROJECT_ZOOM, to[1], PROJECT_ZOOM), instant);
      showLevel(function (s) { return s.getAttribute('data-project') === id; });
      svg.setAttribute('data-level', 'project');
    } else if (level === 'topic' && topicById[id]) {
      state.level = 'topic'; state.topic = id; state.project = null;
      light(id);
      bloomTopic(topicById[id]);
      var at = topicById[id].at;
      var ang = Math.atan2(at[1], at[0]);
      moveTo(frameFor(at[0] + Math.cos(ang) * 70, at[1] + Math.sin(ang) * 70, 1.3), instant);
      showLevel(function (s) { return s.getAttribute('data-level') === 'topic' && s.getAttribute('data-topic') === id; });
      svg.setAttribute('data-level', 'topic');
    } else {
      state.level = 'home'; state.topic = null; state.project = null;
      light(null);
      bloomG.innerHTML = '';
      moveTo(frameFor(), instant);
      showLevel(function (s) { return s.getAttribute('data-level') === 'home'; });
      svg.setAttribute('data-level', 'home');
    }
  }

  function fromHash(instant) {
    var h = '';
    try { h = decodeURIComponent(location.hash.slice(1)); } catch (e) {}
    var m = /^([tp])=(.+)$/.exec(h);
    if (m && m[1] === 't') go('topic', m[2], instant);
    else if (m && m[1] === 'p' && data.projects[m[2]]) go('project', m[2], instant);
    else if (!h || h === 'explore' || h === 'intro' || h === 'map') go('home', null, instant);
  }
  function setHash(h) {
    if (location.hash !== '#' + h) {
      try { history.pushState(null, '', '#' + h); } catch (e) { location.hash = h; return; }
    }
    fromHash(false);
  }
  function up() {
    if (state.level === 'project') setHash('t=' + state.topic);
    else if (state.level === 'topic') setHash('explore');
  }

  // ------------------------------------------------------------ input
  svg.addEventListener('click', function (event) {
    var sat = event.target.closest('.ex-sat');
    if (sat) {
      var href = sat.getAttribute('data-href');
      if (href) {
        if (sat.getAttribute('data-out')) window.open(href, '_blank', 'noopener');
        else location.href = href;
      }
      return;
    }
    var proj = event.target.closest('.ex-proj');
    if (proj) { setHash('p=' + proj.getAttribute('data-project')); return; }
    var topic = event.target.closest('.ex-topic');
    if (topic) { setHash('t=' + topic.getAttribute('data-topic')); return; }
    if (event.target.closest('.ex-knot')) { setHash('explore'); return; }
    up();
  });
  svg.addEventListener('pointerover', function (event) {
    var topic = event.target.closest('.ex-topic');
    light(topic ? topic.getAttribute('data-topic') : null, 'is-hover');
  });
  svg.addEventListener('pointerleave', function () { light(null, 'is-hover'); });
  panel.addEventListener('pointerover', function (event) {
    var row = event.target.closest('[data-go-topic]');
    light(row ? row.getAttribute('data-go-topic') : null, 'is-hover');
  });
  panel.addEventListener('pointerleave', function () { light(null, 'is-hover'); });
  panel.addEventListener('click', function (event) {
    var a = event.target.closest('[data-go-topic], [data-go-project], [data-go-home]');
    if (!a) return;
    event.preventDefault();
    if (a.hasAttribute('data-go-home')) setHash('explore');
    else if (a.hasAttribute('data-go-topic')) setHash('t=' + a.getAttribute('data-go-topic'));
    else setHash('p=' + a.getAttribute('data-go-project'));
    var heading = panel.querySelector('.ex-level:not([hidden]) .ex-name, .ex-level:not([hidden]) .ex-title');
    if (heading && event.detail === 0) { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }); }
  });
  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape' || state.level === 'home') return;
    var r = root.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) return;
    up();
  });
  window.addEventListener('popstate', function () { fromHash(false); });
  window.addEventListener('hashchange', function () { fromHash(false); });
  var resizeTimer = 0;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { fromHash(true); }, 120);
  });

  // ------------------------------------------------------------ beads
  // Two beads per thread, slow, brighter on lit threads.
  var beads = [], running = false, visible = true, last = 0;
  threads.forEach(function (p, i) {
    var len = 0;
    try { len = p.getTotalLength(); } catch (e) {}
    if (!len) return;
    for (var k = 0; k < 2; k++) {
      var b = el('circle', { 'class': 'ex-bead', r: 2.2 }, flowG);
      beads.push({ el: b, path: p, len: len, u: ((i * 0.37) + k * 0.5) % 1, dir: (i + k) % 2 ? 1 : -1 });
    }
  });
  function tick(t) {
    if (!running) return;
    var dt = last ? Math.min(64, t - last) : 16;
    last = t;
    for (var i = 0; i < beads.length; i++) {
      var b = beads[i];
      var lit = b.path.classList.contains('is-on') || b.path.classList.contains('is-hover');
      b.u = (b.u + b.dir * dt * (lit ? 0.00016 : 0.00006) + 1) % 1;
      var pt = b.path.getPointAtLength(b.u * b.len);
      b.el.setAttribute('cx', pt.x); b.el.setAttribute('cy', pt.y);
      b.el.setAttribute('class', lit ? 'ex-bead is-lit' : 'ex-bead');
    }
    requestAnimationFrame(tick);
  }
  function startStop() {
    var want = visible && !document.hidden && !still();
    if (want && !running) { running = true; last = 0; requestAnimationFrame(tick); }
    else if (!want) running = false;
    flowG.style.display = still() ? 'none' : '';
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (es) { visible = es[0].isIntersecting; startStop(); }).observe(svg);
  }
  document.addEventListener('visibilitychange', startStop);

  // ------------------------------------------------------------ first view
  var drawn = false;
  try { drawn = sessionStorage.getItem('ex-drawn') === '1'; } catch (e) {}
  if (!drawn && !still()) {
    svg.classList.add('is-arriving');
    Object.keys(topicEl).forEach(function (id, i) { topicEl[id].style.setProperty('--d', (260 + i * 70) + 'ms'); });
    try { sessionStorage.setItem('ex-drawn', '1'); } catch (e) {}
    setTimeout(function () { svg.classList.remove('is-arriving'); }, 2200);
  }
  fromHash(true);
  startStop();
})();
