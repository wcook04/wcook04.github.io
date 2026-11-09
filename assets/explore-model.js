/* Pure navigation and selection logic, shared with the bounded model checks. */
(function (root, make) {
  var api = make();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ExplorerModel = api;
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';
  function fold(s) { return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }
  function parentOf(data, pid, preferred) {
    var valid = data.config.doors.filter(function (d) { return d.projects.indexOf(pid) >= 0; });
    return valid.some(function (d) { return d.id === preferred; }) ? preferred : (valid[0] || {}).id;
  }
  function resolve(data, hash) {
    var raw = String(hash || '').replace(/^#/, '');
    var special = { projects: 'all', websites: 'all', work: 'all', videos: 'films', contact: 'about', terms: 'terms', introductions: 'intro' };
    if (special[raw]) raw = special[raw];
    if (['all', 'films', 'about', 'terms', 'intro', 'journey'].indexOf(raw) >= 0) return { view: raw };
    var q = new URLSearchParams(raw);
    var pid = q.get('p') || q.get('project');
    if (!pid && data.projects[raw]) pid = raw;
    var topic = q.get('t');
    if (topic && data.config.direct_topics[topic]) pid = data.config.direct_topics[topic];
    if (pid && data.projects[pid]) {
      var via = parentOf(data, pid, q.get('via') || data.config.topic_aliases[topic]);
      var selected = q.get('film');
      return { view: 'project', id: pid, via: via, film: data.projects[pid].films.indexOf(selected) >= 0 ? selected : null };
    }
    var door = q.get('d') || data.config.topic_aliases[topic];
    var d = data.config.doors.find(function (x) { return x.id === door; });
    if (d) {
      if (d.projects.length === 1) return { view: 'project', id: d.projects[0], via: d.id, film: null };
      return { view: 'door', id: d.id };
    }
    return { view: 'home' };
  }
  function hashFor(s) {
    if (s.view === 'home') return 'explore';
    if (s.view === 'door') return 'd=' + encodeURIComponent(s.id);
    if (s.view === 'project') return 'p=' + encodeURIComponent(s.id) + (s.via ? '&via=' + encodeURIComponent(s.via) : '') + (s.film ? '&film=' + encodeURIComponent(s.film) : '');
    return s.view;
  }
  function published(f) { return !!(f && f.youtube); }
  function earlier(data, f) { return f.edition === 'earlier' || published(data.films[f.superseded_by]); }
  function tasters(data, pid) {
    return data.projects[pid].films.map(function (id) { return data.films[id]; }).filter(function (f) { return f && f.format === 'short' && !earlier(data, f); });
  }
  function lead(data, state) {
    var options = tasters(data, state.id);
    if (state.film) return data.films[state.film];
    if (state.via === 'proofs') {
      var reader = options.find(function (f) { return /reader|sk-website/.test(f.id); });
      if (reader) return reader;
    }
    if (state.id === 'maths') return options.find(function (f) { return f.id === 'short-mathematics-overview'; }) || options[0];
    return options[0] || data.projects[state.id].films.map(function (id) { return data.films[id]; }).find(function (f) { return !earlier(data, f); });
  }
  function onward(data, film) {
    return (film && film.leads_to || []).map(function (id) { return data.films[id]; }).filter(Boolean);
  }
  function search(data, query) {
    var words = fold(query).trim().split(/\s+/).filter(Boolean);
    return Object.values(data.projects).filter(function (p) {
      var hay = fold([p.id,p.name,p.label,p.question,p.choice,p.line,p.plain,p.subject,p.summary,(p.aka || []).join(' '),(p.repos || []).join(' ')].join(' '));
      return words.every(function (w) { return hay.indexOf(w) >= 0; });
    });
  }
  function filmList(data, status, history, format) {
    return Object.values(data.films).filter(function (f) {
      return (status !== 'published' || published(f)) && (history || !earlier(data,f)) && (format === 'all' || f.format === format);
    });
  }
  function filmLabel(f) {
    var names = { 'short-mathematics-overview':'The map', 'short-mathematics':'Erdős #257', 'short-quartic':'The result', 'short-quartic-reader':'The reader', 'short-sk-no-gap':'The result', 'short-sk-website':'The reader' };
    return names[f.id] || 'Introduction';
  }
  function routeForFilm(data, pid, fid) {
    var f=data.films[fid], short=f.format==='short'?f:tasters(data,pid).find(function(s){return (s.leads_to||[]).indexOf(fid)>=0;});
    var preferred=/reader|sk-website/.test(fid)||short&&/reader|sk-website/.test(short.id)?'proofs':null;
    return hashFor({view:'project',id:pid,via:parentOf(data,pid,preferred),film:short?short.id:null});
  }
  return { fold:fold, resolve:resolve, hashFor:hashFor, parentOf:parentOf, published:published, earlier:earlier, tasters:tasters, lead:lead, onward:onward, search:search, filmList:filmList, filmLabel:filmLabel, routeForFilm:routeForFilm };
});
