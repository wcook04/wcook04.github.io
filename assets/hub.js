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

/* The project index (index.html, "Projects"). Each project's line opens
   beneath itself to show its videos and code; "Show all" opens every line,
   which is the whole map. The head script stamps html.scripting, so the
   stylesheet keeps lines closed from the first paint; without scripting every
   line is open. A line named in the address (/#zenith) opens on arrival, by
   CSS (:target) before this runs and by this after. Nothing is stored. */
(function () {
  var map = document.querySelector('[data-hub-map]');
  if (!map) return;
  var rows = Array.prototype.slice.call(map.querySelectorAll('.proj'));
  var all = document.querySelector('[data-proj-all]');
  var LABEL_OPEN = 'Show all videos and code', LABEL_CLOSE = 'Hide all videos and code';

  function isOpen(row) { return row.classList.contains('is-open'); }
  function set(row, open) {
    var button = row.querySelector('.proj__toggle');
    row.classList.toggle('is-open', open);
    row.classList.toggle('is-shut', !open);
    if (button) {
      button.setAttribute('aria-expanded', open ? 'true' : 'false');
      var verb = button.querySelector('.proj__verb');
      if (verb) verb.textContent = open ? ': hide ' : ': show ';
    }
  }
  function sync() {
    if (!all) return;
    var every = rows.every(isOpen);
    all.setAttribute('aria-expanded', every ? 'true' : 'false');
    all.textContent = every ? LABEL_CLOSE : LABEL_OPEN;
  }
  function fromAddress() {
    var id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) {}
    var row = id ? document.getElementById(id) : null;
    if (row && row.classList.contains('proj')) { set(row, true); sync(); }
  }

  rows.forEach(function (row) {
    var button = row.querySelector('.proj__toggle');
    var head = row.querySelector('.proj__head');
    if (button) button.addEventListener('click', function () { set(row, !isOpen(row)); sync(); });
    // The whole line opens it, except its links, and except a reader selecting its words.
    if (head) head.addEventListener('click', function (event) {
      if (event.target.closest && event.target.closest('a, button')) return;
      try { if (String(window.getSelection())) return; } catch (e) {}
      set(row, !isOpen(row)); sync();
    });
  });
  if (all) all.addEventListener('click', function () {
    var open = !rows.every(isOpen);
    rows.forEach(function (row) { set(row, open); });
    sync();
  });
  window.addEventListener('hashchange', fromAddress);
  fromAddress();
})();
