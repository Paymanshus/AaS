import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Bricolage Grotesque'", "sans-serif"],
        body: ["'Space Grotesk'", "sans-serif"],
      },
      colors: {
        ink: "var(--ink)",
        paper: "var(--paper)",
        accent: "var(--accent)",
        accentSoft: "var(--accent-soft)",
      },
      boxShadow: {
        punch: "0 14px 40px rgba(0,0,0,0.14)",
      },
    },
  },
  plugins: [],
};

export default config;
