# Fiete Lab — website

Static site for the [Fiete Lab](https://fietelab.mit.edu/) at MIT, hosted on
GitHub Pages at [fietelab.github.io](https://fietelab.github.io/).

> **Editing the site? → see [`INSTRUCTIONS.md`](INSTRUCTIONS.md).**
> Side-by-side: what you see on the page, and which file to change.

## Stack

- [Astro 5](https://astro.build/) (static site, content collections)
- [Tailwind CSS 4](https://tailwindcss.com/)
- GitHub Actions deploys on push to `main`
- Optional weekly OpenAlex sync that opens a PR with new paper candidates

## Structure

```
src/
├── pages/                     route per .astro file
├── content/                   ALL editable content lives here
│   ├── people/                  PI / postdocs / students / affiliates (one .md per person + headshot)
│   ├── alumni/, undergrads/     YAML lists
│   ├── publications/            YAML, full BibTeX-style keys
│   ├── projects/                code releases
│   ├── news/                    homepage announcements
│   └── group-photos/            lab photo carousel (currently 1, on /people)
├── components/                reusable Astro components
├── layouts/Layout.astro       page shell (header, footer)
├── lib/data.ts                helpers (author abbreviation, link map, OpenAlex dedupe)
└── consts.ts                  site name, nav items, affiliation logos
scripts/
├── sync_publications.py       OpenAlex paper sync
├── requirements.txt           Python deps (requests, PyYAML)
└── sync-state.yaml            persistent state for the sync (created on first run)
```

## Develop locally

```bash
npm install
npm run dev          # http://localhost:4321
npm run build        # produces dist/
```

## Deploy

Push to `main`. The workflow at [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml)
builds and deploys to Pages automatically. First time, in repo
**Settings → Pages**, set Source to "GitHub Actions".

## Notes

- [`INSTRUCTIONS.md`](INSTRUCTIONS.md) — visual page-by-page edit map.
- [`CONTENT.md`](CONTENT.md) — task-by-task editing guide (add a person,
  paper, code release).
- [`notes/PROJECT_NOTES.md`](notes/PROJECT_NOTES.md) — design decisions
  log and feature inventory.
- [`notes/slides.md`](notes/slides.md) — Marp deck for presenting the site.
