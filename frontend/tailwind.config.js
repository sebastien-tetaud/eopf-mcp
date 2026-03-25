/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        claude: {
          purple: '#8B5CF6',
          gray: '#F3F4F6',
          text: '#374151',
          border: '#E5E7EB',
        },
      },
    },
  },
  plugins: [],
}
