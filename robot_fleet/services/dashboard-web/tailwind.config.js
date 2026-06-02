/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cyber': {
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
          950: '#083344',
        },
        'surface': {
          DEFAULT: '#f8fafc',
          raised: '#ffffff',
          overlay: '#eef2f6',
          elevated: '#e2e8f0',
        },
        'border': {
          DEFAULT: '#cbd5e1',
          subtle: '#cbd5e1',
          strong: '#94a3b8',
        },
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
        'sans': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-up': 'slideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down': 'slideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
        'fade-in': 'fadeIn 0.15s ease-out',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 6px rgb(8 145 178 / 0.18), 0 0 12px rgb(8 145 178 / 0.08)' },
          '100%': { boxShadow: '0 0 12px rgb(8 145 178 / 0.28), 0 0 24px rgb(8 145 178 / 0.12)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      backgroundImage: {
        'grid-pattern': `linear-gradient(to right, rgb(148 163 184 / 0.35) 1px, transparent 1px),
                         linear-gradient(to bottom, rgb(148 163 184 / 0.35) 1px, transparent 1px)`,
        'radial-glow': 'radial-gradient(ellipse at 50% 0%, rgb(8 145 178 / 0.1) 0%, transparent 50%)',
      },
      backgroundSize: {
        'grid': '24px 24px',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'card': '0 1px 2px 0 rgb(15 23 42 / 0.05), 0 1px 3px -1px rgb(15 23 42 / 0.08)',
        'card-hover': '0 8px 24px -6px rgb(15 23 42 / 0.1), 0 4px 12px -4px rgb(15 23 42 / 0.06)',
        'modal': '0 24px 48px -12px rgb(15 23 42 / 0.12), 0 12px 24px -8px rgb(15 23 42 / 0.08)',
        'glow-sm': '0 0 8px -2px rgb(8 145 178 / 0.2)',
        'glow-md': '0 0 16px -4px rgb(8 145 178 / 0.22)',
      },
    },
  },
  plugins: [],
}
