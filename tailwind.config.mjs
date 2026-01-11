import typography from "@tailwindcss/typography";

export default {
  content: ["./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}"],
  theme: {
    extend: {
      colors: {
        accent: "#C2410C", // deep, refined orange
      },
      typography: {
        DEFAULT: {
          css: {
            "--tw-prose-body": "#1f2937",      // neutral-800
            "--tw-prose-headings": "#111827",  // neutral-900
            "--tw-prose-links": "#C2410C",
            "--tw-prose-bold": "#111827",
            "--tw-prose-counters": "#6b7280",
            "--tw-prose-bullets": "#6b7280",
            "--tw-prose-hr": "#e5e7eb",
            "--tw-prose-quotes": "#111827",
            "--tw-prose-quote-borders": "#C2410C",
            "--tw-prose-captions": "#6b7280",
            "--tw-prose-code": "#111827",
            "--tw-prose-pre-code": "#e5e7eb",
            "--tw-prose-pre-bg": "#0f172a",   // slate-900
            "--tw-prose-th-borders": "#d1d5db",
            "--tw-prose-td-borders": "#e5e7eb",
          },
        },
      },
    },
  },
  plugins: [typography],
};
