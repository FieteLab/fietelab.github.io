/**
 * Hand-picked colors for the canonical topic taxonomy carried over from the
 * original WordPress site. Topics not in this list get an auto-generated
 * color via `generateColor()` below, so adding a new topic to a paper
 * "just works" — no edit required here unless you specifically want a
 * curated palette for it.
 */
const TOPIC_COLORS: Record<string, { bg: string; text: string; ring: string }> = {
  'Theoretical ML': { bg: '#dbeafe', text: '#1e40af', ring: '#93c5fd' },
  'Biologically plausible gradient learning': { bg: '#ede9fe', text: '#6d28d9', ring: '#c4b5fd' },
  'Module/structure emergence': { bg: '#fef3c7', text: '#92400e', ring: '#fcd34d' },
  'Continuous attractors in the brain': { bg: '#e0e7ff', text: '#3730a3', ring: '#a5b4fc' },
  'Error-correcting codes': { bg: '#ffe4e6', text: '#be123c', ring: '#fda4af' },
  'Inferring neural connectivity': { bg: '#d1fae5', text: '#047857', ring: '#6ee7b7' },
  Memory: { bg: '#ffedd5', text: '#9a3412', ring: '#fdba74' },
  'Decision making': { bg: '#ccfbf1', text: '#115e59', ring: '#5eead4' },
  'Navigation circuits and spatial cognition': { bg: '#dcfce7', text: '#166534', ring: '#86efac' },
  'Condensed-matter physics': { bg: '#e7e5e4', text: '#44403c', ring: '#a8a29e' },
}

/**
 * Stable, deterministic hue per unknown topic name (FNV-1a-style hash).
 * Same name always maps to the same color, so the page stays visually
 * consistent across builds even though no one curated it.
 */
function generateColor(name: string) {
  let hash = 2166136261 >>> 0
  for (const ch of name) {
    hash ^= ch.charCodeAt(0)
    hash = Math.imul(hash, 16777619) >>> 0
  }
  const hue = hash % 360
  return {
    bg: `hsl(${hue}, 65%, 92%)`,
    text: `hsl(${hue}, 60%, 32%)`,
    ring: `hsl(${hue}, 60%, 75%)`,
  }
}

export function topicColor(name: string) {
  return TOPIC_COLORS[name] ?? generateColor(name)
}

/**
 * Preferred display order for the curated topics. Topics not on this list
 * still appear — they slot in alphabetically after the curated ones.
 */
export const TOPIC_ORDER = [
  'Theoretical ML',
  'Biologically plausible gradient learning',
  'Module/structure emergence',
  'Continuous attractors in the brain',
  'Error-correcting codes',
  'Inferring neural connectivity',
  'Memory',
  'Decision making',
  'Navigation circuits and spatial cognition',
  'Condensed-matter physics',
] as const

/**
 * Sort topics so curated ones come first in their declared order, then any
 * new topic by name. Used by /publications to build the filter row.
 */
export function orderTopics(topics: Iterable<string>): string[] {
  const orderIdx = (t: string) => {
    const i = (TOPIC_ORDER as readonly string[]).indexOf(t)
    return i === -1 ? Number.POSITIVE_INFINITY : i
  }
  return [...new Set(topics)].sort((a, b) => {
    const ia = orderIdx(a), ib = orderIdx(b)
    return ia !== ib ? ia - ib : a.localeCompare(b)
  })
}
