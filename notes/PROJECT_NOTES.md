# Fiete Lab website — project notes

Lightweight tracking doc. Status of features, design decisions and the
*why* behind them, and parking lot for future work.

## Status (as of initial wrap-up)

### Pages

| Route | Source | Notes |
|---|---|---|
| `/` | `src/pages/index.astro` | Hero + about + news + PI + quick-links |
| `/people/` | `src/pages/people/index.astro` | Group photo + roles + undergrads + alumni |
| `/people/<slug>/` | `src/pages/people/[id].astro` | Per-person bio + auto-detected publication list |
| `/publications/` | `src/pages/publications.astro` | All papers, topic filter, year sections |
| `/code/` | `src/pages/code.astro` | Code releases |
| `/contact/` | `src/pages/contact.astro` | Address + admin email |

### Content collections (Astro `defineCollection`)

| Collection | Files | What lives there |
|---|---|---|
| `people` | 19 `.md` | PI + admin + 5 postdocs + 11 grads + 1 affiliate |
| `alumni` | 35 entries (YAML) | Past members + their next position |
| `undergrads` | 10 entries (YAML) | UROP / undergrad researchers |
| `publications` | 111 entries (YAML) | 1998–2025, BibTeX-style keys |
| `projects` | 4 entries (YAML) | SPUD, grid attractor, STDP, Github org |
| `news` | 6 entries (YAML) | Homepage announcements |
| `group-photos` | 1 (YAML) | Lab outing July 2025 |

### Tooling

- **Stack**: Astro 5, Tailwind 4, sharp for image optimization, no React used.
- **Deploy**: GitHub Action on push to `main` builds + deploys to Pages.
- **OpenAlex sync**: `scripts/sync_publications.py` + weekly GitHub Action that opens a PR with new paper candidates from Ila's profile.

---

## Design decisions log (the *why*)

### Authors are stored as full names in YAML and abbreviated at render time

> "Jaedong Hwang, Ila Fiete" in YAML → "J. Hwang, I. Fiete" on screen.

External co-authors (people without a `.md` file) keep their original
abbreviated form ("S. J. Lee"); the abbreviator detects whichever and
emits one canonical look across the page. This makes:

- person → paper matching trivial (exact substring on the canonical
  full name + optional `authorAliases:`)
- on-screen styling consistent (same comma rules, same initials, etc.)

[Implementation: `src/lib/data.ts:abbreviateAuthor`]

### BibTeX-style slugs for publications

> `qian2025modular` rather than `modular-connectivity-2025`.

Stable, unique, recognizable, easy to grep, easy for the OpenAlex sync
script to compute deterministically.

### Three link tiers in paper bylines

| Author type | Link target | Style |
|---|---|---|
| Current lab member | `/people/<slug>/` | maroon accent |
| Alumnus with website on record | external site | muted gray + hover underline |
| Faculty co-advisor (Paul Liang etc.) | their lab page | muted gray + hover underline |
| External co-author | none | plain text |

Visual differentiation matters — without it, a Nature paper byline is
12 identical blue links and you can't scan for who's a member. See
`src/components/AuthorList.astro`.

### Topic categorization came from the original WordPress page

10 topics, not invented — copied from fietelab.mit.edu/publications/'s
"Categorized by topic" section. 64 of 111 papers tagged. The rest show
only under "All". Each topic has a stable color (`src/lib/topics.ts`).

### Redundant citations stripped from YAML, not just hidden

Once `citation: "Nature (2025)"` was identified as redundant with
`venue: "Nature"` + `year: 2025`, the data was rewritten. The
render-time guard (`isRedundantCitation`) stays as a safety net for
future hand-edits. 39 of 111 entries had their `citation:` line
deleted; 72 informative ones (with DOI / volume / page) remain.

### OpenAlex, not Google Scholar

Google has no API. Scholar scrapers (scholarly, etc.) get blocked from
GitHub Actions runners and break when Google updates the markup.
OpenAlex indexes the same Crossref + PubMed + arXiv corpus, has a free
JSON API, no rate-limit issues in practice. For a lab page, "what's in
OpenAlex" ≈ "what's on Scholar" minus a 1–3 day lag for fresh
preprints.

### Sync is strictly additive + state-tracked

The sync script (`scripts/sync_publications.py`):

- only writes `pending_publications.yaml`, never touches `publications/content.yaml`
- records every OpenAlex work ID it sees in `scripts/sync-state.yaml`
  with status `imported | dropped | pending | manual`
- if you delete an `imported` paper from the YAML, next run flips it to
  `dropped` — never proposed again
- defaults to `--since (current_year - 2)` so back-catalog noise stays
  quiet
- dedupes by DOI (with URL-pattern extraction for Nature, eLife, etc.),
  arXiv ID, OpenAlex ID, exact title key, and fuzzy title (Jaccard
  ≥ 0.7) for preprint→published title drift

### Group photo on `/people`, not on home

Original WordPress site had it on `/people`. Tried home, user pushed
back, moved. Home stays uncluttered.

### Banner is MIT-maroon gradient, no photo

Tried navy with scattered radials, then offered the user MIT maroon /
photo / blue-teal. They chose maroon. Affiliations row is two
white-on-dark logos (MIT BCS + McGovern); no public ICoN logo
exists, so that affiliation lives only in Ila's bio.

### Co-advisor links: detail page only, never the card

The whole `<a>`-wrapped card means a nested `<a>` for the co-advisor
breaks browser rendering. So co-advisors are linked from
`/people/<slug>/` (the detail page) but stay plain text on the
`/people` grid card.

---

## Future work / open questions

- **GitHub Pages first-time setup** still requires a manual click to
  switch Source → "GitHub Actions" in repo settings.
- **More group photos** — only 1 currently. Carousel UI exists in MIT-MI
  reference but not implemented here; would need ~30 lines if we ever
  hit ≥ 3 photos.
- **Topic tagging coverage** — 47 papers untagged because the original
  page didn't categorize them. Could backfill via a manual pass or by
  prompting an LLM with the title + abstract.
- **Alumni → paper byline** — currently we use the alumnus's website as
  the link target, falling back to Scholar. If neither exists, the name
  is plain text. Could add a stub `/people/alumni/<slug>/` page.
- **News dates** — currently free-form `YYYY-MM` strings; no per-day
  ordering. Fine while the list is short.
- **OpenAlex sync coverage** — anchored on Ila's profile only. Catches
  her co-authored papers (which is most lab output) but misses things
  like Adam Eisen ↔ Earl Miller papers without Ila. Extensible to
  per-member if ever needed.

---

## Notable commits

| Commit | What |
|---|---|
| `e45e7fb` | First static-HTML scaffold (later replaced by Astro) |
| `1fdfe8d` | Migrate to Astro 5 + content collections |
| `3c875d5` | Add per-person detail pages |
| `b10c43f` | Topic categorization + filter UI |
| `93159f2` | Color topic tags + per-person publication lists |
| `4dcf3d1` | Unify authors: full names in YAML, abbreviated at render |
| `6e9d4dd` | Rename publication keys to BibTeX style |
| `ba9d810` | Author-link map (members / alumni / collaborators) |
| `7ccad5e` | Group photo, distinct lab-member link color |
| `c06a138` | OpenAlex sync script |
| `e1676aa` | Weekly OpenAlex sync workflow with auto-PR |
| `20c2ed1` | Maroon banner + BCS / McGovern logos |
