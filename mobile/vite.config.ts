import { defineConfig } from "vite";

// Relative asset URLs so the same build runs inside the Android app and in a browser.
export default defineConfig({
  base: "./",
  // Three.js (the 3D tab) is its own chunk, loaded only when that tab opens.
  build: { outDir: "dist", emptyOutDir: true, chunkSizeWarningLimit: 700 },
  define: { __APP_BUILD__: JSON.stringify(new Date().toISOString()) },
});
