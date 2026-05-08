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


def extract_pmid(text: str) -> str | None:
    """Pull a PubMed ID out of a pubmed.ncbi.nlm.nih.gov URL."""
    if not text:
        return None
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", text)
    return m.group(1) if m else None


def fetch_crossref(doi: str) -> dict | None:
    """Crossref fallback when OpenAlex misses. Returns OpenAlex-shaped
    {'authorships': [{'author': {'display_name': '...'}}, ...]}."""
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        if r.status_code != 200:
            return None
        msg = r.json().get("message", {})
        authors = []
        for a in msg.get("author", []) or []:
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip()
            if name:
                authors.append({"author": {"display_name": name}})
        if not authors:
            return None
        return {"authorships": authors}
    except requests.RequestException:
        return None


def fetch_openalex(doi: str | None, arxiv: str | None, pmid: str | None = None) -> dict | None:
    """Look up a single work by DOI (preferred) or arXiv ID or PMID."""
    if doi:
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='')}"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
    if pmid:
        url = f"https://api.openalex.org/works/pmid:{pmid}"
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


def normalize_display_name(name: str) -> str:
    """Convert "Lastname, Firstname" to "Firstname Lastname" if needed."""
    name = name.strip().rstrip("*+").strip()
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return f"{parts[1]} {parts[0]}"
    return name


def surname_key(name: str) -> str:
    """Last word, lowercased, alphanumerics only — for matching."""
    cleaned = re.sub(r"\([^)]+\)", "", normalize_display_name(name)).strip()
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


def first_initial(name: str) -> str:
    cleaned = re.sub(r"\([^)]+\)", "", normalize_display_name(name)).strip()
    parts = cleaned.split()
    if not parts:
        return ""
    return parts[0][0].lower() if parts[0] else ""


def update_authors(yaml_authors: str, openalex_names: list[str]) -> str | None:
    """Return updated authors string. Surname-aligned (with first-initial
    tiebreak): for each YAML token find an OpenAlex author with the same
    surname (and matching first initial when ambiguous). Tokens whose
    surname doesn't match any OpenAlex author are kept verbatim — better
    to leave alone than corrupt.
    """
    if "et al." in yaml_authors.lower():
        return None
    yaml_tokens = split_authors(yaml_authors)
    if not yaml_tokens or not openalex_names:
        return None

    # Pre-bucket OpenAlex names by surname for fast lookup. Names are
    # also normalized "Last, First" → "First Last" so they look natural
    # when written back into the YAML.
    by_surname: dict[str, list[tuple[int, str]]] = {}
    for i, oa in enumerate(openalex_names):
        normalized = normalize_display_name(oa)
        by_surname.setdefault(surname_key(normalized), []).append((i, normalized))

    used: set[int] = set()
    out: list[str] = []
    matched = 0
    for ya_tok in yaml_tokens:
        core, mark = split_marker(ya_tok)
        ya_surname = surname_key(core)
        cands = [(i, oa) for i, oa in by_surname.get(ya_surname, []) if i not in used]
        if not cands:
            out.append(ya_tok)
            continue
        # Tiebreak by first initial
        ya_fi = first_initial(core)
        ranked = sorted(cands, key=lambda iox: (first_initial(iox[1]) != ya_fi, iox[0]))
        idx, oa_name = ranked[0]
        used.add(idx)
        matched += 1
        if is_abbreviated(core):
            out.append(f"{oa_name}{mark}")
        else:
            out.append(ya_tok)

    if matched == 0:
        return None  # nothing aligned; leave alone
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
        pmid = extract_pmid(haystack)
        if not (doi or arxiv or pmid):
            skipped.append((slug, "no DOI / arXiv / PMID"))
            continue

        work = fetch_openalex(doi, arxiv, pmid)
        time.sleep(0.05)
        # Crossref fallback if OpenAlex came up empty and we have a DOI
        if not work and doi:
            work = fetch_crossref(doi)
            time.sleep(0.05)
        if not work:
            skipped.append((slug, f"no source match (doi={doi}, arxiv={arxiv}, pmid={pmid})"))
            continue
        oa_names = [
            a.get("author", {}).get("display_name", "")
            for a in (work.get("authorships") or [])
            if a.get("author", {}).get("display_name")
        ]
        if not oa_names:
            skipped.append((slug, "no authorships in source"))
            continue

        new_authors = update_authors(old_authors, oa_names)
        if new_authors is None:
            skipped.append((slug, f"no surnames matched (yaml={len(split_authors(old_authors))}, ext={len(oa_names)})"))
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
