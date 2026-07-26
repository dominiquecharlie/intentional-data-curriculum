"""Approve or reject pending items. Nothing enters the registry without this step.

python -m src.approve            # interactive
python -m src.approve --list     # show pending without deciding
"""
from __future__ import annotations
import argparse, sys

from .common import (DATA, SEGMENTS, SEGMENT_LABELS, pending, registry, save_json,
                     seen, today)


def _show(item: dict, i: int, n: int) -> None:
    print("\n" + "=" * 72)
    print(f"[{i}/{n}]  score {item.get('relevance_score','-')}/10   {item.get('title','')}")
    print(f"        {item.get('authors','')} | {item.get('venue','')} {item.get('year','') or ''}")
    print(f"        {item.get('url','')}")
    if item.get("summary"):
        print(f"\n  Summary:   {item['summary']}")
    if item.get("score_rationale"):
        print(f"  Rationale: {item['score_rationale']}")
    if item.get("suggested_segments"):
        print(f"  Segments:  {', '.join(item['suggested_segments'])}")
    if item.get("note"):
        print(f"  Note:      {item['note']}")


def _ask_segments(current: list[str]) -> list[str]:
    print("\n  Segment ids:")
    for s in SEGMENTS:
        print(f"    {s:22} {SEGMENT_LABELS[s]}")
    raw = input(f"  Segments [{', '.join(current) or 'none'}]: ").strip()
    if not raw:
        return current
    chosen = [s.strip() for s in raw.replace(",", " ").split() if s.strip() in SEGMENTS]
    return chosen or current


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    items = pending()
    if not items:
        print("nothing pending")
        return 0

    if args.list:
        for i, it in enumerate(items, 1):
            _show(it, i, len(items))
        return 0

    reg = registry()
    known = {r["id"] for r in reg}
    state = seen()
    state.setdefault("fingerprints", {})
    remaining, approved, rejected = [], 0, 0

    for i, item in enumerate(items, 1):
        _show(item, i, len(items))
        if item.get("kind") == "tier_a_change":
            print("\n  This is a change notice on an existing source. Nothing is added to the registry.")
            ans = input("  [d]ismiss, [s]kip for next week: ").strip().lower() or "d"
            if ans.startswith("s"):
                remaining.append(item)
            continue

        ans = input("\n  [a]pprove, [r]eject, [s]kip, [q]uit: ").strip().lower()
        if ans.startswith("q"):
            remaining.extend(items[i - 1:])
            break
        if ans.startswith("s"):
            remaining.append(item)
            continue
        if ans.startswith("r"):
            reason = input("  reason (optional): ").strip()
            key = item.get("fingerprint") or item.get("url", "")
            state["fingerprints"][key] = {"title": item.get("title", ""),
                                          "reason": reason or "rejected at review",
                                          "date": today()}
            rejected += 1
            continue

        segs = _ask_segments(item.get("suggested_segments", []))
        new_id = input("  registry id: ").strip() or item.get("fingerprint", "")[:40]
        if new_id in known:
            print(f"  ! id {new_id} already exists, skipping")
            remaining.append(item)
            continue
        reg.append({"id": new_id, "title": item.get("title", ""),
                    "authors": item.get("authors", ""), "venue": item.get("venue", ""),
                    "year": item.get("year"), "url": item.get("url", ""),
                    "doi": item.get("doi", ""), "type": "supporting",
                    "applies_to": {"curriculum": {"refs": segs, "note": ""}},
                    "summary": item.get("summary", ""),
                    "why_it_matters": input("  why it matters (1 sentence): ").strip(),
                    "added": today(), "last_verified": today(),
                    "status": "active", "superseded_by": None})
        known.add(new_id)
        key = item.get("fingerprint") or item.get("url", "")
        state["fingerprints"][key] = {"title": item.get("title", ""),
                                      "reason": "approved", "date": today()}
        approved += 1

    save_json(DATA / "registry.json", reg)
    save_json(DATA / "pending.json", remaining)
    save_json(DATA / "seen.json", state)
    print(f"\napproved {approved}, rejected {rejected}, {len(remaining)} left pending")
    if approved:
        print("run: python -m src.render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
