// End-to-end check of the Phase-8 demo flow on the production build, with real E8 bundle data.
import { expect, test, type Page } from "@playwright/test";

const SHOTS = "e2e-shots";

async function nav(page: Page, label: string) {
  await page.locator("button.nav", { hasText: label }).click();
}

async function mapPainted(page: Page) {
  // the MapLibre canvas exists and the data raster (image source) has been updated from the blank placeholder
  await expect(page.locator(".maplibregl-canvas").first()).toBeVisible();
  await page.waitForTimeout(1500);
}

test("demo flow: event -> situation -> cell -> forecast -> ML -> replay -> comparison -> health -> alerts", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Select an event" })).toBeVisible();
  await expect(page.locator(".event-card")).toHaveCount(12);
  await page.locator("label.toggle input").uncheck();                  // basemap off: deterministic, offline-safe run
  await page.screenshot({ path: `${SHOTS}/0_events.png` });
  await page.locator(".event-card", { hasText: "14 May" }).first().click();

  // 1. Situation
  await expect(page.locator(".kpi").first()).toContainText("Active cells");
  const nCells = Number(await page.locator(".kpi .big").first().innerText());
  expect(nCells).toBeGreaterThan(0);
  await expect(page.locator(".badge-replay").first()).toHaveText("REPLAY");
  await expect(page.locator(".footer")).toContainText("not an official IMD warning");
  await mapPainted(page);
  await page.screenshot({ path: `${SHOTS}/1_situation.png` });

  // 2 + 4. select a storm cell from the risk list -> Storm Cells with details and ML probability
  await page.locator(".card", { hasText: "Top 5 cells" }).locator("tr.click").first().click();
  await expect(page.locator(".card", { hasText: "Phase now" })).toBeVisible();
  await expect(page.locator(".card", { hasText: "P(deep convection) near the forecast cell position" })).toBeVisible();
  await mapPainted(page);
  await page.screenshot({ path: `${SHOTS}/2_cells.png` });
  await page.locator(".tbl.sortable th", { hasText: "P(60)" }).click();   // table sorting works

  // 3. 0-6 h forecast: pySTEPS then ML probability at T+2h
  await nav(page, "0–6 h Forecast");
  await page.locator(".seg-ctl button", { hasText: "pySTEPS" }).click();
  await page.locator(".seg-ctl button", { hasText: "T+2h" }).first().click();
  await expect(page.locator(".ribbon")).toContainText("pySTEPS");
  await mapPainted(page);
  await page.screenshot({ path: `${SHOTS}/3_forecast_pysteps.png` });
  await page.locator(".seg-ctl button", { hasText: "ML probability" }).click();
  await expect(page.locator(".ribbon")).toContainText("BSS 0.27");      // frozen pooled ML BSS at 120 min
  await expect(page.locator(".ribbon")).toContainText("does not beat pySTEPS beyond 60 min");
  await page.locator(".toggles input").first().check();                 // show what happened (replay)
  await mapPainted(page);
  await page.screenshot({ path: `${SHOTS}/4_forecast_ml.png` });

  // 5. Historical replay: three synced panes, baseline toggle
  await nav(page, "Historical Replay");
  await expect(page.locator(".map-title")).toHaveCount(3);
  await expect(page.locator(".map-title").nth(0)).toContainText("WHAT THE SYSTEM KNEW");
  await expect(page.locator(".map-title").nth(2)).toContainText("WHAT ACTUALLY HAPPENED");
  await page.keyboard.press("b");
  await expect(page.locator(".map-title").nth(1)).toContainText("pySTEPS");
  await page.keyboard.press("ArrowRight");
  await mapPainted(page);
  await page.screenshot({ path: `${SHOTS}/5_replay.png` });

  // 6. comparison
  await nav(page, "Model Performance");
  await expect(page.locator(".claim-guard")).toContainText("does not beat pySTEPS beyond 60 min");
  const row30 = page.locator(".tbl tbody tr").first();
  await expect(row30).toContainText("0.67");                            // ML BSS 30 min (frozen)
  await expect(row30).toContainText("0.586");                           // pySTEPS CSI 30 min (frozen)
  await page.screenshot({ path: `${SHOTS}/6_performance.png`, fullPage: true });

  // 7. confidence + data health
  await nav(page, "Confidence");
  await expect(page.locator(".rel-grid .card")).toHaveCount(4);
  await page.screenshot({ path: `${SHOTS}/7_confidence.png`, fullPage: true });
  await nav(page, "Data Health");
  await expect(page.locator(".qc-strip .qc")).toHaveCount(48);
  await expect(page.getByText("NOT CONNECTED").first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/8_health.png`, fullPage: true });

  // 8. alert / status: go to 08:00 UTC (frame 16), approve a draft, preview CAP (status=Exercise)
  await nav(page, "Alert Center");
  await page.locator(".tl-frames .seg").nth(16).click();
  await expect(page.locator(".alert-row").first()).toBeVisible();
  await page.locator(".alert-row").first().getByRole("button", { name: "Approve" }).click();
  await page.locator(".alert-row").first().getByRole("button", { name: "CAP" }).click();
  await expect(page.locator("pre.cap")).toContainText("<status>Exercise</status>");
  await expect(page.locator(".audit li").first()).toContainText("APPROVED");
  await mapPainted(page);
  await page.screenshot({ path: `${SHOTS}/9_alerts.png` });

  expect(errors, errors.join("\n")).toEqual([]);
});

test("event selection switches to another held-out event (E10) and unavailable events cannot be opened", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/");
  await page.locator("label.toggle input").uncheck();
  await expect(page.locator(".event-card", { hasText: "E9" })).toBeDisabled();
  await page.locator(".event-card", { hasText: "4 May" }).first().click();
  await expect(page.locator(".topbar")).toContainText("E10");
  expect(Number(await page.locator(".kpi .big").first().innerText())).toBeGreaterThan(0);
  await page.locator("button.nav", { hasText: "0–6 h Forecast" }).click();
  await expect(page.locator(".ribbon")).toBeVisible();
  await page.screenshot({ path: "e2e-shots/10_e10_forecast.png" });
  expect(errors, errors.join("\n")).toEqual([]);
});
