import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig(({ mode }) => {
  return {
    root: path.resolve(__dirname, "frontend"),
    plugins: [react(), tailwindcss(), viteSingleFile()],
    esbuild: { pure: mode === "production" ? ["console.debug"] : [] }, // Remove console.debug in production
    build: {
      outDir: path.resolve(__dirname, "getgather", "frontend"),
      assetsInlineLimit: 100000000, // inline all assets
      cssCodeSplit: false,
    },

    server: {
      host: "0.0.0.0",
      proxy: {
        "^/(api|brands|parse|auth|replay|__static|live|mcp|dpage)": {
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
  };
});
