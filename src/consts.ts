export const SITE = {
  name: 'The Fiete Lab',
  title: 'The Fiete Lab @ MIT',
  description:
    'The Fiete Lab studies the dynamics and coding principles that underlie computation in the brain.',
  href: 'https://fietelab.github.io/',
  author: 'Fiete Lab',
  locale: 'en-US',
} as const

export const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/people', label: 'People' },
  { href: '/publications', label: 'Papers' },
  { href: '/code', label: 'Code' },
  { href: '/contact', label: 'Contact' },
] as const

export const SOCIAL_LINKS = [
  { href: 'https://github.com/FieteLab', label: 'GitHub' },
  { href: 'https://scholar.google.com/citations?user=uE-CihIAAAAJ', label: 'Scholar' },
] as const

export const AFFILIATIONS = [
  { name: 'MIT Department of Brain and Cognitive Sciences', href: 'https://bcs.mit.edu/' },
  { name: 'McGovern Institute for Brain Research', href: 'https://mcgovern.mit.edu/' },
  { name: 'K. Lisa Yang Integrative Computational Neuroscience Center', href: 'https://icon.mit.edu/' },
] as const
