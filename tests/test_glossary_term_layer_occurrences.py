from __future__ import annotations

import importlib.util
import re
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "build_glossary_term_layer.py"
spec = importlib.util.spec_from_file_location("root_term_layer", SCRIPT)
assert spec and spec.loader
layer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layer)


def snapshot(phrases, phrase_patterns=None):
    terms = {}
    pairs = []
    for phrase, term_id in phrases:
        pairs.append([phrase, term_id])
        terms[term_id] = {
            "anchor": f"glossary-{term_id}",
            "label": phrase,
            "preview": f"Definition of {phrase}.",
            "card": f"Longer definition of {phrase}.",
        }
    result = {
        "phrases": pairs,
        "terms": terms,
        "glossary_href": "https://example.test/glossary.html",
        "term_count": len(terms),
        "phrase_count": len(pairs),
    }
    if phrase_patterns is not None:
        result["phrase_patterns"] = phrase_patterns
    return result


def page(body):
    return f'''<!doctype html><html><body>{body}<script>
    /* BEGIN generated glossary terms */
    var TERMS = {{}};
    /* END generated glossary terms */
    </script></body></html>'''


def anchors(result):
    return re.findall(r'<a class="term(?: is-again)?" data-term="([^"]+)"', result)


def test_links_more_than_eight_distinct_concepts_in_one_paragraph():
    phrases = [(f"concept{i}", f"term_{i}") for i in range(12)]
    result = layer.build(page("<p>" + " ".join(x[0] for x in phrases) + "</p>"), snapshot(phrases))
    assert anchors(result) == [f"term_{i}" for i in range(12)]


def test_every_repeat_is_hoverable_but_only_first_is_visually_cued():
    result = layer.build(page("<p>signal signal signal</p><p>signal again: signal</p>"), snapshot([("signal", "signal")]))
    assert result.count('data-term="signal"') == 5
    assert result.count('class="term" data-term="signal"') == 1
    assert result.count('class="term is-again" data-term="signal"') == 4


def test_protected_markup_and_opt_out_remain_unlinked():
    body = '''<p>signal <a href="/elsewhere">signal</a> <code>signal</code>
      <button>signal</button> <span class="tag">signal</span>
      <span data-term-auto="off"><em>signal</em></span> signal</p>'''
    result = layer.build(page(body), snapshot([("signal", "signal")]))
    assert result.count('data-term="signal"') == 2
    assert '<a href="/elsewhere">signal</a>' in result
    assert '<code>signal</code>' in result
    assert '<button>signal</button>' in result
    assert '<span class="tag">signal</span>' in result
    assert '<span data-term-auto="off"><em>signal</em></span>' in result


def test_rebuild_is_stable_and_regrades_from_document_order():
    source = page('<p>alpha beta alpha</p><p>beta alpha</p>')
    data = snapshot([("alpha", "alpha"), ("beta", "beta")])
    once = layer.build(source, data)
    twice = layer.build(once, data)
    assert twice == once
    assert once.index('class="term" data-term="alpha"') < once.index('class="term is-again" data-term="alpha"')
    assert once.index('class="term" data-term="beta"') < once.index('class="term is-again" data-term="beta"')


def test_governed_pattern_matches_newline_and_nbsp_with_exact_source_spans():
    pattern = r"(?<![\w])formal[\s\u00a0]+verification(?![\w])"
    data = snapshot(
        [("formal verification", "formal_verification")],
        {"formal verification": pattern},
    )
    result = layer.build(
        page("<p>formal\nverification and formal&nbsp;verification</p>"), data
    )
    assert result.count('data-term="formal_verification"') == 2
    assert '>formal\nverification</a>' in result
    assert '>formal&nbsp;verification</a>' in result


def test_governed_pattern_matches_typographic_hyphen_but_literal_snapshot_does_not():
    phrase = "fail-closed"
    pattern = r"(?<![\w])fail[-\u2010-\u2015\u2212]closed(?![\w])"
    patterned = layer.build(
        page("<p>fail‑closed and fail-closed</p>"),
        snapshot([(phrase, "fail_closed")], {phrase: pattern}),
    )
    legacy = layer.build(
        page("<p>fail‑closed and fail-closed</p>"), snapshot([(phrase, "fail_closed")])
    )
    assert patterned.count('data-term="fail_closed"') == 2
    assert legacy.count('data-term="fail_closed"') == 1


def test_governed_pattern_is_compiled_once_and_literal_legacy_path_is_unchanged():
    layer.governed_phrase_re.cache_clear()
    pattern = r"(?<![\w])formal[\s\u00a0]+verification(?![\w])"
    data = snapshot(
        [("formal verification", "formal_verification"), ("signal", "signal")],
        {"formal verification": pattern},
    )
    source = page("<p>formal verification signal formal\nverification signal</p>")
    once = layer.build(source, data)
    twice = layer.build(once, data)
    assert twice == once
    assert once.count('data-term="formal_verification"') == 2
    assert once.count('data-term="signal"') == 2
    assert layer.governed_phrase_re.cache_info().misses == 1
