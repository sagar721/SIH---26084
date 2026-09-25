// Bundle loading and raster decoding. All data are static files from pipelines/replay/build_bundle.py.
import type { Bundle, CellForecast, EventCard } from "./types";
import { decodeBT, decodeP, irColor, pColor } from "./colors";

const ROOT = "./bundles";

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return (await r.json()) as T;
}

export const loadIndex = () => getJSON<{ default: string; events: EventCard[] }>(`${ROOT}/index.json`);

export async function loadBundle(event: string): Promise<Bundle> {
  const b = `${ROOT}/${event}`;
  const [manifest, skill, health, places, alerts, scores, tracks] = await Promise.all([
    getJSON<Bundle["manifest"]>(`${b}/manifest.json`), getJSON<Bundle["skill"]>(`${b}/skill.json`),
    getJSON<Bundle["health"]>(`${b}/health.json`), getJSON<Bundle["places"]>(`${b}/places.json`),
    getJSON<Bundle["alerts"]>(`${b}/alerts.json`), getJSON<Bundle["scores"]>(`${b}/scores.json`),
    getJSON<Bundle["tracks"]>(`${b}/tracks.json`),
  ]);
  return { manifest, skill, health, places, alerts, scores, tracks };
}

const jsonCache = new Map<string, Promise<unknown>>();
function cachedJSON<T>(url: string): Promise<T> {
  if (!jsonCache.has(url)) jsonCache.set(url, getJSON<T>(url));
  return jsonCache.get(url) as Promise<T>;
}

export const pad2 = (n: number) => String(n).padStart(2, "0");
export const pad3 = (n: number) => String(n).padStart(3, "0");
export const cellsUrl = (ev: string, frame: number) => `${ROOT}/${ev}/cells/f${pad2(frame)}.geojson`;
export const contourUrl = (ev: string, frame: number) => `${ROOT}/${ev}/contours/f${pad2(frame)}.geojson`;
export const loadCells = (ev: string, frame: number) => cachedJSON<GeoJSON.FeatureCollection>(cellsUrl(ev, frame));
export const loadContours = (ev: string, frame: number) => cachedJSON<GeoJSON.FeatureCollection>(contourUrl(ev, frame));
export const loadCellForecasts = (ev: string, issue: number) =>
  cachedJSON<Record<string, CellForecast>>(`${ROOT}/${ev}/cellfc/i${pad2(issue)}.json`);

export type Layer =
  | { kind: "obs"; frame: number }
  | { kind: "pysteps"; issue: number; lead: number }
  | { kind: "ml"; issue: number; lead: number };

export function layerUrl(ev: string, l: Layer): string {
  if (l.kind === "obs") return `${ROOT}/${ev}/obs/f${pad2(l.frame)}.png`;
  return `${ROOT}/${ev}/fc/${l.kind}_i${pad2(l.issue)}_l${pad3(l.lead)}.png`;
}

// ---- 8-bit data tiles -> Uint8Array (red channel), LRU-cached ----
const codeCache = new Map<string, Promise<{ w: number; h: number; data: Uint8Array }>>();
const MAX_TILES = 160;

export function loadCodes(url: string) {
  const hit = codeCache.get(url);
  if (hit) {
    codeCache.delete(url);
    codeCache.set(url, hit);
    return hit;
  }
  const p = new Promise<{ w: number; h: number; data: Uint8Array }>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas");
      c.width = img.width; c.height = img.height;
      const ctx = c.getContext("2d", { willReadFrequently: true })!;
      ctx.drawImage(img, 0, 0);
      const rgba = ctx.getImageData(0, 0, img.width, img.height).data;
      const data = new Uint8Array(img.width * img.height);
      for (let i = 0; i < data.length; i++) data[i] = rgba[i * 4];
      resolve({ w: img.width, h: img.height, data });
    };
    img.onerror = () => reject(new Error(`tile ${url} failed to load`));
    img.src = url;
  });
  codeCache.set(url, p);
  if (codeCache.size > MAX_TILES) codeCache.delete(codeCache.keys().next().value as string);
  return p;
}

/** Colourise a decoded tile into a data URL for a MapLibre image source. */
export async function renderLayer(ev: string, l: Layer, pThreshold = 0.1): Promise<string> {
  const { w, h, data } = await loadCodes(layerUrl(ev, l));
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const ctx = c.getContext("2d")!;
  const img = ctx.createImageData(w, h);
  const px = img.data;
  for (let i = 0; i < data.length; i++) {
    let rgba: number[];
    if (l.kind === "ml") {
      rgba = pColor(decodeP(data[i]), pThreshold);
    } else if (l.kind === "pysteps" && data[i] === 255) {
      const x = i % w, y = (i / w) | 0;          // hatched: no pySTEPS forecast (inflow edge / outside grid)
      rgba = (x + y) % 7 < 2 ? [120, 120, 120, 120] : [0, 0, 0, 0];
    } else {
      rgba = irColor(decodeBT(data[i]));
    }
    px[i * 4] = rgba[0]; px[i * 4 + 1] = rgba[1]; px[i * 4 + 2] = rgba[2]; px[i * 4 + 3] = rgba[3];
  }
  ctx.putImageData(img, 0, 0);
  return c.toDataURL("image/png");
}

/** Value readout at a lon/lat from a decoded tile (Web-Mercator display grid). */
export async function sampleLayer(ev: string, l: Layer, lon: number, lat: number,
                                  b: { west: number; south: number; east: number; north: number }) {
  const { w, h, data } = await loadCodes(layerUrl(ev, l));
  const merc = (la: number) => Math.log(Math.tan(Math.PI / 4 + (la * Math.PI) / 360));
  const x = Math.floor(((lon - b.west) / (b.east - b.west)) * w);
  const y = Math.floor(((merc(b.north) - merc(lat)) / (merc(b.north) - merc(b.south))) * h);
  if (x < 0 || y < 0 || x >= w || y >= h) return null;
  const code = data[y * w + x];
  return l.kind === "ml" ? decodeP(code) : decodeBT(code);
}
