/* The day / night switch, adapted from the Plectis site's docs.js. An extra:
   without this script the page follows the system's scheme. It stamps
   data-theme on <html>, remembers only a real choice (a choice equal to the
   system's scheme clears the stored one) and flips without a smear. The
   storage key is the Plectis sites' own, so a reader's choice carries between
   the sites on this host that read it. The map's lines are hub-map.js. */
(function () {
  var KEY = 'plectis-theme';
  var root = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  var toggle = null;

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function resolved() {
    var s = stored();
    if (s === 'dark' || s === 'light') return s;
    return mq && mq.matches ? 'dark' : 'light';
  }
  function apply(theme) {
    root.setAttribute('data-theme', theme);
    try { root.style.colorScheme = theme; } catch (e) {}
    if (toggle) toggle.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
  }
  function flip(next) {
    root.classList.add('vt-theme');
    apply(next);
    void root.offsetWidth;
    var lift = function () { root.classList.remove('vt-theme'); };
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(function () { window.requestAnimationFrame(lift); });
    } else { lift(); }
  }

  apply(resolved());
  if (mq && mq.addEventListener) {
    mq.addEventListener('change', function () { if (!stored()) flip(resolved()); });
  }

  var SUN = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"></path></svg>';
  var MOON = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"></path></svg>';

  function mountToggle() {
    var bar = document.querySelector('.hub-header__inner');
    if (!bar || bar.querySelector('.theme-toggle')) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'theme-toggle';
    btn.setAttribute('role', 'switch');
    btn.setAttribute('aria-label', 'Dark mode');
    btn.title = 'Switch light / dark';
    btn.setAttribute('aria-checked', root.getAttribute('data-theme') === 'dark' ? 'true' : 'false');
    btn.innerHTML =
      '<span class="theme-toggle__track">' +
        '<span class="theme-toggle__ico theme-toggle__ico--sun">' + SUN + '</span>' +
        '<span class="theme-toggle__ico theme-toggle__ico--moon">' + MOON + '</span>' +
        '<span class="theme-toggle__knob"></span>' +
      '</span>';
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      var system = mq && mq.matches ? 'dark' : 'light';
      try { if (next === system) localStorage.removeItem(KEY); else localStorage.setItem(KEY, next); } catch (e) {}
      flip(next);
    });
    toggle = btn;
    bar.appendChild(btn);
  }

  function ready() { mountToggle(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
  else ready();
})();

/* The terms (index.html, "Terms used on this page"). The build links the first
   use of each defined term in a block to its definition at the foot of the
   page, so every definition is one link away without this script. This adds a
   card beside the word: after a short dwell for a pointer, at once for keys
   (focus), on a tap for touch. The card stays while the pointer is on it, Esc
   closes it, and it reads its words from the definition already on the page,
   so the two can never disagree. Nothing is fetched or stored. */
(function () {
  var card = null, owner = null, openTimer = 0, closeTimer = 0;
  var fine = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function definition(id) {
    var def = document.getElementById('t-' + id);
    if (!def) return null;
    var dt = def.querySelector('dt'), pre = def.querySelector('.def__preview'), det = def.querySelector('.def__detail');
    return { term: dt ? dt.textContent : id, preview: pre ? pre.textContent : '', detail: det ? det.textContent : '' };
  }
  function build() {
    card = document.createElement('div');
    card.className = 'term-card';
    card.setAttribute('role', 'tooltip');
    card.id = 'term-card';
    card.addEventListener('pointerenter', function () { clearTimeout(closeTimer); });
    card.addEventListener('pointerleave', function () { closeSoon(); });
    document.body.appendChild(card);
  }
  function place(link) {
    var r = link.getBoundingClientRect(), w = card.offsetWidth, h = card.offsetHeight;
    var left = Math.max(12, Math.min(window.innerWidth - w - 12, r.left + r.width / 2 - w / 2));
    var top = r.bottom + 10;
    if (top + h > window.innerHeight - 12 && r.top - h - 10 > 12) top = r.top - h - 10;
    card.style.left = (left + window.scrollX) + 'px';
    card.style.top = (top + window.scrollY) + 'px';
  }
  function open(link) {
    var d = definition(link.getAttribute('data-term'));
    if (!d) return;
    if (!card) build();
    if (owner && owner !== link) owner.removeAttribute('aria-expanded');
    owner = link;
    card.innerHTML = '';
    var t = document.createElement('p'); t.className = 'term-card__term'; t.textContent = d.term;
    var p = document.createElement('p'); p.className = 'term-card__preview'; p.textContent = d.preview;
    var q = document.createElement('p'); q.className = 'term-card__detail'; q.textContent = d.detail;
    card.appendChild(t); card.appendChild(p); card.appendChild(q);
    link.setAttribute('aria-describedby', 'term-card');
    link.setAttribute('aria-expanded', 'true');
    card.classList.remove('is-open');
    place(link);
    requestAnimationFrame(function () { card.classList.add('is-open'); });
  }
  function close() {
    clearTimeout(openTimer);
    if (!card || !owner) return;
    card.classList.remove('is-open');
    owner.removeAttribute('aria-expanded');
    owner.removeAttribute('aria-describedby');
    owner = null;
  }
  function closeSoon() { clearTimeout(closeTimer); closeTimer = setTimeout(close, 160); }

  document.addEventListener('pointerover', function (event) {
    var link = event.target.closest && event.target.closest('a.term');
    if (!link || !fine) return;
    clearTimeout(closeTimer); clearTimeout(openTimer);
    openTimer = setTimeout(function () { open(link); }, owner ? 0 : 380);
  });
  document.addEventListener('pointerout', function (event) {
    var link = event.target.closest && event.target.closest('a.term');
    if (!link) return;
    clearTimeout(openTimer);
    closeSoon();
  });
  document.addEventListener('focusin', function (event) {
    var link = event.target.closest && event.target.closest('a.term');
    if (link) open(link); else if (owner && !(card && card.contains(event.target))) close();
  });
  document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a.term');
    if (link && !fine && owner !== link) { event.preventDefault(); open(link); return; }
    if (!link && card && !card.contains(event.target)) close();
  });
  document.addEventListener('keydown', function (event) { if (event.key === 'Escape') close(); });
  window.addEventListener('resize', close);
})();
