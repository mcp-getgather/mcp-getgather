import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    root: path.resolve(__dirname, "frontend"),
    plugins: [react(), tailwindcss()],
    esbuild: { pure: mode === "production" ? ["console.debug"] : [] }, // Remove console.debug in production
    build: {
      outDir: path.resolve(__dirname, "getgather", "frontend"),
      assetsDir: "__assets",
    },
    define: {
      "import.meta.env.MULTI_USER_ENABLED": env.MULTI_USER_ENABLED === "true",
    },
    server: {
      host: "0.0.0.0",
      proxy: {
        "^/(api|brands|link/create|link/status|parse|auth|replay|__static|live|mcp|inspector|dpage)":
          {
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
