/* Behaviour for the home page and the project pages. The pages are complete without this file:
   every tile and stop is a link, and the stop a visitor arrived from is marked by CSS :target.
   This adds: the introduction playing in the page, silent preview loops, the picture that travels
   between the map and a project page, and forwarding for the old page's addresses. */
(function () {
  "use strict";
  var root = document.documentElement;
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)");
  var fine = window.matchMedia("(hover: hover) and (pointer: fine)");
  var saving = !!(navigator.connection && navigator.connection.saveData);
  function moving() { return !calm.matches && !saving; }
  function one(selector, scope) { return (scope || document).querySelector(selector); }
  function all(selector, scope) { return Array.prototype.slice.call((scope || document).querySelectorAll(selector)); }

  /* ---- old addresses: #p=<id>, #intro, #d=<group>, #t=<topic> ---- */
  function forward() {
    var hash = location.hash;
    var named = hash.match(/^#p=([a-z0-9-]+)/);
    if (named) {
      var anchor = document.getElementById("p-" + named[1]);
      var tile = anchor && anchor.parentNode && one(".tile", anchor.parentNode);
      if (tile) { location.replace(tile.getAttribute("href")); return; }
      if (anchor) { location.replace("#p-" + named[1]); return; }
    }
    if (/^#(d|t)=/.test(hash) && document.getElementById("map")) location.replace("#map");
    if (hash === "#intro") location.replace("#p-intro");
  }
  forward();
  window.addEventListener("hashchange", forward);

  /* ---- one silent loop at a time ---- */
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

  /* ---- map tiles: the loop plays while the pointer or the keyboard is on the tile ---- */
  var tileClip = null;
  function tileOn(tile) {
    if (!moving() || !fine.matches) return;
    var src = tile.getAttribute("data-loop");
    var pic = one(".tile__pic", tile);
    if (!src || !pic || (tileClip && tileClip.parentNode === pic)) return;
    drop(tileClip);
    tileClip = clip(src, true);
    pic.appendChild(tileClip);
    start(tileClip);
  }
  function tileOff(tile) {
    if (tileClip && tileClip.parentNode === one(".tile__pic", tile)) { drop(tileClip); tileClip = null; }
  }
  all(".tile").forEach(function (tile) {
    tile.addEventListener("pointerenter", function () { tileOn(tile); });
    tile.addEventListener("pointerleave", function () { tileOff(tile); });
    tile.addEventListener("focus", function () { tileOn(tile); });
    tile.addEventListener("blur", function () { tileOff(tile); });
    /* The picture travels to the project page's stage (cross-document view transition). */
    tile.addEventListener("click", function () {
      var pic = one(".tile__pic", tile);
      var screen = document.getElementById("screen");
      all(".is-travelling").forEach(function (el) { el.classList.remove("is-travelling"); });
      if (screen) screen.classList.add("no-travel");
      if (pic) pic.classList.add("is-travelling");
    });
  });
  window.addEventListener("pageshow", function () {
    all(".is-travelling").forEach(function (el) { el.classList.remove("is-travelling"); });
    var screen = document.getElementById("screen");
    if (screen) screen.classList.remove("no-travel");
  });

  /* ---- a pause control for anything that moves by itself ---- */
  function control(host, video, repeat) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "ctl";
    function label() { button.textContent = video.ended ? "Replay" : (video.paused ? "Play preview" : "Pause"); }
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      if (video.ended) { video.currentTime = 0; start(video); }
      else if (video.paused) start(video);
      else video.pause();
    });
    ["playing", "pause", "ended"].forEach(function (name) { video.addEventListener(name, label); });
    label();
    host.appendChild(button);
    return button;
  }
  function wide() { return window.innerWidth >= 700; }

  /* ---- a project page's stage: the video's own loop ---- */
  var screen = document.getElementById("screen");
  if (screen && moving() && screen.getAttribute("data-loop-l")) {
    /* Twice through, then it rests on its last frame: motion beside reading text should stop. */
    var loop = clip(screen.getAttribute(wide() ? "data-loop-l" : "data-loop-s"), false);
    var rounds = 0;
    loop.addEventListener("ended", function () { rounds += 1; if (rounds < 2 && !loop.dataset.held) { loop.currentTime = 0; start(loop); } });
    screen.appendChild(loop);
    control(screen, loop, false);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !loop.dataset.held && !loop.ended) start(loop); else if (!loop.ended) loop.pause();
        });
      }, { threshold: 0.4 }).observe(screen);
    } else start(loop);
    one(".ctl", screen).addEventListener("click", function () { loop.dataset.held = loop.paused ? "" : "1"; });
    document.addEventListener("visibilitychange", function () { if (document.hidden) loop.pause(); });
  }

  /* ---- the home page's stage: the introduction ---- */
  var player = document.getElementById("player");
  if (player) {
    var stage = one(".player__screen", player);
    var bar = one(".player__bar", player);
    var play = one("[data-play]", player);
    var idle = null, idleControl = null, film = null, close = null;

    function idleStart() {
      if (!moving() || film || idle || !player.getAttribute("data-idle-l")) return;
      idle = clip(player.getAttribute(window.innerWidth > 860 ? "data-idle-l" : "data-idle-n"), false);
      stage.appendChild(idle);
      idleControl = control(bar, idle, false);
      idleControl.classList.add("ctl--bar");
      start(idle);
    }
    function idleStop() {
      drop(idle); idle = null;
      if (idleControl && idleControl.parentNode) idleControl.parentNode.removeChild(idleControl);
      idleControl = null;
    }
    function shift(change) {
      if (document.startViewTransition && !calm.matches) document.startViewTransition(change); else change();
    }
    function open() {
      if (film) return;
      idleStop();
      film = document.createElement("video");
      film.controls = true;
      film.playsInline = true;
      film.preload = "auto";
      film.className = "is-live";
      film.setAttribute("aria-label", "Introduction, with captions in the picture");
      film.src = player.getAttribute("data-film");
      stage.appendChild(film);
      start(film);                       /* inside the click, so sound is allowed */
      close = document.createElement("button");
      close.type = "button";
      close.className = "close";
      close.textContent = "Close the video";
      close.addEventListener("click", shut);
      bar.insertBefore(close, bar.firstChild);
      film.addEventListener("ended", shut);
      shift(function () { player.classList.add("is-playing"); root.classList.add("is-cinema"); });
      film.focus({ preventScroll: true });
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
      });
      play.focus({ preventScroll: true });
    }
    play.addEventListener("click", function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button) return;
      event.preventDefault();
      open();
    });
    stage.addEventListener("click", function () { if (!film) open(); });
    document.addEventListener("keydown", function (event) { if (event.key === "Escape" && film) shut(); });
    if (document.readyState === "complete") idleStart(); else window.addEventListener("load", idleStart);
    document.addEventListener("visibilitychange", function () { if (document.hidden && idle) idle.pause(); });
  }
})();
