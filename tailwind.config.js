/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f3f9f3',
          100: '#e7f3e5',
          200: '#d1e7cd',
          300: '#aed2a7',
          400: '#83b77a',
          500: '#5a9c52',
          600: '#3d7f3a',
          700: '#326730',
          800: '#2c5129',
          900: '#254425',
          950: '#132613',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('tailwindcss/plugin')(({ addComponents }) => {
      addComponents({
        '.prose': {
          // Basic typography styles
          maxWidth: '65ch',
          color: '#374151',
          // Add more prose styles here
        },
      })
    }),
    // Add aspect-ratio plugin
    require('tailwindcss/plugin')(({ addComponents }) => {
      addComponents({
        '.aspect-w-1': {
          position: 'relative',
          paddingBottom: 'calc(var(--tw-aspect-h) / var(--tw-aspect-w) * 100%)',
          '--tw-aspect-w': '1',
        },
        '.aspect-h-1': {
          '--tw-aspect-h': '1',
        },
        // Add more aspect ratios as needed
      })
    })
  ],
} 