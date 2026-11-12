import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f3ecdf",
        "paper-deep": "#e7dcc8",
        ink: "#1c1915",
        moss: "#1e5c49",
        "moss-deep": "#14382d",
        clay: "#b85c32",
        chat: "#141a17",
        "chat-raise": "#1d2622",
        cream: "#f6f1e7",
      },
      fontFamily: {
        serif: ["var(--font-fraunces)", "Iowan Old Style", "Palatino", "serif"],
        sans: ["var(--font-outfit)", "Avenir Next", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        panel: "0 20px 50px -30px rgba(28, 25, 21, 0.45)",
      },
    },
  },
  plugins: [],
};

export default config;
