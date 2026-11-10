/* Question-led explorer: native links, explicit states, progressive motion. */
(function () {
  'use strict';
  var source=document.getElementById('explorer-data');
  if(!source||!window.ExplorerModel)return;
  var data=JSON.parse(source.textContent),M=window.ExplorerModel;
  var main=document.getElementById('main'),homeHTML=main.innerHTML;
  var popover=document.getElementById('glossary-card'),dialog=document.getElementById('film-dialog');
  var terms=Object.fromEntries(data.terms.map(function(t){return[t.id,t];}));
  var state=M.resolve(data,location.hash),currentHash='',lastFocus={},activeTerm=null,glossaryTimer=0,ignoreTermFocus=false;
  var filmFilters={status:'all',history:false,format:'all'},projectQuery='';
  var motion=window.matchMedia('(prefers-reduced-motion: reduce)'),pendingTransition=null,lastFilmOpener=null,journeyObserver=null,navSerial=0;
  document.documentElement.classList.add('studio-root');
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function clock(f){var s=f.duration_seconds||f.cut_seconds;return s?Math.floor(s/60)+':'+String(s%60).padStart(2,'0'):'';}
  var ART_FALLBACK={research:'research',proofs:'proofs',assistants:'trace',explaining:'funnel',code:'code',testing:'bugs',maths:'research',quartic:'quantum','lean-exposition':'magnets','proof-reader':'proofs',atlas:'proofs','formal-verification':'proofs','agent-trace':'trace','one-checkout':'trace','safety-core':'trace',codemap:'code','code-ontology-bridge':'code',zenith:'bugs',funnel:'funnel','narration-ir':'funnel'};
  function object(kind,cls){return '<div class="focus-object '+(cls||'')+'">'+(data.objects[kind]||data.objects[ART_FALLBACK[kind]]||'')+'</div>';}
  function byDoor(id){return data.config.doors.find(function(d){return d.id===id;});}
  function routeLink(route,text,cls,parent){return '<a href="#'+esc(route)+'" data-route="'+esc(route)+'"'+(parent?' data-parent="'+esc(parent)+'"':'')+(cls?' class="'+cls+'"':'')+'>'+text+'</a>';}
  function external(url,text,cls){return '<a href="'+esc(url)+'" target="_blank" rel="noopener"'+(cls?' class="'+cls+'"':'')+'>'+text+' <span aria-hidden="true">↗</span></a>';}
  function crumb(parent,text){return '<nav class="breadcrumb" aria-label="You are here"><button type="button" class="back-button" data-up="'+esc(parent)+'"><span aria-hidden="true">←</span> '+esc(text)+'</button></nav>';}
  function termMarkup(item,field){
    var text=item[field]||'',spans=[];
    (item.term_refs||[]).forEach(function(b){if(b.field!==field||!terms[b.term_id])return;var pos=-1;for(var i=0;i<(b.occurrence||1);i++){pos=text.indexOf(b.surface,pos+1);if(pos<0)return;}spans.push({start:pos,end:pos+b.surface.length,id:b.term_id});});
    spans.sort(function(a,b){return a.start-b.start;});var out='',end=0;
    spans.forEach(function(s){if(s.start<end)return;out+=esc(text.slice(end,s.start))+'<button class="term-trigger" type="button" data-term="'+esc(s.id)+'" aria-expanded="false" aria-controls="glossary-card">'+esc(text.slice(s.start,s.end))+'</button>';end=s.end;});
    return out+esc(text.slice(end));
  }
  function watchRoute(f){var owner=Object.keys(data.projects).find(function(pid){return data.projects[pid].films.indexOf(f.id)>=0;});return owner?projectRoute(owner,null,f.id):/introduction/.test(f.id)?'intro':null;}
  function player(f){var id=(f.youtube.split('v=')[1]||'').split('&')[0];return '<div class="film-player"><iframe src="https://www.youtube.com/embed/'+esc(id)+'?rel=0" title="'+esc(f.title)+'" loading="lazy" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>';}
  function filmAction(f,label,cls){var r=f.youtube&&watchRoute(f);if(r)return routeLink(r,esc(label),cls);return f.youtube?external(f.youtube,esc(label),cls):'<button type="button" class="'+(cls||'text-button')+'" data-film="'+esc(f.id)+'">'+esc(label)+'</button>';}
  function filmVisual(f,compact){
    if(f.youtube)return player(f);
    var stem=f.still||f.poster,image=stem?'<img src="'+esc(asset(stem+'-640.webp'))+'" width="1280" height="720" alt="" loading="'+(compact?'lazy':'eager')+'" decoding="async">':'<span class="film-blank">'+esc(f.short||f.title)+'</span>';
    var inner=image+'<span class="film-visual__shade"></span><span class="film-visual__action">'+(f.youtube?'<span aria-hidden="true">▶</span> Watch on YouTube':'Video in preparation · read the transcript')+'</span><span class="film-time">'+clock(f)+'</span>';
    if(f.youtube)return '<a class="film-visual" href="'+esc(f.youtube)+'" target="_blank" rel="noopener" aria-label="Watch '+esc(f.title)+'">'+inner+'</a>';
    return '<button class="film-visual is-coming" data-film="'+esc(f.id)+'" type="button" aria-label="Read the recorded transcript: '+esc(f.title)+'">'+inner+'</button>';
  }
  function projectRoute(pid,via,film){return M.hashFor({view:'project',id:pid,via:via||M.parentOf(data,pid),film:film||null});}
  function connectionLinks(door){var others=[];data.config.bridges.forEach(function(b){var to=b.from===door?b.to:b.to===door?b.from:null;if(to)others.push(routeLink('d='+to,'<span>'+esc(b.label)+'</span> <span aria-hidden="true">→</span>','related-route'));});return others.length?'<span class="eyebrow">Connected ideas</span>'+others.join(''):'';}
  function filmKnot(f,label,now,route){var t=esc(label)+' <span class="knot-time">'+clock(f)+'</span>'+(now?' <span class="knot-now">playing here</span>':'');if(f.youtube&&route)return '<a class="knot-link" href="#'+esc(route)+'" data-route="'+esc(route)+'"><span class="knot" aria-hidden="true"></span><span class="knot-text">'+t+'</span><span class="knot-go" aria-hidden="true">▶</span></a>';if(f.youtube)return '<a class="knot-link" href="'+esc(f.youtube)+'" target="_blank" rel="noopener"><span class="knot" aria-hidden="true"></span><span class="knot-text">'+t+'</span><span class="knot-go" aria-hidden="true">▶</span></a>';return '<button type="button" class="knot-link is-coming" data-film="'+esc(f.id)+'"><span class="knot" aria-hidden="true"></span><span class="knot-text">'+t+'<small>In preparation. Read the transcript.</small></span></button>';}
  function linkKnot(url,label,note){return '<a class="knot-link" href="'+esc(url)+'" target="_blank" rel="noopener"><span class="knot" aria-hidden="true"></span><span class="knot-text">'+esc(label)+(note?'<small>'+esc(note)+'</small>':'')+'</span><span class="knot-go" aria-hidden="true">↗</span></a>';}
  function strand(p,f,via){
    var items=[];
    if(f)items.push(['short',filmKnot(f,'Short video',false,projectRoute(p.id,via,f.id))]);
    M.onward(data,f).forEach(function(n){items.push(['long',filmKnot(n,n.id==='long-lean-readers'?'Full video, three readers':'Full video',false,projectRoute(p.id,via,n.id))]);});
    if(p.url)items.push(['site',linkKnot(p.url,'Website')]);
    if(p.repo_records.length)items.push(['code',linkKnot(p.repo_records[0].href,'Code')]);
    return '<ol class="strand" aria-label="'+esc(p.name)+': videos, website and code">'+items.map(function(x){return '<li class="strand__item strand__item--'+x[0]+'">'+x[1]+'</li>';}).join('')+'</ol>';
  }
  function strandCard(pid,via){
    var p=data.projects[pid],f=M.lead(data,{view:'project',id:pid,via:via});
    return '<article class="strand-card ink-'+p.area+'">'+(f?filmVisual(f,true):'')+'<div class="strand-card__body">'+routeLink(projectRoute(pid,via,f&&f.id),'<span>'+esc(p.name)+'</span> <span aria-hidden="true">→</span>','strand-card__name',via)+'<h2>'+esc(f?f.title:p.plain)+'</h2><p class="strand-card__take">'+(f?termMarkup(f,'takeaway'):esc(p.plain))+'</p>'+strand(p,f,via)+'</div></article>';
  }
  function doorView(d){
    function grid(ids){return '<div class="strand-grid strand-grid--'+Math.min(ids.length,3)+'">'+ids.map(function(p){return strandCard(p,d.id);}).join('')+'</div>';}
    var body=d.id==='proofs'?'<h2 class="strand-group">Read a paper beside its Lean proof</h2>'+grid(d.projects.slice(0,3))+'<h2 class="strand-group">How much a proof covers</h2>'+grid(d.projects.slice(3)):grid(d.projects);
    var tour=d.id==='explaining'?routeLink('journey','Follow one result from paper to video <span aria-hidden="true">→</span>','journey-invitation'):'';
    var count=d.projects.length===1?'One project':d.projects.length+' projects';
    return '<section class="door-view ink-'+d.ink+'">'+crumb('home','All questions')+'<header class="door-head"><div class="door-head__text"><p class="eyebrow">'+count+'. Each starts with a short video.</p><h1 tabindex="-1">'+esc(d.question)+'</h1><p class="focus-caption">'+esc(d.caption)+'</p>'+tour+'</div><div class="door-head__art" data-shape="'+d.id+'">'+object(d.id)+'</div></header>'+body+'<div class="local-connections">'+connectionLinks(d.id)+'</div></section>';
  }
  function websiteAction(p){
    if(!p.url)return '';var label='Open the website',url=p.url;
    if(['quartic','lean-exposition','proof-reader'].indexOf(p.id)>=0)label='Open the reader';
    if(p.id==='maths')label='Explore the maths map';if(p.id==='atlas')label='Explore Atlas';if(p.id==='formal-verification')label='Explore the component map';if(p.id==='code-ontology-bridge')label='Explore the study';
    if(p.id==='zenith'&&p.routes&&p.routes[0]){label='Read this study';url=p.routes[0].href;}
    return external(url,esc(label),'resource-action');
  }
  function everything(p,f,via){
    var films=p.films.map(function(id){return data.films[id];}).filter(Boolean),now=films.filter(function(x){return !M.earlier(data,x);}),old=films.filter(function(x){return M.earlier(data,x);});
    now.sort(function(a,b){return (a.format==='short'?0:1)-(b.format==='short'?0:1);});
    function li(cls,html){return '<li class="strand__item '+cls+'">'+html+'</li>';}
    var out=now.map(function(x){return li('strand__item--'+(x.format==='short'?'short':'long')+(f&&x.id===f.id?' is-current':''),filmKnot(x,(x.format==='short'?'Short video: ':'Full video: ')+x.title,f&&x.id===f.id&&!!x.youtube,projectRoute(p.id,via,x.id)));}).join('');
    if(p.url)out+=li('strand__item--site',linkKnot(p.url,'Website: '+p.name));
    (p.routes||[]).forEach(function(r){out+=li('strand__item--site strand__item--sub',linkKnot(r.href,r.label));});
    p.repo_records.forEach(function(r){out+=li('strand__item--code',linkKnot(r.href,'Code: '+r.name,r.description||''));});
    old.forEach(function(x){out+=li('strand__item--long strand__item--earlier',filmKnot(x,'Earlier edition: '+x.title,f&&x.id===f.id&&!!x.youtube,projectRoute(p.id,via,x.id)));});
    return '<div class="everything"><p class="eyebrow">Everything in '+esc(p.name)+'</p><ol class="strand strand--vertical">'+out+'</ol></div>';
  }
  function resourceDetails(p){
    return '<details class="resource-details"><summary>About this work, credits and limits <span aria-hidden="true">+</span></summary><div class="resource-details__grid"><div><h3>What it is</h3><p>'+termMarkup(p,'summary')+'</p></div><div><h3>Credits and limits</h3>'+(p.credit?'<p>'+esc(p.credit)+'</p>':'')+(p.status?'<p>'+esc(p.status)+'</p>':'<p>No further limits are recorded for this project.</p>')+'</div></div></details>';
  }
  function smallInteraction(kind){
    var set=(data.demo||{})[kind];if(!set||!set.length)return '';
    return '<div class="specimen-controls" role="group" aria-label="Parts of the drawing">'+set.map(function(x,i){return '<button type="button" data-demo="'+esc(x[0])+'" data-caption="'+esc(x[2])+'" aria-pressed="'+(i===0)+'">'+esc(x[1])+'</button>';}).join('')+'</div><p class="demo-caption">'+esc(set[0][2])+'</p>';
  }
  function projectConnections(p,via){
    var result=[];data.links.forEach(function(l){var to=l.from===p.id?l.to:l.to===p.id?l.from:null;if(to&&data.projects[to])result.push(routeLink(projectRoute(to),'<span>'+esc(l.label)+'</span><strong>'+esc(data.projects[to].name)+' <span aria-hidden="true">→</span></strong>','related-route'));});
    data.config.doors.forEach(function(d){if(d.id!==via&&d.projects.indexOf(p.id)>=0)result.push(routeLink('d='+d.id,'<span>Another way into this work</span><strong>'+esc(d.question)+' →</strong>','related-route'));});
    return result.length?'<span class="eyebrow">Connected work</span>'+result.slice(0,3).join(''):'';
  }
  function projectView(s){
    var p=data.projects[s.id],d=byDoor(s.via),shorts=M.tasters(data,p.id),chosen=s.film&&data.films[s.film];
    var entry=chosen&&chosen.format==='short'?chosen:(chosen&&shorts.find(function(t){return (t.leads_to||[]).indexOf(chosen.id)>=0;}))||M.lead(data,{view:'project',id:s.id,via:s.via});
    // The player shows the chosen video; otherwise the short video if it is published, else a published full video.
    var f=chosen||(M.published(entry)?entry:M.onward(data,entry).concat(p.films.map(function(id){return data.films[id];})).find(function(x){return x&&M.published(x)&&!M.earlier(data,x);})||entry);
    var reader=!!(entry&&/reader|sk-website/.test(entry.id)&&['quartic','lean-exposition'].indexOf(p.id)>=0);
    var question=reader?(p.id==='quartic'?'Read OpenAI’s quantum query paper beside its Lean proof.':'Read OpenAI’s spin-glass paper beside its Lean proof.'):p.question;
    var tabs=shorts.length>1?'<div class="taster-tabs" aria-label="Choose a short video">'+shorts.map(function(t){return '<button type="button" data-taster="'+t.id+'" aria-pressed="'+(f&&t.id===f.id)+'">'+esc(M.filmLabel(t))+'</button>';}).join('')+'</div>':'';
    var kind=reader?'proof-reader':p.id,set=(data.demo||{})[kind]||[],initial=set.length?set[0][0]:'';
    var drawing='<div class="interactive-specimen" data-shape="'+s.via+'">'+object(kind)+'</div>'+smallInteraction(kind);
    var media='<div class="project-media">'+(f?tabs+filmVisual(f,false)+'<div class="film-caption"><p class="eyebrow">'+(f.format==='short'?'Short video':'Full video')+' · '+clock(f)+(f.youtube?'':' · in preparation')+'</p><p>'+termMarkup(f,'takeaway')+'</p></div>':'')+drawing+'</div>';
    var parent=d&&d.projects.length>1?'d='+s.via:'home',parentLabel=d&&d.projects.length>1?d.question:'All questions';
    return '<section class="project-view ink-'+p.area+'" data-project="'+p.id+'" data-demo-state="'+esc(initial)+'">'+crumb(parent,parentLabel)+'<div class="project-layout"><div class="project-story"><p class="eyebrow">'+esc(p.name)+'</p><h1 tabindex="-1">'+esc(question)+'</h1><p class="project-answer">'+(reader?esc(p.plain):termMarkup(p,'line'))+'</p><div class="resource-actions">'+websiteAction(p)+'</div>'+everything(p,f,s.via)+'</div>'+media+'</div>'+resourceDetails(p)+'<div class="local-connections">'+projectConnections(p,s.via)+'</div></section>';
  }
  function searchRows(){
    var results=M.search(data,projectQuery);if(!results.length)return '<div class="empty-result"><h2>No matching project.</h2><p>Try a subject or a tool name.</p><button type="button" data-clear-search>Show all projects</button></div>';
    return results.map(function(p){return routeLink(projectRoute(p.id),'<span class="index-number">'+String(Object.keys(data.projects).indexOf(p.id)+1).padStart(2,'0')+'</span><span><strong>'+esc(p.choice)+'</strong><small>'+esc(p.name)+' · '+esc(p.subject||'')+'</small></span><span aria-hidden="true">↗</span>','project-index-row ink-'+p.area);}).join('');
  }
  function allView(){return '<section class="index-view">'+crumb('home','All questions')+'<div class="index-heading"><h1 tabindex="-1">All the work.</h1><label class="search-label">Find a subject, project or repository<input id="project-search" type="search" placeholder="Try quantum, Lean, NVIDIA…" value="'+esc(projectQuery)+'" autocomplete="off"></label></div><div class="project-index" id="project-results">'+searchRows()+'</div><div class="index-links">'+routeLink('terms','Browse the glossary →')+routeLink('about','Contributions & contact →')+'<a href="all.html">Complete static catalogue →</a></div></section>';}
  function filmRow(f){
    var next=M.onward(data,f),owners=Object.values(data.projects).filter(function(p){return p.films.indexOf(f.id)>=0;});
    return '<article class="film-row">'+filmVisual(f,true)+'<div><p class="eyebrow">'+(f.format==='short'?'Short video':'Full video')+' · '+clock(f)+(f.youtube?'':' · Coming soon')+'</p><h2>'+filmAction(f,f.title,'film-title-button')+'</h2><p class="film-row-takeaway">'+termMarkup(f,'takeaway')+'</p>'+(next.length?'<div class="film-row-onward"><span>Then</span>'+next.map(function(n){return filmAction(n,n.short+' · '+clock(n),'inline-action');}).join('')+'</div>':'')+'<div class="film-projects">'+owners.map(function(owner){return routeLink(M.routeForFilm(data,owner.id,f.id),'Open '+esc(owner.name)+' →','film-project-link');}).join('')+'</div></div></article>';
  }
  function filmRows(){return M.filmList(data,filmFilters.status,filmFilters.history,filmFilters.format).map(filmRow).join('')||'<p class="empty-result">No videos match those filters.</p>';}
  function filmsView(){return '<section class="films-view">'+crumb('home','All questions')+'<div class="index-heading"><h1 tabindex="-1">Every video.</h1><p>Each short video of about two minutes leads to a full video.</p></div><div class="film-filters"><label>Show<select id="film-status"><option value="all"'+(filmFilters.status==='all'?' selected':'')+'>Published & forthcoming</option><option value="published"'+(filmFilters.status==='published'?' selected':'')+'>Published only</option></select></label><label>Length<select id="film-format"><option value="all"'+(filmFilters.format==='all'?' selected':'')+'>All videos</option><option value="short"'+(filmFilters.format==='short'?' selected':'')+'>Short videos</option><option value="long"'+(filmFilters.format==='long'?' selected':'')+'>Full videos</option></select></label><label class="check-label"><input type="checkbox" id="film-history"'+(filmFilters.history?' checked':'')+'> Include earlier editions</label><span id="film-count"></span></div><div id="film-results">'+filmRows()+'</div></section>';}
  function introView(){
    var f=data.films['short-introduction'],n=data.films['long-introduction'];var existing=Object.values(data.films).filter(function(x){return /introduction/.test(x.id)&&x.youtube&&!M.earlier(data,x);}).slice(-1)[0],tour=M.published(n)?n:(existing||n);
    return '<section class="intro-view">'+crumb('home','All questions')+'<div class="intro-heading"><p class="eyebrow">Will Cook</p><h1 tabindex="-1">The work, and how it fits together.</h1><p>'+esc(data.owner.lede)+'</p></div><div class="intro-films"><article><h2>A short introduction</h2>'+filmVisual(f,false)+'<p>'+esc(f.takeaway)+'</p></article><article><h2>The full tour</h2>'+filmVisual(tour,false)+'<p>'+esc(tour===n?n.takeaway:tour.title)+'</p></article></div>'+(existing&&tour!==existing?'<p class="published-intro">Already available: '+filmAction(existing,existing.title+' · '+clock(existing),'inline-action')+'</p>':'')+'</section>';
  }
  function aboutView(){return '<section class="about-view">'+crumb('home','All questions')+'<div class="about-heading"><p class="eyebrow">About Will Cook</p><h1 tabindex="-1">Making the work understandable.</h1><p>'+esc(data.owner.lede)+'</p><p>'+esc(data.owner.availability)+'</p><div class="contact-links">'+data.owner.contact.map(function(c){return external(c.href,esc(c.label),'resource-action');}).join('')+'</div></div><details class="contributions-details"><summary>Contributions to other projects <span>+</span></summary><ul>'+data.contributions.map(function(c){return '<li><strong>'+external('https://github.com/wcook04/'+c.repo,esc(c.upstream))+'</strong><p>'+esc(c.what)+'</p>'+(c.evidence?external(c.evidence.href,esc(c.evidence.label)):'')+'</li>';}).join('')+'</ul></details><details class="contributions-details"><summary>Earlier work <span>+</span></summary><ul>'+data.earlier.map(function(x){return '<li>'+external(x.href,esc(x.name))+'<p>'+esc(x.note)+'</p></li>';}).join('')+'</ul></details></section>';}
  function termRows(query){return data.terms.filter(function(t){return M.fold([t.term,...(t.aliases||[])].join(' ')).includes(M.fold(query));}).sort(function(a,b){return a.term.localeCompare(b.term);}).map(function(t){return '<details class="term-definition" id="term-'+esc(t.id)+'"><summary>'+esc(t.term)+' <span aria-hidden="true">+</span></summary><p>'+esc(t.preview)+'</p><p>'+esc(t.detail)+'</p></details>';}).join('');}
  function termsView(){return '<section class="terms-view">'+crumb('home','All questions')+'<div class="index-heading"><h1 tabindex="-1">A word in context.</h1><label class="search-label">Find a term<input type="search" id="term-search" placeholder="Try Lean, query or commit…"></label></div><div id="term-results">'+termRows('')+'</div></section>';}
  function asset(path){return (data.embeddedAssets||{})[path]||path;}
  function journeyView(){
    var p=data.projects.quartic,full=data.films['quartic-query'];
    var steps=[
      {title:'Start with a question.',copy:'How many checks of the input does a quantum computer need?',visual:object('quartic'),link:external(p.routes[0].href,'Read OpenAI’s paper','resource-action')},
      {title:'Follow the proof.',copy:'The formal proof records the definitions and steps in Lean.',visual:object('proof-reader'),link:external(p.repo_records[0].href,'Open the Lean proof','resource-action')},
      {title:'Make a way to read it.',copy:'The reader places explanations beside the corresponding Lean declarations.',visual:'<img src="'+esc(asset('assets/sites/quartic-light-720.webp'))+'" width="720" height="395" alt="The supplied Quartic Reader website capture" loading="lazy">',link:external(p.url,'Open Quartic Reader','resource-action')},
      {title:'Explain it in a video.',copy:'The same result becomes a narrated mathematical explanation.',visual:filmVisual(full,true),link:filmAction(full,'Watch the full explanation · '+clock(full),'resource-action')}
    ];
    return '<section class="journey-view ink-explain">'+crumb('d=explaining','Making explanations')+'<div class="journey-heading"><p class="eyebrow">One worked example · Quantum computing</p><h1 tabindex="-1">Follow one result.</h1><p>OpenAI’s paper, its Lean proof, the reader website and the video, in order.</p></div><div class="journey-layout"><div class="journey-sticky" aria-hidden="true">'+steps.map(function(s,i){return '<div class="journey-frame'+(i===0?' is-current':'')+'" data-journey-frame="'+i+'"><div class="journey-frame-body">'+s.visual+'</div><span class="journey-progress">'+String(i+1).padStart(2,'0')+' / 04</span></div>';}).join('')+'</div><div class="journey-steps">'+steps.map(function(s,i){return '<article class="journey-step" id="journey-step-'+i+'" data-journey-step="'+i+'"><span class="eyebrow">'+String(i+1).padStart(2,'0')+' / 04</span><h2>'+s.title+'</h2><p>'+s.copy+'</p><div class="journey-inline-visual">'+s.visual+'</div>'+s.link+'</article>';}).join('')+'</div></div><div class="journey-end">'+routeLink(projectRoute('narration-ir'),'How are the pictures planned? Explore Narration IR →','journey-invitation')+routeLink('home','Return to all questions →')+'</div></section>';
  }
  function attachJourney(){
    if(!main.querySelector('.journey-view'))return;
    // The sticky illustration is a visual duplicate; all real actions remain
    // in the matching, keyboard-readable step.
    main.querySelectorAll('.journey-sticky a,.journey-sticky button').forEach(function(n){n.setAttribute('tabindex','-1');});
    if(!window.IntersectionObserver)return;
    journeyObserver=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){var n=entry.target.dataset.journeyStep;main.querySelectorAll('[data-journey-frame]').forEach(function(f){f.classList.toggle('is-current',f.dataset.journeyFrame===n);});}});},{rootMargin:'-20% 0px -35% 0px',threshold:0});
    main.querySelectorAll('[data-journey-step]').forEach(function(n){journeyObserver.observe(n);});
  }
  function pageHTML(s){if(s.view==='door')return doorView(byDoor(s.id));if(s.view==='project')return projectView(s);if(s.view==='all')return allView();if(s.view==='films')return filmsView();if(s.view==='about')return aboutView();if(s.view==='terms')return termsView();if(s.view==='intro')return introView();if(s.view==='journey')return journeyView();return homeHTML;}
  function attachThreads(){
    var scene=main.querySelector('.question-scene');if(!scene)return;var svg=scene.querySelector('.scene-threads'),box=scene.getBoundingClientRect(),NS='http://www.w3.org/2000/svg';svg.setAttribute('viewBox','0 0 '+box.width+' '+box.height);var group=svg.querySelector('g');group.textContent='';
    data.config.bridges.forEach(function(b){var a=scene.querySelector('[data-door="'+b.from+'"] .door-object').getBoundingClientRect(),z=scene.querySelector('[data-door="'+b.to+'"] .door-object').getBoundingClientRect();var x1=a.left+a.width/2-box.left,y1=a.top+a.height*.55-box.top,x2=z.left+z.width/2-box.left,y2=z.top+z.height*.55-box.top;var path=document.createElementNS(NS,'path');path.setAttribute('d','M'+x1+','+y1+' C'+(x1+(x2-x1)*.3)+','+(y1+(y2-y1)*.7)+' '+(x2-(x2-x1)*.3)+','+(y2-(y2-y1)*.7)+' '+x2+','+y2);path.setAttribute('data-from',b.from);path.setAttribute('data-to',b.to);path.setAttribute('pathLength','1');group.appendChild(path);});
  }
  function cleanTransitionNames(){main.querySelectorAll('[data-shape]').forEach(function(n){n.style.viewTransitionName='none';});}
  function upgradePlayers(){main.querySelectorAll('a[data-yt]').forEach(function(a){var w=document.createElement('div');w.className=a.className.replace(/\byt\b/,'film-player');var f=document.createElement('iframe');f.src='https://www.youtube.com/embed/'+a.dataset.yt+'?rel=0';f.title=a.dataset.title||'Video';f.setAttribute('loading','lazy');f.setAttribute('allow','accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');f.setAttribute('referrerpolicy','strict-origin-when-cross-origin');f.setAttribute('allowfullscreen','');w.appendChild(f);a.replaceWith(w);});}
  function upgradeLinks(){document.querySelectorAll('a[data-route]').forEach(function(a){var raw=a.dataset.route;if(a.dataset.parent&&raw.startsWith('p=')&&!raw.includes('via='))raw+='&via='+a.dataset.parent;a.setAttribute('href','#'+M.hashFor(M.resolve(data,raw)));});}
  function updateFilmCount(){var c=document.getElementById('film-count');if(c)c.textContent=M.filmList(data,filmFilters.status,filmFilters.history,filmFilters.format).length+' videos';}
  function update(s,keyboard,restore){
    closeGlossary();if(dialog.open)dialog.close();if(journeyObserver){journeyObserver.disconnect();journeyObserver=null;}state=s;main.innerHTML=pageHTML(s);currentHash=M.hashFor(s);attachJourney();upgradeLinks();upgradePlayers();
    document.querySelectorAll('[data-nav]').forEach(function(a){var on=a.dataset.nav===s.view||(a.dataset.nav==='home'&&['door','project'].includes(s.view));if(on)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});attachThreads();var heading=main.querySelector('h1');document.title=(heading?heading.textContent+' — ':'')+'Will Cook';document.querySelector('.studio-announcement').textContent=heading?heading.textContent:'';if(s.view==='films')updateFilmCount();
    if(restore&&lastFocus[currentHash]){var prev=Array.from(main.querySelectorAll('[data-route]')).find(function(a){return a.dataset.route===lastFocus[currentHash];});if(prev)prev.focus({preventScroll:true});else if(heading)heading.focus({preventScroll:true});}else if(keyboard&&heading)heading.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'});
  }
  function navigate(raw,options){
    options=options||{};var target=M.resolve(data,raw),hash=M.hashFor(target);if(hash===currentHash&&!options.force)return;
    if(document.activeElement&&document.activeElement.dataset.route)lastFocus[currentHash]=document.activeElement.dataset.route;var prior=currentHash;
    if(!options.history){var record={explorer:true,from:options.preserveParent&&history.state?history.state.from:prior};try{if(options.replace)history.replaceState(record,'','#'+hash);else history.pushState(record,'','#'+hash);}catch(e){location.hash=hash;}}
    var shape=target.via||target.id||(state.via||state.id),old=shape&&main.querySelector('[data-shape="'+shape+'"]');if(pendingTransition){pendingTransition.skipTransition();pendingTransition=null;}cleanTransitionNames();if(old)old.style.viewTransitionName='selected-object';
    var serial=++navSerial;
    if(document.startViewTransition&&!motion.matches&&!options.instant){var transition=document.startViewTransition(function(){if(serial!==navSerial)return;update(target,options.keyboard,options.restore);var selected=shape&&main.querySelector('[data-shape="'+shape+'"]');if(selected)selected.style.viewTransitionName='selected-object';});pendingTransition=transition;transition.ready.catch(function(){});transition.updateCallbackDone.catch(function(){});transition.finished.catch(function(){}).finally(function(){if(pendingTransition===transition){pendingTransition=null;cleanTransitionNames();}});}else update(target,options.keyboard,options.restore);
  }
  function goUp(wanted){var destination=wanted||((state.view==='project'&&byDoor(state.via).projects.length>1)?'d='+state.via:'home'),normal=M.hashFor(M.resolve(data,destination));if(history.state&&history.state.explorer&&history.state.from===normal)history.back();else navigate(destination,{replace:true,keyboard:true,restore:true});}
  function showFilm(fid,opener){var f=data.films[fid];if(!f)return;lastFilmOpener=opener;var lines=(f.transcript||'').split('\n').filter(function(s){return s.startsWith('- ');}).map(function(s){return '<p>'+esc(s.slice(2))+'</p>';}).join('');dialog.querySelector('.dialog-content').innerHTML='<button class="dialog-close" type="button" data-close-film aria-label="Close transcript">×</button><p class="eyebrow">Recorded video · '+clock(f)+'</p><h2 id="film-dialog-title">'+esc(f.title)+'</h2><p class="transcript-status">The video is not published yet. This is the transcript of the recording.</p><div class="transcript-text">'+(lines||'<p>'+esc(f.takeaway||'A transcript was not supplied for this video.')+'</p>')+'</div>';dialog.showModal();dialog.querySelector('[data-close-film]').focus();}
  function closeFilm(){dialog.close();if(lastFilmOpener&&lastFilmOpener.isConnected)lastFilmOpener.focus({preventScroll:true});}
  function closeGlossary(){clearTimeout(glossaryTimer);popover.hidden=true;if(activeTerm){activeTerm.setAttribute('aria-expanded','false');activeTerm=null;}}
  function returnTermFocus(old){if(!old)return;ignoreTermFocus=true;old.focus({preventScroll:true});requestAnimationFrame(function(){ignoreTermFocus=false;});}
  function placeGlossary(){if(!activeTerm||popover.hidden)return;var b=activeTerm.getBoundingClientRect(),w=Math.min(360,window.innerWidth-32);popover.style.width=w+'px';popover.style.left=Math.max(16,Math.min(window.innerWidth-w-16,b.left))+'px';var h=popover.getBoundingClientRect().height;popover.style.top=(b.bottom+12+h>window.innerHeight?Math.max(12,b.top-h-12):b.bottom+12)+'px';}
  function showGlossary(button,pin){clearTimeout(glossaryTimer);var t=terms[button.dataset.term];if(!t)return;if(activeTerm&&activeTerm!==button)activeTerm.setAttribute('aria-expanded','false');activeTerm=button;button.setAttribute('aria-expanded','true');popover.setAttribute('role','dialog');popover.setAttribute('aria-label',t.term);popover.setAttribute('aria-describedby','glossary-preview');popover.innerHTML='<div class="glossary-top"><strong>'+esc(t.term)+'</strong><button type="button" data-close-term aria-label="Close definition">×</button></div><p id="glossary-preview">'+esc(t.preview)+'</p><details><summary>Technical definition</summary><p>'+esc(t.detail)+'</p></details>'+routeLink('terms','All terms →','all-terms-link');popover.hidden=false;popover.dataset.pinned=pin?'true':'false';placeGlossary();if(pin)popover.querySelector('summary').focus({preventScroll:true});}
  document.addEventListener('click',function(event){
    var jump=event.target.closest('[data-scroll]');if(jump){var target=document.getElementById(jump.dataset.scroll);if(target){event.preventDefault();target.scrollIntoView({behavior:motion.matches?'auto':'smooth',block:'start'});}return;}
    var a=event.target.closest('[data-route]');if(a){if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button>0)return;event.preventDefault();var raw=a.dataset.route;if(a.dataset.parent&&raw.startsWith('p=')&&!raw.includes('via='))raw+='&via='+a.dataset.parent;navigate(raw,{keyboard:event.detail===0});return;}
    var up=event.target.closest('[data-up]');if(up){goUp(up.dataset.up);return;}var taster=event.target.closest('[data-taster]');if(taster){var selectedId=taster.dataset.taster;navigate(projectRoute(state.id,state.via,selectedId),{replace:true,instant:true,preserveParent:true});var replacement=main.querySelector('[data-taster="'+selectedId+'"]');if(replacement)replacement.focus({preventScroll:true});return;}
    var film=event.target.closest('[data-film]');if(film){showFilm(film.dataset.film,film);return;}if(event.target.closest('[data-close-film]')){closeFilm();return;}var term=event.target.closest('[data-term]');if(term){showGlossary(term,true);return;}
    if(event.target.closest('[data-close-term]')){var old=activeTerm;closeGlossary();returnTermFocus(old);return;}if(!popover.contains(event.target)&&!popover.hidden)closeGlossary();
    var demo=event.target.closest('[data-demo]');if(demo){var pv=main.querySelector('.project-view');pv.dataset.demoState=demo.dataset.demo;pv.querySelectorAll('[data-demo]').forEach(function(b){b.setAttribute('aria-pressed',String(b===demo));});var cap=pv.querySelector('.demo-caption');if(cap)cap.textContent=demo.dataset.caption||'';return;}
    if(event.target.closest('[data-clear-search]')){projectQuery='';var input=document.getElementById('project-search');input.value='';document.getElementById('project-results').innerHTML=searchRows();input.focus();}
  });
  document.addEventListener('input',function(event){if(event.target.id==='project-search'){projectQuery=event.target.value;document.getElementById('project-results').innerHTML=searchRows();}if(event.target.id==='term-search')document.getElementById('term-results').innerHTML=termRows(event.target.value);});
  document.addEventListener('change',function(event){if(event.target.id==='film-status')filmFilters.status=event.target.value;else if(event.target.id==='film-format')filmFilters.format=event.target.value;else if(event.target.id==='film-history')filmFilters.history=event.target.checked;else return;document.getElementById('film-results').innerHTML=filmRows();updateFilmCount();});
  document.addEventListener('pointerover',function(event){var term=event.target.closest('[data-term]');if(term&&event.pointerType!=='touch'){clearTimeout(glossaryTimer);glossaryTimer=setTimeout(function(){showGlossary(term,false);},220);}var door=event.target.closest('[data-door]');if(door)main.querySelectorAll('.scene-threads path').forEach(function(p){p.classList.toggle('is-active',p.dataset.from===door.dataset.door||p.dataset.to===door.dataset.door);});});
  document.addEventListener('pointerout',function(event){var term=event.target.closest('[data-term]');if(term&&(!event.relatedTarget||!term.contains(event.relatedTarget))){clearTimeout(glossaryTimer);if(popover.dataset.pinned!=='true')glossaryTimer=setTimeout(closeGlossary,280);}var door=event.target.closest('[data-door]');if(door&&(!event.relatedTarget||!door.contains(event.relatedTarget)))main.querySelectorAll('.scene-threads path').forEach(function(p){p.classList.remove('is-active');});});
  popover.addEventListener('pointerenter',function(){clearTimeout(glossaryTimer);});popover.addEventListener('pointerleave',function(){if(popover.dataset.pinned!=='true')glossaryTimer=setTimeout(closeGlossary,280);});
  popover.addEventListener('toggle',function(){requestAnimationFrame(placeGlossary);},true);
  popover.addEventListener('focusout',function(event){if(event.relatedTarget&&!popover.contains(event.relatedTarget)&&event.relatedTarget!==activeTerm)closeGlossary();});
  document.addEventListener('focusin',function(event){if(!ignoreTermFocus&&event.target.matches('[data-term]'))showGlossary(event.target,false);var door=event.target.closest('[data-door]');if(door)main.querySelectorAll('.scene-threads path').forEach(function(p){p.classList.toggle('is-active',p.dataset.from===door.dataset.door||p.dataset.to===door.dataset.door);});});
  document.addEventListener('focusout',function(event){if(event.target.matches('[data-term]')){clearTimeout(glossaryTimer);if(!event.relatedTarget||!popover.contains(event.relatedTarget))glossaryTimer=setTimeout(closeGlossary,150);}var door=event.target.closest('[data-door]');if(door&&(!event.relatedTarget||!door.contains(event.relatedTarget)))main.querySelectorAll('.scene-threads path').forEach(function(p){p.classList.remove('is-active');});});
  document.addEventListener('keydown',function(event){if(event.key!=='Escape')return;if(dialog.open){event.preventDefault();closeFilm();return;}if(!popover.hidden){var old=activeTerm;closeGlossary();returnTermFocus(old);return;}if(state.view!=='home'){event.preventDefault();goUp();}});
  dialog.addEventListener('click',function(event){if(event.target===dialog){var r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeFilm();}});dialog.addEventListener('cancel',function(event){event.preventDefault();closeFilm();});
  var themeButton=document.querySelector('.theme-button');function theme(value){document.documentElement.dataset.theme=value;themeButton.setAttribute('aria-label','Switch to '+(value==='dark'?'light':'dark')+' theme');try{localStorage.setItem('will-cook-theme',value);}catch(e){}}
  try{theme(localStorage.getItem('will-cook-theme')||'dark');}catch(e){theme('dark');}themeButton.addEventListener('click',function(){theme(document.documentElement.dataset.theme==='dark'?'light':'dark');});
  function historyChanged(){var next=M.resolve(data,location.hash);if(M.hashFor(next)!==currentHash)navigate(location.hash,{history:true,restore:true,keyboard:true});}window.addEventListener('popstate',historyChanged);window.addEventListener('hashchange',historyChanged);
  var resizeTimer;window.addEventListener('resize',function(){clearTimeout(resizeTimer);resizeTimer=setTimeout(function(){attachThreads();closeGlossary();},120);});
  try{history.replaceState({explorer:true,from:null},'','#'+M.hashFor(state));}catch(e){}update(state,false,false);
})();
