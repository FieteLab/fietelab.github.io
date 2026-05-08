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
