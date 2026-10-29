// Fills both sheets of marks.html from its one template.
['sheet-day', 'sheet-night'].forEach(function (id) {
  document.getElementById(id).appendChild(document.getElementById('rows').content.cloneNode(true));
});
