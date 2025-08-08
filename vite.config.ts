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
    proxy: {
      "^/(brands|link|parse|start|auth|replay|static)": {
        target: "http://127.0.0.1:8000/",
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./frontend/src"),
    },
  },
});
