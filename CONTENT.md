# Editing the Fiete Lab website

**You don't need to know how to code to edit this site.** Almost every piece
of content lives in plain text files inside [src/content/](src/content/).
Each file is one of two formats:

- `.md` — Markdown. Top section between `---` is structured info (name,
  title, photo); below the second `---` is a free-text bio.
- `.yaml` — A list. Each block is one entry (a paper, an alumnus, a news
  item).

Edit a file → save → push to GitHub → the site rebuilds automatically.

If something looks wrong after you push, open the **Actions** tab on the
GitHub repo to see the build error.

---

## Add a new lab member

1. Open [src/content/people/](src/content/people/).
2. Copy any existing file (e.g. `nathan-cloos.md`) and rename it to
   `firstname-lastname.md`.
3. Drop the headshot into [src/content/people/images/](src/content/people/images/) — name it
   `firstname-lastname.jpg` (or `.png` / `.jpeg`).
4. Edit the fields at the top:

   ```yaml
   ---
   name: "Jane Doe"
   role: "Graduate Student"      # PI | Administrative Assistant | Postdoc | Graduate Student | Affiliate
   title: "PhD, EECS"            # one short line shown under the name
   coAdvisor: "Josh McDermott"   # optional — delete this line if not co-advised
   avatar: "./images/jane-doe.jpg"
   website: "https://janedoe.io" # optional
   email: "jane@mit.edu"         # optional
   order: 30                     # optional — controls order within the role section (lower = earlier)
   authorAliases:                # optional — see "Publications on a person's page" below
     - "JD Doe"
     - "J. Doe"
   ---

   Write the bio here in regular paragraphs. A blank line starts a new paragraph.
   ```

5. Commit and push. The new card will appear on
   [/people](https://fietelab.github.io/people).

### Publications on a person's page

When you visit `/people/<slug>/`, the site automatically lists every paper
in `publications/content.yaml` whose `authors:` string contains a match for
this person's name. The match is generous — it accepts forms like
`J. Doe`, `J.D. Doe`, `JD Doe`, `Jane Doe` — but unusual citation styles
sometimes slip through.

If a paper is missing from a person's list (or an extra paper shows up),
add an `authorAliases:` array to the person's `.md` file. Each entry is a
literal substring that will mark a paper as theirs. For example, to make
sure a paper that lists `J.D. Hwang*` is included for Jaedong Hwang:

```yaml
authorAliases:
  - "J.D. Hwang"
```

### To remove a member (e.g. someone graduates)

Move them to **alumni** instead of deleting:

1. Delete (or move out of `people/`) their `.md` file.
2. Open [src/content/alumni/content.yaml](src/content/alumni/content.yaml)
   and add a new block at the top:

   ```yaml
   jane-doe:
     name: "Jane Doe"
     wasA: "Graduate Student"
     now: "Research Scientist, Google DeepMind"
     website: "https://janedoe.io"   # optional
   ```

---

## Add a paper

Open [src/content/publications/content.yaml](src/content/publications/content.yaml).
Add a block at the top of the relevant year section:

```yaml
my-paper-2026:                        # any unique slug, lowercase + dashes
  title: "My Amazing Paper"
  topics: ["Memory", "Theoretical ML"]   # optional — see allowed topics below
  authors: "Jane Doe, Ila Fiete"      # FULL names for lab members; abbreviated OK for others
  year: 2026
  venue: "Nature"                     # journal name or "arXiv preprint" or "NeurIPS"
  citation: "Nature 999, 1-10 (2026)" # optional but nice to include
  link: "https://arxiv.org/abs/2601.00001"
  annotation: "(spotlight)"           # optional — used for awards / co-first / co-senior notes
```

**Author convention.** Write lab members' **full names** ("Jane Doe", "Ila
Fiete") so they automatically appear under each person's `/people/<slug>/`
page. External co-authors can stay in any abbreviated form ("S. J. Lee").
The site abbreviates everyone uniformly at display time → `J. Doe, I.
Fiete, S. J. Lee`. Co-first / co-senior markers (`*`, `+`) on a name
("Jane Doe*") are preserved.

Papers are automatically grouped and sorted by year on
[/publications](https://fietelab.github.io/publications). The page also has
a "Filter by topic" bar at the top — pick a topic to show only matching
papers.

**Allowed topics** (must match exactly, capitalization included):
- `Theoretical ML`
- `Biologically plausible gradient learning`
- `Module/structure emergence`
- `Continuous attractors in the brain`
- `Error-correcting codes`
- `Inferring neural connectivity`
- `Memory`
- `Decision making`
- `Navigation circuits and spatial cognition`
- `Condensed-matter physics`

A paper can be tagged with as many topics as fit (or none).

### Adding a new topic

Just put the new topic string in any paper's `topics: [...]` field —
the filter pill and a stable per-name color appear automatically. The
hash-based color is deterministic (same name → same color across
builds), so the page stays visually consistent without anyone curating
the palette.

If you want to *override* the auto-generated color for a topic (e.g. a
specific hex matched to a poster), add an entry to `TOPIC_COLORS` in
[`src/lib/topics.ts`](src/lib/topics.ts):

```ts
'Reinforcement learning': { bg: '#ddd6fe', text: '#5b21b6', ring: '#a78bfa' },
```

To pin a new topic in a particular position in the filter row, also
add it to `TOPIC_ORDER` in the same file. Topics not in `TOPIC_ORDER`
slot in alphabetically after the curated list — fine for most cases.

> **Watch out for typos.** `"Memorry"` and `"Memory"` are treated as
> two different topics. Spell carefully and pick one canonical
> capitalization for each.

---

### Pull new papers automatically (OpenAlex sync)

The repo ships a one-shot script that fetches papers from
[OpenAlex](https://openalex.org) — a free, open replacement for Google
Scholar — using Ila Fiete's profile as the source of truth.

```bash
pip install -r scripts/requirements.txt
python scripts/sync_publications.py
```

This writes `pending_publications.yaml` at the repo root with proposed
new entries. Open it, copy any block that looks correct into
[`src/content/publications/content.yaml`](src/content/publications/content.yaml),
edit the venue / authors / topics / link as you see fit, then commit. The
next run will detect those slugs and stop proposing them.

**The script never modifies `publications/content.yaml`.** It only
writes the pending file. You're always in control of what lands in the
real data.

**Drops are respected.** If you delete an imported paper from the YAML,
the state file (`scripts/sync-state.yaml`) remembers its OpenAlex ID and
won't re-suggest it.

**Defaults to the last 2 years.** Pass `--since 2020` to expand the
window if you're back-filling old papers.

**Why not Google Scholar?** Google has no public API. Every "Scholar
sync" tool actually scrapes the page, gets blocked from cloud IPs, and
breaks when Google tweaks the markup. OpenAlex indexes the same
Crossref/PubMed/arXiv data and is free + stable.

---

## Add a news item

Open [src/content/news/content.yaml](src/content/news/content.yaml). Add a block:

```yaml
my-news-item:
  date: "2026-03"            # year, or year-month, or year-month-day — sorted as text
  text: "Welcome to new lab members joining this spring."
  link: "https://example.com"  # optional
```

News appears on the homepage in reverse chronological order.

---

## Add a code release

Open [src/content/projects/content.yaml](src/content/projects/content.yaml). Add a block:

```yaml
my-project:
  name: "My Project"
  description: |
    Multi-line description of what the code does and how to cite it.
  githubUrl: "https://github.com/FieteLab/my-project"   # optional
  paperLink: "https://arxiv.org/abs/2601.00001"         # optional
  paperTitle: "Doe & Fiete (2026)"                      # optional
  otherLinks:                                            # optional
    - { label: "Demo", url: "https://example.com" }
```

---

## Edit the homepage text

The "About the lab" paragraphs live in
[src/pages/index.astro](src/pages/index.astro). Search for the words you
want to change, edit them, save. The hero tagline is just below `<h1>The
Fiete Lab</h1>`.

## Edit the contact page

[src/pages/contact.astro](src/pages/contact.astro) — same idea, all the text
is right there.

---

## Running the site locally (optional)

If you want to preview your changes before pushing:

```bash
npm install   # only the first time
npm run dev   # opens http://localhost:4321
```

If you don't have Node.js, install it from <https://nodejs.org/> first
(LTS version is fine).

---

## What if I break something?

Every change is versioned by git. If a push breaks the site:

1. On GitHub, go to the **Commits** view.
2. Find the last commit before the breakage.
3. Click "Revert".

Or ask anyone who's comfortable with git to roll back for you.
