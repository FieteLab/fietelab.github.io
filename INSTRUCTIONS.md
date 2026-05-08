# Editing the Fiete Lab website — visual guide

**For lab members who don't write code.** Each section below shows what
appears on the live site, then tells you which file to open and what to
change.

If you'd like real screenshots in this guide, drop PNGs into
[`docs/screenshots/`](docs/screenshots/) using the filenames suggested
under each section — the markdown image links are already wired up.

---

## TL;DR — what to edit, by task

| If you want to change… | Open this file |
|---|---|
| Hero title, tagline, "About the lab" paragraphs, explore cards | [`src/content/site/home.md`](src/content/site/home.md) |
| Banner gradient color | [`src/pages/index.astro`](src/pages/index.astro) (the `<!-- Hero -->` section) |
| Affiliation logos in the banner | [`src/consts.ts`](src/consts.ts) (logo files in [`public/`](public/)) |
| Add / remove a news item on the home page | [`src/content/news/content.yaml`](src/content/news/content.yaml) |
| Add / remove a current member | new `.md` file in [`src/content/people/`](src/content/people/) |
| Move someone from current → alumni | delete their `.md`, add a YAML block in [`src/content/alumni/content.yaml`](src/content/alumni/content.yaml) |
| Link a co-advisor or external collaborator from paper bylines | YAML block in [`src/content/collaborators/content.yaml`](src/content/collaborators/content.yaml) |
| Add a paper | YAML block in [`src/content/publications/content.yaml`](src/content/publications/content.yaml) |
| Add a code release | YAML block in [`src/content/projects/content.yaml`](src/content/projects/content.yaml) |
| Replace a headshot | drop new file in [`src/content/people/images/`](src/content/people/images/), update `avatar:` in the person's `.md` |
| Replace the group photo | new image in [`src/content/group-photos/images/`](src/content/group-photos/images/), edit [`src/content/group-photos/content.yaml`](src/content/group-photos/content.yaml) |
| Site name, nav items, social links | [`src/consts.ts`](src/consts.ts) |
| Contact info | [`src/content/site/contact.md`](src/content/site/contact.md) |

For the workflow of editing/saving/pushing, see "Local preview" at the
bottom.

---

## Page 1 — Home (`/`)

![home](docs/screenshots/home.png)

```
 ┌────────────────────────────────────────────────────────────────────┐
 │ ① Sticky nav: Home  People  Papers  Code  Contact                  │
 ├────────────────────────────────────────────────────────────────────┤
 │ ② Hero (maroon gradient banner)                                    │
 │     The Fiete Lab                                                  │
 │     Our goal is to better understand the dynamics and coding…      │
 │     [BCS logo]   [McGovern logo]                                   │
 ├────────────────────────────────────────────────────────────────────┤
 │ ③ About the lab                                                    │
 │     three paragraphs                                               │
 ├────────────────────────────────────────────────────────────────────┤
 │ ④ Recent news (light gray section)                                 │
 │     YYYY-MM   short news line                                      │
 │     YYYY-MM   short news line                                      │
 ├────────────────────────────────────────────────────────────────────┤
 │ ⑤ Principal Investigator card                                       │
 ├────────────────────────────────────────────────────────────────────┤
 │ ⑥ Quick links: People → / Papers → / Code →                         │
 ├────────────────────────────────────────────────────────────────────┤
 │ ⑦ Footer                                                            │
 └────────────────────────────────────────────────────────────────────┘
```

| Callout | What it is | File to edit |
|---|---|---|
| ① | Header / nav | [`src/components/Header.astro`](src/components/Header.astro) — and `NAV_LINKS` in [`src/consts.ts`](src/consts.ts) for the link list |
| ② | Hero banner — title, tagline | [`src/content/site/home.md`](src/content/site/home.md) (frontmatter `heroTitle` and `heroTagline`). Banner gradient + logo styling stay in [`src/pages/index.astro`](src/pages/index.astro); the `AFFILIATIONS` array and logo paths live in [`src/consts.ts`](src/consts.ts). |
| ③ | About the lab | Markdown body of [`src/content/site/home.md`](src/content/site/home.md) — paragraphs are plain text, blank line = new paragraph; supports italics with `*word*`, bold with `**word**`, links with `[text](url)`. |
| ④ | Recent news | [`src/content/news/content.yaml`](src/content/news/content.yaml) — copy a block, change `date` (YYYY-MM or YYYY-MM-DD), `text`, optional `link`. |
| ⑤ | PI card | **Auto-generated** from [`src/content/people/ila-fiete.md`](src/content/people/ila-fiete.md). |
| ⑥ | Quick links / explore cards | `exploreCards:` array in [`src/content/site/home.md`](src/content/site/home.md) — add or remove blocks. |
| ⑦ | Footer | [`src/components/Footer.astro`](src/components/Footer.astro) (address) and `SOCIAL_LINKS` in [`src/consts.ts`](src/consts.ts). |

### Banner color

In [`src/pages/index.astro`](src/pages/index.astro), find the `<!-- Hero -->` section. The colors are inline:

```astro
style="background: linear-gradient(135deg, #14060c 0%, #45091c 55%, #8a1538 100%);"
```

Three hex colors: deep base → mid → bright accent. Pick from
[colorhunt.co](https://colorhunt.co/) and replace.

### Replacing the affiliation logos

1. Drop a new white-on-transparent logo into [`public/`](public/) (e.g. `public/my-logo.png`).
2. In [`src/consts.ts`](src/consts.ts), update the matching entry in `AFFILIATIONS`:

   ```ts
   { name: 'My Center', href: 'https://example.org/', logo: '/my-logo.png' },
   ```

---

## Page 2 — People (`/people/`)

![people](docs/screenshots/people.png)

```
 ┌────────────────────────────────────────────────────────────────────┐
 │  People                                                             │
 │  intro paragraph                                                    │
 ├────────────────────────────────────────────────────────────────────┤
 │  ① Group photo banner                                               │
 ├────────────────────────────────────────────────────────────────────┤
 │  ② PI card (clickable → /people/ila-fiete/)                         │
 ├────────────────────────────────────────────────────────────────────┤
 │  Postdocs              Graduate Students          Affiliates       │
 │  ┌────┐  ┌────┐        ┌────┐  ┌────┐  ┌────┐    ┌────┐            │
 │  │card│  │card│        │card│  │card│  │card│    │card│            │
 │  └────┘  └────┘        └────┘  └────┘  └────┘    └────┘            │
 ├────────────────────────────────────────────────────────────────────┤
 │  ③ Undergraduate Researchers — 1-line list                          │
 ├────────────────────────────────────────────────────────────────────┤
 │  ④ Group Alumni — name + role + now-at + Website / Scholar pills    │
 └────────────────────────────────────────────────────────────────────┘
```

| Callout | What | File |
|---|---|---|
| ① | Group photo at top | [`src/content/group-photos/content.yaml`](src/content/group-photos/content.yaml) — newest entry by `date:` is shown. Image files in [`src/content/group-photos/images/`](src/content/group-photos/images/). |
| ② | All person cards (PI, postdocs, grads, affiliates) | One [`src/content/people/<slug>.md`](src/content/people/) per person. |
| ③ | Undergrads list | [`src/content/undergrads/content.yaml`](src/content/undergrads/content.yaml) |
| ④ | Alumni list | [`src/content/alumni/content.yaml`](src/content/alumni/content.yaml) |

### Add a new lab member

1. Copy any existing `.md` in [`src/content/people/`](src/content/people/) (e.g. `nathan-cloos.md`) → rename to `firstname-lastname.md`.
2. Drop a headshot into [`src/content/people/images/`](src/content/people/images/) → name it the same slug.
3. Edit the frontmatter (top of the file between the two `---` lines):

   ```yaml
   ---
   name: "Jane Doe"
   role: "Graduate Student"      # PI | Administrative Assistant | Postdoc | Graduate Student | Affiliate
   title: "PhD, EECS"
   coAdvisor: "Josh McDermott"   # optional, delete the line if none
   avatar: "./images/jane-doe.jpg"
   website: "https://janedoe.io"
   scholar: "https://scholar.google.com/citations?user=ABC123"
   email: "jane@mit.edu"
   order: 30                     # optional, lower = earlier in the section
   ---
   ```

4. Below the second `---`, write the bio in plain paragraphs (blank line between paragraphs).

### Move someone to alumni

1. Delete (or move out of) their `.md` file in [`src/content/people/`](src/content/people/).
2. Add a block at the top of [`src/content/alumni/content.yaml`](src/content/alumni/content.yaml):

   ```yaml
   jane-doe:
     name: "Jane Doe"
     wasA: "Graduate Student"
     now: "Research Scientist, OpenAI"
     website: "https://janedoe.io"     # optional
     scholar: "https://scholar.google.com/citations?user=ABC123"
   ```

### Person detail page (`/people/<slug>/`)

Each lab member's page renders:

- Headshot, role badge, title, co-advisor (linked if known)
- The bio you wrote in the markdown body
- **Publications:** every paper in [`src/content/publications/content.yaml`](src/content/publications/content.yaml)
  whose `authors:` field contains this person's full name. Their own
  name shows in **bold**. Other authors link to their `/people/` page,
  alumni link to their website, faculty co-advisors link to their lab
  pages.

If a paper is missing or extra, add `authorAliases: ["J. Hwang", "JD Hwang"]` to the person's frontmatter — see
[`src/content/people/jaedong-hwang.md`](src/content/people/jaedong-hwang.md) for an example.

---

## Page 3 — Papers (`/publications/`)

![papers](docs/screenshots/papers.png)

```
 ┌────────────────────────────────────────────────────────────────────┐
 │  Papers                                                             │
 │  ① Filter by topic:  [All]  [Theoretical ML]  [Memory]  …            │
 ├────────────────────────────────────────────────────────────────────┤
 │  2025                                                               │
 │  ② Title (linked)                                                   │
 │     Authors — colored: maroon = current member, gray = alumnus      │
 │     ③ Venue · citation · ④ topic-tags     ⑤ [arXiv ↗ / Journal ↗]   │
 │  ─────────────────────────────────────────────────────────────────  │
 │  Title …                                                            │
 │                                                                     │
 │  2024                                                               │
 │  …                                                                  │
 └────────────────────────────────────────────────────────────────────┘
```

| Callout | What | File |
|---|---|---|
| ① | Topic filter pills + Year filter row + Search box | Auto-generated. New tags in `topics:` on a paper get a stable hash-based color and a filter pill automatically; no code edit required. To recolor or pin a topic position, edit [`src/lib/topics.ts`](src/lib/topics.ts). |
| ② | Paper title (linked) | YAML `title:` and `link:` on each entry in [`src/content/publications/content.yaml`](src/content/publications/content.yaml) |
| ③ | Venue / citation | YAML `venue:` and (optional) `citation:` |
| ④ | Topic tags | YAML `topics: ["Memory", "Theoretical ML"]` (see allowed list below) |
| ⑤ | Link pill (auto-labeled arXiv / bioRxiv / Journal etc.) | Inferred from `link:` URL — no separate field needed |

### Add a paper manually

In [`src/content/publications/content.yaml`](src/content/publications/content.yaml), add a block at the top of the year section:

```yaml
hwang2026myamazing:                # firstauthor + year + first-significant-word
  title: "My Amazing Paper"
  topics: ["Memory", "Theoretical ML"]   # optional; see list below
  authors: "Jane Doe, Ila Fiete"   # FULL names for lab members; abbreviated forms ok for externals
  year: 2026
  venue: "Nature"
  citation: "Nature 999, 1-10 (2026)"  # only if has volume/page/DOI info
  link: "https://arxiv.org/abs/2601.00001"
  annotation: "(spotlight)"        # optional, e.g. "(oral)" or "* co-first authors"
```

**Allowed topic strings** (case-sensitive):
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

A paper can have any number of topics (or none — those still show under "All").

### Add a paper automatically (OpenAlex)

```bash
pip install -r scripts/requirements.txt
python scripts/sync_publications.py
```

Writes `pending_publications.yaml` at the repo root with proposed new
entries from Ila's OpenAlex profile. Review, copy good ones into
[`src/content/publications/content.yaml`](src/content/publications/content.yaml), commit. The script never modifies your YAML directly. **A weekly GitHub Action runs the same script and opens a PR with the candidates** — see [`.github/workflows/sync-publications.yml`](.github/workflows/sync-publications.yml).

---

## Page 4 — Code (`/code/`)

![code](docs/screenshots/code.png)

Each card is one entry in [`src/content/projects/content.yaml`](src/content/projects/content.yaml). Cards are sorted newest-first; the year pill in the corner comes from the `year:` field.

```yaml
my-project:
  name: "My Project"
  year: 2026
  description: |
    Multi-line description of what the code does.
  githubUrl: "https://github.com/FieteLab/my-project"
  paperSlug: "doe2026myproject"     # references publications/content.yaml
  otherLinks:
    - { label: "Demo", url: "https://example.com" }
```

**`paperSlug:`** points at the matching entry in `publications/content.yaml`. The `/code` page pulls authors / title / venue / year / link from there, so a citation never needs to be retyped.

---

## Page 5 — Contact (`/contact/`)

All editable text lives in [`src/content/site/contact.md`](src/content/site/contact.md).

```yaml
---
intro: "Get in touch with the lab."
cards:
  - title: "Address"
    body: |
      MIT Department of …<br/>
      Building 46, Suite 5065<br/>
      …
  - title: "Administrative Contact"
    body: |
      <strong>Name</strong><br/>
      Role<br/>
      <a href="mailto:user@mit.edu">user@mit.edu</a>
---
```

Each card maps 1:1 to a card on the page. Add a card by appending
another `- title: …` block. Simple HTML (`<br/>`, `<strong>`, `<a>`) is
allowed inside `body`.

---

## Local preview

```bash
npm install      # only the first time
npm run dev      # http://localhost:4321 — auto-reloads on save
```

If you don't have Node.js, install it from <https://nodejs.org/> (LTS).

## Push your changes

```bash
git add <files-you-changed>
git commit -m "describe what you did"
git push
```

The site rebuilds automatically. Watch for green/red on the
[Actions tab](https://github.com/FieteLab/fietelab.github.io/actions); a red ❌ means the
build failed and you need to look at what broke.

## If something goes wrong

Every change is versioned. On GitHub:

1. **Commits** view → find the last commit before the breakage.
2. Click **Revert**.
3. Merge the auto-generated revert PR.

Or ask anyone comfortable with git to roll back for you.
