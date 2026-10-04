import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Must match the port `agentcore dev --port` is started on (Makefile AGENT_PORT).
const agent = `http://127.0.0.1:${process.env.AGENT_PORT ?? "8080"}`;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/invocations": { target: agent, changeOrigin: true },
      "/ping": { target: agent, changeOrigin: true },
    },
  },
});
