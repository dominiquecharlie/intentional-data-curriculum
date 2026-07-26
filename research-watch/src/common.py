"""Shared helpers for Research Watch."""
from __future__ import annotations
import json, os, re, hashlib, datetime, time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config"
OUTPUT = ROOT / "output"
TEMPLATES = ROOT / "templates"

SEGMENTS = ["W1-S1", "W1-S2", "W2-S1", "W2-S2", "W3-S1", "W3-S2",
            "toolkit-diagnostic", "toolkit-sorting", "toolkit-rubric",
            "toolkit-charter", "toolkit-report"]

SEGMENT_LABELS = {
    "W1-S1": "Workshop 1, core content",
    "W1-S2": "Workshop 1, responsible use",
    "W2-S1": "Workshop 2, the fiduciary frame",
    "W2-S2": "Workshop 2, governance architecture",
    "W3-S1": "Workshop 3, the evaluation rubric",
    "W3-S2": "Workshop 3, scoring a real tool",
    "toolkit-diagnostic": "Toolkit, literacy diagnostic",
    "toolkit-sorting": "Toolkit, scenario sorting worksheet",
    "toolkit-rubric": "Toolkit, tool evaluation rubric",
    "toolkit-charter": "Toolkit, governance charter",
    "toolkit-report": "Toolkit, upskilling report",
}

BANNED_PHRASES = [
    (re.compile(r",\s+not\s+(?:a|an|the)?\s*[a-z]"), 'the "X, not Y" construction'),
    (re.compile(r"\brather than\b"), '"rather than" contrast'),
]


def today() -> str:
    return datetime.date.today().isoformat()


def load_yaml(name: str) -> dict:
    with open(CONFIG / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def registry():
    return load_json(DATA / "registry.json", [])


def seen():
    return load_json(DATA / "seen.json", {})


def pending():
    return load_json(DATA / "pending.json", [])


def normalise_url(url: str) -> str:
    if not url:
        return ""
    u = url.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("?")[0].split("#")[0].rstrip("/")
    return u


def fingerprint(item: dict) -> str:
    """Dedupe key: DOI first, then normalised URL, then title hash."""
    doi = (item.get("doi") or "").strip().lower()
    if doi:
        return "doi:" + doi
    url = normalise_url(item.get("url", ""))
    if url:
        return "url:" + url
    title = re.sub(r"\W+", " ", (item.get("title") or "").lower()).strip()
    return "title:" + hashlib.sha256(title.encode()).hexdigest()[:20]


def check_house_style(text: str) -> list[str]:
    """Return a list of house-style violations found in generated text."""
    problems = []
    if "—" in text or "–" in text:
        problems.append("contains an em dash or en dash")
    for pattern, label in BANNED_PHRASES:
        if pattern.search(text):
            problems.append(f"contains {label}")
    branding = load_yaml("branding.yaml")
    for banned in branding.get("banned_strings", []):
        # word-boundary match so "ARCH" does not fire inside "Research"
        if re.search(rf"(?<![A-Za-z]){re.escape(banned)}(?![A-Za-z])", text, re.I):
            problems.append(f"contains banned string {banned!r}")
    return problems


def polite_sleep(seconds: float = 1.0) -> None:
    time.sleep(seconds)
