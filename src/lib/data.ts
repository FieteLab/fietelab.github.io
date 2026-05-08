import { getCollection, type CollectionEntry } from 'astro:content'

/**
 * Build a regex that matches abbreviated forms of a person's name in a
 * publication's `authors` string. Handles common citation styles:
 *   "Jaedong Hwang" → matches "J. Hwang", "JD Hwang", "J. D. Hwang"
 *   "Ila Fiete"    → matches "I. R. Fiete", "I.R. Fiete", "IR Fiete"
 *   "Adam Joseph Eisen" → matches "A. Eisen", "A.J. Eisen", "AJ Eisen"
 */
function authorRegex(fullName: string): RegExp {
  const cleaned = fullName.replace(/\([^)]+\)/g, '').replace(/\s+/g, ' ').trim()
  const tokens = cleaned.split(' ').filter(Boolean)
  if (tokens.length < 2) return /(?!)/
  const last = tokens[tokens.length - 1].replace(/[^A-Za-z\-]/g, '')
  const firstInitial = tokens[0][0]
  // First initial, then up to 3 optional middle-initial tokens (each is a
  // capital letter possibly followed by a period and space), then the
  // surname at a word boundary. Asterisks and other annotation chars are
  // tolerated by relying on \b which treats them as boundaries.
  return new RegExp(`\\b${firstInitial}(?:[A-Z]?\\.?\\s*){0,3}${last}\\b`, 'i')
}

/**
 * Return all publications a person co-authored, newest first.
 * Uses (a) explicit `authorAliases` from the person's frontmatter as
 * substring matches, plus (b) an auto-derived regex from the full name.
 */
export async function getPublicationsByPerson(
  person: CollectionEntry<'people'>,
): Promise<CollectionEntry<'publications'>[]> {
  const aliases = person.data.authorAliases ?? []
  const re = authorRegex(person.data.name)
  const all = await getCollection('publications')
  return all
    .filter((p) => {
      const text = p.data.authors
      if (aliases.length > 0) {
        const lower = text.toLowerCase()
        if (aliases.some((a) => lower.includes(a.toLowerCase()))) return true
      }
      return re.test(text)
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
