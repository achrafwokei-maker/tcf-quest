import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Optional port overrides (used to run a throwaway test copy beside the real app).
const env = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env ?? {};

// Local only: bind to 127.0.0.1 so nothing is reachable from other devices on the network.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: Number(env.TCFQUEST_WEB_PORT ?? 5173),
    strictPort: true,
    proxy: { "/api": `http://127.0.0.1:${env.TCFQUEST_API_PORT ?? 8787}` },
  },
  preview: { host: "127.0.0.1", port: 4173 },
});
