import { defineCollection, z } from 'astro:content'
import { glob, file } from 'astro/loaders'

const people = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/people' }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.enum([
        'PI',
        'Administrative Assistant',
        'Postdoc',
        'Graduate Student',
        'Affiliate',
      ]),
      title: z.string(),
      coAdvisor: z.string().optional(),
      avatar: image().optional(),
      website: z.string().url().optional(),
      email: z.string().email().optional(),
      scholar: z.string().url().optional(),
      github: z.string().url().optional(),
      linkedin: z.string().url().optional(),
      order: z.number().optional(),
      // Override or extend automatic author-name matching used to attach
      // papers to this person on their detail page. e.g. ["JD Hwang", "J. Hwang"]
      authorAliases: z.array(z.string()).optional(),
    }),
})

const undergrads = defineCollection({
  loader: file('src/content/undergrads/content.yaml'),
  schema: z.object({
    name: z.string(),
    years: z.string(),
    now: z.string().nullable().optional(),
  }),
})

const alumni = defineCollection({
  loader: file('src/content/alumni/content.yaml'),
  schema: z.object({
    name: z.string(),
    wasA: z.string(),
    now: z.string().nullable().optional(),
    website: z.string().url().optional(),
    scholar: z.string().url().optional(),
  }),
})

const publications = defineCollection({
  loader: file('src/content/publications/content.yaml'),
  schema: z.object({
    title: z.string(),
    authors: z.string(),
    year: z.number(),
    venue: z.string(),
    citation: z.string().optional(),
    link: z.string().url().optional(),
    annotation: z.string().optional(),
    topics: z.array(z.string()).optional(),
  }),
})

const projects = defineCollection({
  loader: file('src/content/projects/content.yaml'),
  schema: z.object({
    name: z.string(),
    description: z.string(),
    year: z.number().int().optional(),
    githubUrl: z.string().url().optional(),
    // Reference an entry in publications/content.yaml by its slug. The
    // /code page pulls authors / title / venue / link from there, so a
    // citation is never duplicated.
    paperSlug: z.string().optional(),
    otherLinks: z
      .array(z.object({ label: z.string(), url: z.string().url() }))
      .optional(),
  }),
})

const news = defineCollection({
  loader: file('src/content/news/content.yaml'),
  schema: z.object({
    date: z.string(),
    text: z.string(),
    link: z.string().url().optional(),
  }),
})

const groupPhotos = defineCollection({
  loader: file('src/content/group-photos/content.yaml'),
  schema: ({ image }) =>
    z.object({
      image: image(),
      caption: z.string(),
      date: z.string().optional(),
    }),
})

const collaborators = defineCollection({
  loader: file('src/content/collaborators/content.yaml'),
  schema: z.object({
    name: z.string(),
    url: z.string().url(),
  }),
})

// Editable copy for static pages — pulled out of the .astro templates
// so non-coders can edit text without touching layout code.
const site = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/site' }),
  schema: z.object({
    // home.md
    heroTitle: z.string().optional(),
    heroTagline: z.string().optional(),
    exploreCards: z
      .array(
        z.object({
          href: z.string(),
          title: z.string(),
          description: z.string(),
        }),
      )
      .optional(),
    // contact.md
    intro: z.string().optional(),
    cards: z
      .array(z.object({ title: z.string(), body: z.string() }))
      .optional(),
  }),
})

export const collections = {
  people,
  undergrads,
  alumni,
  publications,
  projects,
  news,
  groupPhotos,
  collaborators,
  site,
}
