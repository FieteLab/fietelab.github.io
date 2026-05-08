# Fiete Lab — website

Static site for the [Fiete Lab](https://fietelab.mit.edu/) at MIT.
Built with [Astro 5](https://astro.build/) + Tailwind 4. Deployed to
GitHub Pages at `fietelab.github.io`.

## How it's organized

```
src/
├── content/                    ← all editable content lives here
│   ├── people/                  PI, postdocs, students, affiliates (one .md per person)
│   ├── people/images/           headshots
│   ├── alumni/content.yaml      group alumni
│   ├── undergrads/content.yaml  undergraduate researchers
│   ├── publications/content.yaml  full paper list
│   ├── projects/content.yaml    open-source code releases
│   └── news/content.yaml        homepage announcements
├── content.config.ts            collection schemas (don't edit unless you know Zod)
├── components/                  reusable Astro components
├── layouts/Layout.astro         shared page shell (header + footer)
├── pages/                       one .astro file per route (/, /people, /publications, ...)
├── lib/data.ts                  helpers for sorting people / grouping papers
├── consts.ts                    site name, nav links, social links
└── styles/global.css            Tailwind + theme tokens
```

**Editing content?** See **[CONTENT.md](CONTENT.md)** — non-coder friendly.

## Develop locally

```bash
npm install
npm run dev          # http://localhost:4321
npm run build        # produces dist/
npm run preview      # serves dist/ for a final check
```

## Deploy

The repo is intended to live at
[`FieteLab/fietelab.github.io`](https://github.com/FieteLab/fietelab.github.io).

Pushes to `main` are built and deployed automatically by the GitHub Actions
workflow at [.github/workflows/deploy.yml](.github/workflows/deploy.yml).
The first time you deploy, go to **Settings → Pages** on the GitHub repo
and set "Source" to "GitHub Actions".

## Stack

- [Astro 5](https://astro.build/) — content collections, MDX, image optimization via `sharp`.
- [Tailwind CSS 4](https://tailwindcss.com/) — styling via `@tailwindcss/vite`.
- [astro-icon](https://www.astroicon.dev/) — Lucide icons (currently unused; ready when needed).
