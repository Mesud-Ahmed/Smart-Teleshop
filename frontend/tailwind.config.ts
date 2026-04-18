import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sand: "#f4ead7",
        clay: "#c96f3d",
        coffee: "#39261a",
        basil: "#586b4f",
      },
      fontFamily: {
        display: ["Georgia", "serif"],
        body: ["Trebuchet MS", "sans-serif"],
      },
      boxShadow: {
        card: "0 24px 60px rgba(57, 38, 26, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
