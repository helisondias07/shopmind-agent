import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#07090f",
        panel: "#10151e",
        raise: "#182131",
        line: "#2a3548",
        mist: "#93a0b5",
        snow: "#f4f7fb",
        signal: "#3ef0c1",
        ion: "#7eb0ff",
        flare: "#ff5d3a",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        signal: "0 0 0 1px rgba(62, 240, 193, 0.35), 0 16px 50px -24px rgba(62, 240, 193, 0.45)",
      },
    },
  },
  plugins: [],
};

export default config;
