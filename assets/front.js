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
    tile.addEventListener("pointerenter", function () { ahead(tile); });
    tile.addEventListener("focus", function () { ahead(tile); });
    tile.addEventListener("touchstart", function () { ahead(tile); }, { passive: true });
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

  /* ---- a pause control for anything that moves by itself; it leaves when the motion has stopped ---- */
  function control(host, video) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "ctl";
    function label() { button.textContent = video.paused ? "Play" : "Pause"; }
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      if (video.paused) { video.dataset.held = ""; start(video); }
      else { video.dataset.held = "1"; video.pause(); }
    });
    video.addEventListener("playing", label);
    video.addEventListener("pause", label);
    label();
    host.appendChild(button);
    return { remove: function () { if (button.parentNode) button.parentNode.removeChild(button); } };
  }
  function wide() { return window.innerWidth >= 700; }

  /* ---- a project page's stage: the video's own clip ---- */
  var screen = document.getElementById("screen");
  if (screen && moving() && screen.getAttribute("data-loop-l")) {
    /* Twice through, then it rests on its last frame, which is the poster: motion beside reading text should stop. */
    var loop = clip(screen.getAttribute(wide() ? "data-loop-l" : "data-loop-s"), false);
    var rounds = 0, rested = false;
    screen.appendChild(loop);
    var loopControl = control(screen, loop);
    loop.addEventListener("ended", function () {
      rounds += 1;
      if (rounds < 2) { loop.currentTime = 0; start(loop); }
      else { rested = true; loopControl.remove(); }
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (rested) return;
          if (entry.isIntersecting) { if (!loop.dataset.held) start(loop); } else loop.pause();
        });
      }, { threshold: 0.4 }).observe(screen);
    } else start(loop);
    document.addEventListener("visibilitychange", function () { if (document.hidden && !rested) loop.pause(); });
  }

  /* ---- the home page's stage: the introduction ---- */
  var player = document.getElementById("player");
  if (player) {
    var stage = one(".player__screen", player);
    var bar = one(".player__bar", player);
    var play = one("[data-play]", player);
    var idle = null, idleControl = null, film = null, close = null;

    function idleStart() {
      /* Only where the whole scene is shown. Narrower layouts show its last frame, cropped to the four cards. */
      if (!moving() || film || idle || window.innerWidth <= 1180 || !player.getAttribute("data-idle")) return;
      idle = clip(player.getAttribute("data-idle"), false);
      stage.appendChild(idle);
      idleControl = control(stage, idle);
      idle.addEventListener("ended", function () { if (idleControl) idleControl.remove(); idleControl = null; });
      start(idle);
    }
    function idleStop() {
      drop(idle); idle = null;
      if (idleControl) idleControl.remove();
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
    function idleWhenSeen() {
      /* A visitor who arrives at the map (#map) has not seen the stage: start the scene when they scroll up to it. */
      if (!("IntersectionObserver" in window)) { idleStart(); return; }
      var watch = new IntersectionObserver(function (entries) {
        if (entries.some(function (entry) { return entry.isIntersecting; })) { watch.disconnect(); idleStart(); }
      }, { threshold: 0.5 });
      watch.observe(stage);
    }
    if (document.readyState === "complete") idleWhenSeen(); else window.addEventListener("load", idleWhenSeen);
    document.addEventListener("visibilitychange", function () { if (document.hidden && idle) idle.pause(); });
  }
})();
