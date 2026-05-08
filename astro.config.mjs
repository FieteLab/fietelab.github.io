import { defineConfig } from 'astro/config'
import mdx from '@astrojs/mdx'
import sitemap from '@astrojs/sitemap'
import icon from 'astro-icon'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  site: 'https://fietelab.github.io',
  base: '/',
  image: {
    service: {
      entrypoint: 'astro/assets/services/sharp',
      config: { limitInputPixels: false },
    },
  },
  integrations: [mdx(), sitemap(), icon()],
  vite: { plugins: [tailwindcss()] },
  server: { port: 4321, host: true },
  devToolbar: { enabled: false },
})
