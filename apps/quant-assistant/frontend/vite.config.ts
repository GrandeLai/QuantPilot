import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5175,
    strictPort: true,
    proxy: {
      // 市场数据来自 stock-assistant（端口 8001）
      "/api/data": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
      // 量化计算来自 Rust quant-assistant（端口 8002）
      "/api/backtest": {
        target: "http://localhost:8002",
        changeOrigin: true,
      },
      "/api/walk-forward": {
        target: "http://localhost:8002",
        changeOrigin: true,
      },
      "/api/optimize": {
        target: "http://localhost:8002",
        changeOrigin: true,
      },
      "/api/indicators": {
        target: "http://localhost:8002",
        changeOrigin: true,
      },
    },
  },
});
