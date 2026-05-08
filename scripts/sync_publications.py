#!/usr/bin/env python3
"""Pull new papers for the Fiete Lab from Ila Fiete's OpenAlex profile.

Strict additive sync. The script writes only `pending_publications.yaml`,
never modifies `publications/content.yaml` directly. After you review the
pending file, append the entries you want into `publications/content.yaml`
yourself — the next run will detect the slugs and mark them as imported.

Drops are respected: if you delete an imported paper from the YAML, the
state file remembers it as `dropped` and never re-proposes it.

Usage:
    pip install -r scripts/requirements.txt
    python scripts/sync_publications.py            # check, write pending file
    python scripts/sync_publications.py --no-state # don't touch state file

Files involved:
    src/content/publications/content.yaml   ← reads existing entries
    scripts/sync-state.yaml                 ← read+write, tracks every seen ID
    pending_publications.yaml               ← written each run
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

try:
    import requests
    import yaml
except ImportError as e:
    sys.exit(
        f"missing dependency: {e.name}.  run `pip install -r scripts/requirements.txt`"
    )

ROOT = Path(__file__).resolve().parent.parent
PUBS_FILE = ROOT / "src" / "content" / "publications" / "content.yaml"
STATE_FILE = ROOT / "scripts" / "sync-state.yaml"
PENDING_FILE = ROOT / "pending_publications.yaml"

# Hardcoded — the lab is built around Ila's authorship. Extending this to
# every member would catch a few extra papers (Adam with Earl Miller,
# Bryan with Josh McDermott) but explodes the false-positive rate; not
# worth the noise.
ILA_FIETE_OPENALEX_ID = "A5083541135"

OPENALEX_BASE = "https://api.openalex.org/works"
USER_AGENT = "fietelab-website-sync/0.1 (mailto:fietelabcolab@gmail.com)"

STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for",
    "with", "from", "by", "into", "onto", "about", "as", "is", "are", "be",
    "we", "do", "does",
}


# ---------------------------------------------------------------- helpers


def load_publications() -> dict[str, dict]:
    return yaml.safe_load(PUBS_FILE.read_text()) or {}


def load_state() -> dict:
    if STATE_FILE.exists():
        return yaml.safe_load(STATE_FILE.read_text()) or {"seen": {}}
    return {"seen": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Auto-managed by scripts/sync_publications.py.\n"
        "# Tracks every OpenAlex work the sync has ever seen and what was\n"
        "# done with it. Do not hand-edit unless you know what you're doing.\n"
        "# Status values: imported | dropped | pending | manual\n"
    )
    STATE_FILE.write_text(header + yaml.safe_dump(state, sort_keys=False, allow_unicode=True))


# ----------------------------------------------------------- identifiers


DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
ARXIV_RE = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
ARXIV_OLD_RE = re.compile(r"\b([a-z\-]+/\d{7})(v\d+)?\b", re.I)


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi.strip(), flags=re.I)
    return doi.lower().rstrip(".")


def extract_doi(text: str) -> str | None:
    if not text:
        return None
    m = DOI_RE.search(text)
    if m:
        return normalize_doi(m.group(0))
    # URL-shaped DOIs that don't put the full DOI in the path.
    # Nature: nature.com/articles/<accession>  →  10.1038/<accession>
    m = re.search(r"nature\.com/articles/([^/?#\"]+)", text)
    if m:
        return normalize_doi(f"10.1038/{m.group(1)}")
    # eLife: elifesciences.org/articles/XXXXX  →  10.7554/eLife.XXXXX
    m = re.search(r"elifesciences\.org/articles/(\d+)", text)
    if m:
        return normalize_doi(f"10.7554/eLife.{m.group(1)}")
    return None


def extract_arxiv(text: str) -> str | None:
    m = (ARXIV_RE.search(text or "") if text else None) or (
        ARXIV_OLD_RE.search(text or "") if text else None
    )
    return m.group(1).lower() if m else None


def title_tokens(title: str) -> set[str]:
    """Significant words for fuzzy title comparison (length ≥ 4)."""
    return {
        t for t in re.findall(r"[a-z0-9]+", (title or "").lower())
        if len(t) >= 4 and t not in STOP_WORDS
    }


def fuzzy_title_match(a: str, b: str) -> bool:
    """Token-Jaccard ≥ 0.7 → treat as the same paper."""
    ta, tb = title_tokens(a), title_tokens(b)
    if not ta or not tb:
        return False
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union >= 0.7


def extract_openalex_id(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"openalex\.org/(W\d+)", url, re.I)
    return m.group(1) if m else None


def title_key(title: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", " ", (title or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def collect_identifiers(pub: dict) -> set[str]:
    ids: set[str] = set()
    text = " ".join(
        str(pub.get(k, "")) for k in ("title", "link", "citation", "authors", "venue")
    )
    if d := extract_doi(text):
        ids.add(f"doi:{d}")
    if a := extract_arxiv(text):
        ids.add(f"arxiv:{a}")
    if oa := extract_openalex_id(pub.get("link", "")):
        ids.add(f"openalex:{oa}")
    if t := pub.get("title"):
        ids.add(f"title:{title_key(t)}")
    return ids


# -------------------------------------------------------------- OpenAlex


@dataclass
class Work:
    openalex_id: str
    title: str
    authors: list[str]
    year: int
    venue: str
    doi: str | None
    arxiv: str | None
    url: str

    def identifiers(self) -> set[str]:
        ids = {f"openalex:{self.openalex_id}", f"title:{title_key(self.title)}"}
        if self.doi:
            ids.add(f"doi:{self.doi}")
        if self.arxiv:
            ids.add(f"arxiv:{self.arxiv}")
        return ids


def _venue(work: dict) -> str:
    primary = work.get("primary_location") or {}
    src = primary.get("source") or {}
    name = src.get("display_name")
    if name:
        return name
    if work.get("type") == "preprint":
        return "arXiv preprint"
    return (work.get("type") or "preprint").replace("-", " ")


def _arxiv_from_locations(work: dict) -> str | None:
    for loc in [work.get("primary_location")] + (work.get("locations") or []):
        if not loc:
            continue
        url = loc.get("landing_page_url") or ""
        if a := extract_arxiv(url):
            return a
    return None


def _best_url(work: dict, doi: str | None, arxiv: str | None) -> str:
    if doi:
        return f"https://doi.org/{doi}"
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv}"
    primary = (work.get("primary_location") or {}).get("landing_page_url")
    return primary or work.get("id", "")


def fetch_works(openalex_id: str) -> list[Work]:
    out: list[Work] = []
    cursor = "*"
    while True:
        params = {
            "filter": f"author.id:{openalex_id}",
            "per-page": 200,
            "cursor": cursor,
            "select": (
                "id,title,authorships,publication_year,doi,type,"
                "primary_location,locations"
            ),
        }
        url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        data = r.json()
        for w in data.get("results", []):
            try:
                title = w.get("title") or ""
                if not title or not w.get("publication_year"):
                    continue
                doi = normalize_doi(w.get("doi"))
                arxiv = _arxiv_from_locations(w)
                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in (w.get("authorships") or [])
                    if a.get("author", {}).get("display_name")
                ]
                wid = re.sub(r".*/", "", w.get("id", ""))
                if not wid.startswith("W"):
                    continue
                out.append(Work(
                    openalex_id=wid,
                    title=title,
                    authors=authors,
                    year=int(w["publication_year"]),
                    venue=_venue(w),
                    doi=doi,
                    arxiv=arxiv,
                    url=_best_url(w, doi, arxiv),
                ))
            except Exception as e:
                print(f"  ! skipping malformed work: {e}", file=sys.stderr)
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.1)
    return out


# ----------------------------------------------------------- slug helpers


def first_significant_word(title: str) -> str:
    for w in re.findall(r"[A-Za-z][A-Za-z0-9-]*", title):
        if w.lower() not in STOP_WORDS:
            return re.sub(r"[^a-z0-9]", "", w.lower())
    return "paper"


def first_author_lastname(authors: list[str]) -> str:
    if not authors:
        return "unknown"
    first = re.sub(r"\([^)]+\)", "", authors[0]).strip()
    if "International Brain Laboratory" in first:
        return "ibl"
    tokens = first.split()
    if not tokens:
        return "unknown"
    return re.sub(r"[^a-z]", "", tokens[-1].lower()) or "unknown"


def make_slug(work: Work, taken: set[str]) -> str:
    base = f"{first_author_lastname(work.authors)}{work.year}{first_significant_word(work.title)}"
    if base not in taken:
        return base
    for suffix in "abcdefghij":
        candidate = f"{base}{suffix}"
        if candidate not in taken:
            return candidate
    return f"{base}{int(time.time())}"


# --------------------------------------------------------------- pending


def yaml_pub_block(slug: str, work: Work) -> str:
    lines = [f"{slug}:"]
    lines.append(f'  title: {yaml.dump(work.title, default_flow_style=False).strip()}')
    authors = ", ".join(work.authors)
    lines.append(f'  authors: {yaml.dump(authors, default_flow_style=False).strip()}')
    lines.append(f"  year: {work.year}")
    lines.append(f'  venue: {yaml.dump(work.venue, default_flow_style=False).strip()}')
    lines.append(f'  link: "{work.url}"')
    return "\n".join(lines) + "\n"


def write_pending(proposals: list[tuple[str, Work]]) -> None:
    if not proposals:
        if PENDING_FILE.exists():
            PENDING_FILE.unlink()
        return
    out = [
        "# Proposed new publications from OpenAlex (Ila Fiete's profile).",
        "# Review each block; copy the ones you want into",
        "# src/content/publications/content.yaml. The next sync run will",
        "# detect them as imported and stop proposing them. To explicitly",
        "# drop a candidate forever, delete this whole pending file after",
        "# any genuinely-wanted entries have been merged — the script will",
        "# remember the rest as `dropped` in scripts/sync-state.yaml.",
        "",
    ]
    for slug, work in proposals:
        first = work.authors[0] if work.authors else "?"
        out.append(f"# OpenAlex {work.openalex_id}; first author {first}")
        out.append(yaml_pub_block(slug, work))
    PENDING_FILE.write_text("\n".join(out))


# ----------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    ap.add_argument(
        "--no-state", action="store_true",
        help="Don't read or write scripts/sync-state.yaml.",
    )
    ap.add_argument(
        "--since", type=int, default=None,
        help="Only consider works from this year or later (default: 2 years before now).",
    )
    args = ap.parse_args()
    cutoff_year = args.since if args.since else time.gmtime().tm_year - 2

    pubs = load_publications()
    pub_ids: dict[str, str] = {}  # ident → slug
    for slug, p in pubs.items():
        for ident in collect_identifiers(p):
            pub_ids.setdefault(ident, slug)

    state = {"seen": {}} if args.no_state else load_state()
    seen: dict[str, dict] = state.setdefault("seen", {})

    # Reconcile state with current YAML before fetching:
    #   imported → dropped if its slug is gone
    #   pending  → imported if any of its identifiers now show up in YAML
    for wid, info in list(seen.items()):
        if info.get("status") == "imported":
            slug = info.get("slug")
            if slug and slug not in pubs:
                info["status"] = "dropped"
                info.pop("slug", None)
        elif info.get("status") == "pending":
            ids = set()
            if d := info.get("doi"):
                ids.add(f"doi:{d}")
            if a := info.get("arxiv"):
                ids.add(f"arxiv:{a}")
            if t := info.get("title"):
                ids.add(f"title:{title_key(t)}")
            ids.add(f"openalex:{wid}")
            for ident in ids:
                if ident in pub_ids:
                    info["status"] = "imported"
                    info["slug"] = pub_ids[ident]
                    break

    # If a pending entry is no longer being proposed (i.e. user emptied
    # pending_publications.yaml without merging), we'll catch it below by
    # scanning what we propose this round.

    print(f"  fetching works for Ila Fiete ({ILA_FIETE_OPENALEX_ID})…", flush=True)
    try:
        works = fetch_works(ILA_FIETE_OPENALEX_ID)
    except requests.RequestException as e:
        print(f"  ! OpenAlex error: {e}", file=sys.stderr)
        return 2

    print(f"    {len(works)} total works on Ila's profile")

    proposals: list[tuple[str, Work]] = []
    taken_slugs: set[str] = set(pubs.keys())
    proposed_wids: set[str] = set()
    yaml_titles = [p.get("title", "") for p in pubs.values()]

    for w in works:
        if w.year < cutoff_year:
            continue  # old paper; either we have it or chose not to
        if any(i in pub_ids for i in w.identifiers()):
            continue  # already in YAML by DOI / arXiv / title-key match
        # Last-line fuzzy title check for cases like preprint→published title drift
        if any(fuzzy_title_match(w.title, t) for t in yaml_titles):
            continue
        prior = seen.get(w.openalex_id)
        if prior and prior.get("status") in ("imported", "dropped"):
            continue  # respect prior decisions
        new_slug = make_slug(w, taken_slugs)
        taken_slugs.add(new_slug)
        proposals.append((new_slug, w))
        proposed_wids.add(w.openalex_id)
        seen[w.openalex_id] = {
            "title": w.title[:200],
            "doi": w.doi,
            "arxiv": w.arxiv,
            "year": w.year,
            "status": "pending",
            "slug": new_slug,
        }

    # Anything previously `pending` that we did NOT re-propose this round
    # (because the user removed it from pending_publications.yaml without
    # merging) → mark `dropped` so we never re-suggest it.
    for wid, info in list(seen.items()):
        if info.get("status") == "pending" and wid not in proposed_wids:
            info["status"] = "dropped"
            info.pop("slug", None)

    write_pending(proposals)
    print(f"\n→ {len(proposals)} new candidate(s) → {PENDING_FILE.relative_to(ROOT)}")
    if not args.no_state:
        save_state(state)
        print(f"→ state           → {STATE_FILE.relative_to(ROOT)}")
    if not proposals:
        print("Nothing new from OpenAlex.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
