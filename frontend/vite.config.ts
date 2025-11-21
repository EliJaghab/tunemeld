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
      name: "serve-dist-files",
      configureServer(server) {
        // Serve static images from images/ directory
        server.middlewares.use((req, res, next) => {
          if (req.url && req.url.startsWith("/images/")) {
            const imagePath = path.join(__dirname, req.url);
            if (fs.existsSync(imagePath) && fs.statSync(imagePath).isFile()) {
              // Determine MIME type based on file extension
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
              return fs.createReadStream(imagePath).pipe(res);
            }
          }
          next();
        });

        // Serve v1 compiled JS files from src/ when requested from root
        server.middlewares.use((req, res, next) => {
          if (
            req.url &&
            req.url.endsWith(".js") &&
            !req.url.startsWith("/@") &&
            !req.url.startsWith("/node_modules")
          ) {
            // Try src/ first for v1 files
            const srcPath = path.join(__dirname, "src", req.url);
            if (fs.existsSync(srcPath) && fs.statSync(srcPath).isFile()) {
              res.setHeader("Content-Type", "application/javascript");
              return fs.createReadStream(srcPath).pipe(res);
            }
          }
          next();
        });

        // Check if the requested file exists in the dist folder
        server.middlewares.use((req, res, next) => {
          if (req.url) {
            const distPath = path.join(__dirname, "dist", req.url);
            if (fs.existsSync(distPath) && fs.statSync(distPath).isFile()) {
              // Set correct MIME type
              if (req.url.endsWith(".js")) {
                res.setHeader("Content-Type", "application/javascript");
              } else if (req.url.endsWith(".css")) {
                res.setHeader("Content-Type", "text/css");
              }
              return fs.createReadStream(distPath).pipe(res);
            }
          }
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
    open: "/",
  },
  css: {
    postcss: "./postcss.config.cjs",
  },
});
