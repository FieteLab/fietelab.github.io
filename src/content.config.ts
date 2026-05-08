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
    githubUrl: z.string().url().optional(),
    paperLink: z.string().url().optional(),
    paperTitle: z.string().optional(),
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

export const collections = { people, undergrads, alumni, publications, projects, news }
