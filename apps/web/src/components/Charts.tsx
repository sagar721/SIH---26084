// Small dependency-free SVG charts. They only plot frozen numbers from the bundle; nothing is computed here.
import type { ReactNode } from "react";

export interface Series { name: string; color: string; points: { x: number; y: number | null }[]; dashed?: boolean; width?: number }

export function LineChart({ series, xLabel, yLabel, yMin, yMax, height = 180, refLine, marker, xTicks, shadeBelow }: {
  series: Series[]; xLabel: string; yLabel: string; yMin: number; yMax: number; height?: number;
  refLine?: { y: number; label: string }; marker?: number; xTicks?: number[]; shadeBelow?: number;
}) {
  const W = 340, H = height, L = 38, R = 8, T = 8, B = 30;
  const xs = series.flatMap((s) => s.points.map((p) => p.x));
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const sx = (x: number) => L + ((x - x0) / (x1 - x0 || 1)) * (W - L - R);
  const sy = (y: number) => T + (1 - (Math.max(yMin, Math.min(yMax, y)) - yMin) / (yMax - yMin)) * (H - T - B);
  const ticksY = [0, 0.25, 0.5, 0.75, 1].map((f) => yMin + f * (yMax - yMin));
  const tx = xTicks ?? Array.from(new Set(xs)).sort((a, b) => a - b);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label={`${yLabel} vs ${xLabel}`}>
      {shadeBelow !== undefined && <rect x={L} y={sy(shadeBelow)} width={W - L - R} height={H - B - sy(shadeBelow)} className="shade" />}
      {ticksY.map((t) => (
        <g key={t}><line x1={L} x2={W - R} y1={sy(t)} y2={sy(t)} className="grid" />
          <text x={L - 4} y={sy(t) + 3} className="tick" textAnchor="end">{t.toFixed(2)}</text></g>))}
      {tx.map((t) => <text key={t} x={sx(t)} y={H - B + 12} className="tick" textAnchor="middle">{t}</text>)}
      {refLine && <g><line x1={L} x2={W - R} y1={sy(refLine.y)} y2={sy(refLine.y)} className="ref" />
        <text x={W - R} y={sy(refLine.y) - 3} className="tick" textAnchor="end">{refLine.label}</text></g>}
      {marker !== undefined && <line x1={sx(marker)} x2={sx(marker)} y1={T} y2={H - B} className="marker" />}
      {series.map((s) => {
        const segs: string[] = [];
        let cur = "";
        s.points.forEach((p) => {
          if (p.y === null || !Number.isFinite(p.y)) { if (cur) segs.push(cur); cur = ""; return; }
          cur += `${cur ? "L" : "M"}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`;
        });
        if (cur) segs.push(cur);
        return <g key={s.name}>
          {segs.map((d, i) => <path key={i} d={d} fill="none" stroke={s.color} strokeWidth={s.width ?? 1.8} strokeDasharray={s.dashed ? "4 3" : undefined} />)}
          {s.points.filter((p) => p.y !== null).map((p) => <circle key={p.x} cx={sx(p.x)} cy={sy(p.y as number)} r={2.2} fill={s.color} />)}
        </g>;
      })}
      <text x={(L + W - R) / 2} y={H - 4} className="axis" textAnchor="middle">{xLabel}</text>
      <text x={10} y={(T + H - B) / 2} className="axis" textAnchor="middle" transform={`rotate(-90 10 ${(T + H - B) / 2})`}>{yLabel}</text>
    </svg>
  );
}

export function Legend({ items }: { items: { color: string; label: string; dashed?: boolean }[] }) {
  return <div className="chart-legend">{items.map((i) => (
    <span key={i.label}><svg width="18" height="8"><line x1="0" x2="18" y1="4" y2="4" stroke={i.color} strokeWidth="2"
      strokeDasharray={i.dashed ? "4 3" : undefined} /></svg>{i.label}</span>))}</div>;
}

export function Reliability({ curves, title }: { curves: { name: string; color: string; bins: { mean_p: number; obs_freq: number; n: number }[] }[]; title: string }) {
  const W = 200, H = 200, P = 26;
  const s = (v: number) => P + v * (W - 2 * P);
  const sy = (v: number) => H - P - v * (H - 2 * P);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart small" role="img" aria-label={title}>
      <line x1={s(0)} y1={sy(0)} x2={s(1)} y2={sy(1)} className="ref" />
      {[0, 0.5, 1].map((t) => <g key={t}><text x={s(t)} y={H - 10} className="tick" textAnchor="middle">{t}</text>
        <text x={P - 4} y={sy(t) + 3} className="tick" textAnchor="end">{t}</text></g>)}
      {curves.map((c) => (
        <g key={c.name}>
          <path d={c.bins.map((b, i) => `${i ? "L" : "M"}${s(b.mean_p).toFixed(1)},${sy(b.obs_freq).toFixed(1)}`).join("")}
                fill="none" stroke={c.color} strokeWidth={1.8} />
          {c.bins.map((b) => <circle key={b.mean_p} cx={s(b.mean_p)} cy={sy(b.obs_freq)} r={2.5} fill={c.color}><title>{`p=${b.mean_p.toFixed(2)} obs=${b.obs_freq.toFixed(2)} n=${b.n}`}</title></circle>)}
        </g>))}
      <text x={W / 2} y={12} className="axis" textAnchor="middle">{title}</text>
    </svg>
  );
}

export function Sparkline({ values, color, height = 34, invert, marker }: { values: (number | null)[]; color: string; height?: number;
                                                                           invert?: boolean; marker?: number }) {
  const W = 150, H = height;
  const v = values.filter((x): x is number => x !== null);
  if (v.length < 2) return <span className="muted">—</span>;
  const lo = Math.min(...v), hi = Math.max(...v);
  const sx = (i: number) => 2 + (i / (values.length - 1)) * (W - 4);
  const sy = (x: number) => { const f = (x - lo) / (hi - lo || 1); return 2 + (invert ? f : 1 - f) * (H - 4); };
  const d = values.map((x, i) => (x === null ? "" : `${i && values[i - 1] !== null ? "L" : "M"}${sx(i).toFixed(1)},${sy(x).toFixed(1)}`)).join("");
  return <svg viewBox={`0 0 ${W} ${H}`} className="spark"><path d={d} fill="none" stroke={color} strokeWidth={1.6} />
    {marker !== undefined && <line x1={sx(marker)} x2={sx(marker)} y1={0} y2={H} className="marker" />}</svg>;
}

export function Card({ title, eyebrow, children, badge, className }: { title?: string; eyebrow?: string; children: ReactNode;
                                                                       badge?: ReactNode; className?: string }) {
  return (
    <section className={`card ${className ?? ""}`}>
      {(eyebrow || title) && <header>{eyebrow && <div className="eyebrow">{eyebrow}</div>}
        {title && <h3>{title}{badge}</h3>}</header>}
      {children}
    </section>
  );
}

export function About({ children }: { children: ReactNode }) {
  return <div className="about"><div className="eyebrow">About this view</div>{children}</div>;
}
