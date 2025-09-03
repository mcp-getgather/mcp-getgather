import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  root: path.resolve(__dirname, "frontend"),
  plugins: [react(), tailwindcss()],
  build: {
    outDir: path.resolve(__dirname, "getgather", "frontend"),
    assetsDir: "__assets",
  },
  server: {
    host: "0.0.0.0",
    proxy: {
      "^/(api|brands|link/create|link/status|parse|auth|replay|__static|live|mcp|inspector)": {
        target: "http://127.0.0.1:23456/",
        changeOrigin: false,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./frontend/src"),
      "@generated": path.resolve(__dirname, "./frontend/__generated__"),
    },
  },
});
