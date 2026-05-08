# Fiete Lab — Website

Static site for the [Fiete Lab](https://fietelab.mit.edu/) at MIT, designed to
be hosted on GitHub Pages.

## Structure

```
.
├── index.html          # Home
├── people.html         # PI, postdocs, students, alumni
├── publications.html   # Recent papers
├── code.html           # Open-source repos
├── contact.html        # Contact info
├── assets/
│   ├── css/style.css
│   └── js/nav.js
└── .nojekyll           # Disable Jekyll processing on GitHub Pages
```

Plain HTML/CSS — no build step.

## Local preview

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy to GitHub Pages

This repo is intended to live at
[`FieteLab/fietelab.github.io`](https://github.com/FieteLab/fietelab.github.io),
which is a *user/organization* Pages repo — anything pushed to the default
branch is served at <https://fietelab.github.io/>.

```bash
git remote add origin https://github.com/FieteLab/fietelab.github.io.git
git push -u origin main
```

In the repo's **Settings → Pages**, set the source to the `main` branch root.

## Editing content

- **People:** edit [people.html](people.html). Each member is a `<div class="person">` block.
- **Papers:** edit [publications.html](publications.html). Each paper is a `<li class="pub">` block.
- **News:** edit the `.news-list` block in [index.html](index.html).
- **Styles:** [assets/css/style.css](assets/css/style.css).
