"""Regenerate the foundations block and a markdown reference from registry.json.

python -m src.render                       # writes output/foundations.html and output/reference.md
python -m src.render --inject PATH         # splices the block into a citation reference page

The interactive segment map in the citation reference stays hand maintained.
Research Watch owns the sources list only.
"""
from __future__ import annotations
import argparse, re, sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .common import OUTPUT, TEMPLATES, load_yaml, registry, today, check_house_style

START = "<!-- research-watch:foundations:start -->"
END = "<!-- research-watch:foundations:end -->"


def _env():
    return Environment(loader=FileSystemLoader(TEMPLATES),
                       autoescape=select_autoescape(["html", "j2"]),
                       trim_blocks=True, lstrip_blocks=True)


def render() -> tuple[str, str]:
    recs = [r for r in registry()
            if r.get("status", "active") == "active" and r.get("type") != "context"]
    order = {"foundational": 0, "standard": 1, "policy": 2, "supporting": 3}
    recs.sort(key=lambda r: (order.get(r.get("type"), 9), r.get("id", "")))
    branding = load_yaml("branding.yaml")
    env = _env()
    html = env.get_template("foundations.html.j2").render(
        records=recs, branding=branding, generated=today(), count=len(recs))
    md = env.get_template("reference.md.j2").render(
        records=recs, branding=branding, generated=today(), count=len(recs))
    return html, md


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inject", metavar="PATH", help="citation reference page to splice into")
    args = ap.parse_args(argv)

    html, md = render()

    problems = check_house_style(re.sub(r"<[^>]+>", " ", html))
    if problems:
        print("HOUSE STYLE FAILURE: " + "; ".join(problems))
        return 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "foundations.html").write_text(html, encoding="utf-8")
    (OUTPUT / "reference.md").write_text(md, encoding="utf-8")
    print(f"wrote output/foundations.html and output/reference.md ({html.count('fnd-row')} sources)")

    if args.inject:
        target = args.inject
        with open(target, encoding="utf-8") as fh:
            page = fh.read()
        block = f"{START}\n{html}\n{END}"
        if START in page and END in page:
            page = re.sub(re.escape(START) + r".*?" + re.escape(END), block, page, flags=re.S)
        else:
            # match the whole block: from the opening div up to the footer that follows it
            m = re.search(r'<div class="foundations">.*?(?=\n*<div class="footer-note">)', page, re.S)
            if not m:
                print(f"! could not find an insertion point in {target}. "
                      f"Add {START} and {END} markers where the block belongs.")
                return 1
            page = page[:m.start()] + block + page[m.end():]
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(page)
        print(f"injected the foundations block into {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
