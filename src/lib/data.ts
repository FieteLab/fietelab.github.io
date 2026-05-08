import { getCollection, type CollectionEntry } from 'astro:content'

/**
 * Abbreviate one author name for display.
 *   "Jaedong Hwang"           → "J. Hwang"
 *   "Adam Joseph Eisen"       → "A. Eisen"
 *   "Qiyao (Catherine) Liang" → "Q. Liang"
 *   "I. R. Fiete"             → "I. R. Fiete"   (already abbreviated, untouched)
 *   "S. J. Lee"               → "S. J. Lee"
 *   "International Brain Laboratory" → unchanged
 */
export function abbreviateAuthor(author: string): string {
  // Preserve trailing markers like "*", "+" that denote co-first / co-senior
  const trailingMatch = author.match(/^(.*?)([\*\+]+)\s*$/)
  const trailing = trailingMatch ? trailingMatch[2] : ''
  const core = (trailingMatch ? trailingMatch[1] : author).trim()

  const cleaned = core.replace(/\([^)]+\)/g, '').replace(/\s+/g, ' ').trim()
  const tokens = cleaned.split(' ').filter(Boolean)
  if (tokens.length < 2) return author

  // Heuristic: if the FIRST token looks like a spelled-out first name
  // (>=3 chars, starts with a capital, contains lowercase, no period),
  // abbreviate it; otherwise return the original (already abbreviated).
  const first = tokens[0]
  const looksFull = first.length >= 3 && /[a-z]/.test(first) && !first.endsWith('.')
  if (!looksFull) return author

  const last = tokens[tokens.length - 1]
  return `${first[0]}. ${last}${trailing}`
}

/** Format the comma-separated authors string with each author abbreviated. */
export function formatAuthors(authors: string): string {
  return authors
    .split(',')
    .map((a) => abbreviateAuthor(a.trim()))
    .join(', ')
}

/**
 * Build a map from canonical author full-name to a link target. Includes
 * (1) current lab members (→ /people/<slug>/), (2) alumni who have a
 * personal website on record (→ external URL), and (3) named external
 * collaborators from the `collaborators` content collection.
 */
export async function getAuthorLinkMap(): Promise<
  Map<string, { href: string; external: boolean }>
> {
  const map = new Map<string, { href: string; external: boolean }>()
  const people = await getCollection('people')
  for (const p of people) {
    map.set(p.data.name, { href: `/people/${p.id}/`, external: false })
    for (const alias of p.data.authorAliases ?? []) {
      map.set(alias, { href: `/people/${p.id}/`, external: false })
    }
  }
  const alumni = await getCollection('alumni')
  for (const a of alumni) {
    const target = a.data.website ?? a.data.scholar
    if (target) {
      map.set(a.data.name, { href: target, external: true })
    }
  }
  const collaborators = await getCollection('collaborators')
  for (const c of collaborators) {
    if (!map.has(c.data.name)) {
      map.set(c.data.name, { href: c.data.url, external: true })
    }
  }
  return map
}

/**
 * Old / alternate names a citation may use for the same venue. When we
 * check whether a citation is redundant, we accept any of these as
 * equivalent to the canonical venue. e.g. citation="Proc. ICML (2025)"
 * with venue="ICML" → redundant.
 */
const VENUE_ALIASES: Record<string, string[]> = {
  ICML: ['Proc. ICML', 'ICML, PMLR', 'ICML PMLR'],
  NeurIPS: ['Proc. NeurIPS', 'Advances in NIPS'],
  ICLR: ['Proceedings of ICLR'],
  TMLR: ['Trans. MLR', 'Transactions on Machine Learning Research'],
  UAI: [
    'PMLR Conference on Uncertainty in AI',
    'Conference on Uncertainty in AI',
  ],
  CCN: ['Conference on Cognitive Computational Neuroscience'],
  'Nature Neuroscience': ['Nature Neurosci.', 'Nature Neurosci'],
  'PLOS Computational Biology': ['PLoS Comp. Biol.'],
  'Journal of Neurophysiology': ['J. Neurophysiology'],
  'Journal of Neuroscience': ['J. Neuroscience'],
  'Journal of Applied Physics': ['J. Applied Physics'],
  'Current Opinion in Systems Biology': ['Curr. Opinion in Systems Biol.'],
  'Current Opinion in Neurobiology': ['Curr. Op. Neurobiology'],
  'Allerton Conference': [
    '50th Allerton Conf. on Communication, Control, and Computing',
  ],
}

/**
 * True when a `citation` string adds nothing on top of `venue` + `year`.
 * Accepts old venue aliases ("Proc. ICML" for "ICML") and a leading "In "
 * (book chapters / "In Advances in NIPS"). Anything with extra info — DOI,
 * arXiv ID, volume, page range, additional preprint — is kept.
 */
export function isRedundantCitation(
  citation: string,
  venue: string,
  year: number,
): boolean {
  const norm = (s: string) =>
    s.replace(/[().,;:]/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase()
  const c = norm(citation)
  const y = String(year)
  const candidates = [venue, ...(VENUE_ALIASES[venue] ?? [])]
  for (const a of candidates) {
    const v = norm(a)
    if (
      c === v ||
      c === `${v} ${y}` ||
      c === `${y} ${v}` ||
      c === `in ${v}` ||
      c === `in ${v} ${y}`
    ) {
      return true
    }
  }
  return false
}

/**
 * Return all publications a person co-authored, newest first.
 *
 * Primary match: the person's full name appears verbatim in the paper's
 *   `authors` string (this is the canonical form after the YAML rewrite).
 * Fallbacks: explicit `authorAliases` from the frontmatter, plus a
 *   permissive regex match for any abbreviated form that escaped the
 *   rewrite.
 */
export async function getPublicationsByPerson(
  person: CollectionEntry<'people'>,
): Promise<CollectionEntry<'publications'>[]> {
  const fullName = person.data.name
  const aliases = person.data.authorAliases ?? []
  const cleaned = fullName.replace(/\([^)]+\)/g, '').replace(/\s+/g, ' ').trim()
  const tokens = cleaned.split(' ').filter(Boolean)
  const last = tokens.length >= 2 ? tokens[tokens.length - 1].replace(/[^A-Za-z\-]/g, '') : ''
  const firstInitial = tokens.length >= 2 ? tokens[0][0] : ''
  const fallbackRe = last
    ? new RegExp(`\\b${firstInitial}(?:[A-Z]?\\.?\\s*){0,3}${last}\\b`, 'i')
    : /(?!)/

  const all = await getCollection('publications')
  return all
    .filter((p) => {
      const text = p.data.authors
      if (text.includes(fullName)) return true
      if (aliases.length > 0) {
        const lower = text.toLowerCase()
        if (aliases.some((a) => lower.includes(a.toLowerCase()))) return true
      }
      return fallbackRe.test(text)
    })
    .sort((a, b) => b.data.year - a.data.year)
}

const ROLE_ORDER: Record<CollectionEntry<'people'>['data']['role'], number> = {
  PI: 0,
  'Administrative Assistant': 1,
  Postdoc: 2,
  'Graduate Student': 3,
  Affiliate: 4,
}

export async function getAllPeople(): Promise<CollectionEntry<'people'>[]> {
  const people = await getCollection('people')
  return people.sort((a, b) => {
    const ra = ROLE_ORDER[a.data.role] ?? 99
    const rb = ROLE_ORDER[b.data.role] ?? 99
    if (ra !== rb) return ra - rb
    const oa = a.data.order ?? 999
    const ob = b.data.order ?? 999
    if (oa !== ob) return oa - ob
    return a.data.name.localeCompare(b.data.name)
  })
}

export async function getPeopleByRole(): Promise<
  Map<CollectionEntry<'people'>['data']['role'], CollectionEntry<'people'>[]>
> {
  const all = await getAllPeople()
  const map = new Map<
    CollectionEntry<'people'>['data']['role'],
    CollectionEntry<'people'>[]
  >()
  for (const p of all) {
    const arr = map.get(p.data.role) ?? []
    arr.push(p)
    map.set(p.data.role, arr)
  }
  return map
}

export async function getPublicationsByYear(): Promise<
  Map<number, CollectionEntry<'publications'>[]>
> {
  const pubs = await getCollection('publications')
  pubs.sort((a, b) => b.data.year - a.data.year)
  const map = new Map<number, CollectionEntry<'publications'>[]>()
  for (const p of pubs) {
    const arr = map.get(p.data.year) ?? []
    arr.push(p)
    map.set(p.data.year, arr)
  }
  return new Map([...map.entries()].sort((a, b) => b[0] - a[0]))
}
