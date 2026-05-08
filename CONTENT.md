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
  authors: "J. Doe, I. R. Fiete"
  year: 2026
  venue: "Nature"                     # journal name or "arXiv preprint" or "NeurIPS"
  citation: "Nature 999, 1-10 (2026)" # optional but nice to include
  link: "https://arxiv.org/abs/2601.00001"
  annotation: "(spotlight)"           # optional — used for awards / co-first / co-senior notes
```

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
