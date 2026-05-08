#!/usr/bin/env python3
"""For every paper in publications/content.yaml whose venue is still
arXiv / bioRxiv / preprint, ask OpenAlex whether a journal or
conference version of the same paper now exists. Reports candidates;
does NOT modify the YAML.

Strategy: for each preprint entry, fetch its OpenAlex record by
DOI/arXiv and walk every `locations[]` entry. If any location's
host_source has type 'journal' or 'conference' (i.e. not 'repository'
which is what arXiv/bioRxiv are tagged as), that's a published
version. Also check `versions[]` of related works.

Usage:
    python scripts/check_published.py
"""

from __future__ import annotations

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
    return None


def extract_arxiv(text: str) -> str | None:
    if not text:
        return None
    m = ARXIV_RE.search(text)
    return m.group(1).lower() if m else None


def is_preprint_venue(venue: str) -> bool:
    v = (venue or "").lower()
    return any(t in v for t in ("arxiv", "biorxiv", "preprint", "openreview"))


def fetch_openalex(doi: str | None, arxiv: str | None) -> dict | None:
    if doi:
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='')}"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
    if arxiv:
        url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(f'10.48550/arxiv.{arxiv}', safe='')}"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
    return None


def find_journal_version(work: dict) -> dict | None:
    """If a work has any location whose source.type is journal/conference,
    return a dict {venue, doi, year, type}. Otherwise None."""
    candidates: list[dict] = []
    for loc in [work.get("primary_location")] + (work.get("locations") or []):
        if not loc:
            continue
        src = loc.get("source") or {}
        stype = (src.get("type") or "").lower()
        name = src.get("display_name", "")
        if not name:
            continue
        if stype in ("journal", "conference"):
            candidates.append({
                "venue": name,
                "doi": (loc.get("doi") or work.get("doi") or "").replace("https://doi.org/", ""),
                "year": work.get("publication_year"),
                "type": stype,
                "url": loc.get("landing_page_url"),
            })
    if not candidates:
        return None
    # Prefer journal over conference (more "published" feeling)
    candidates.sort(key=lambda c: 0 if c["type"] == "journal" else 1)
    return candidates[0]


def search_openalex_by_title(
    title: str,
    expected_first_surname: str,
    expected_year: int,
    doi_to_skip: str | None = None,
) -> dict | None:
    """Fallback: search OpenAlex by title and look for a non-preprint
    Work that ALSO has a matching first-author surname AND was published
    in the same year or later than our preprint. Without these guards
    the search returns lots of loose-match false positives."""
    if not title or not expected_first_surname:
        return None
    params = {
        "search": title[:200],
        "per-page": 5,
        "select": "id,title,doi,publication_year,primary_location,locations,authorships",
    }
    url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        if r.status_code != 200:
            return None
        for hit in r.json().get("results", []):
            hit_doi = (hit.get("doi") or "").lower().replace("https://doi.org/", "")
            if doi_to_skip and hit_doi == doi_to_skip.lower():
                continue
            # Author check
            auths = hit.get("authorships") or []
            if not auths:
                continue
            first = (auths[0].get("author") or {}).get("display_name", "").lower()
            first_surname = re.sub(r"[^a-z]", "", first.split()[-1]) if first.split() else ""
            if first_surname != expected_first_surname.lower():
                continue
            # Year sanity
            year = hit.get("publication_year")
            if not year or year < expected_year:
                continue
            # Title overlap (Jaccard ≥ 0.5 on long words)
            our_words = {w for w in re.findall(r"[a-z]{4,}", title.lower())}
            their_words = {w for w in re.findall(r"[a-z]{4,}", (hit.get("title") or "").lower())}
            if our_words and their_words:
                overlap = len(our_words & their_words) / max(len(our_words | their_words), 1)
                if overlap < 0.5:
                    continue
            ver = find_journal_version(hit)
            if ver:
                return ver
    except requests.RequestException:
        pass
    return None


def main() -> int:
    pubs = yaml.safe_load(PUBS_FILE.read_text()) or {}
    candidates = 0
    print(f"Scanning {len(pubs)} entries for preprints...\n")
    for slug, p in pubs.items():
        if not isinstance(p, dict):
            continue
        if not is_preprint_venue(p.get("venue", "")):
            continue
        text = " ".join([p.get("link", ""), p.get("citation", "")])
        doi = extract_doi(text)
        arxiv = extract_arxiv(text)
        if not (doi or arxiv):
            continue

        work = fetch_openalex(doi, arxiv)
        time.sleep(0.05)
        ver = find_journal_version(work) if work else None
        if not ver and p.get("title"):
            # First author surname for the search guardrail
            first_author = (p.get("authors") or "").split(",")[0].strip().rstrip("*+").strip()
            first_author = re.sub(r"\([^)]+\)", "", first_author).strip()
            tokens = first_author.split()
            first_surname = re.sub(r"[^a-zA-Z]", "", tokens[-1]).lower() if tokens else ""
            ver = search_openalex_by_title(
                p["title"], first_surname, p.get("year", 0), doi_to_skip=doi,
            )
            time.sleep(0.05)
        if not ver:
            continue
        candidates += 1
        print(f"• {slug:30s}  {p['venue']!r} → {ver['venue']!r} ({ver.get('year')})")
        print(f"   title: {p['title'][:90]}")
        print(f"   DOI:   {ver.get('doi') or '(no doi)'}")
        if ver.get("url"):
            print(f"   url:   {ver['url']}")
        print()
    print(f"{candidates} preprint(s) appear to have a published version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
