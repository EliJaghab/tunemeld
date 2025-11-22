import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import fs from "fs";

export default defineConfig({
  plugins: [
    react({
      jsxRuntime: "automatic",
    }),
    {
      name: "serve-static-files",
      enforce: "post", // Run after Vite's internal middleware and React plugin
      configureServer(server) {
        // Use a single middleware that handles all static file serving
        // This runs LAST, after Vite has processed all module requests
        server.middlewares.use((req, res, next) => {
          if (!req.url) {
            return next();
          }

          // CRITICAL: Let Vite handle ALL module-related requests first
          // This includes React Refresh, HMR, and any /src/ imports
          if (
            req.url.startsWith("/@") ||
            req.url.startsWith("/node_modules") ||
            req.url.startsWith("/src/") ||
            req.url.includes("react-refresh") ||
            req.url.includes("@react-refresh") ||
            req.url.includes("?") || // Query params (HMR uses these)
            req.url.startsWith("/@vite") ||
            req.url.startsWith("/@id")
          ) {
            return next();
          }

          // Serve static images from images/ directory
          if (req.url.startsWith("/images/")) {
            const imagePath = path.join(__dirname, req.url);
            if (fs.existsSync(imagePath) && fs.statSync(imagePath).isFile()) {
              const ext = path.extname(imagePath).toLowerCase();
              const mimeTypes: Record<string, string> = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".svg": "image/svg+xml",
                ".gif": "image/gif",
                ".webp": "image/webp",
              };
              const contentType = mimeTypes[ext] || "application/octet-stream";
              res.setHeader("Content-Type", contentType);
              fs.createReadStream(imagePath).pipe(res);
              return; // Stop middleware chain
            }
          }

          // Serve v1 legacy files from src/ folder (for dev) or dist/ (for built files)
          // This handles v1 files like main.js, themeInit.js, etc.
          // Try src/ first (dev mode), then dist/ (built files)
          if (
            req.url.endsWith(".js") ||
            req.url.endsWith(".css") ||
            req.url.endsWith(".html")
          ) {
            // First try src/ (for dev mode - compiled TypeScript files)
            const srcPath = path.join(__dirname, "src", req.url);
            if (fs.existsSync(srcPath) && fs.statSync(srcPath).isFile()) {
              if (req.url.endsWith(".js")) {
                res.setHeader("Content-Type", "application/javascript");
              } else if (req.url.endsWith(".css")) {
                res.setHeader("Content-Type", "text/css");
              } else if (req.url.endsWith(".html")) {
                res.setHeader("Content-Type", "text/html");
              }
              fs.createReadStream(srcPath).pipe(res);
              return; // Stop middleware chain
            }

            // Fallback to dist/ (for built/production files)
            const distPath = path.join(__dirname, "dist", req.url);
            if (fs.existsSync(distPath) && fs.statSync(distPath).isFile()) {
              if (req.url.endsWith(".js")) {
                res.setHeader("Content-Type", "application/javascript");
              } else if (req.url.endsWith(".css")) {
                res.setHeader("Content-Type", "text/css");
              } else if (req.url.endsWith(".html")) {
                res.setHeader("Content-Type", "text/html");
              }
              fs.createReadStream(distPath).pipe(res);
              return; // Stop middleware chain
            }
          }

          // If we get here, let Vite handle it (or 404)
          next();
        });
      },
    },
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@/components": path.resolve(__dirname, "./src/components"),
      "@/config": path.resolve(__dirname, "./src/config"),
      "@/services": path.resolve(__dirname, "./src/services"),
      "@/utils": path.resolve(__dirname, "./src/utils"),
      "@/routing": path.resolve(__dirname, "./src/routing"),
      "@/state": path.resolve(__dirname, "./src/state"),
      "@/types": path.resolve(__dirname, "./src/types"),
      "@/v2": path.resolve(__dirname, "./src/v2"),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: false,
    sourcemap: false,
    rollupOptions: {
      input: {
        v2: path.resolve(__dirname, "index-v2.html"),
      },
      output: {
        manualChunks: {
          "react-vendor": ["react", "react-dom", "react-router-dom"],
          "three-vendor": [
            "three",
            "@react-three/fiber",
            "@react-three/postprocessing",
            "postprocessing",
          ],
        },
      },
    },
  },
  server: {
    port: 3000,
    open: "/index-v2.html",
  },
  css: {
    postcss: "./postcss.config.cjs",
  },
});
