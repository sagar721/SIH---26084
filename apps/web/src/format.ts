// Formatting helpers (monospace readouts). Pure; unit-tested.

export const fmt = (v: number | null | undefined, d = 2) => (v === null || v === undefined || !Number.isFinite(v) ? "—" : v.toFixed(d));

export function utcIst(iso: string): { utc: string; ist: string; date: string } {
  const t = new Date(iso);
  const hhmm = (d: Date) => `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
  const ist = new Date(t.getTime() + 330 * 60000);
  return { utc: hhmm(t), ist: hhmm(ist), date: t.toISOString().slice(0, 10) };
}

export function addMinutes(iso: string, min: number): string {
  return new Date(new Date(iso).getTime() + min * 60000).toISOString().replace(/\.000Z$/, "Z");
}

export const leadLabel = (m: number) => (m === 0 ? "T+0" : m < 60 ? `T+${m}m` : `T+${m / 60}h`);

/** Destination point from lon/lat, bearing (deg from north) and distance (km); spherical earth, display only. */
export function destination(lon: number, lat: number, bearing: number, km: number): [number, number] {
  const R = 6371, d = km / R, b = (bearing * Math.PI) / 180;
  const p1 = (lat * Math.PI) / 180, l1 = (lon * Math.PI) / 180;
  const p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(b));
  const l2 = l1 + Math.atan2(Math.sin(b) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2));
  return [(l2 * 180) / Math.PI, (p2 * 180) / Math.PI];
}

/** Keys of the frozen per-issue tables look like "2026-05-14 08:00:00"; manifest times are ISO with Z. */
export const issueKey = (iso: string) => iso.replace("T", " ").replace("Z", "");
