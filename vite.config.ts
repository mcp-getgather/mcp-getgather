import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

// https://vitejs.dev/config/
export default defineConfig({
  root: path.resolve(__dirname, "frontend"),
  plugins: [react(), tailwindcss()],
  build: {
    outDir: path.resolve(__dirname, "getgather", "api", "frontend"),
  },
  server: {
    host: "0.0.0.0",
    proxy: {
      "^/(api|brands|link/create|link/status|parse|start|auth|replay|static|live|mcp)":
        {
          target: "http://127.0.0.1:8000/",
          changeOrigin: false,
        },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./frontend/src"),
    },
  },
});
