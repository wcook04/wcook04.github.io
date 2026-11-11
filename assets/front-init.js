/* Runs before first paint. Marks the page as scripted, and, when the visitor comes back from a project page,
   gives the matching tile the picture's transition name so the picture travels back to its place. */
(function () {
  var root = document.documentElement;
  root.classList.add("js");
  if (!("onpagereveal" in window)) return;
  window.addEventListener("pagereveal", function (event) {
    if (!event.viewTransition || !window.navigation || !navigation.activation || !navigation.activation.from) return;
    var from = new URL(navigation.activation.from.url).pathname.match(/^\/work\/([a-z0-9-]+)\//);
    var here = document.body && document.body.getAttribute("data-entry");
    if (!from || from[1] === here) return;
    var tile = document.querySelector('.tile[data-entry="' + from[1] + '"] .tile__pic');
    if (!tile) return;
    tile.classList.add("is-travelling");
    event.viewTransition.finished.finally(function () { tile.classList.remove("is-travelling"); });
  });
})();
