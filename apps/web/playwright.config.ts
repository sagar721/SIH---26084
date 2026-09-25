import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  timeout: 120_000,
  use: { baseURL: "http://localhost:4173", viewport: { width: 1440, height: 900 }, launchOptions: { args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] } },
  webServer: { command: "npm run preview", url: "http://localhost:4173", reuseExistingServer: true, timeout: 60_000 },
  reporter: [["list"]],
});
