/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
  ],
  // Safelist specific classes to ensure they're not purged
  safelist: [
    'w-1/2', 'w-1/3', 'w-2/3', 'w-1/4', 'w-2/4', 'w-3/4', 'w-1/5', 'w-2/5', 'w-3/5', 'w-4/5',
    'h-1/2', 'h-1/3', 'h-2/3', 'h-1/4', 'h-2/4', 'h-3/4', 'h-1/5', 'h-2/5', 'h-3/5', 'h-4/5',
    'italic'
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
      // Explicitly extend the width and height scales if needed
      width: {
        '1/2': '50%',
        '1/3': '33.333333%',
        '2/3': '66.666667%',
        '1/4': '25%',
        '2/4': '50%',
        '3/4': '75%',
        '1/5': '20%',
        '2/5': '40%',
        '3/5': '60%',
        '4/5': '80%',
      },
      height: {
        '1/2': '50%',
        '1/3': '33.333333%',
        '2/3': '66.666667%',
        '1/4': '25%',
        '2/4': '50%',
        '3/4': '75%',
        '1/5': '20%',
        '2/5': '40%',
        '3/5': '60%',
        '4/5': '80%',
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