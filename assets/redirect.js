/* Old Plectis addresses keep working. The Plectis website moved from /plectis/
   to /practical-formal-verification/ when its repository was renamed, and
   GitHub Pages answers the old addresses with this host's 404 page. The old
   front door, /plectis/ itself, opens the home page, which lists every website
   and film; any deeper old address forwards to the same page at the new
   address, keeping its query and fragment. Other missing addresses stay on the
   404 page. */
(function () {
  var from = '/plectis/';
  var to = '/practical-formal-verification/';
  var path = window.location.pathname;
  if (path === '/plectis' || path === from || path === from + 'index.html') {
    window.location.replace('/' + window.location.hash);
  } else if (path.indexOf(from) === 0) {
    window.location.replace(to + path.slice(from.length) + window.location.search + window.location.hash);
  }
})();
