import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.VITE_API_PROXY_TARGET;

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    hmr: {
      overlay: true,
    },
    proxy: backendTarget
      ? {
          "/api": {
            target: backendTarget,
            changeOrigin: true,
            ws: true,
          },
          "/ws": {
            target: backendTarget,
            changeOrigin: true,
            ws: true,
          },
        }
      : undefined,
  },
  build: {
    sourcemap: false,
    minify: "esbuild",
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ["react", "react-dom"],
  },
  esbuild: {
    target: "esnext",
  },
});
