/**
 * @fileoverview Tailwind CSS theme extension for Mission Control.
 *
 * `content` tells Tailwind which files to scan for class names so unused utilities
 * are purged in production. The `theme.extend` block adds fleet-specific colors,
 * fonts, motion, and shadows used across layout and page components.
 */

/** @type {import('tailwindcss').Config} */
export default {
  // Globs of files Tailwind should scan when generating the utility stylesheet.
  content: [
    // Root HTML shell may contain Tailwind classes on static markup.
    "./index.html",
    // All first-party React / TS sources under src/ (pages, components, hooks, etc.).
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  // Theme customization; we only *extend* defaults so stock utilities still work.
  theme: {
    extend: {
      // Named color palettes referenced as `bg-cyber-500`, `text-surface-raised`, etc.
      colors: {
        // Cyan “cyber” accent scale used for primary CTAs and active nav chrome.
        'cyber': {
          50: '#ecfeff',   // Near-white cyan tint for subtle chip backgrounds.
          100: '#cffafe',  // Soft cyan wash for hover / selected surfaces.
          200: '#a5f3fc',  // Light cyan for borders and secondary accents.
          300: '#67e8f9',  // Mid-light cyan for decorative highlights.
          400: '#22d3ee',  // Bright cyan for icons and focus rings.
          500: '#06b6d4',  // Primary brand cyan (buttons, gradients).
          600: '#0891b2',  // Deeper cyan matching CSS --color-accent.
          700: '#0e7490',  // Dark cyan for pressed / muted accent states.
          800: '#155e75',  // Very dark cyan for text on light chips.
          900: '#164e63',  // Near-navy cyan for dense UI chrome.
          950: '#083344',  // Darkest cyan for rare high-contrast needs.
        },
        // Surface colors for cards, raised panels, and overlays (light theme).
        'surface': {
          DEFAULT: '#f8fafc', // Default panel fill (soft slate white).
          raised: '#ffffff',  // Fully raised white (modals, tooltips).
          overlay: '#eef2f6', // Slightly tinted overlay behind dialogs.
          elevated: '#e2e8f0', // Elevated strip / secondary panel fill.
        },
        // Border tokens so components can use `border-border` consistently.
        'border': {
          DEFAULT: '#cbd5e1', // Standard hairline border color.
          subtle: '#cbd5e1',  // Alias kept for semantic clarity in class names.
          strong: '#94a3b8',  // Stronger border for emphasis / focus containers.
        },
      },
      // Font stacks that match the Google Fonts loaded in index.html.
      fontFamily: {
        // Monospace for IDs, ports, logs, and Graphviz-adjacent UI.
        'mono': ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
        // Primary UI sans; Inter is preconnected in index.html.
        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      // Extra type scale smaller than Tailwind’s default `xs`.
      fontSize: {
        // Tiny labels (DAG legend chips, dense table captions).
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      // Named animation utilities consumed as `animate-fade-in`, etc.
      animation: {
        // Slow pulse for “system online” / in-progress indicators.
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        // Soft cyan glow oscillation for accent chrome.
        'glow': 'glow 2s ease-in-out infinite alternate',
        // Modal panel entrance (used by Modal component).
        'slide-up': 'slideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        // Optional downward entrance for dropdowns / banners.
        'slide-down': 'slideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        // Backdrop / shell fade used by Modal overlay.
        'fade-in': 'fadeIn 0.15s ease-out',
      },
      // Keyframe definitions backing the animation names above.
      keyframes: {
        // Alternate box-shadow intensity for the glow animation.
        glow: {
          '0%': { boxShadow: '0 0 6px rgb(8 145 178 / 0.18), 0 0 12px rgb(8 145 178 / 0.08)' },
          '100%': { boxShadow: '0 0 12px rgb(8 145 178 / 0.28), 0 0 24px rgb(8 145 178 / 0.12)' },
        },
        // Slide content up while fading in (modal body).
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        // Slide content down while fading in (menus).
        slideDown: {
          '0%': { transform: 'translateY(-8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        // Simple opacity fade for overlays.
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      // Reusable background images for decorative shells.
      backgroundImage: {
        // Light grid texture (optional page backgrounds).
        'grid-pattern': `linear-gradient(to right, rgb(148 163 184 / 0.35) 1px, transparent 1px),
                         linear-gradient(to bottom, rgb(148 163 184 / 0.35) 1px, transparent 1px)`,
        // Soft radial cyan wash from the top center of a viewport.
        'radial-glow': 'radial-gradient(ellipse at 50% 0%, rgb(8 145 178 / 0.1) 0%, transparent 50%)',
      },
      // Pair with `bg-grid-pattern` via `bg-grid` size utility.
      backgroundSize: {
        // 24px pitch for the grid pattern lines.
        'grid': '24px 24px',
      },
      // Slightly larger radii than Tailwind defaults for Mission Control cards.
      borderRadius: {
        'xl': '0.75rem',  // Card / panel corner radius.
        '2xl': '1rem',    // Modal outer corner radius.
      },
      // Elevation tokens used by Card, Modal, and hover states.
      boxShadow: {
        // Resting card elevation (subtle slate shadow).
        'card': '0 1px 2px 0 rgb(15 23 42 / 0.05), 0 1px 3px -1px rgb(15 23 42 / 0.08)',
        // Lifted card on hover (paired with `.card-hover` in index.css).
        'card-hover': '0 8px 24px -6px rgb(15 23 42 / 0.1), 0 4px 12px -4px rgb(15 23 42 / 0.06)',
        // Deep modal shadow for dialogs above the page.
        'modal': '0 24px 48px -12px rgb(15 23 42 / 0.12), 0 12px 24px -8px rgb(15 23 42 / 0.08)',
        // Small cyan glow for focused / live indicators.
        'glow-sm': '0 0 8px -2px rgb(8 145 178 / 0.2)',
        // Medium cyan glow for stronger emphasis.
        'glow-md': '0 0 16px -4px rgb(8 145 178 / 0.22)',
      },
    },
  },
  // No third-party Tailwind plugins; keep the build lean.
  plugins: [],
}
