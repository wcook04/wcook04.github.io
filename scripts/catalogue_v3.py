#!/usr/bin/env python3
"""Author, migrate and derive the Plectis catalogue without a network service.

The v3 JSON is the authored record; v2 is a temporary rendering adapter.
`build_graph` always uses real publication states, never preview presentation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote, urlparse

SCHEMA = "will_cook_site_family_v3"
HOME = "https://wcook04.github.io/"
YOUTUBE = re.compile(r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$")
HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(kind, slug):
    return f"{kind}:{slug}"


def source(collection, index, **extra):
    return {"collection": collection, "index": index, **extra}


def publication(platform, url=None, *, seconds=None, media=None):
    result = {"id": platform, "platform": platform,
              "state": "published" if url else "in_preparation", "url": url}
    if seconds is not None:
        result["duration_seconds"] = seconds
    if media:
        result["thumbnail_stem"] = media
    return result


def public_location(resource, platform=None, *, include_unlisted=False):
    allowed = {"published", "unlisted"} if include_unlisted else {"published"}
    entries = [p for p in resource.get("publications", [])
               if p["state"] in allowed and p.get("url")
               and (platform is None or p["platform"] == platform)]
    return next((p for p in entries if p.get("preferred")), entries[0] if entries else None)


def entity_index(data, glossary=None):
    rows = [dict(data["owner"], type="person")]
    for field, typ in [("projects", "project"), ("areas", "area"), ("topics", "topic"),
                       ("collections", "collection"), ("people", "person")]:
        rows.extend(dict(x, type=x.get("type", typ)) for x in data.get(field, []))
    rows.extend(data.get("resources", []))
    if glossary:
        rows.extend(dict(t, id=ref("term", t["id"]), type="term") for t in glossary.get("terms", []))
    return {x["id"]: x for x in rows}


def rels(data, typ=None, *, start=None, end=None):
    return sorted([r for r in data["relationships"]
                   if (typ is None or r["type"] == typ)
                   and (start is None or r["from"] == start)
                   and (end is None or r["to"] == end)],
                  key=lambda r: (r.get("order", 0), r["id"]))


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def migrate_v2(old, glossary):
    """Lossless v2->v3 migration of source fields, plus typed relationships.

    New individual paper records are made only for existing single-paper routes.
    A route to a paper collection remains an index, not an invented paper.
    `source` is a one-time compatibility locator, not a second copy of the data.
    """
    if old.get("schema") != "will_cook_site_family_v2":
        raise ValueError("Expected will_cook_site_family_v2")
    data = {"schema": SCHEMA, "updated": old["updated"], "about": old["about"],
            "owner": {"id": "person:will-cook", **deepcopy(old["owner"])},
            "presentation": {"hero": deepcopy(old.get("hero", {})),
                             "projects_lede": old.get("projects_lede", ""),
                             "home_resource": "home", "preferred_video_platform": "youtube"},
            "projects": [], "resources": [], "areas": [], "topics": [],
            "collections": [], "people": [], "relationships": [],
            "glossary_file": "glossary.json"}
    resources = {}
    edge_keys = set()

    def add_resource(item):
        if item["id"] in resources:
            raise ValueError("Duplicate resource: " + item["id"])
        item.setdefault("aliases", [])
        item.setdefault("publications", [])
        item.setdefault("term_refs", [])
        resources[item["id"]] = item
        data["resources"].append(item)
        return item["id"]

    def edge(a, b, typ, **kw):
        key = (a, b, typ, kw.get("role"))
        if key in edge_keys:
            raise ValueError("Duplicate relationship: " + repr(key))
        edge_keys.add(key)
        # Stable identifier depends on meaning, never on position or copy.
        ident = "rel:" + sha256("|".join(str(x or "") for x in key).encode()).hexdigest()[:16]
        row = {"id": ident, "from": a, "to": b, "type": typ, **kw}
        data["relationships"].append(row)
        return row

    add_resource({"id": "home", "type": "website", "slug": "home", "title": old["owner"]["name"],
                  "publications": [publication("web", old["owner"]["home"])],
                  "source": {"collection": "owner", "index": 0, "field": "home"}})

    for i, f in enumerate(old["films"]):
        keep = {k: deepcopy(v) for k, v in f.items()
                if k not in {"id", "youtube", "duration_seconds", "still", "leads_to", "superseded_by"}}
        rid = ref("film", f["id"])
        keep.update(id=rid, slug=f["id"], type="video", source=source("films", i),
                    publications=[publication("youtube", f.get("youtube"),
                                              seconds=f.get("duration_seconds"), media=f.get("still"))],
                    chapters=[])
        add_resource(keep)
        for order, target in enumerate(f.get("leads_to", [])):
            edge(rid, ref("film", target), "leads_to", role="deeper_video", order=order,
                 label="Full video", source={"field": "leads_to", "owner": rid})
        if f.get("superseded_by"):
            edge(rid, ref("film", f["superseded_by"]), "superseded_by",
                 activation="when_target_is_published", source={"field": "superseded_by", "owner": rid})

    for i, r in enumerate(old["repos"]):
        add_resource({"id": ref("repo", r["id"]), "slug": r["id"], "type": "repository",
                      "title": r["name"], "description": r["description"], "repository_kind": "own",
                      "publications": [publication("github", r["href"])], "source": source("repos", i)})

    single_papers = {
        ("quartic", "https://wcook04.github.io/quartic-query-lean/#/read/original"):
            ("quartic-original", "OpenAI’s quantum query-complexity paper", "original"),
        ("quartic", "https://wcook04.github.io/quartic-query-lean/#/read/exposition"):
            ("quartic-exposition", "Exposition of the quantum query-complexity result", "exposition"),
        ("lean-exposition", "https://wcook04.github.io/lean-exposition-site/read/expository/"):
            ("sk-exposition", "Exposition of the Sherrington–Kirkpatrick result", "exposition"),
        ("proof-reader", "https://wcook04.github.io/proof-reader/#/contextual-embeddings"):
            ("contextual-embeddings", "Contextual Embeddings", "original"),
        ("zenith", "https://wcook04.github.io/plectis-zenith/assets/paper.pdf"):
            ("zenith-program-repair", "Earlier paper on program repair", "earlier_study"),
    }
    film_roles = {"short-sk-website": "reader_taster", "short-quartic-reader": "reader_taster",
                  "short-proof-reader": "reader_taster", "long-lean-readers": "reader_walkthrough",
                  "short-mathematics": "result_taster", "short-sk-no-gap": "result_taster",
                  "short-quartic": "result_taster", "short-mathematics-overview": "collection_taster",
                  "mathematics": "proof_explanation", "sk-no-gap": "proof_explanation",
                  "quartic-query": "proof_explanation", "interfaces": "earlier_site_tour"}
    repo_roles = {"plectis-erdos": "papers_and_source", "plectis-erdos-lean": "proof_code",
                  "lean-exposition-site": "site_deployment", "quartic-query-lean": "proofs_and_reader_source",
                  "lean-exposition": "papers_and_reader_source"}
    for collection in ("sites", "projects"):
        for i, original in enumerate(old[collection]):
            pid = ref("project", original["id"])
            project = {k: deepcopy(v) for k, v in original.items()
                       if k not in {"id", "films", "repos", "routes", "url"}}
            project.update(id=pid, slug=original["id"], source=source(collection, i), term_refs=[])
            data["projects"].append(project)
            for order, fid in enumerate(original.get("films", [])):
                role = film_roles.get(fid, "taster" if fid.startswith("short-") else "full_video")
                edge(ref("film", fid), pid, "resource_for", role=role, order=order,
                     source={"collection": collection, "index": i, "field": "films"})
            for order, rid in enumerate(original.get("repos", [])):
                role = "method_material" if original["id"] == "funnel" else repo_roles.get(rid, "source_code")
                edge(ref("repo", rid), pid, "resource_for", role=role, order=order,
                     source={"collection": collection, "index": i, "field": "repos"})
            if collection != "sites":
                continue
            sid = add_resource({"id": ref("site", original["id"]), "slug": original["id"],
                                "type": "website", "title": original["name"],
                                "publications": [publication("web", original["url"])],
                                "source": source("sites", i, field="url")})
            edge(sid, pid, "resource_for", role="primary_website", order=0,
                 source={"collection": collection, "index": i, "field": "url"})
            for order, route in enumerate(original.get("routes", [])):
                known_paper = single_papers.get((original["id"], route["href"]))
                if known_paper:
                    slug, title, role = known_paper
                    record = {"id": ref("paper", slug), "slug": slug, "type": "paper", "title": title,
                              "paper_role": role, "bibliographic_title": None,
                              "title_is_descriptive": slug != "contextual-embeddings"}
                    if slug == "contextual-embeddings":
                        record["bibliographic_title"] = "Contextual Embeddings"
                else:
                    slug = original["id"] + "-" + _slug(route["label"])
                    role = "paper_index" if "papers" in route["label"].lower() else (
                        "pull_request" if "/pull/" in route["href"] else "project_route")
                    record = {"id": ref("link", slug), "slug": slug, "type": "link", "title": route["label"],
                              "link_role": role}
                record.update(publications=[publication("web", route["href"])],
                              source=source("sites", i, field="routes", route_index=order))
                rid = add_resource(record)
                edge(rid, pid, "resource_for", role=role, order=order, label=route["label"],
                     source={"collection": "sites", "index": i, "field": "routes", "route_index": order})
                edge(rid, sid, "available_through", order=order)

    for i, area in enumerate(old.get("areas", [])):
        data["areas"].append({"id": ref("area", area["id"]), "slug": area["id"],
                              **{k: deepcopy(v) for k, v in area.items() if k not in {"id", "items"}},
                              "source": source("areas", i)})
        for order, pid in enumerate(area["items"]):
            edge(ref("project", pid), ref("area", area["id"]), "in_area", order=order)
    for i, topic in enumerate(old.get("topics", [])):
        data["topics"].append({"id": ref("topic", topic["id"]), "slug": topic["id"],
                               **{k: deepcopy(v) for k, v in topic.items() if k not in {"id", "items", "area"}},
                               "area_ref": ref("area", topic["area"]), "source": source("topics", i)})
        for order, pid in enumerate(topic["items"]):
            edge(ref("project", pid), ref("topic", topic["id"]), "in_topic", order=order)
    for i, coll in enumerate(old.get("collections", [])):
        cid = ref("collection", coll["id"])
        data["collections"].append({"id": cid, "slug": coll["id"],
                                    **{k: deepcopy(v) for k, v in coll.items() if k not in {"id", "members", "film"}},
                                    "source": source("collections", i)})
        for order, pid in enumerate(coll["members"]):
            edge(ref("project", pid), cid, "member_of", order=order)
        if coll.get("film"):
            edge(ref("film", coll["film"]), cid, "resource_for", role="shared_walkthrough", order=0)
    for order, fid in enumerate(old.get("intro", {}).get("films", [])):
        edge(ref("film", fid), "home", "introduces", order=order)
    for i, link in enumerate(old.get("links", [])):
        typ = "worked_example" if link["label"].startswith("Worked example:") else (
            "supports_video_stage" if link["from"] == "narration-ir" and link["to"] == "funnel" else
            "related_application" if link["from"] == "codemap" and link["to"] == "code-ontology-bridge" else "related")
        edge(ref("project", link["from"]), ref("project", link["to"]), typ,
             label=link["label"], order=i, source=source("links", i))
    for i, c in enumerate(old.get("contributions", [])):
        rid = add_resource({"id": ref("repo", c["repo"]), "slug": c["repo"], "type": "repository",
                            "title": c["repo"], "description": c["what"], "repository_kind": "contribution_fork",
                            "upstream": "https://github.com/" + c["upstream"],
                            "publications": [publication("github", "https://github.com/wcook04/" + c["repo"])],
                            "source": source("contributions", i)})
        edge(rid, "home", "listed_in", role="contribution", order=i)
        if c.get("evidence"):
            lid = add_resource({"id": "link:contribution-" + c["repo"], "slug": "contribution-" + c["repo"],
                                "type": "link", "link_role": "contribution_evidence", "title": c["evidence"]["label"],
                                "publications": [publication("web", c["evidence"]["href"])],
                                "source": source("contributions", i, field="evidence")})
            edge(lid, rid, "evidence_for", label=c["evidence"]["label"])
    for i, item in enumerate(old.get("earlier", [])):
        slug = item["href"].rstrip("/").split("/")[-1]
        rid = add_resource({"id": ref("repo", slug), "slug": slug, "type": "repository",
                            "title": item["name"], "description": item["note"],
                            "repository_kind": "retired" if "Retired" in item["note"] else "earlier",
                            "publications": [publication("github", item["href"])], "source": source("earlier", i)})
        edge(rid, "home", "listed_in", role="earlier_work", order=i)

    bind_terms(data, glossary)
    return data


def bind_terms(data, glossary):
    """Write explicit bindings; this is a build helper, not a runtime matcher.

    Name spans are protected. Broad everyday aliases are excluded. A copy edit
    invalidating a stored surface is caught by validation. An editor can adjust
    bindings without changing definitions or visible prose.
    """
    broad = {"skill", "model", "commit", "record", "check", "proof", "coverage", "context",
             "route", "grounding", "trace", "query", "score", "full", "partial", "accepted"}
    names = sorted({n for p in data["projects"] for n in [p.get("name"), p.get("label"), *p.get("aka", [])] if n},
                   key=len, reverse=True)
    protect = re.compile("|".join(re.escape(n) for n in names), re.I) if names else None
    candidates = []
    for term in glossary.get("terms", []):
        for word in [term["term"], *term.get("aliases", [])]:
            if word.lower() not in broad and len(word) >= 2:
                candidates.append((word, term["id"]))
    candidates.sort(key=lambda x: -len(x[0]))
    for item in data["projects"] + data["resources"]:
        bindings = []
        fields = ["line", "plain", "summary"] if item["id"].startswith("project:") else ["takeaway"]
        for field in fields:
            text = item.get(field, "")
            blocked = [(m.start(), m.end()) for m in protect.finditer(text)] if protect else []
            matched, occupied = set(), []
            for word, tid in candidates:
                if tid in matched:
                    continue
                pattern = re.compile(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", re.I)
                for occurrence, match in enumerate(pattern.finditer(text), 1):
                    if any(a < match.end() and match.start() < b for a, b in blocked + occupied):
                        continue
                    # Store the occurrence of this exact surface, not the
                    # case-insensitive alias. Rendering deliberately uses no
                    # aliases and must find the same span after serialisation.
                    surface = match.group()
                    exact_occurrence = len(list(re.finditer(re.escape(surface), text[:match.start()]))) + 1
                    bindings.append({"field": field, "term_id": tid, "surface": surface, "occurrence": exact_occurrence})
                    occupied.append((match.start(), match.end())); matched.add(tid)
                    break
        item["term_refs"] = bindings


def adapt_v3_to_v2(data):
    """Return a v2-shaped rendering view. Never write it over canonical v3.

    All video-to-video continuations survive as arrays. Non-video onward
    resources stay in canonical v3 and are exposed by continuations(). Old
    templates that read [0] must still be upgraded; the adapter cannot make a
    one-target UI N:N or turn a paper into a film record.
    """
    if data.get("schema") != SCHEMA:
        return deepcopy(data)
    index = entity_index(data)
    owner = {k: deepcopy(v) for k, v in data["owner"].items() if k != "id"}
    old = {"schema": "will_cook_site_family_v2", "about": data["about"], "updated": data["updated"],
           "owner": owner, "projects_lede": data["presentation"].get("projects_lede", ""),
           "sites": [], "projects": [], "repos": [], "films": [], "intro": {"films": []},
           "areas": [], "links": [], "collections": [], "contributions": [], "earlier": [],
           "hero": deepcopy(data["presentation"].get("hero", {})), "topics": []}
    for p in data["projects"]:
        original = {k: deepcopy(v) for k, v in p.items() if k not in {"id", "slug", "source", "term_refs", "aliases", "credits"}}
        original["id"] = p["slug"]
        attachments = rels(data, "resource_for", end=p["id"])
        original["films"] = [index[r["from"]]["slug"] for r in attachments if index[r["from"]]["type"] == "video"]
        original["repos"] = [index[r["from"]]["slug"] for r in attachments if index[r["from"]]["type"] == "repository"]
        collection = p.get("source", {}).get("collection")
        if collection not in {"sites", "projects"}:
            collection = "sites" if any(r.get("role") == "primary_website" for r in attachments) else "projects"
        if collection == "sites":
            sites = [index[r["from"]] for r in attachments if r.get("role") == "primary_website"]
            if sites:
                loc = public_location(sites[0]); original["url"] = loc["url"] if loc else None
            routes = [r for r in attachments if index[r["from"]].get("source", {}).get("field") == "routes"]
            original["routes"] = [{"label": r.get("label") or index[r["from"]]["title"],
                                    "href": (public_location(index[r["from"]]) or {}).get("url")}
                                   for r in routes]
        old[collection].append(original)
    for r in data["resources"]:
        src = r.get("source", {}); collection = src.get("collection")
        if r["type"] == "video":
            f = {k: deepcopy(v) for k, v in r.items() if k not in {
                "id", "slug", "type", "source", "publications", "chapters", "aliases", "term_refs", "credits"}}
            f["id"] = r["slug"]
            loc = public_location(r, "youtube")
            f.update(youtube=loc["url"] if loc else None,
                     duration_seconds=loc.get("duration_seconds") if loc else None,
                     still=loc.get("thumbnail_stem") if loc else None)
            f["leads_to"] = [index[x["to"]]["slug"] for x in rels(data, "leads_to", start=r["id"])
                             if index[x["to"]]["type"] == "video"]
            replacements = rels(data, "superseded_by", start=r["id"])
            if replacements:
                f["superseded_by"] = index[replacements[0]["to"]]["slug"]
            old["films"].append(f)
        elif collection == "repos":
            old["repos"].append({"id": r["slug"], "name": r["title"],
                                 "href": (public_location(r) or {}).get("url"), "description": r["description"]})
        elif collection == "contributions" and r["type"] == "repository":
            c = {"repo": r["slug"], "upstream": r["upstream"].removeprefix("https://github.com/"), "what": r["description"]}
            evidence = rels(data, "evidence_for", end=r["id"])
            if evidence:
                link = index[evidence[0]["from"]]
                c["evidence"] = {"label": link["title"], "href": (public_location(link) or {}).get("url")}
            old["contributions"].append(c)
        elif collection == "earlier":
            old["earlier"].append({"name": r["title"], "href": (public_location(r) or {}).get("url"), "note": r["description"]})
    for field, membership in [("areas", "in_area"), ("topics", "in_topic"), ("collections", "member_of")]:
        for x in data[field]:
            item = {k: deepcopy(v) for k, v in x.items() if k not in {"id", "slug", "source", "area_ref", "term_refs"}}
            item["id"] = x["slug"]
            key = "members" if field == "collections" else "items"
            item[key] = [index[r["from"]]["slug"] for r in rels(data, membership, end=x["id"])]
            if field == "topics": item["area"] = index[x["area_ref"]]["slug"]
            if field == "collections":
                videos = [r for r in rels(data, "resource_for", end=x["id"]) if index[r["from"]]["type"] == "video"]
                if videos: item["film"] = index[videos[0]["from"]]["slug"]
            old[field].append(item)
    old["intro"]["films"] = [index[r["from"]]["slug"] for r in rels(data, "introduces", end="home")]
    for r in sorted(data["relationships"], key=lambda x: x.get("source", {}).get("index", 0)):
        if r.get("source", {}).get("collection") == "links":
            old["links"].append({"from": index[r["from"]]["slug"], "to": index[r["to"]]["slug"], "label": r["label"]})
    return old


def continuations(data, film_id, *, published_only=False):
    index = entity_index(data)
    fid = film_id if film_id.startswith("film:") else ref("film", film_id)
    output = []
    for r in rels(data, "leads_to", start=fid):
        target = index[r["to"]]; location = public_location(target)
        if published_only and not location: continue
        output.append({"relationship": deepcopy(r), "resource": deepcopy(target), "publication": deepcopy(location)})
    return output


def project_resources(data, project_id, *, role=None):
    index = entity_index(data)
    pid = project_id if project_id.startswith("project:") else ref("project", project_id)
    return [{"relationship": deepcopy(r), "resource": deepcopy(index[r["from"]]),
             "publication": deepcopy(public_location(index[r["from"]]))}
            for r in rels(data, "resource_for", end=pid) if role is None or r.get("role") == role]


def edition_state(data, resource_id):
    index = entity_index(data); item = index[resource_id]
    if item.get("edition") == "earlier": return "earlier"
    for r in rels(data, "superseded_by", start=resource_id):
        if r.get("activation") != "when_target_is_published" or public_location(index[r["to"]]):
            return "earlier"
    return "current"


def build_graph(data, glossary):
    """Lossless typed graph projection; no preview flag or derived fake URL."""
    index = entity_index(data, glossary)
    nodes = []
    for item in index.values():
        node = deepcopy(item)
        if item.get("publications") is not None:
            loc = public_location(item)
            node["url"] = loc["url"] if loc else None
            node["publicly_available"] = bool(loc)
        if item["type"] == "video":
            node["edition_state"] = edition_state(data, item["id"])
        nodes.append(node)
    edges = deepcopy(data["relationships"])
    for item in data["projects"] + data["resources"]:
        for binding in item.get("term_refs", []):
            key = f'{item["id"]}|{binding["field"]}|{binding["term_id"]}|{binding["surface"]}|{binding["occurrence"]}'
            edges.append({"id": "termref:" + sha256(key.encode()).hexdigest()[:16],
                          "from": item["id"], "to": ref("term", binding["term_id"]),
                          "type": "uses_term", **deepcopy(binding)})
    for term in glossary.get("terms", []):
        tid = ref("term", term["id"])
        for other in term.get("related_terms", []):
            target = ref("term", other)
            key = f"{tid}|related_term|{target}"
            edges.append({"id": "termref:" + sha256(key.encode()).hexdigest()[:16],
                          "from": tid, "to": target, "type": "related_term"})
        for link in term.get("references", []):
            if not link.get("resource_id"): continue
            key = f'{tid}|reference|{link["resource_id"]}|{link["url"]}'
            edges.append({"id": "termref:" + sha256(key.encode()).hexdigest()[:16],
                          "from": tid, "to": link["resource_id"], "type": "reference",
                          "label": link["label"], "url": link["url"]})
    return {"schema": "will_cook_catalogue_graph_v2", "source_schema": SCHEMA,
            "updated": data["updated"], "about": "Generated from sites.json and glossary.json; not an authoring source.",
            "node_types": sorted({n["type"] for n in nodes}),
            "edge_types": sorted({r["type"] for r in edges}), "nodes": nodes, "edges": edges}


def explicit_term_html(item, field, glossary):
    """Render only authored term references, never substring guesses."""
    text = item.get(field, ""); by_id = {t["id"]: t for t in glossary.get("terms", [])}
    spans = []
    for b in item.get("term_refs", []):
        if b["field"] != field or b["term_id"] not in by_id: continue
        matches = list(re.finditer(re.escape(b["surface"]), text))
        if len(matches) < b.get("occurrence", 1): continue
        m = matches[b.get("occurrence", 1) - 1]
        spans.append((m.start(), m.end(), b["term_id"]))
    out, end = [], 0
    for a, b, tid in sorted(spans):
        if a < end: continue
        out += [html.escape(text[end:a]), f'<a class="term" href="#t-{html.escape(tid)}" data-term="{html.escape(tid)}">{html.escape(text[a:b])}</a>']
        end = b
    out.append(html.escape(text[end:])); return "".join(out)


def _all_urls(value):
    if isinstance(value, dict):
        for item in value.values(): yield from _all_urls(item)
    elif isinstance(value, list):
        for item in value: yield from _all_urls(item)
    elif isinstance(value, str) and value.startswith(("https://", "http://", "mailto:")):
        yield value


def semantic_errors(data, glossary, asset_root=None):
    errors = []
    all_rows = [data["owner"]] + sum([data.get(k, []) for k in ["projects", "resources", "areas", "topics", "collections", "people"]], [])
    ids = [x["id"] for x in all_rows]
    if len(ids) != len(set(ids)): errors.append("Entity IDs must be unique across every collection")
    index = entity_index(data)
    term_ids = {t["id"] for t in glossary.get("terms", [])}
    if len(term_ids) != len(glossary.get("terms", [])): errors.append("Glossary IDs repeat")
    for term in glossary.get("terms", []):
        for other in term.get("related_terms", []):
            if other not in term_ids: errors.append(term["id"] + ": unknown related glossary term " + other)
        for reference in term.get("references", []):
            target = reference.get("resource_id")
            if target is not None and target not in index:
                errors.append(term["id"] + ": glossary reference names an unknown resource " + target)
    rid = [r["id"] for r in data["relationships"]]
    if len(rid) != len(set(rid)): errors.append("Relationship IDs repeat")
    edge_keys = set()
    signature = {
        "resource_for": ({"video", "website", "repository", "paper", "link"}, {"project", "collection"}),
        "leads_to": ({"video"}, {"video", "paper", "website", "repository", "link"}),
        "superseded_by": ({"video", "paper"}, {"video", "paper"}),
        "in_area": ({"project"}, {"area"}), "in_topic": ({"project"}, {"topic"}),
        "member_of": ({"project", "video", "paper", "website", "repository", "link"}, {"collection"}),
        "introduces": ({"video"}, {"website", "project", "collection", "topic"}),
        "available_through": ({"paper", "link"}, {"website"}),
        "evidence_for": ({"link", "paper"}, {"repository", "project"}),
        "listed_in": ({"repository", "link"}, {"website", "collection"}),
        "worked_example": ({"project"}, {"project"}),
        "supports_video_stage": ({"project"}, {"project"}),
        "related_application": ({"project"}, {"project"}),
        "related": ({"project", "video", "paper", "website", "repository", "link"},
                    {"project", "video", "paper", "website", "repository", "link"}),
        "derived_from": ({"repository", "paper", "video", "website"}, {"repository", "paper", "video", "website"}),
    }
    for edge in data["relationships"]:
        a, b, typ = edge["from"], edge["to"], edge["type"]
        if a not in index or b not in index:
            errors.append(f'{edge["id"]}: dangling endpoint {a} -> {b}'); continue
        if a == b: errors.append(f'{edge["id"]}: self relationship is not meaningful')
        key = (a, b, typ, edge.get("role"))
        if key in edge_keys: errors.append(f'{edge["id"]}: duplicate semantic relationship')
        edge_keys.add(key)
        if typ in signature:
            left, right = signature[typ]
            if index[a]["type"] not in left or index[b]["type"] not in right:
                errors.append(f'{edge["id"]}: {typ} has incompatible endpoint types')
        if typ == "resource_for" and not edge.get("role"):
            errors.append(f'{edge["id"]}: resource_for needs its contextual role')
        if typ == "superseded_by" and index[a]["type"] != index[b]["type"]:
            errors.append(f'{edge["id"]}: editions must have the same resource type')
    # Every active project is assigned once to a main area, and to a topic.
    for p in data["projects"]:
        if len(rels(data, "in_area", start=p["id"])) != 1:
            errors.append(p["id"] + ": exactly one primary area is required")
        if not rels(data, "in_topic", start=p["id"]):
            errors.append(p["id"] + ": no topic reaches this project")
    for t in data["topics"]:
        if t.get("area_ref") not in index or index.get(t.get("area_ref"), {}).get("type") != "area":
            errors.append(t["id"] + ": unknown presentation area")
        if not rels(data, "in_topic", end=t["id"]): errors.append(t["id"] + ": empty topic")
    # A cycle of replacement pointers can retire every video; reject it.
    adj = defaultdict(list)
    for edge in rels(data, "superseded_by"): adj[edge["from"]].append(edge["to"])
    visiting, done = set(), set()
    def visit(node):
        if node in visiting: errors.append("Replacement cycle reaches " + node); return
        if node in done: return
        visiting.add(node)
        for nxt in adj[node]: visit(nxt)
        visiting.remove(node); done.add(node)
    for node in list(adj): visit(node)
    for r in data["resources"]:
        if r["id"] != "home" and not any(e["from"] == r["id"] and e["type"] in {
                "resource_for", "introduces", "member_of", "listed_in", "evidence_for", "available_through"}
                for e in data["relationships"]):
            errors.append(r["id"] + ": resource has no catalogue placement")
        pubs = r.get("publications", [])
        if len({p["id"] for p in pubs}) != len(pubs): errors.append(r["id"] + ": publication IDs repeat")
        if sum(bool(p.get("preferred")) for p in pubs) > 1: errors.append(r["id"] + ": more than one preferred publication")
        for pub in pubs:
            url = pub.get("url")
            if pub["state"] in {"published", "unlisted"} and not url:
                errors.append(r["id"] + ": a published location needs a real URL")
            if pub["state"] == "in_preparation" and url:
                errors.append(r["id"] + ": a planned publication must not have a fake playable URL")
            if url and urlparse(url).scheme not in {"https", "http"}:
                errors.append(r["id"] + ": publication URL must be HTTP(S)")
            if pub["platform"] == "youtube" and url and not YOUTUBE.match(url):
                errors.append(r["id"] + ": invalid YouTube watch URL")
            if r["type"] == "video" and pub["state"] in {"published", "unlisted"}:
                if not isinstance(pub.get("duration_seconds"), (int, float)) or pub["duration_seconds"] <= 0:
                    errors.append(r["id"] + ": published video needs measured duration")
                if not pub.get("thumbnail_stem") and not pub.get("thumbnail_url"):
                    errors.append(r["id"] + ": published video needs a thumbnail")
        if r["type"] == "video":
            if not any(e["from"] == r["id"] and e["type"] in {"resource_for", "introduces", "member_of"}
                       for e in data["relationships"]):
                errors.append(r["id"] + ": video has no project, collection or introduction placement")
            if r.get("format") == "short" and not rels(data, "leads_to", start=r["id"]):
                errors.append(r["id"] + ": taster needs an explicit continuation")
            seen_starts = set(); chapter_ids = set(); previous_start = {}
            for chapter in r.get("chapters", []):
                if chapter["id"] in chapter_ids: errors.append(r["id"] + ": repeated chapter ID")
                chapter_ids.add(chapter["id"])
                base = chapter.get("publication_id", "cut")
                loc = next((p for p in pubs if p["id"] == base), None)
                duration = r.get("cut_seconds") if base == "cut" else (loc or {}).get("duration_seconds")
                if base != "cut" and loc is None: errors.append(r["id"] + ": chapter names unknown publication")
                if (base, chapter["start_seconds"]) in seen_starts: errors.append(r["id"] + ": repeated chapter start")
                seen_starts.add((base, chapter["start_seconds"]))
                if base in previous_start and chapter["start_seconds"] <= previous_start[base]:
                    errors.append(r["id"] + ": chapters are not ordered within their timebase")
                previous_start[base] = chapter["start_seconds"]
                for target in chapter.get("related_resources", []):
                    if target not in index: errors.append(r["id"] + ": chapter links an unknown resource")
                if duration is None: errors.append(r["id"] + ": chapter has no measured timebase")
                elif chapter["start_seconds"] >= duration: errors.append(r["id"] + ": chapter starts after video end")
                if chapter.get("end_seconds") is not None and (chapter["end_seconds"] <= chapter["start_seconds"] or
                                                              (duration is not None and chapter["end_seconds"] > duration)):
                    errors.append(r["id"] + ": invalid chapter end")
    for item in data["projects"] + data["resources"]:
        for credit in item.get("credits", []):
            person = index.get(credit["person_id"])
            if person is None or person["type"] not in {"person", "organisation"}:
                errors.append(item["id"] + ": credit names an unknown person or organisation")
        spans = defaultdict(list)
        for b in item.get("term_refs", []):
            if b["term_id"] not in term_ids: errors.append(item["id"] + ": undefined glossary reference " + b["term_id"])
            text = item.get(b["field"], "")
            if not isinstance(text, str): errors.append(item["id"] + ": term binding names a non-text field"); continue
            matches = list(re.finditer(re.escape(b["surface"]), text))
            if len(matches) < b.get("occurrence", 1):
                errors.append(item["id"] + ": stale glossary surface " + b["surface"]); continue
            match = matches[b.get("occurrence", 1) - 1]
            if any(a < match.end() and match.start() < z for a, z in spans[b["field"]]):
                errors.append(item["id"] + ": overlapping glossary references")
            spans[b["field"]].append((match.start(), match.end()))
        if asset_root:
            stems = [item.get("poster")] + [p.get("thumbnail_stem") for p in item.get("publications", [])]
            files = [item.get("thumbnail")]
            if item.get("capture"):
                files += [f'{item["capture"]}-{theme}-{width}.webp' for theme in ("light", "dark") for width in (720, 1440)]
            for stem in filter(None, stems): files += [f"{stem}-{w}.webp" for w in (640, 1280)]
            for file in filter(None, files):
                if not file.startswith("assets/") or ".." in Path(file).parts or not (Path(asset_root) / file).is_file():
                    errors.append(item["id"] + ": missing or invalid local asset " + file)
    return errors


def validate(data, glossary, *, schema_path=None, glossary_schema_path=None, asset_root=None):
    """JSON Schema (shape) plus semantic validation (cross-record meaning)."""
    errors = []
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return ["Install jsonschema 4.x to validate the bundled Draft 2020-12 schema"]
    for value, path in [(data, schema_path or HERE / "sites.schema.json"),
                        (glossary, glossary_schema_path or HERE / "glossary.schema.json")]:
        schema = read_json(path)
        Draft202012Validator.check_schema(schema)
        for issue in Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value):
            errors.append("/" + "/".join(map(str, issue.absolute_path)) + ": " + issue.message)
    if not errors: errors.extend(semantic_errors(data, glossary, asset_root))
    return errors


def coverage(data, glossary, *, original=None, original_graph=None):
    graph = build_graph(data, glossary)
    result = {"authored_entity_counts": dict(Counter(x["type"] for x in entity_index(data).values())),
              "original_assets": {"projects": len(data["projects"]), "videos": sum(r["type"] == "video" for r in data["resources"]),
                                  "glossary_terms": len(glossary["terms"])},
              "canonical_relationships": len(data["relationships"]),
              "canonical_relationship_types": dict(Counter(e["type"] for e in data["relationships"])),
              "derived_graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"]),
                                "node_types": dict(Counter(n["type"] for n in graph["nodes"])),
                                "edge_types": dict(Counter(e["type"] for e in graph["edges"]))},
              "published_videos": sum(r["type"] == "video" and bool(public_location(r)) for r in data["resources"]),
              "unpublished_videos": sum(r["type"] == "video" and not public_location(r) for r in data["resources"])}
    if original is not None:
        adapted = adapt_v3_to_v2(data)
        result["v2_round_trip_equal"] = adapted == original
        before, after = set(_all_urls(original)), set(_all_urls(data))
        result["source_urls"] = len(before)
        result["preserved_source_urls"] = len(before & after)
        result["missing_source_urls"] = sorted(before - after)
        result["source_counts"] = {key: len(original.get(key, [])) for key in ("sites", "projects", "films", "repos", "areas", "topics", "collections", "links", "contributions", "earlier")}
    if original_graph is not None:
        result["checkpoint_graph"] = {"nodes": len(original_graph["nodes"]), "edges": len(original_graph["edges"]),
                                      "node_types": dict(Counter(n["type"] for n in original_graph["nodes"])),
                                      "edge_types": dict(Counter(e["type"] for e in original_graph["edges"]))}
    return result


def jsonld(data):
    """Conservative metadata projection; this portfolio is not a watch page.

    No invented upload dates, media byte URLs, authorship or ratings. Video
    watch-page rich-results metadata is a separate publication-time concern.
    """
    owner = data["owner"]; home = owner["home"]
    graph = [{"@type": "Person", "@id": home + "#person", "name": owner["name"], "url": home,
              "sameAs": [c["href"] for c in owner.get("contact", []) if c["href"].startswith("https://")]},
             {"@type": "WebSite", "@id": home + "#website", "url": home, "name": owner["name"],
              "author": {"@id": home + "#person"}}]
    listed = []
    for r in data["resources"]:
        loc = public_location(r)
        if not loc or r["id"] == "home": continue
        if r["type"] not in {"website", "repository", "paper"}: continue
        if r.get("repository_kind") in {"contribution_fork", "earlier", "retired"}: continue
        kind = {"website": "WebPage", "repository": "SoftwareSourceCode", "paper": "ScholarlyArticle"}[r["type"]]
        row = {"@type": kind, "@id": home + "#resource-" + quote(r["id"], safe=""),
               "name": r["title"], "url": loc["url"]}
        if r["type"] == "repository": row["codeRepository"] = loc["url"]
        if r.get("description"): row["description"] = r["description"]
        graph.append(row); listed.append({"@type": "ListItem", "position": len(listed) + 1, "item": {"@id": row["@id"]}})
    graph.append({"@type": "ItemList", "@id": home + "#resources", "name": "Projects, papers and source code", "itemListElement": listed})
    return {"@context": "https://schema.org", "@graph": graph}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    migrate = sub.add_parser("migrate"); migrate.add_argument("v2"); migrate.add_argument("glossary"); migrate.add_argument("out")
    check = sub.add_parser("validate"); check.add_argument("sites"); check.add_argument("glossary"); check.add_argument("--assets")
    export = sub.add_parser("export"); export.add_argument("sites"); export.add_argument("glossary"); export.add_argument("out")
    adapt = sub.add_parser("adapt"); adapt.add_argument("sites"); adapt.add_argument("out")
    args = parser.parse_args(argv)
    if args.command == "migrate":
        old, glossary = read_json(args.v2), read_json(args.glossary); data = migrate_v2(old, glossary)
        errors = validate(data, glossary)
        if errors: raise SystemExit("\n".join(errors))
        report = coverage(data, glossary, original=old)
        if not report["v2_round_trip_equal"] or report["missing_source_urls"]:
            raise SystemExit("Migration did not preserve source; see round-trip comparison")
        out = Path(args.out); write_json(out / "sites.json", data); write_json(out / "glossary.json", glossary)
        write_json(out / "migration-coverage.json", report)
        print(json.dumps(report, indent=2))
    elif args.command == "validate":
        data, glossary = read_json(args.sites), read_json(args.glossary)
        errors = validate(data, glossary, asset_root=args.assets)
        if errors: raise SystemExit("\n".join(errors))
        print(json.dumps(coverage(data, glossary), indent=2))
    elif args.command == "adapt":
        write_json(args.out, adapt_v3_to_v2(read_json(args.sites)))
    else:
        data, glossary = read_json(args.sites), read_json(args.glossary); out = Path(args.out)
        errors = validate(data, glossary)
        if errors: raise SystemExit("\n".join(errors))
        write_json(out / "catalogue.json", build_graph(data, glossary))
        write_json(out / "structured-data.jsonld", jsonld(data))
        write_json(out / "rendering-v2.json", adapt_v3_to_v2(data))


if __name__ == "__main__":
    main()
