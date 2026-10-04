    if (!document.querySelector("a.term, [data-term-preview-only][data-term]")) return;

    function el(tag, cls, text) {
      var n = document.createElement(tag);
      if (cls) n.className = cls;
      if (text) n.textContent = text;
      return n;
    }
    function termAnchorFrom(target) {
      if (!target || !target.closest) return null;
      var a = target.closest("a.term, [data-term-preview-only][data-term]");
      if (!a && target.querySelector) a = target.querySelector("[data-term-preview-only][data-term]");
      return a && TERMS[a.getAttribute("data-term")] ? a : null;
    }
    function passiveTerm(anchor) {
      return anchor && anchor.hasAttribute("data-term-preview-only");
    }
    function termDescriptionTarget(anchor) {
      return passiveTerm(anchor) ? anchor.closest("a[href], summary") : anchor;
    }

    // Grade the page: the first mention of a term keeps the dotted rule, later
    // ones drop it and keep the behaviour. Done at runtime rather than in the
    // markup so that with scripting off every mention keeps its rule, which is
    // the safe direction to fail in.
    var seen = {};
    Array.prototype.forEach.call(document.querySelectorAll("a.term"), function (a) {
      var k = a.getAttribute("data-term");
      if (seen[k]) a.classList.add("is-again");
      seen[k] = true;
    });

    // Placement is reading-block aware: given a choice, the card goes to
    // whichever side covers less of the paragraph the word sits in.
    function placeFloater(node, anchor) {
      node.hidden = false;
      var rect = anchor.getBoundingClientRect();
      var readingBlock = anchor.closest("p, li, h1, h2");
      var readingRect = readingBlock ? readingBlock.getBoundingClientRect() : null;
      var width = node.offsetWidth || 352;
      var height = node.offsetHeight || 120;
      var edge = 8, gap = 12;
      var left = Math.min(Math.max(8, rect.left), Math.max(8, window.innerWidth - width - 8));
      var aboveTop = rect.top - height - gap;
      var belowTop = rect.bottom + gap;
      var aboveFits = aboveTop >= edge;
      var belowFits = belowTop + height <= window.innerHeight - edge;
      var tiePrefersAbove = rect.top > window.innerHeight * 0.42;
      var placeAbove;
      if (aboveFits && belowFits && readingRect) {
        var aboveOverlap = Math.max(0, Math.min(aboveTop + height, readingRect.bottom) -
          Math.max(aboveTop, readingRect.top));
        var belowOverlap = Math.max(0, Math.min(belowTop + height, readingRect.bottom) -
          Math.max(belowTop, readingRect.top));
        placeAbove = aboveOverlap === belowOverlap ? tiePrefersAbove : aboveOverlap < belowOverlap;
      } else if (aboveFits && belowFits) { placeAbove = tiePrefersAbove; }
      else if (aboveFits) { placeAbove = true; }
      else if (belowFits) { placeAbove = false; }
      else { placeAbove = rect.top > window.innerHeight / 2; }
      var top = placeAbove
        ? Math.max(edge, aboveTop)
        : Math.min(window.innerHeight - height - edge, belowTop);
      node.setAttribute("data-placement", placeAbove ? "above" : "below");
      node.style.left = left + "px";
      node.style.top = top + "px";
    }

    var tip = el("div", "term-tip");
    tip.id = "mc-term-tip";
    tip.setAttribute("role", "tooltip");
    tip.hidden = true;
    var tipLabel = el("div", "term-tip__label");
    var tipText = el("div", "term-tip__text");
    var tipRule = el("div", "term-tip__rule"); tipRule.hidden = true;
    var tipDeep = el("div", "term-tip__deep"); tipDeep.hidden = true;
    var tipFull = el("a", "term-tip__full", "See this in the glossary \u2192"); tipFull.hidden = true;
    var tipBack = el("button", "term-tip__back", "Back to page");
    tipBack.type = "button"; tipBack.hidden = true;
    var tipCue = el("div", "term-tip__cue");
    tip.appendChild(tipLabel);
    tip.appendChild(tipText);
    tip.appendChild(tipRule);
    tip.appendChild(tipDeep);
    var tipActions = el("div", "term-tip__actions");
    tipActions.appendChild(tipBack);
    tipActions.appendChild(tipFull);
    tip.appendChild(tipActions);
    tip.appendChild(tipCue);
    tip.appendChild(el("div", "term-tip__escape", "Esc to close"));
    document.body.appendChild(tip);

    var tipFor = null;   // the anchor the card currently describes
    var tier = 0;        // 0 = hover preview, 1 = expanded in place
    var tipHideTimer = 0;
    var tipFadeTimer = 0;
    var suppressFocusPreview = false;
    var suppressPointerPreview = false;
    var previewIntent = null;
    var pointerX = null, pointerY = null;

    var presentationState = "idle";
    function refreshPresentation() {
      if (tipFor && !tip.hidden && !tip.classList.contains("is-leaving")) {
        renderTier(TERMS[tipFor.getAttribute("data-term")], tipFor);
        placeFloater(tip, tipFor);
      }
    }
    function installPresentation() {
      var asset = window.__MICROCOSM_TERM_PREVIEWS__ || {};
      function ready() {
        (asset.terms || []).forEach(function (row) {
          var id = String(row.object_id || "").replace(/^term:/, "");
          if (TERMS[id]) TERMS[id] = row;
        });
        presentationState = "ready";
        refreshPresentation();
      }
      if (!asset.math_css || !/^math\/[a-f0-9]+\.css$/.test(asset.math_css)) {
        ready();
        return;
      }
      var style = document.createElement("link");
      style.rel = "stylesheet";
      style.href = "/plectis/assets/" + asset.math_css;
      style.setAttribute("data-term-math", "");
      style.addEventListener("load", ready, {once:true});
      style.addEventListener("error", function () { presentationState = "failed"; }, {once:true});
      document.head.appendChild(style);
    }
    function loadPresentation() {
      if (presentationState !== "idle") return;
      presentationState = "loading";
      if (window.__MICROCOSM_TERM_PREVIEWS__) { installPresentation(); return; }
      var script = document.createElement("script");
      script.src = "/plectis/assets/term-previews.js";
      script.async = true;
      script.setAttribute("data-term-previews", "");
      script.addEventListener("load", installPresentation, {once:true});
      script.addEventListener("error", function () { presentationState = "failed"; }, {once:true});
      document.head.appendChild(script);
    }
    // Share the published presentation, never a second browser typesetter.
    // The embedded plain snapshot remains a usable network-failure fallback.
    if (window.requestIdleCallback) window.requestIdleCallback(loadPresentation, {timeout:3000});
    else window.setTimeout(loadPresentation, 1200);
    function plainTerm(text) {
      return String(text || "").replace(/\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]/g, "[formula in glossary]");
    }
    function setTermContent(node, data, field) {
      if (data[field + "_html"]) node.innerHTML = data[field + "_html"];
      else node.textContent = plainTerm(data[field]);
    }
    function renderTier(data, anchor) {
      tipLabel.textContent = data.preferred_label || "";
      if (tier === 1) {
        tip.classList.add("is-expanded");
        var lead = data.reader_preview || "";
        var card = data.reader_card || lead;
        setTermContent(tipText, data, data.reader_card ? "reader_card" : "reader_preview");
        if (lead && card.indexOf(lead) === -1) {
          var prefix = document.createElement("span");
          setTermContent(prefix, data, "reader_preview");
          prefix.appendChild(document.createTextNode(" "));
          tipText.insertBefore(prefix, tipText.firstChild);
        }
        if (data.reader_rule && data.reader_rule !== data.reader_card) {
          setTermContent(tipRule, data, "reader_rule"); tipRule.hidden = false;
        } else { tipRule.textContent = ""; tipRule.hidden = true; }
        if (data.reader_deep && data.reader_deep !== data.reader_card &&
            data.reader_deep !== data.reader_rule) {
          setTermContent(tipDeep, data, "reader_deep"); tipDeep.hidden = false;
        } else { tipDeep.textContent = ""; tipDeep.hidden = true; }
        var nativeLink = passiveTerm(anchor) ? anchor.closest("a[href]") : anchor;
        tipFull.href = nativeLink ? nativeLink.getAttribute("href") : "";
        tipFull.hidden = false;
        tipBack.hidden = false;
        tipCue.textContent = "Click the term again, or use the link, to open the complete glossary entry";
      } else {
        tip.classList.remove("is-expanded");
        setTermContent(tipText, data, data.reader_preview ? "reader_preview" : "reader_card");
        tipRule.textContent = ""; tipRule.hidden = true;
        tipDeep.textContent = ""; tipDeep.hidden = true;
        tipFull.hidden = true;
        tipBack.hidden = true;
        tipCue.textContent = passiveTerm(anchor) ? "" : "Click to expand here and stay on this page";
      }
    }
    function showTip(anchor, intent) {
      loadPresentation();
      var data = TERMS[anchor.getAttribute("data-term")];
      if (!data) return;
      if (tipHideTimer) { clearTimeout(tipHideTimer); tipHideTimer = 0; }
      if (tipFadeTimer) { clearTimeout(tipFadeTimer); tipFadeTimer = 0; }
      tip.classList.remove("is-leaving");
      previewIntent = intent || null;
      if (tipFor === anchor && !tip.hidden) return;
      if (tipFor && tipFor !== anchor) termDescriptionTarget(tipFor).removeAttribute("aria-describedby");
      if (tipFor !== anchor) tier = 0; // a different term always starts collapsed
      tipFor = anchor;
      termDescriptionTarget(anchor).setAttribute("aria-describedby", tip.id);
      renderTier(data, anchor);
      placeFloater(tip, anchor);
    }
    function expandTip(anchor) {
      loadPresentation();
      var data = TERMS[anchor.getAttribute("data-term")];
      if (!data) return false;
      if (tipHideTimer) { clearTimeout(tipHideTimer); tipHideTimer = 0; }
      if (tipFadeTimer) { clearTimeout(tipFadeTimer); tipFadeTimer = 0; }
      tip.classList.remove("is-leaving");
      tier = 1;
      if (tipFor && tipFor !== anchor) termDescriptionTarget(tipFor).removeAttribute("aria-describedby");
      tipFor = anchor;
      previewIntent = "click";
      termDescriptionTarget(anchor).setAttribute("aria-describedby", tip.id);
      renderTier(data, anchor);
      placeFloater(tip, anchor); // reposition: the card grew
      return true;
    }
    function hideTip(immediate) {
      tier = 0;
      previewIntent = null;
      if (tipFor) { termDescriptionTarget(tipFor).removeAttribute("aria-describedby"); tipFor = null; }
      if (tip.hidden) return;
      if (immediate) {
        if (tipFadeTimer) { clearTimeout(tipFadeTimer); tipFadeTimer = 0; }
        tip.hidden = true;
        tip.classList.remove("is-leaving");
        return;
      }
      // Leave as a quick fade rather than a blink, so moving between terms
      // reads as one continuous surface.
      tip.classList.add("is-leaving");
      if (tipFadeTimer) clearTimeout(tipFadeTimer);
      tipFadeTimer = setTimeout(function () {
        tipFadeTimer = 0;
        tip.hidden = true;
        tip.classList.remove("is-leaving");
      }, 90);
    }
    function scheduleHideTip() {
      if (tipHideTimer) clearTimeout(tipHideTimer);
      tipHideTimer = setTimeout(hideTip, 110); // grace so the pointer can land on the card
    }

    tip.addEventListener("mouseenter", function () {
      if (suppressPointerPreview) return;
      if (tipHideTimer) { clearTimeout(tipHideTimer); tipHideTimer = 0; }
      if (tipFadeTimer) { clearTimeout(tipFadeTimer); tipFadeTimer = 0; }
      tip.classList.remove("is-leaving");
    });
    tip.addEventListener("mouseleave", scheduleHideTip);
    function releasePointerSuppression() {
      suppressPointerPreview = false;
    }
    tipBack.addEventListener("click", function () {
      var anchor = termDescriptionTarget(tipFor);
      suppressFocusPreview = true;
      suppressPointerPreview = true;
      document.addEventListener("mousemove", releasePointerSuppression, { once: true, capture: true });
      hideTip(true);
      requestAnimationFrame(function () {
        if (anchor && typeof anchor.focus === "function") {
          try { anchor.focus({ preventScroll: true }); } catch (e) { anchor.focus(); }
        }
        requestAnimationFrame(function () {
          hideTip(true);
          suppressFocusPreview = false;
        });
      });
    });

    document.addEventListener("keydown", function (ev) {
      if ((ev.key === "Escape" || ev.key === "Esc") && !tip.hidden) {
        suppressPointerPreview = true;
        document.addEventListener("mousemove", releasePointerSuppression, { once: true, capture: true });
        hideTip();
      }
    });
    // An unmodified first activation expands in place. Activating the SAME term
    // again follows its glossary link, so the word is a preview -> drilldown
    // control without losing native link semantics. Modified clicks keep their
    // native new-tab behaviour from either tier.
    document.addEventListener("click", function (ev) {
      if (tip.contains(ev.target)) return;
      var onTerm = termAnchorFrom(ev.target);
      if (onTerm) {
        if (passiveTerm(onTerm)) {
          if (!tip.hidden) hideTip(true);
          return; // surrounding link/summary keeps every native activation
        }
        if (ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
        if (tipFor === onTerm && tier === 1 && !tip.hidden) {
          hideTip(true);
          return; // second activation: allow the anchor's native navigation
        }
        ev.preventDefault();
        expandTip(onTerm);
        return;
      }
      if (!tip.hidden) hideTip();
    });
    window.addEventListener("resize", function () {
      if (!tip.hidden && tipFor) placeFloater(tip, tipFor);
    });
    window.addEventListener("scroll", function () {
      if (tip.hidden || tier !== 0 || previewIntent !== "pointer" || !tipFor) return;
      var hit = pointerX !== null && document.elementFromPoint
        ? document.elementFromPoint(pointerX, pointerY) : null;
      var hoverTarget = termDescriptionTarget(tipFor);
      if (!hit || (!hoverTarget.contains(hit) && !tip.contains(hit))) hideTip(true);
    }, { passive: true });

    // Delegated, as on the sheet: four document listeners rather than four on
    // every anchor.
    document.addEventListener("mouseover", function (ev) {
      if (typeof ev.clientX === "number") { pointerX = ev.clientX; pointerY = ev.clientY; }
      if (suppressPointerPreview) return;
      var anchor = termAnchorFrom(ev.target);
      if (!anchor) return;
      if (ev.relatedTarget && termDescriptionTarget(anchor).contains(ev.relatedTarget)) return;
      showTip(anchor, "pointer");
    }, true);
    document.addEventListener("mouseout", function (ev) {
      var anchor = termAnchorFrom(ev.target);
      if (!anchor) return;
      if (ev.relatedTarget && termDescriptionTarget(anchor).contains(ev.relatedTarget)) return;
      scheduleHideTip();
    }, true);
    document.addEventListener("focusin", function (ev) {
      if (suppressFocusPreview) return;
      var anchor = termAnchorFrom(ev.target);
      if (anchor) showTip(anchor, "focus");
    }, true);
    document.addEventListener("focusout", function (ev) {
      if (termAnchorFrom(ev.target)) scheduleHideTip();
    }, true);
