import { defineConfig } from "vite";

// Relative asset URLs so the same build runs inside the Android app and in a browser.
export default defineConfig({
  base: "./",
  build: { outDir: "dist", emptyOutDir: true },
});
