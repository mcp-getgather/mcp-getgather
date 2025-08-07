import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const OUT_DIR = path.resolve(__dirname, "getgather", "api", "frontend");

// https://vitejs.dev/config/
export default defineConfig({
  root: path.resolve(__dirname, "frontend"),
  plugins: [react()],
  build: {
    outDir: OUT_DIR,
  },
  server: {
    proxy: {
      "^/(brands|link|parse|start|auth|replay|static)|^/$": {
        target: "http://127.0.0.1:8000/",
        changeOrigin: true,
      },
    },
  },
});
