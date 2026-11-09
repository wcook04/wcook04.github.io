/* The home page's map of how the work connects (index.html, "How the work
   connects"). The drawing is static SVG written by scripts/build_hub.py: three
   strands leave one knot, the introduction, and each project is a stop on its
   area's strand. Threads join projects that share a subject, a method or a
   film; brackets over a strand name a collection. Every stop is already a
   link to its project's card, so nothing here is needed to read or use the map.

   What this adds:
   - pointing at or tabbing to a stop lights it, its threads and brackets and
     the stops they reach, steps the rest back, and shows its caption under
     the drawing (what it is and what it connects to);
   - for a pointer, one bead of light runs along each lit thread, once;
   - the first time the map comes into view in a session, the strands are
     drawn out from the knot and the stops arrive along them, left to right.
   None of the motion runs under reduced motion or Save-Data, or in a hidden
   tab. Nothing is fetched or stored except a session flag for the drawing.

   Adapted from the previous home map (this file before 9 November 2026),
   itself adapted from the Plectis film map's cables and Magic UI's
   AnimatedBeam (MIT License, Copyright (c) Magic UI): the lit route in full
   ink with the rest stepped back, and the one-off bead along it. */
(function () {
  'use strict';
  var svg = document.querySelector('[data-plait]');
  if (!svg || !window.matchMedia) return;
  var NS = 'http://www.w3.org/2000/svg';
  var stops = Array.prototype.slice.call(svg.querySelectorAll('.pl-stop[data-id]'));
  var threads = Array.prototype.slice.call(svg.querySelectorAll('.pl-thread'));
  var brackets = Array.prototype.slice.call(svg.querySelectorAll('.pl-bracket'));
  var captions = {};
  Array.prototype.forEach.call(document.querySelectorAll('.pl-cap[data-for]'), function (p) {
    captions[p.getAttribute('data-for')] = p;
  });
  var current = null, beads = [];

  function quiet() {
    try { if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return true; } catch (e) {}
    try { if (navigator.connection && navigator.connection.saveData) return true; } catch (e) {}
    return document.hidden;
  }

  function clearBeads() {
    beads.forEach(function (b) { if (b.parentNode) b.parentNode.removeChild(b); });
    beads = [];
  }

  function bead(path) {
    var length = 0;
    try { length = path.getTotalLength(); } catch (e) { return; }
    if (!length) return;
    var dot = document.createElementNS(NS, 'circle');
    dot.setAttribute('r', '3.2');
    dot.setAttribute('class', 'pl-bead');
    svg.appendChild(dot);
    beads.push(dot);
    var start = null, duration = Math.min(900, 280 + length * 1.6);
    function frame(t) {
      if (!dot.parentNode) return;
      if (start === null) start = t;
      var k = Math.min(1, (t - start) / duration);
      var eased = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      var p = path.getPointAtLength(eased * length);
      dot.setAttribute('cx', p.x); dot.setAttribute('cy', p.y);
      dot.setAttribute('opacity', String(k < 0.85 ? 1 : (1 - k) / 0.15));
      if (k < 1) requestAnimationFrame(frame); else if (dot.parentNode) dot.parentNode.removeChild(dot);
    }
    requestAnimationFrame(frame);
  }

  function light(id, withBeads) {
    if (id === current) return;
    current = id;
    clearBeads();
    Object.keys(captions).forEach(function (k) { captions[k].hidden = k !== id; });
    if (!id) {
      svg.classList.remove('is-lit');
      stops.concat(threads, brackets).forEach(function (el) { el.classList.remove('is-on'); });
      return;
    }
    var on = {}; on[id] = true;
    threads.forEach(function (t) {
      var hit = t.getAttribute('data-a') === id || t.getAttribute('data-b') === id;
      t.classList.toggle('is-on', hit);
      if (hit) {
        on[t.getAttribute('data-a')] = true; on[t.getAttribute('data-b')] = true;
        if (withBeads && !quiet()) bead(t);
      }
    });
    brackets.forEach(function (b) {
      var members = (b.getAttribute('data-members') || '').split(' ');
      var hit = members.indexOf(id) !== -1;
      b.classList.toggle('is-on', hit);
      if (hit) members.forEach(function (m) { on[m] = true; });
    });
    stops.forEach(function (s) { s.classList.toggle('is-on', !!on[s.getAttribute('data-id')]); });
    svg.classList.add('is-lit');
  }

  stops.forEach(function (stop) {
    var id = stop.getAttribute('data-id');
    if (id === 'films') return;
    stop.addEventListener('pointerenter', function () { light(id, true); });
    stop.addEventListener('focus', function () { light(id, false); });
  });
  svg.addEventListener('pointerleave', function () { light(null); });
  svg.addEventListener('focusout', function (event) {
    if (!svg.contains(event.relatedTarget)) light(null);
  });
  document.addEventListener('keydown', function (event) { if (event.key === 'Escape') light(null); });

  // The first view in a session: strands drawn out from the knot, then the stops.
  var KEY = 'plait-drawn';
  var drawn = false;
  try { drawn = sessionStorage.getItem(KEY) === '1'; } catch (e) {}
  if (drawn || quiet() || !('IntersectionObserver' in window)) return;
  var box = svg.viewBox && svg.viewBox.baseVal;
  var width = box && box.width ? box.width : 1200;
  function at(el) {
    var x = 0;
    try { var b = el.getBBox(); x = b.x + b.width / 2; } catch (e) {}
    return 520 + Math.round((x / width) * 620);
  }
  stops.concat(threads, brackets).forEach(function (el) { el.style.setProperty('--d', at(el) + 'ms'); });
  svg.classList.add('is-drawing');
  svg.style.visibility = 'hidden';
  var seen = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      seen.disconnect();
      svg.style.visibility = '';
      // Restart the animations now that the drawing is on screen.
      svg.classList.remove('is-drawing'); void svg.getBoundingClientRect(); svg.classList.add('is-drawing');
      try { sessionStorage.setItem(KEY, '1'); } catch (e) {}
      setTimeout(function () {
        svg.classList.remove('is-drawing');
        stops.concat(threads, brackets).forEach(function (el) { el.style.removeProperty('--d'); });
      }, 2200);
    });
  }, { threshold: 0.12 });
  seen.observe(svg);
})();
