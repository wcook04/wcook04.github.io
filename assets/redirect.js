/* Old Plectis addresses keep working. The Plectis website moved from /plectis/
   to /practical-formal-verification/ when its repository was renamed, and
   GitHub Pages answers the old addresses with this host's 404 page. This
   forwards each one to the same page at the new address, keeping its query
   and fragment. Other missing addresses stay on the 404 page. */
(function () {
  var from = '/plectis/';
  var to = '/practical-formal-verification/';
  var path = window.location.pathname;
  if (path === '/plectis' || path.indexOf(from) === 0) {
    var rest = path === '/plectis' ? '' : path.slice(from.length);
    window.location.replace(to + rest + window.location.search + window.location.hash);
  }
})();
