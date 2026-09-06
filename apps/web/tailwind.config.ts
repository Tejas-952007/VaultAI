import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: "#070A0F",
        navy: "#0F172A",
        slate: {
          800: "#1E293B",
          900: "#0F172A",
        },
        emerald: {
          500: "#10B981",
        },
        cyan: {
          500: "#06B6D4",
        },
        amber: {
          500: "#F59E0B",
        },
        alert: {
          500: "#EF4444",
        }
      },
      animation: {
        'scanline': 'scanline 8s linear infinite',
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        }
      }
    },
  },
  plugins: [],
};
export default config;