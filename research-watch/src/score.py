"""Score candidates against the relevance rubric.

python -m src.score            # scores data/pending_raw.json into data/pending.json
python -m src.score --offline  # wiring test with a deterministic stub scorer

Needs ANTHROPIC_API_KEY in the environment for real scoring.
"""
from __future__ import annotations
import argparse, json, os, re, sys

from .common import DATA, CONFIG, load_yaml, load_json, save_json, seen, today, SEGMENTS


def _rubric() -> str:
    return (CONFIG / "rubric.md").read_text(encoding="utf-8")


def _prompt(item: dict) -> str:
    return (f"Title: {item.get('title','')}\n"
            f"Authors: {item.get('authors','')}\n"
            f"Venue: {item.get('venue','')} ({item.get('year','')})\n"
            f"Abstract: {item.get('abstract','')[:1200]}\n\n"
            "Score this item.")


def _coerce(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"no JSON in model reply: {raw[:200]}")
    data = json.loads(m.group(0))
    score = int(data.get("score", 0))
    segs = [s for s in (data.get("suggested_segments") or []) if s in SEGMENTS]
    return {"relevance_score": max(0, min(10, score)),
            "score_rationale": str(data.get("rationale", ""))[:600],
            "suggested_segments": segs,
            "summary": str(data.get("summary", ""))[:400]}


def score_with_api(items: list[dict], model: str) -> list[dict]:
    import anthropic
    client = anthropic.Anthropic()
    rubric = _rubric()
    out = []
    for i, item in enumerate(items, 1):
        try:
            resp = client.messages.create(
                model=model, max_tokens=400, system=rubric,
                messages=[{"role": "user", "content": _prompt(item)}])
            item.update(_coerce(resp.content[0].text))
        except Exception as exc:
            print(f"  ! scoring failed for {item.get('title','')[:60]}: {exc}")
            item.update({"relevance_score": 0, "score_rationale": f"scoring error: {exc}",
                         "suggested_segments": [], "summary": ""})
        out.append(item)
        print(f"  [{i}/{len(items)}] {item['relevance_score']:>2}/10  {item.get('title','')[:70]}")
    return out


def score_offline(items: list[dict]) -> list[dict]:
    """Deterministic stub so the pipeline can be exercised without an API key."""
    keywords = ("nonprofit", "governance", "literacy", "community", "participatory",
                "co-production", "public sector", "board")
    for item in items:
        blob = f"{item.get('title','')} {item.get('abstract','')}".lower()
        hits = sum(1 for k in keywords if k in blob)
        item.update({"relevance_score": min(10, hits * 2),
                     "score_rationale": f"offline stub scorer matched {hits} curriculum keyword(s).",
                     "suggested_segments": [], "summary": item.get("title", "")[:200]})
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="stub scorer, no API key needed")
    args = ap.parse_args(argv)

    cfg = load_yaml("sources.yaml")
    raw = load_json(DATA / "pending_raw.json", [])
    changes = [i for i in raw if i.get("kind") == "tier_a_change"]
    candidates = [i for i in raw if i.get("kind") != "tier_a_change"]

    if not candidates:
        print("no candidates to score")
    elif args.offline or not os.environ.get("ANTHROPIC_API_KEY"):
        if not args.offline:
            print("ANTHROPIC_API_KEY not set, falling back to the offline stub scorer")
        candidates = score_offline(candidates)
    else:
        candidates = score_with_api(candidates, cfg["scoring"]["model"])

    drop = cfg["scoring"]["worth_a_look_threshold"]
    state = seen()
    state.setdefault("fingerprints", {})
    kept = []
    for item in candidates:
        item["discovered_date"] = today()
        if item.get("relevance_score", 0) < drop:
            state["fingerprints"][item.get("fingerprint", item.get("url", ""))] = {
                "title": item.get("title", ""), "score": item.get("relevance_score", 0),
                "reason": "below threshold", "date": today()}
        else:
            kept.append(item)

    save_json(DATA / "pending.json", changes + kept)
    save_json(DATA / "seen.json", state)
    print(f"{len(kept)} candidate(s) kept, {len(changes)} Tier A change(s), "
          f"{len(candidates) - len(kept)} dropped below threshold {drop}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
