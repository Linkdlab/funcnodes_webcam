import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import dts from "vite-plugin-dts";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    dts({
      insertTypesEntry: true,
    }),
  ],
  resolve: {
    alias: {},
  },
  server: {
    watch: {
      usePolling: true,
      additionalPaths: (watcher) => {
        watcher.add(path.resolve(__dirname, "src/**")); // Watch all files in the src directory
      },
    },
  },
  define: {
    "process.env.NODE_ENV": JSON.stringify(mode),
  },
  build: {
    lib: {
      entry: path.resolve(__dirname, "src/index.tsx"),
      name: "FuncNodesPlugin",
      formats: ["es", "cjs", "umd", "iife"],
      fileName: (format) => `index.${format}.js`,
    },
    rollupOptions: {
      external: ["react", "react-dom", "@linkdlab/funcnodes_react_flow"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "@linkdlab/funcnodes_react_flow": "FuncNodesReactFlow",
        },
      },
    },
  },
}));
