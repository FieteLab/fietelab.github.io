import { getCollection, type CollectionEntry } from 'astro:content'

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
