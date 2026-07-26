"""Build and optionally send the weekly digest.

python -m src.digest            # writes output/digest.md and prints it
python -m src.digest --send     # also emails it (needs SMTP_* env vars)
"""
from __future__ import annotations
import argparse, os, smtplib, sys
from email.message import EmailMessage

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .common import DATA, OUTPUT, TEMPLATES, load_yaml, pending, today, check_house_style


def build() -> tuple[str, int]:
    cfg = load_yaml("sources.yaml")
    items = pending()
    changes = [i for i in items if i.get("kind") == "tier_a_change"]
    cands = [i for i in items if i.get("kind") != "tier_a_change"]
    rec_t = cfg["scoring"]["recommend_threshold"]
    recommended = sorted([i for i in cands if i.get("relevance_score", 0) >= rec_t],
                         key=lambda i: -i.get("relevance_score", 0))
    worth = sorted([i for i in cands if i.get("relevance_score", 0) < rec_t],
                   key=lambda i: -i.get("relevance_score", 0))

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    text = env.get_template("digest.md.j2").render(
        date=today(), changes=changes, recommended=recommended, worth=worth,
        total=len(items), branding=load_yaml("branding.yaml"))

    problems = check_house_style(text)
    if problems:
        print("house style warnings in digest: " + "; ".join(problems))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "digest.md").write_text(text, encoding="utf-8")
    return text, len(items)


def send(text: str, n: int) -> None:
    cfg = load_yaml("sources.yaml")["digest"]
    host, user, pw = (os.environ.get("SMTP_HOST"), os.environ.get("SMTP_USER"),
                      os.environ.get("SMTP_PASSWORD"))
    if not all([host, user, pw]):
        print("SMTP_HOST, SMTP_USER and SMTP_PASSWORD are required to send. Nothing sent.")
        return
    msg = EmailMessage()
    msg["Subject"] = cfg["subject_template"].format(n=n)
    msg["From"] = user
    msg["To"] = cfg["to"]
    msg.set_content(text)
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port) as s:
        s.login(user, pw)
        s.send_message(msg)
    print(f"digest sent to {cfg['to']}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    args = ap.parse_args(argv)
    text, n = build()
    print(text)
    if n == 0:
        print("\nzero items this week, nothing to send")
        return 0
    if args.send:
        send(text, n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
