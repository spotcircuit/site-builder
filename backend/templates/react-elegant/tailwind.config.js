/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '{{COLOR_PRIMARY}}',
        secondary: '{{COLOR_SECONDARY}}',
      },
      fontFamily: {
        heading: ['{{FONT_HEADING}}', 'sans-serif'],
        body: ['{{FONT_BODY}}', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
