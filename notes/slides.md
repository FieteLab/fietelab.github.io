---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    background: #ffffff;
    color: #1a1a1a;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  section.lead {
    background: linear-gradient(135deg, #14060c 0%, #45091c 55%, #8a1538 100%);
    color: #fff;
  }
  h1 { color: #8a1538; }
  section.lead h1 { color: #fff; }
  code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }
  blockquote {
    border-left: 4px solid #8a1538;
    color: #4a5160;
    font-style: italic;
  }
  .small { font-size: 0.75em; }
---

<!-- _class: lead -->

# The Fiete Lab website

A guided tour, for lab members, of the new GitHub Pages site.

<small>github.com/FieteLab/fietelab.github.io</small>

---

## Why we redid it

- Old site was on WordPress: hard to keep current, slow, prone to plugin drift
- New site is just files in git: anyone with a GitHub account can edit a paper, news item, or person — without learning Astro or CSS
- Everything reproducible, versioned, free to host

---

## What changed

| Old (WordPress) | New (this site) |
|---|---|
| Visual editor | Plain Markdown / YAML files |
| One person updates | Anyone via PR |
| Manual paper entry | Weekly OpenAlex bot opens a PR with new candidates |
| Hand-curated topics | Same topics, but rendered with colored filter chips |
| `<wpforms>` and friends | None of that |

---

## Stack

- **[Astro 5](https://astro.build/)** — static site, content collections
- **[Tailwind CSS 4](https://tailwindcss.com/)** — styling
- **GitHub Pages** — hosting (free, custom-domain-ready)
- **GitHub Actions** — auto-deploy on `git push`
- **OpenAlex** — open replacement for Google Scholar API

No backend, no database. Everything renders to plain HTML at build time.

---

## Repository layout

```
src/
├── content/                    ← all editable content lives here
│   ├── people/                  one .md per current member
│   ├── alumni/, undergrads/     YAML lists
│   ├── publications/            YAML, BibTeX-style keys
│   ├── projects/                code releases
│   ├── news/                    homepage announcements
│   └── group-photos/
├── pages/                       one .astro file per route
└── components/, layouts/, lib/  the actual code
```

> Edit `src/content/`. Don't touch the rest unless you're changing layout.

---

## Adding a person — full walkthrough

1. Drop their headshot into `src/content/people/images/`
2. Copy any existing `.md` (e.g. `nathan-cloos.md`) → rename to `firstname-lastname.md`
3. Edit the YAML frontmatter:

```yaml
---
name: "Jane Doe"
role: "Graduate Student"
title: "PhD, EECS"
avatar: "./images/jane-doe.jpg"
website: "https://janedoe.io"
scholar: "https://scholar.google.com/citations?user=ABC"
---

Bio paragraphs go here.
```

4. `git push`. The site rebuilds itself.

---

## Adding a paper

```yaml
hwang2026myamazing:                    # firstauthor + year + first-word
  title: "My Amazing Paper"
  authors: "Jane Doe, Ila Fiete"       # full names for lab members
  year: 2026
  venue: "Nature"
  link: "https://arxiv.org/abs/2601.00001"
  topics: ["Memory", "Theoretical ML"]
```

That's it. Authors auto-link to their `/people/` page. Topic tags
appear with their canonical color. The page rebuilds.

---

## Or: let the bot do it

Every Monday a GitHub Action runs `scripts/sync_publications.py`:

1. Pulls Ila Fiete's OpenAlex profile
2. Dedupes against papers we already have (DOI / arXiv / title)
3. Opens a PR titled "OpenAlex sync: N new candidate(s)"
4. PR body lists titles + links — review in the browser, merge

Strict additive: drops are remembered, manual edits never overwritten.

---

## Author link tiers

In a paper byline, names are colored by what they link to:

- **Maroon = current lab member** → their `/people/` profile
- *Gray-italic = alumnus or external collaborator* → external site
- Plain text = unknown / outside contributor

A reader scanning a 12-author Nature paper can spot the lab members at a glance.

---

## Customization knobs (no coding)

| Want to change | File |
|---|---|
| Site title, nav items | `src/consts.ts` |
| Affiliation logos | `src/consts.ts` + `public/` |
| Banner gradient | `src/pages/index.astro` (3 hex colors) |
| Topic colors | `src/lib/topics.ts` |
| Contact info | `src/pages/contact.astro` |

For real edits, see [`INSTRUCTIONS.md`](../INSTRUCTIONS.md) — page-by-page edit map.

---

## Workflow

```bash
# locally, while editing
npm run dev      # http://localhost:4321 — auto-reloads

# when ready
git add ...
git commit -m "..."
git push
```

The site is rebuilt and redeployed in ~60 seconds. If a build fails,
a red ❌ appears on the GitHub Actions tab — click in to see what
broke.

---

<!-- _class: lead -->

## Questions?

- Visual edit map: [`INSTRUCTIONS.md`](../INSTRUCTIONS.md)
- Task recipes: [`CONTENT.md`](../CONTENT.md)
- Project status / decisions: [`notes/PROJECT_NOTES.md`](PROJECT_NOTES.md)

<small>github.com/FieteLab/fietelab.github.io</small>
