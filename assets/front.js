/* Behaviour for the home page and the project pages. The pages are complete without this file:
   every tile and stop is a link, and the stop a visitor arrived from is marked by CSS :target.
   This adds: the introduction playing in the page, silent previews under the pointer, the picture
   that travels between the map and a project page, and forwarding for the old page's addresses. */
(function () {
  "use strict";
  var root = document.documentElement;
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)");
  var fine = window.matchMedia("(hover: hover) and (pointer: fine)");
  var saving = !!(navigator.connection && navigator.connection.saveData);
  function moving() { return !calm.matches && !saving; }
  function one(selector, scope) { return (scope || document).querySelector(selector); }
  function all(selector, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }

  /* ---- addresses the earlier home page used ---- */
  function forward() {
    var hash = location.hash;
    var named = hash.match(/^#p=([a-z0-9-]+)/);
    if (named) {
      var anchor = document.getElementById("p-" + named[1]);
      var tile = anchor && anchor.parentNode && one(".tile", anchor.parentNode);
      if (tile) { location.replace(tile.getAttribute("href")); return; }
      if (anchor) { location.replace("#p-" + named[1]); return; }
    }
    if (!document.getElementById("map") || !one(".home")) return;
    var heading = hash.match(/^#h-([a-z0-9-]+)$/);
    var term = hash.match(/^#t-([a-z0-9-]+)$/);
    if (/^#(d|t)=/.test(hash)) location.replace("#map");
    else if (hash === "#intro") location.replace("#p-intro");
    else if (heading && document.getElementById("p-" + heading[1])) location.replace("#p-" + heading[1]);
    else if (term) location.replace("/all.html#term-" + term[1]);
    else if (hash === "#terms") location.replace("/all.html#terms");
    else if (hash === "#more") location.replace("/all.html#about");
  }
  forward();
  window.addEventListener("hashchange", forward);

  /* ---- silent clips ---- */
  function clip(src, repeat) {
    var video = document.createElement("video");
    video.muted = true;
    video.defaultMuted = true;
    video.playsInline = true;
    video.loop = !!repeat;
    video.preload = "auto";
    video.setAttribute("aria-hidden", "true");
    video.tabIndex = -1;
    video.addEventListener("playing", function () { video.classList.add("is-live"); });
    video.src = src;
    return video;
  }
  function drop(video) {
    if (!video) return;
    video.pause();
    video.removeAttribute("src");
    video.load();
    if (video.parentNode) video.parentNode.removeChild(video);
  }
  function start(video) {
    var attempt = video.play();
    if (attempt && attempt.catch) attempt.catch(function () {});
  }

  /* ---- previews: a picture plays its clip while the pointer or the keyboard rests on it.
     Every clip opens on the still it covers and ends on it, so nothing jumps. One clip at a time. ---- */
  var showing = null, showingIn = null, waiting = 0;
  function previewOn(pic, src) {
    if (!moving() || !fine.matches || !src || !pic || showingIn === pic) return;
    clearTimeout(waiting);
    waiting = setTimeout(function () {      /* a short dwell, so sweeping along a row starts nothing */
      drop(showing);
      showing = clip(src, true);
      showingIn = pic;
      pic.appendChild(showing);
      start(showing);
    }, 120);
  }
  function previewOff(pic) {
    clearTimeout(waiting);
    if (showingIn === pic) { drop(showing); showing = null; showingIn = null; }
  }
  var fetched = {};
  function ahead(tile) {
    /* Fetch the project page while the visitor is deciding, so the picture has somewhere to travel to at once. */
    var href = tile.getAttribute("href");
    if (fetched[href] || saving) return;
    fetched[href] = true;
    var link = document.createElement("link");
    link.rel = "prefetch";
    link.href = href;
    document.head.appendChild(link);
  }
  all(".tile").forEach(function (tile) {
    var pic = one(".tile__pic", tile);
    var src = tile.getAttribute("data-loop");
    tile.addEventListener("pointerenter", function () { ahead(tile); previewOn(pic, src); });
    tile.addEventListener("pointerleave", function () { previewOff(pic); });
    tile.addEventListener("focus", function () { ahead(tile); previewOn(pic, src); });
    tile.addEventListener("blur", function () { previewOff(pic); });
    tile.addEventListener("touchstart", function () { ahead(tile); }, { passive: true });
    /* The picture travels to the project page's stage (cross-document view transition). */
    tile.addEventListener("click", function () {
      var stage = document.getElementById("screen");
      all(".is-travelling").forEach(function (el) { el.classList.remove("is-travelling"); });
      if (stage) stage.classList.add("no-travel");
      if (pic) pic.classList.add("is-travelling");
    });
  });
  window.addEventListener("pageshow", function () {
    all(".is-travelling").forEach(function (el) { el.classList.remove("is-travelling"); });
    var stage = document.getElementById("screen");
    if (stage) stage.classList.remove("no-travel");
  });

  /* ---- a project page's stage: the same preview, larger. It never starts by itself, because several
     clips count up to the number the sentence beside them states. ---- */
  var screen = document.getElementById("screen");
  if (screen && screen.getAttribute("data-loop-l")) {
    screen.addEventListener("pointerenter", function () { previewOn(screen, screen.getAttribute("data-loop-l")); });
    screen.addEventListener("pointerleave", function () { previewOff(screen); });
  }

  /* ---- the home page's stage: the introduction ---- */
  var player = document.getElementById("player");
  if (player) {
    var stage = one(".player__screen", player);
    var bar = one(".player__bar", player);
    var play = one("[data-play]", player);
    var idle = null, pause = null, film = null, close = null;

    /* The idle scene: plays once where the whole scene is shown, and rests on its last frame, which is the still.
       front-init.js hid the still for these visitors (class "moves"), so the scene builds from nothing once. */
    function idleStart() {
      if (!moving() || film || idle || window.innerWidth <= 1180 || !player.getAttribute("data-idle")) { root.classList.remove("moves"); return; }
      idle = clip(player.getAttribute("data-idle"), false);
      idle.addEventListener("error", function () { root.classList.remove("moves"); });
      stage.appendChild(idle);
      pause = document.createElement("button");
      pause.type = "button";
      pause.className = "ctl";
      function label() { pause.textContent = idle && idle.paused ? "Play" : "Pause"; }
      pause.addEventListener("click", function (event) {
        event.stopPropagation();
        if (idle.paused) start(idle); else idle.pause();
      });
      idle.addEventListener("playing", label);
      idle.addEventListener("pause", label);
      idle.addEventListener("ended", function () { if (pause && pause.parentNode) pause.parentNode.removeChild(pause); pause = null; });
      label();
      stage.appendChild(pause);
      start(idle);
    }
    function idleStop() {
      drop(idle); idle = null;
      if (pause && pause.parentNode) pause.parentNode.removeChild(pause);
      pause = null;
      root.classList.remove("moves");       /* the still is the picture again */
    }
    function shift(change) {
      if (document.startViewTransition && !calm.matches) document.startViewTransition(change); else change();
    }
    function open() {
      if (film) return;
      film = document.createElement("video");
      film.controls = true;
      film.playsInline = true;
      film.preload = "auto";
      film.setAttribute("aria-label", "Introduction, with captions in the picture");
      /* The still stays under the video until its first frame exists. */
      film.addEventListener("playing", function () { if (film) film.classList.add("is-live"); });
      film.addEventListener("ended", shut);
      film.src = player.getAttribute("data-film");
      start(film);                           /* inside the click, so sound is allowed */
      close = document.createElement("button");
      close.type = "button";
      close.className = "close";
      close.textContent = "Close the video";
      close.addEventListener("click", shut);
      shift(function () {                    /* one change of layout, with nothing shown half way */
        idleStop();
        stage.appendChild(film);
        bar.insertBefore(close, bar.firstChild);
        player.classList.add("is-playing");
        root.classList.add("is-cinema");
        film.focus({ preventScroll: true });
      });
    }
    function shut() {
      if (!film) return;
      var gone = film;
      film = null;
      gone.pause();
      shift(function () {
        drop(gone);
        if (close && close.parentNode) close.parentNode.removeChild(close);
        close = null;
        player.classList.remove("is-playing");
        root.classList.remove("is-cinema");
        play.focus({ preventScroll: true });   /* after the button is shown again, or it cannot take focus */
      });
    }
    play.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button) return;
      event.preventDefault();
      open();
    });
    stage.addEventListener("click", function () { if (!film) open(); });
    document.addEventListener("keydown", function (event) { if (event.key === "Escape" && film) shut(); });
    /* A visitor who arrives at the map (#map) has not seen the stage: the scene starts when it is in view. */
    if ("IntersectionObserver" in window) {
      var watch = new IntersectionObserver(function (entries) {
        if (entries.some(function (entry) { return entry.isIntersecting; })) { watch.disconnect(); idleStart(); }
      }, { threshold: 0.5 });
      watch.observe(stage);
    } else idleStart();
    document.addEventListener("visibilitychange", function () { if (document.hidden && idle && !idle.ended) idle.pause(); });
  } else root.classList.remove("moves");
})();
