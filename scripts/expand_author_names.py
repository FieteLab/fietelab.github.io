#!/usr/bin/env python3
"""For each paper in publications/content.yaml, fetch full author names
from OpenAlex and replace the abbreviated tokens in the YAML's `authors:`
field. Lab-member full names + co-first/co-senior markers are preserved.

Skips:
- Papers with "et al." in the authors string (consortium / IBL papers).
- Papers where we can't locate a DOI / arXiv / OpenAlex ID.
- Papers whose OpenAlex author count differs from our YAML count (likely
  truncation or shuffled ordering — prefer to leave alone over corrupt).
- Tokens whose surname doesn't match OpenAlex's at the same position.

Usage:
    pip install -r scripts/requirements.txt
    python scripts/expand_author_names.py            # writes in place
    python scripts/expand_author_names.py --dry-run  # report only
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse
from pathlib import Path

try:
    import requests
    import yaml
except ImportError as e:
    sys.exit(f"missing dep: {e.name}.  pip install -r scripts/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
PUBS_FILE = ROOT / "src" / "content" / "publications" / "content.yaml"
USER_AGENT = "fietelab-website-sync/0.1 (mailto:fietelabcolab@gmail.com)"

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
ARXIV_RE = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")


def normalize_doi(doi: str) -> str:
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip(), flags=re.I)
    return doi.lower().rstrip(".")


def extract_doi(text: str) -> str | None:
    if not text:
        return None
    m = DOI_RE.search(text)
    if m:
        return normalize_doi(m.group(0))
    m = re.search(r"nature\.com/articles/([^/?#\"]+)", text)
    if m:
        return normalize_doi(f"10.1038/{m.group(1)}")
    m = re.search(r"elifesciences\.org/articles/(\d+)", text)
    if m:
        return normalize_doi(f"10.7554/eLife.{m.group(1)}")
    return None


def extract_arxiv(text: str) -> str | None:
    if not text:
        return None
    m = ARXIV_RE.search(text)
    return m.group(1).lower() if m else None


def fetch_openalex(doi: str | None, arxiv: str | None) -> dict | None:
    """Look up a single work by DOI (preferred) or arXiv ID."""
    if doi:
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='')}"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
    if arxiv:
        # OpenAlex indexes arXiv preprints as DOI 10.48550/arXiv.<id>
        for variant in (f"10.48550/arxiv.{arxiv}", f"10.48550/arxiv.{arxiv.upper()}"):
            url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(variant, safe='')}"
            try:
                r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
                if r.status_code == 200:
                    return r.json()
            except requests.RequestException:
                pass
        # Fallback: full-text search
        params = {
            "search": f"arXiv:{arxiv}",
            "per-page": 5,
            "select": "id,title,authorships,doi",
        }
        url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code == 200:
                for hit in r.json().get("results", []):
                    hit_doi = (hit.get("doi") or "").lower()
                    if arxiv in hit_doi or f"arxiv.{arxiv}" in hit_doi:
                        return hit
        except requests.RequestException:
            pass
    return None


def surname_key(name: str) -> str:
    """Last word, lowercased, alphanumerics only — for matching."""
    cleaned = re.sub(r"\([^)]+\)", "", name).strip().rstrip("*+").strip()
    tokens = cleaned.split()
    if not tokens:
        return ""
    return re.sub(r"[^a-z]", "", tokens[-1].lower())


def is_abbreviated(token: str) -> bool:
    """A token is 'abbreviated' if its first whitespace-separated piece is
    a single capital + period (e.g. "Y.") or two letters + period
    ("YR." — unlikely)."""
    cleaned = re.sub(r"\([^)]+\)", "", token).strip()
    parts = cleaned.split()
    if not parts:
        return False
    first = parts[0]
    # Already full if first part is ≥ 3 chars, mixed case, no period
    if len(first) >= 3 and re.search(r"[a-z]", first) and not first.endswith("."):
        return False
    return True


def split_authors(s: str) -> list[str]:
    """Split a comma-separated authors string, preserving 'et al.'
    parenthetical groups."""
    return [t.strip() for t in s.split(",") if t.strip()]


def split_marker(token: str) -> tuple[str, str]:
    """Return (core, trailing-markers). Markers are * or +."""
    m = re.match(r"^(.*?)([\*\+]+)\s*$", token)
    if not m:
        return token, ""
    return m.group(1).strip(), m.group(2)


def update_authors(yaml_authors: str, openalex_names: list[str]) -> str | None:
    """Return updated authors string, or None if we couldn't safely match."""
    if "et al." in yaml_authors.lower():
        return None
    yaml_tokens = split_authors(yaml_authors)
    if len(yaml_tokens) != len(openalex_names):
        return None  # count mismatch; bail

    out = []
    for ya_tok, oa_name in zip(yaml_tokens, openalex_names):
        core, mark = split_marker(ya_tok)
        if surname_key(core) != surname_key(oa_name):
            # Surname mismatch at this position; ordering may differ.
            # Keep ours rather than risk corruption.
            out.append(ya_tok)
            continue
        if is_abbreviated(core):
            out.append(f"{oa_name}{mark}")
        else:
            out.append(ya_tok)
    return ", ".join(out)


def parse_yaml_blocks(text: str):
    """Yield (slug, body, start, end) for each top-level entry."""
    starts = [m.start() for m in re.finditer(r"(?m)^[a-z][a-zA-Z0-9_-]*:\s*$", text)]
    starts.append(len(text))
    for i in range(len(starts) - 1):
        block = text[starts[i] : starts[i + 1]]
        m = re.match(r"^([a-z][a-zA-Z0-9_-]*):", block)
        if m:
            yield m.group(1), block, starts[i], starts[i + 1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", help="Limit to specific slugs.")
    args = ap.parse_args()

    text = PUBS_FILE.read_text()

    updates: list[tuple[str, str, str, int, int]] = []  # (slug, old, new, start, end)
    skipped = []

    for slug, body, start, end in parse_yaml_blocks(text):
        if args.only and slug not in args.only:
            continue
        title_m = re.search(r'^  title:\s*"(.+?)"\s*$', body, re.M)
        authors_m = re.search(r'^  authors:\s*"(.+?)"\s*$', body, re.M)
        link_m = re.search(r'^  link:\s*"(.+?)"\s*$', body, re.M)
        citation_m = re.search(r'^  citation:\s*"(.+?)"\s*$', body, re.M)
        if not (title_m and authors_m):
            continue
        old_authors = authors_m.group(1)
        if "et al." in old_authors.lower():
            skipped.append((slug, "has 'et al.'"))
            continue

        haystack = " ".join(filter(None, [
            link_m.group(1) if link_m else "",
            citation_m.group(1) if citation_m else "",
        ]))
        doi = extract_doi(haystack)
        arxiv = extract_arxiv(haystack)
        if not (doi or arxiv):
            skipped.append((slug, "no DOI / arXiv ID"))
            continue

        work = fetch_openalex(doi, arxiv)
        time.sleep(0.05)
        if not work:
            skipped.append((slug, f"OpenAlex no match (doi={doi}, arxiv={arxiv})"))
            continue
        oa_names = [
            a.get("author", {}).get("display_name", "")
            for a in (work.get("authorships") or [])
            if a.get("author", {}).get("display_name")
        ]
        if not oa_names:
            skipped.append((slug, "OpenAlex has no authorships"))
            continue

        new_authors = update_authors(old_authors, oa_names)
        if new_authors is None:
            skipped.append((slug, f"count mismatch (yaml={len(split_authors(old_authors))}, openalex={len(oa_names)})"))
            continue
        if new_authors == old_authors:
            continue  # no abbreviated tokens or all surnames mismatched

        # Locate the exact line offset of the authors: ... in `text`
        au_re = re.compile(r'^(  authors:\s*")' + re.escape(old_authors) + r'(")\s*$', re.M)
        match = au_re.search(text, start, end)
        if not match:
            skipped.append((slug, "could not locate authors line"))
            continue
        updates.append((slug, old_authors, new_authors, match.start(2) - len(old_authors), match.start(2)))

    # Print report
    print(f"\n{'='*70}\n{len(updates)} entries to update; {len(skipped)} skipped\n{'='*70}")
    for slug, old, new, *_ in updates[:80]:
        print(f"\n• {slug}")
        print(f"   was: {old[:200]}")
        print(f"   now: {new[:200]}")
    if skipped:
        print(f"\nSkipped ({len(skipped)}):")
        for slug, why in skipped[:20]:
            print(f"  {slug:40s}  {why}")

    if args.dry_run:
        return 0

    # Apply rewrites in reverse so offsets stay valid
    new_text = text
    for slug, old, new, lo, hi in sorted(updates, key=lambda u: -u[3]):
        new_text = new_text[:lo] + new + new_text[hi:]

    if new_text != text:
        PUBS_FILE.write_text(new_text)
        print(f"\nWrote {len(updates)} updates to {PUBS_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
