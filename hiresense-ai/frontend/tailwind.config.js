/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0B1220",
          900: "#111A2E",
          800: "#1B2740",
          700: "#28365300",
        },
        slate: {
          925: "#0E1524",
        },
        teal: {
          accent: "#2FD1B8",
        },
        amber: {
          accent: "#F5A623",
        },
        surface: "#F6F7FB",
      },
      fontFamily: {
        display: ["Segoe UI", "system-ui", "-apple-system", "sans-serif"],
        body: ["Segoe UI", "system-ui", "-apple-system", "sans-serif"],
        mono: ["SFMono-Regular", "Consolas", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
