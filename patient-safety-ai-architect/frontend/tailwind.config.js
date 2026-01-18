/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Patient Safety Theme Colors
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // Severity colors
        severity: {
          nearMiss: '#94a3b8',   // Gray - Near Miss
          noHarm: '#22c55e',     // Green - No Harm
          mild: '#eab308',       // Yellow - Mild
          moderate: '#f97316',   // Orange - Moderate
          severe: '#ef4444',     // Red - Severe
          death: '#7f1d1d',      // Dark Red - Death
        },
      },
      fontFamily: {
        sans: ['Pretendard', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
