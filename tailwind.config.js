/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  theme: {
    extend: {},
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