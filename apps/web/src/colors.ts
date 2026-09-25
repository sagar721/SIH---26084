// Colour scales (UI_UX_SPEC §2). Pure functions: unit-tested in colors.test.ts.

export const NODATA = 255;

/** Bundle code -> brightness temperature (K); null for no data. */
export function decodeBT(code: number): number | null {
  return code === NODATA ? null : code + 160;
}

/** Bundle code -> probability 0..1; null for no data. */
export function decodeP(code: number): number | null {
  return code === NODATA ? null : code / 250;
}

type RGBA = [number, number, number, number];

// Enhanced IR: warm grey above 273 K; blue -> green -> yellow -> red -> magenta from 273 K down to 200 K.
const IR_STOPS: [number, RGBA][] = [
  [310, [120, 120, 120, 0]],
  [290, [150, 150, 150, 50]],
  [273, [205, 205, 205, 120]],
  [253, [70, 130, 200, 190]],
  [235, [40, 170, 90, 215]],
  [221, [240, 210, 40, 230]],
  [208, [215, 50, 40, 240]],
  [200, [190, 40, 190, 245]],
];

export function irColor(bt: number | null): RGBA {
  if (bt === null) return [150, 150, 150, 70];
  if (bt >= IR_STOPS[0][0]) return IR_STOPS[0][1];
  for (let i = 1; i < IR_STOPS.length; i++) {
    const [t1, c1] = IR_STOPS[i - 1];
    const [t2, c2] = IR_STOPS[i];
    if (bt >= t2) {
      const f = (t1 - bt) / (t1 - t2);
      return [0, 1, 2, 3].map((j) => Math.round(c1[j] + f * (c2[j] - c1[j]))) as RGBA;
    }
  }
  return IR_STOPS[IR_STOPS.length - 1][1];
}

// Probability: single-hue sequential, 5 bins (0.1/0.3/0.5/0.7/0.9), colour-blind-safe; below threshold transparent.
export const P_BINS = [0.1, 0.3, 0.5, 0.7, 0.9];
export const P_COLORS: RGBA[] = [
  [218, 218, 235, 170], [188, 189, 220, 195], [158, 154, 200, 215], [117, 107, 177, 230], [84, 39, 143, 240],
];

export function pBin(p: number | null): number {
  if (p === null) return -1;
  let b = -1;
  for (let i = 0; i < P_BINS.length; i++) if (p >= P_BINS[i]) b = i;
  return b;
}

export function pColor(p: number | null, threshold: number): RGBA {
  if (p === null) return [0, 0, 0, 0];
  const b = pBin(p);
  if (b < 0 || p < threshold) return [0, 0, 0, 0];
  return P_COLORS[b];
}

export const PHASE_STYLE: Record<string, { color: string; dash: number[]; width: number; label: string }> = {
  Initiation: { color: "#2A9D8F", dash: [1, 2], width: 1.5, label: "Initiation (dotted)" },
  Developing: { color: "#E9A23B", dash: [4, 2], width: 1.8, label: "Developing (dashed)" },
  Mature: { color: "#C0392B", dash: [1, 0], width: 3, label: "Mature (solid, thick)" },
  Decaying: { color: "#7D6B91", dash: [1, 0], width: 1, label: "Decaying (thin)" },
  Unclassified: { color: "#6B6457", dash: [2, 2], width: 1, label: "Unclassified (grey)" },
};

export const METHOD_STYLE: Record<string, { color: string; label: string }> = {
  persistence: { color: "#6B6457", label: "Persistence" },
  pysteps_advection: { color: "#1F6FB2", label: "pySTEPS" },
  pysteps_np31: { color: "#8FB8DE", label: "Neighbourhood pySTEPS (no fit)" },
  ml: { color: "#B23A2E", label: "ML ml-v0 (probability)" },
};
