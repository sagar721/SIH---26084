import { useEffect, useMemo, useState } from "react";
import type { Bundle, CellForecast, CellProps } from "./types";
import { loadCellForecasts, loadCells, loadContours } from "./data";
import { destination } from "./format";

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): T | null {
  const [v, setV] = useState<T | null>(null);
  useEffect(() => {
    let live = true;
    fn().then((r) => live && setV(r)).catch(() => live && setV(null));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return v;
}

export const useCells = (ev: string, frame: number) => useAsync(() => loadCells(ev, frame), [ev, frame]);
export const useContours = (ev: string, frame: number | null) =>
  useAsync(() => (frame === null ? Promise.resolve(null) : loadContours(ev, frame)), [ev, frame]);
export const useCellFc = (ev: string, issue: number | null) =>
  useAsync(() => (issue === null ? Promise.resolve(null) : loadCellForecasts(ev, issue)), [ev, issue]);

export function cellList(fc: GeoJSON.FeatureCollection | null): CellProps[] {
  return (fc?.features ?? []).map((f) => f.properties as CellProps);
}

/** Motion arrows = pySTEPS field-advection displacement over the next 30 min (frozen Phase-3 object predictions). */
export function useArrows(cells: CellProps[], fc: Record<string, CellForecast> | null): GeoJSON.FeatureCollection {
  return useMemo(() => {
    const feats: GeoJSON.Feature[] = [];
    for (const c of cells) {
      const p = fc?.[String(c.cell)]?.by_lead?.["30"]?.field_advection;
      if (!p) continue;
      const bearing = (Math.atan2(p.lon - c.lon, p.lat - c.lat) * 180) / Math.PI;
      const head = [destination(p.lon, p.lat, bearing + 150, 12), destination(p.lon, p.lat, bearing - 150, 12)];
      feats.push({ type: "Feature", properties: {}, geometry: { type: "MultiLineString",
        coordinates: [[[c.lon, c.lat], [p.lon, p.lat]], [head[0], [p.lon, p.lat], head[1]]] } });
    }
    return { type: "FeatureCollection", features: feats };
  }, [cells, fc]);
}

export function issueAt(b: Bundle, frame: number) {
  return b.manifest.issues.find((i) => i.frame === frame) ?? null;
}
