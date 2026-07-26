"""Fetch candidates. Tier A watches the evidence base for change; Tier B discovers new work.

python -m src.fetch [--dry-run]
Writes candidates to data/pending_raw.json for scoring.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, datetime, urllib.parse
import xml.etree.ElementTree as ET

import requests

from .common import (DATA, load_yaml, load_json, save_json, seen, save_json,
                     fingerprint, polite_sleep, today)

UA = {"User-Agent": "IntentionalDataResearchWatch/1.0 (dominique.charlie@intentionaldata.org)"}
TIMEOUT = 30


def _get(url: str, **kw):
    return requests.get(url, headers=UA, timeout=TIMEOUT, **kw)


# ---------- Tier A ----------

def watch_page_hash(src: dict, state: dict) -> list[dict]:
    try:
        r = _get(src["url"])
        r.raise_for_status()
    except Exception as exc:
        print(f"  ! {src['id']}: fetch failed ({exc})")
        return []
    digest = hashlib.sha256(r.content).hexdigest()
    key = f"hash:{src['id']}"
    previous = state.get(key)
    state[key] = {"hash": digest, "checked": today()}
    if previous and previous.get("hash") != digest:
        return [dict(kind="tier_a_change", id=src["id"], title=f"Change detected: {src['label']}",
                     url=src["url"], doi="", authors="", venue="", year=None,
                     note="The page content changed since the last check. Review for a new edition, errata, or a revision.")]
    return []


def watch_crossref(src: dict, state: dict) -> list[dict]:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(src['doi'])}"
    try:
        r = _get(url)
        r.raise_for_status()
        msg = r.json()["message"]
    except Exception as exc:
        print(f"  ! {src['id']}: crossref failed ({exc})")
        return []
    stamp = msg.get("indexed", {}).get("date-time", "")
    updates = msg.get("update-to") or []
    key = f"crossref:{src['id']}"
    previous = state.get(key)
    state[key] = {"indexed": stamp, "updates": len(updates), "checked": today()}
    out = []
    if previous and previous.get("updates", 0) != len(updates):
        out.append(dict(kind="tier_a_change", id=src["id"],
                        title=f"Crossref update notice: {src['label']}",
                        url=f"https://doi.org/{src['doi']}", doi=src["doi"],
                        authors="", venue="", year=None,
                        note="Crossref reports an update, correction, or retraction notice. Verify before the next cohort."))
    return out


def watch_semantic_scholar_citations(src: dict, state: dict) -> list[dict]:
    url = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{src['doi']}/citations"
           "?fields=title,abstract,year,authors,externalIds,url&limit=25")
    try:
        r = _get(url)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        rows = r.json().get("data", [])
    except Exception as exc:
        print(f"  ! {src['id']}: semantic scholar failed ({exc})")
        return []
    return [_s2_record(row.get("citingPaper", {}), f"cites {src['id']}") for row in rows]


def watch_semantic_scholar_search(src: dict, state: dict) -> list[dict]:
    url = ("https://api.semanticscholar.org/graph/v1/paper/search"
           f"?query={urllib.parse.quote(src['query'])}"
           "&fields=title,abstract,year,authors,externalIds,url&limit=20")
    try:
        r = _get(url)
        r.raise_for_status()
        rows = r.json().get("data", [])
    except Exception as exc:
        print(f"  ! {src['id']}: semantic scholar search failed ({exc})")
        return []
    return [_s2_record(row, f"search: {src['query']}") for row in rows]


def _s2_record(paper: dict, via: str) -> dict:
    ids = paper.get("externalIds") or {}
    authors = ", ".join(a.get("name", "") for a in (paper.get("authors") or [])[:4])
    return dict(kind="candidate", title=paper.get("title") or "",
                abstract=(paper.get("abstract") or "")[:1500],
                url=paper.get("url") or "", doi=(ids.get("DOI") or ""),
                authors=authors, venue=paper.get("venue") or "Semantic Scholar",
                year=paper.get("year"), discovered_via=via)


# ---------- Tier B ----------

def arxiv_search(query: str, categories: list[str], limit: int) -> list[dict]:
    cat = " OR ".join(f"cat:{c}" for c in categories)
    search = f"({cat}) AND all:{query}"
    url = ("http://export.arxiv.org/api/query?search_query="
           f"{urllib.parse.quote(search)}&sortBy=submittedDate&sortOrder=descending&max_results={limit}")
    try:
        r = _get(url)
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception as exc:
        print(f"  ! arxiv failed ({exc})")
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("a:entry", ns):
        def txt(tag):
            el = entry.find(f"a:{tag}", ns)
            return (el.text or "").strip() if el is not None else ""
        authors = ", ".join((a.findtext("a:name", default="", namespaces=ns) or "")
                            for a in entry.findall("a:author", ns)[:4])
        out.append(dict(kind="candidate", title=txt("title"), abstract=txt("summary")[:1500],
                        url=txt("id"), doi="", authors=authors, venue="arXiv preprint",
                        year=int(txt("published")[:4]) if txt("published")[:4].isdigit() else None,
                        discovered_via=f"arXiv: {query}"))
    return out


def openalex_search(query: str, days: int, limit: int) -> list[dict]:
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    url = ("https://api.openalex.org/works?filter=from_publication_date:"
           f"{since}&search={urllib.parse.quote(query)}&per-page={limit}"
           "&mailto=dominique.charlie@intentionaldata.org")
    try:
        r = _get(url)
        r.raise_for_status()
        rows = r.json().get("results", [])
    except Exception as exc:
        print(f"  ! openalex failed ({exc})")
        return []
    out = []
    for w in rows:
        authors = ", ".join((a.get("author") or {}).get("display_name", "")
                            for a in (w.get("authorships") or [])[:4])
        host = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "OpenAlex"
        out.append(dict(kind="candidate", title=w.get("title") or "",
                        abstract=(_invert(w.get("abstract_inverted_index")) or "")[:1500],
                        url=w.get("doi") or w.get("id") or "",
                        doi=(w.get("doi") or "").replace("https://doi.org/", ""),
                        authors=authors, venue=host,
                        year=w.get("publication_year"), discovered_via=f"OpenAlex: {query}"))
    return out


def _invert(idx):
    if not idx:
        return ""
    positions = {}
    for word, spots in idx.items():
        for s in spots:
            positions[s] = word
    return " ".join(positions[k] for k in sorted(positions))


# ---------- driver ----------

WATCHERS = {"page_hash": watch_page_hash, "crossref": watch_crossref,
            "semantic_scholar_citations": watch_semantic_scholar_citations,
            "semantic_scholar_search": watch_semantic_scholar_search}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="skip network, prove wiring")
    ap.add_argument("--skip-tier-b", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_yaml("sources.yaml")
    state = seen()
    found: list[dict] = []

    if args.dry_run:
        print("dry run: no network calls made")
        save_json(DATA / "pending_raw.json", [])
        return 0

    print("Tier A, watching the evidence base")
    for src in cfg.get("tier_a", []):
        fn = WATCHERS.get(src.get("method", ""))
        if not fn:
            print(f"  ! unknown method for {src.get('id')}")
            continue
        got = fn(src, state)
        if got:
            print(f"  {src['id']}: {len(got)} item(s)")
        found.extend(got)
        polite_sleep()

    if not args.skip_tier_b:
        print("Tier B, discovering new work")
        tb = cfg.get("tier_b", {})
        for q in tb.get("queries", []):
            found.extend(arxiv_search(q, tb.get("arxiv_categories", []), tb.get("max_per_query", 15)))
            polite_sleep()
            found.extend(openalex_search(q, tb.get("lookback_days", 30), tb.get("max_per_query", 15)))
            polite_sleep()

    # dedupe against seen and within this run
    fresh, batch_keys = [], set()
    for item in found:
        if item.get("kind") == "tier_a_change":
            fresh.append(item)
            continue
        key = fingerprint(item)
        if key in state.get("fingerprints", {}) or key in batch_keys:
            continue
        if not item.get("title"):
            continue
        batch_keys.add(key)
        item["fingerprint"] = key
        fresh.append(item)

    save_json(DATA / "pending_raw.json", fresh)
    save_json(DATA / "seen.json", state)
    print(f"\n{len(fresh)} item(s) to score, written to data/pending_raw.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
