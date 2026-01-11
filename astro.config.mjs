import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

const repoName = "quotient-site";
const isProd = process.env.NODE_ENV === "production";

export default defineConfig({
  site: `https://simpsong00.github.io/${repoName}/`,
  base: isProd ? `/${repoName}` : "/",
  integrations: [tailwind()],
});
