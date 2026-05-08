# Maintenance checklist for future Claude Code agents

This file is for an LLM agent (or a careful human) updating the Fiete Lab
website on a recurring basis. It assumes you've read
[`PROJECT_NOTES.md`](PROJECT_NOTES.md) for context on conventions.

Run through whichever tasks the user asks about. Each section is
self-contained — you can do (1) without (2) and vice versa.

---

## 1. Check for new publications

**Source of truth:** Ila Fiete's Google Scholar profile —
<https://scholar.google.co.kr/citations?user=uE-CihIAAAAJ>

The OpenAlex weekly bot (see [`.github/workflows/sync-publications.yml`](../.github/workflows/sync-publications.yml))
runs `scripts/sync_publications.py` and opens a PR with new candidates,
but Scholar usually surfaces papers a few days earlier and is the
canonical reference for this lab. So when the user asks "what's new",
re-check Scholar directly.

### Procedure

1. **Window:** check the current year and previous year. e.g. running
   in May 2027 → look at 2026 and 2027 entries on Scholar.
2. **Fetch the Scholar page.** If WebFetch from inside the agent fails
   (Google sometimes serves a CAPTCHA to automated requests), ask the
   user to paste the relevant rows into the chat.
3. **For each Scholar entry that isn't already in
   [`src/content/publications/content.yaml`](../src/content/publications/content.yaml):**
   - Cross-check via Crossref to get DOI, full author list, exact
     venue:
     ```bash
     curl -sH "User-Agent: fietelab-website-sync/0.1" \
       "https://api.crossref.org/works?query.author=Ila+Fiete&filter=from-pub-date:YYYY-01-01&rows=20"
     ```
   - Decide whether it's a real lab paper. Heuristics:
     - "Preview" / "News & Views" articles are fine to include if Ila
       or a lab member wrote them (we have a few already).
     - Massive consortium papers (IBL, "mind of a mouse" style) are
       fine — use the abbreviated `"First, et al. (Consortium)"` form.
     - Skip papers where Ila is incidental (rare; usually only an issue
       with author-name collisions).
   - **Generate a BibTeX-style slug:** `<firstauthor-lastname><year><first-significant-word>`.
     Match the convention in `scripts/sync_publications.py`. Stop
     words: `a, an, the, and, or, of, in, on, at, to, for, with,
     from, by, into, onto, about, as, is, are, be, we, do, does`.
   - **Authors line:** full names for lab members + alumni + named
     external collaborators in
     [`src/content/collaborators/content.yaml`](../src/content/collaborators/content.yaml);
     abbreviated form for everyone else. Co-first gets `*`, co-senior
     gets `+` (with a matching `annotation:` line).
   - **Topics: required.** Always add a `topics: [...]` line for every
     new entry — leaving it off makes the paper invisible to the topic
     filter. Pick from the curated list in
     [`src/lib/topics.ts`](../src/lib/topics.ts) when one fits.
     Use multiple tags when genuinely multidisciplinary (e.g.
     `["Memory", "Navigation circuits and spatial cognition"]`). If
     nothing fits, invent a new short topic name (e.g.
     `"Altered brain states"`) — it will auto-color and auto-slot
     into the filter row, no `topics.ts` edit required.

     **Do NOT use the `_Claude` suffix.** That postfix was a
     one-time marker for the bulk-tagging audit; ongoing edits should
     use canonical topic names directly. If you want to convert an
     existing `Foo_Claude` tag to canonical, just delete the suffix in
     the YAML.
4. **If a preprint we have is now journal-published:**
   *Update the existing entry, don't add a duplicate.* Rename slug to
   the new publication year, change `year` / `venue` / `link`, and
   keep both references in `citation:`. Example:
   ```yaml
   eisen2026similar:
     # ... renamed from eisen2025similar (was bioRxiv)
     citation: "bioRxiv 10.1101/2025.08.21.671540 (2025) and Cell Reports 45(3) (2026)"
   ```
5. **Verify the link.** `curl -sLI "<link>" -o /dev/null -w "%{http_code}"`. 200 = OK; 403/406 = bot-block but
   browser-OK (typical for Cell, eLife, bioRxiv, PNAS, journals.aps —
   leave them); 404 = wrong link, fix it.
6. **`npm run build`** — must produce 0 errors, 0 warnings.
7. **Commit** with a message of the form
   `Add N publications: <short summary>`.

### Files touched

- [`src/content/publications/content.yaml`](../src/content/publications/content.yaml) — the only data file
- (auto-updated by the OpenAlex sync, but you might want to update it manually too):
  [`scripts/sync-state.yaml`](../scripts/sync-state.yaml) — if you imported a paper that was previously `pending` there, flip its status to `imported`.

---

## 2. Check that lab member info is current

For each [`src/content/people/<slug>.md`](../src/content/people/) file:

### a. Links still resolve

Bulk check:

```bash
for f in src/content/people/*.md; do
  for url in $(grep -oE 'https?://[^"]+' "$f"); do
    code=$(curl -sLI -o /dev/null -w "%{http_code}" --max-time 10 -A "Mozilla/5.0" "$url")
    [ "$code" != "200" ] && [ "$code" != "403" ] && [ "$code" != "406" ] && \
      echo "$f: $code  $url"
  done
done
```

Anything that prints needs investigation. 200/403/406 are fine; 404
means the page moved or was deleted.

### b. Bio still matches reality

Common drift to look for:

| Symptom | Fix |
|---|---|
| Bio says "PhD student" but person's website now says "Postdoc, X" | They graduated — move them to [`src/content/alumni/content.yaml`](../src/content/alumni/content.yaml), delete their `.md`. |
| Person mentions "co-advised by X" but `coAdvisor:` field is empty (or vice versa) | Sync the two; ensure X has a block in [`src/content/collaborators/content.yaml`](../src/content/collaborators/content.yaml) so X's name links from the byline. |
| `website:` 404 but person has a new domain | Update the URL. |
| New affiliation (e.g. fellowship, prize) prominent on their site | Add a sentence to the bio paragraph. |

### c. Co-advisor links

Every value of `coAdvisor:` in any person's frontmatter must appear as a
`name:` in [`src/content/collaborators/content.yaml`](../src/content/collaborators/content.yaml).
Quick audit:

```bash
grep -h '^coAdvisor:' src/content/people/*.md | sort -u
grep -h 'name:' src/content/collaborators/content.yaml | sort -u
```

If a co-advisor isn't in the collection, add a YAML block with their
lab page URL — no code edit needed.

### d. Add new lab members

When a new member joins:

1. Drop a headshot into [`src/content/people/images/`](../src/content/people/images/)
2. Copy any existing `.md` (e.g. `nathan-cloos.md`) → rename to `firstname-lastname.md`
3. Set `name`, `role`, `title`, `coAdvisor` (optional), `avatar`,
   `website`, `scholar`, `email`, `order` fields
4. Body: 1-3 paragraph bio
5. Build + commit

When a current member graduates / leaves:

1. Add an `alumni` entry with `wasA:` (former role) and `now:` (next position).
2. Delete their `.md` file from `src/content/people/`.
3. Their headshot in `images/` can stay or be moved to a `images/_alumni/` subfolder if the file gets crowded.

---

## 3. Update year grouping when the calendar rolls over

The year filter on `/publications` shows the 5 most-recent years
individually (most recent first), then ONE 5-year bucket, then ONE
catchall for everything older. The boundaries are computed dynamically
from the YAML — the script picks the 5 most-recent years that *have*
papers in the YAML, not by calendar year.

So mostly nothing to do — adding new entries auto-shifts the buckets.
But there are a couple of moments when you should verify the result
still looks right:

### When the calendar year changes

Once a paper from a new year is added (e.g. when the first 2027 paper
goes in), the recent-5 will roll. **Open `/publications` and confirm:**

- The pill row reads `All  2027  2026  2025  2024  2023`, then bucket
  `2022–2018`, then catchall `2017–1998`.
- The catchall count went up by one (the year that just rolled out of
  the recent-5).

If anything looks off, the logic is in
[`src/pages/publications.astro`](../src/pages/publications.astro) —
search for `RECENT_N` and `BUCKET_SIZE`.

### When you start having empty years in the recent window

If a year produces no papers (e.g. mid-year 2027 with no published
work yet), the filter quietly skips it — only years *with* papers
appear as individual pills. This is intentional. Nothing to do.

### If you ever want to change the policy

Two knobs at the top of the script section in
[`src/pages/publications.astro`](../src/pages/publications.astro):

```ts
const RECENT_N = 5      // how many recent years stay individual
const BUCKET_SIZE = 5   // size of the single bucket between recent and catchall
```

Bump either to taste. The catchall always covers everything older.

---

## 4. Universal post-edit checklist

Whatever you changed, before you say "done":

- [ ] `npm run build` passes with 0 errors, 0 warnings
- [ ] Spot-check the affected page in `npm run dev` if practical
- [ ] Commit with a clear message; don't bundle unrelated changes
- [ ] Do **not** `git push` unless the user explicitly asks
- [ ] If you ran the OpenAlex sync, the `pending_publications.yaml`
      file at the repo root is gitignored and ephemeral — leave it
      alone or delete it after merging the entries you want
- [ ] If you renamed a slug or removed an entry that the OpenAlex
      sync had imported, run `python scripts/sync_publications.py`
      once after your changes — it will reconcile state automatically
      (slug-not-in-YAML → status flips to `dropped`)

---

## 5. Project conventions you must not break

These are documented in [`PROJECT_NOTES.md`](PROJECT_NOTES.md) under
"Design decisions log" — short version:

- **Authors:** full names in YAML for lab members + alumni;
  abbreviated forms ("S. J. Lee") for external co-authors. Render-time
  abbreviator handles display uniformly.
- **Slugs:** BibTeX style (`hwang2025learn`). All lowercase, no dashes.
- **Co-first / co-senior:** `*` / `+` as a trailing marker on the
  name; matching `annotation:` line.
- **Topics:** any string is accepted; new ones get a stable hashed
  color and an auto-added filter pill. Pin a curated color/order in
  [`src/lib/topics.ts`](../src/lib/topics.ts) only if you specifically
  want one. Don't use the `_Claude` suffix for new tags.
- **Citations:** never repeat just `venue + year` — leave the field
  out. Only fill it for DOI / volume / page / preprint history.
- **Author-link map:** lab members → `/people/<slug>/` (maroon),
  alumni → `website ?? scholar` (gray), external collaborators listed
  in [`src/content/collaborators/content.yaml`](../src/content/collaborators/content.yaml)
  (gray), everyone else → plain text.
- **Group photo:** lives only on `/people/`. Capped at `max-w-3xl` and
  16:9 aspect ratio.

When in doubt, look at how the most recent commits handled the same
case (`git log -p src/content/publications/content.yaml` shows
exemplars of every paper-add commit).

---

## 6. What lives where

| File | Purpose |
|---|---|
| [INSTRUCTIONS.md](../INSTRUCTIONS.md) | Visual page-by-page edit map (for humans) |
| [CONTENT.md](../CONTENT.md) | Task-by-task editing recipes (for humans) |
| [notes/PROJECT_NOTES.md](PROJECT_NOTES.md) | Design decisions log + status |
| [notes/MAINTENANCE.md](MAINTENANCE.md) | This file — recurring tasks for agents |
| [notes/slides.md](slides.md) | Marp deck for presenting the site |
