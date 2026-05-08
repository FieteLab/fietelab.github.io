/**
 * Color palette for topic tags. Each topic maps to a Tailwind-100 / 700 pair
 * that has WCAG AA contrast. Adding a new topic? Add a color row below; if
 * you forget, the default stone-gray is used.
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

const FALLBACK = { bg: '#f3f4f6', text: '#374151', ring: '#d1d5db' }

export function topicColor(name: string) {
  return TOPIC_COLORS[name] ?? FALLBACK
}

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
