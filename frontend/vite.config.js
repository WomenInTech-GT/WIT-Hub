import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';

const pages = ['index', 'career-resources', 'internships', 'events', 'projects', 'about', 'quiz'];

export default defineConfig({
  base: './',
  server: { port: 4000, strictPort: true },
  build: {
    rollupOptions: {
      input: Object.fromEntries(pages.map(page => [
        page, fileURLToPath(new URL(`./${page}.html`, import.meta.url))
      ]))
    }
  }
});
