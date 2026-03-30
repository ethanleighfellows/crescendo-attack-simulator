/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // DynamoAI brand palette
        dynamo: {
          navy:    '#0A1929',   // deepest background / header
          dark:    '#0F2137',   // card dark variant
          mid:     '#1B3A5C',   // borders, dividers
          purple:  '#7C3AED',   // primary accent
          violet:  '#6D28D9',   // hover state
          light:   '#EDE9FE',   // purple tint backgrounds
          teal:    '#06B6D4',   // secondary accent
          text:    '#1E293B',   // body text
          muted:   '#64748B',   // muted text
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.08)',
        elevated: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
    },
  },
  plugins: [],
};
