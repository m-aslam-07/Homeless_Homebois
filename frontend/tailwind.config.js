/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3A6361',    // Darkest Teal - Main headers, primary buttons, darker backgrounds
          dark: '#2D4F4D',       // Darker shade for hover states
          light: '#4A7A78',      // Lighter shade for subtle variations
        },
        secondary: {
          DEFAULT: '#6BA368',    // Medium Green - Success states, accents, secondary buttons
          dark: '#5A8F58',       // Darker shade for hover states
          light: '#7CB37A',      // Lighter shade for subtle variations
        },
        accent: {
          DEFAULT: '#D3D28C',    // Tan/Khaki - Borders, cards, subtle highlights
          dark: '#C4C378',       // Darker shade
          light: '#E2E1A0',      // Lighter shade
        },
        background: {
          DEFAULT: '#F1F4A6',    // Pale Yellow - Main app background, light container backgrounds
          dark: '#E8EB9A',       // Slightly darker for contrast
        },
      },
    },
  },
  plugins: [],
}
