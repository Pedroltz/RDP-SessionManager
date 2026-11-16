import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://pedroltz.github.io",
  base: "/RDP-SessionManager",
  output: "static",
  vite: {
    build: {
      // Keep the shared script cacheable across both language pages.
      assetsInlineLimit: 0
    },
    server: {
      allowedHosts: [".ngrok-free.app"]
    }
  },
  build: {
    format: "directory"
  }
});
