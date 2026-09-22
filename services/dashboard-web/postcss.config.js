/**
 * @fileoverview PostCSS pipeline configuration for the dashboard SPA.
 *
 * Vite invokes PostCSS whenever it processes CSS (including `src/index.css`).
 * We run Tailwind first so `@tailwind` / `@apply` directives expand into real CSS,
 * then Autoprefixer so vendor prefixes match the browserslist defaults.
 */

/** @type {import('postcss-load-config').Config} */
export default {
  // Ordered list of PostCSS plugins applied to every stylesheet Vite emits.
  plugins: {
    // Expand Tailwind directives and utility classes into concrete CSS rules.
    tailwindcss: {},
    // Add vendor prefixes (e.g. -webkit-) based on Autoprefixer defaults.
    autoprefixer: {},
  },
}
