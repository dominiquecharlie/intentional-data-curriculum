"""Render the internal stream view: which sources feed which line of work.

python -m src.streams          # writes output/streams.md
python -m src.streams --print  # to stdout

Internal only. Never published, never injected into the citation reference.
The public page stays curriculum-facing; see templates/reference.md.j2.
"""
from __future__ import annotations
import argparse, sys

from .common import OUTPUT, registry, today, check_house_style

STREAMS = [
    ("curriculum", "Curriculum", "Co-Produced AI Governance workshop series and toolkit"),
    ("rootwork", "Rootwork", "Community data infrastructure"),
    ("case_management", "Case management", "Custom software clients own outright"),
]


def build() -> str:
    recs = [r for r in registry() if r.get("status", "active") == "active"]
    order = {"foundational": 0, "standard": 1, "policy": 2, "context": 3, "supporting": 4}
    recs.sort(key=lambda r: (order.get(r.get("type"), 9), r.get("id", "")))

    lines = ["# Stream view", "",
             "Which sources feed which line of work. Generated from `data/registry.json` "
             f"by `python -m src.streams`. Last regenerated {today()}.", "",
             "**Internal.** The public citation reference renders the curriculum column only.", ""]

    # coverage matrix
    lines += ["## Coverage", "",
              "| Source | " + " | ".join(n for _, n, _ in STREAMS) + " |",
              "|---|" + "---|" * len(STREAMS)]
    for r in recs:
        marks = ["yes" if k in r.get("applies_to", {}) else "" for k, _, _ in STREAMS]
        lines.append(f"| {r['title']} | " + " | ".join(marks) + " |")
    lines.append("")

    for key, name, blurb in STREAMS:
        hits = [r for r in recs if key in r.get("applies_to", {})]
        lines += [f"## {name}", "", f"{blurb}. {len(hits)} of {len(recs)} sources.", ""]
        if not hits:
            lines += ["Nothing mapped yet.", ""]
            continue
        for r in hits:
            entry = r["applies_to"][key]
            refs = ", ".join(entry.get("refs") or []) or "stream level"
            note = entry.get("note") or r.get("why_it_matters", "")
            lines += [f"### {r['title']}", "",
                      f"{note}", "",
                      f"Refs: {refs}. Type: {r.get('type')}. <{r.get('url','')}>", ""]

    unmapped = [r for r in recs if len(r.get("applies_to", {})) == 1]
    lines += ["## Curriculum only", "",
              "Sources with no Rootwork or case management application recorded. "
              "Revisit when those work streams take shape.", ""]
    lines += [f"- {r['title']}" for r in unmapped] or ["- none"]
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args(argv)

    md = build()
    problems = check_house_style(md)
    if problems:
        print("HOUSE STYLE FAILURE: " + "; ".join(problems))
        return 1

    if args.to_stdout:
        print(md)
        return 0
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "streams.md").write_text(md, encoding="utf-8")
    print("wrote output/streams.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
