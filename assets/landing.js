/* The home page's instrument. The page is complete without this script: the
   weave is a list of links and every project is on the page. This script
   selects one row at a time, shows what each mark leads to in the stage, plays
   the films' silent loops, runs a slow tour until the reader touches the page,
   and shows glossary definitions on hover. Design notes: docs/landing.md. */
(function () {
  'use strict';
  var root = document.documentElement;
  var work = document.getElementById('work');
  if (!work) return;
  var stage = document.getElementById('stage');
  var rows = [].slice.call(work.querySelectorAll('.row[data-row]'));
  var byId = {};
  rows.forEach(function (row) {
    byId[row.dataset.row] = { row: row, article: document.getElementById('p-' + row.dataset.row) };
  });
  var wide = window.matchMedia('(min-width: 1100px)');
  var calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  var saver = navigator.connection && navigator.connection.saveData;
  var current = null;
  var live = null;          // the playing <video>
  if (!calm.matches) root.classList.add('motion');

  /* ------------------------------------------------------------ the frame */
  function stopLoop() {
    if (!live) return;
    var v = live; live = null;
    v.pause(); v.removeAttribute('src'); v.load();
    if (v.parentNode) v.parentNode.removeChild(v);
  }
  function playLoop(frame) {
    stopLoop();
    var src = frame.dataset.loop;
    if (!src || calm.matches || saver || document.hidden) return;
    var v = document.createElement('video');
    v.muted = true; v.loop = true; v.playsInline = true; v.setAttribute('muted', ''); v.setAttribute('playsinline', '');
    v.setAttribute('aria-hidden', 'true'); v.tabIndex = -1; v.preload = 'auto'; v.disablePictureInPicture = true;
    v.addEventListener('playing', function () { v.classList.add('is-live'); }, { once: true });
    v.src = src;
    frame.insertBefore(v, frame.querySelector('.frame__chip'));
    live = v;
    var p = v.play();
    if (p && p.catch) p.catch(function () {});
  }
  /* Put one of an article's resources (a strip tile) in its frame. */
  function feature(article, tile) {
    var frame = article.querySelector('.frame');
    if (!frame || !tile) return;
    [].forEach.call(article.querySelectorAll('.tile'), function (t) { t.classList.toggle('is-shown', t === tile); });
    if (frame.dataset.res === tile.dataset.res) { if (!live || live.parentNode !== frame) playLoop(frame); return; }
    frame.href = tile.href;
    frame.target = tile.target; frame.rel = tile.rel;
    frame.setAttribute('aria-label', tile.getAttribute('aria-label'));
    ['res', 'col', 'chip'].forEach(function (k) { frame.dataset[k] = tile.dataset[k]; });
    if (tile.dataset.loop) frame.dataset.loop = tile.dataset.loop; else delete frame.dataset.loop;
    frame.querySelector('.frame__chip').textContent = tile.dataset.chip;
    var old = frame.querySelector('img, .blank');
    var next;
    if (tile.dataset.img) {
      next = document.createElement('img');
      next.alt = ''; next.width = 1280; next.height = 720; next.decoding = 'async';
      next.srcset = tile.dataset.img + ' 720w, ' + tile.dataset.img2 + ' 1440w';
      next.sizes = '(min-width: 1100px) 760px, 100vw';
      next.src = tile.dataset.img;
    } else {
      next = tile.querySelector('.blank').cloneNode(true);
    }
    stopLoop();
    if (old) frame.replaceChild(next, old); else frame.insertBefore(next, frame.firstChild);
    playLoop(frame);
  }
  function tileFor(article, key) {
    var tiles = article.querySelectorAll('.tile');
    for (var i = 0; i < tiles.length; i++) if (tiles[i].dataset.res === key) return tiles[i];
    return tiles[0];
  }

  /* ---------------------------------------------------------- selecting */
  function select(id, key, opts) {
    var item = byId[id];
    if (!item || !item.article) return;
    opts = opts || {};
    if (current !== id) {
      rows.forEach(function (row) {
        var on = row.dataset.row === id;
        row.classList.toggle('is-on', on);
        var label = row.querySelector('.row__label');
        if (on) label.setAttribute('aria-current', 'true'); else label.removeAttribute('aria-current');
        byId[row.dataset.row].article.classList.toggle('is-on', on);
      });
      current = id;
      if (!opts.quiet && window.history && history.replaceState) {
        try { history.replaceState(null, '', id === 'intro' ? location.pathname + location.search : '#p=' + id); } catch (e) {}
      }
    }
    if (wide.matches) feature(item.article, tileFor(item.article, key || item.article.querySelector('.tile').dataset.res));
  }

  /* -------------------------------------------------------------- the tour */
  var tour = null, touched = false, TOUR_MS = 6000;
  function endTour() {
    touched = true;
    if (tour) { clearInterval(tour); tour = null; }
    root.classList.remove('touring');
  }
  function step() {
    if (document.hidden || !wide.matches) return;
    var r = stage.getBoundingClientRect();
    if (r.bottom < 120 || r.top > window.innerHeight - 120) return;
    var i = rows.findIndex(function (row) { return row.dataset.row === current; });
    select(rows[(i + 1) % rows.length].dataset.row, null, { quiet: true });
  }
  function startTour() {
    if (touched || calm.matches || saver || !wide.matches || location.hash) return;
    root.classList.add('touring');
    tour = setInterval(step, TOUR_MS);
  }
  ['pointermove', 'pointerdown', 'keydown', 'focusin', 'touchstart', 'wheel'].forEach(function (type) {
    work.addEventListener(type, endTour, { passive: true });
  });

  /* ------------------------------------------------------ pointer and keys */
  var dwell = null;
  function later(fn) { clearTimeout(dwell); dwell = setTimeout(fn, 110); }
  rows.forEach(function (row) {
    var id = row.dataset.row;
    var label = row.querySelector('.row__label');
    row.addEventListener('pointerenter', function (ev) {
      if (ev.pointerType === 'touch' || !wide.matches) return;
      later(function () { select(id); });
    });
    row.addEventListener('pointerleave', function () { clearTimeout(dwell); });
    label.addEventListener('focus', function () { if (wide.matches) select(id); });
    label.addEventListener('click', function (ev) {
      if (!wide.matches) { select(id); return; }       // one column: follow the link to the article
      ev.preventDefault();
      select(id);
      var frame = byId[id].article.querySelector('.frame');
      if (ev.detail === 0 && frame) frame.focus();       // Enter on the label moves into the stage
    });
    label.addEventListener('keydown', function (ev) {
      if (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp') return;
      var i = rows.indexOf(row) + (ev.key === 'ArrowDown' ? 1 : -1);
      if (i < 0 || i >= rows.length) return;
      ev.preventDefault();
      rows[i].querySelector('.row__label').focus();
    });
    [].forEach.call(row.querySelectorAll('.knot'), function (knot) {
      knot.tabIndex = -1;                                 // the stage's strip repeats these links
      knot.addEventListener('pointerenter', function (ev) {
        if (ev.pointerType === 'touch' || !wide.matches) return;
        later(function () { select(id, knot.dataset.knot); });
      });
    });
  });
  [].forEach.call(stage.querySelectorAll('.tile'), function (tile) {
    var article = tile.closest('.proj');
    function show() { if (wide.matches) feature(article, tile); }
    tile.addEventListener('pointerenter', function (ev) { if (ev.pointerType !== 'touch') later(show); });
    tile.addEventListener('pointerleave', function () { clearTimeout(dwell); });
    tile.addEventListener('focus', show);
  });

  /* -------------------------------------------------- one column: loops in view */
  var seen = null;
  function watchFrames() {
    if (seen) { seen.disconnect(); seen = null; }
    if (wide.matches || !('IntersectionObserver' in window)) return;
    stopLoop();
    var best = null;
    seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && en.intersectionRatio >= 0.6) { best = en.target; playLoop(best); }
        else if (best === en.target) { best = null; stopLoop(); }
      });
    }, { threshold: [0, 0.6] });
    [].forEach.call(stage.querySelectorAll('.frame'), function (f) { seen.observe(f); });
  }
  if (wide.addEventListener) wide.addEventListener('change', function () { watchFrames(); if (wide.matches) select(current || 'intro', null, { quiet: true }); });
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stopLoop();
    else if (wide.matches && current) playLoop(byId[current].article.querySelector('.frame'));
  });

  /* ------------------------------------------------------------ addresses */
  function fromHash() {
    var h = location.hash.replace(/^#/, '');
    if (!h) return null;
    var m = /^(p|d|t)=([\w-]+)/.exec(h);
    if (m && m[1] === 'p' && byId[m[2]]) return m[2];
    if (m && m[1] === 'd') {
      var first = rows.filter(function (r) { return r.dataset.group === m[2]; })[0];
      if (first) return first.dataset.row;
    }
    if (m && m[1] === 't' && work.dataset.topics) {
      try { var map = JSON.parse(work.dataset.topics); if (map[m[2]] && byId[map[m[2]]]) return map[m[2]]; } catch (e) {}
    }
    if (h === 'intro') return 'intro';
    if (h.indexOf('p-') === 0 && byId[h.slice(2)]) return h.slice(2);
    return null;
  }
  window.addEventListener('hashchange', function () { var id = fromHash(); if (id) { endTour(); select(id, null, { quiet: true }); } });

  /* ---------------------------------------------------------------- start */
  var first = fromHash();
  var entered = false;
  try { entered = sessionStorage.getItem('weave-entered') === '1'; sessionStorage.setItem('weave-entered', '1'); } catch (e) {}
  if (!entered && !calm.matches) {
    root.classList.add('enter');
    setTimeout(function () { root.classList.remove('enter'); }, 1600);
  }
  select(first || 'intro', null, { quiet: true });
  if (first && !wide.matches && byId[first].article.scrollIntoView) byId[first].article.scrollIntoView();
  watchFrames();
  setTimeout(startTour, 5000);

  /* ------------------------------------------------------- glossary cards */
  var card = document.getElementById('termcard');
  var hideTimer = null;
  function showTerm(link) {
    var def = document.getElementById('t-' + link.dataset.term);
    if (!def || !card) return;
    clearTimeout(hideTimer);
    card.textContent = '';
    var name = document.createElement('strong');
    name.textContent = def.querySelector('dt').textContent;
    card.appendChild(name);
    card.appendChild(document.createTextNode(def.querySelector('.def__preview').textContent));
    card.hidden = false;
    var r = link.getBoundingClientRect();
    var w = Math.min(320, window.innerWidth - 24);
    card.style.width = w + 'px';
    var left = Math.max(12, Math.min(r.left, window.innerWidth - w - 12));
    card.style.left = (left + window.scrollX) + 'px';
    var top = r.bottom + 8;
    if (top + card.offsetHeight > window.innerHeight - 8) top = r.top - card.offsetHeight - 8;
    card.style.top = (top + window.scrollY) + 'px';
    link.setAttribute('aria-describedby', 'termcard');
  }
  function hideTerm(now) {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(function () { if (card) card.hidden = true; }, now ? 0 : 160);
  }
  document.addEventListener('pointerover', function (ev) {
    var link = ev.target.closest && ev.target.closest('a.term');
    if (link) showTerm(link); else if (card && ev.target.closest && ev.target.closest('#termcard')) clearTimeout(hideTimer);
  });
  document.addEventListener('pointerout', function (ev) {
    if (ev.target.closest && (ev.target.closest('a.term') || ev.target.closest('#termcard'))) hideTerm(false);
  });
  document.addEventListener('focusin', function (ev) { if (ev.target.matches && ev.target.matches('a.term')) showTerm(ev.target); });
  document.addEventListener('focusout', function (ev) { if (ev.target.matches && ev.target.matches('a.term')) hideTerm(true); });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') hideTerm(true); });
})();
