import { useState } from "react";
import type { Ctx } from "../App";
import { About, Card, Legend, LineChart } from "../components/Charts";
import { fmt, leadLabel, utcIst } from "../format";
import { METHOD_STYLE } from "../colors";
import type { Method } from "../types";

const METHODS: Method[] = ["persistence", "pysteps_advection", "pysteps_np31", "ml"];

// ------------------------------------------------------------------ 6. Persistence vs pySTEPS vs ML
export function PerformanceScreen({ ctx }: { ctx: Ctx }) {
  const s = ctx.bundle.skill;
  const [scope, setScope] = useState<string>("pooled");
  const events = Object.keys(s.by_event);
  const series = (k: "CSI" | "BSS") => METHODS.map((m) => ({
    name: m, color: METHOD_STYLE[m].color,
    points: (scope === "pooled" ? s.pooled[m] : s.by_event[scope]?.[m] ?? []).map((r) => ({ x: r.lead_min, y: (r as Record<string, number | null>)[k] })),
  }));
  const leads = [30, 60, 120, 180, 240, 360];
  const best = (L: number, k: "CSI" | "BSS") => {
    const vals = METHODS.map((m) => s.pooled[m].find((r) => r.lead_min === L)?.[k] ?? -9);
    return METHODS[vals.indexOf(Math.max(...vals))];
  };
  return (
    <div className="page">
      <div className="page-head"><div className="eyebrow">Evidence · Model performance (frozen ml-v0)</div>
        <h1>Persistence vs pySTEPS vs neighbourhood pySTEPS vs ML</h1>
        <div className="claim-guard">{s.claim_guard}</div></div>
      <div className="seg-ctl"><span className="eyebrow">Scope</span>
        <button className={scope === "pooled" ? "on" : ""} onClick={() => setScope("pooled")}>3 held-out events pooled</button>
        {events.map((e) => <button key={e} className={scope === e ? "on" : ""} onClick={() => setScope(e)}>{e.split("_")[0]} only</button>)}</div>
      <div className="two-col">
        <Card eyebrow="Probability skill" title="BSS vs training climatology (higher is better; 0 = no skill)">
          <LineChart series={series("BSS")} xLabel="lead (min)" yLabel="BSS" yMin={-1} yMax={1} refLine={{ y: 0, label: "no skill" }} shadeBelow={0} />
          <Legend items={METHODS.map((m) => ({ color: METHOD_STYLE[m].color, label: METHOD_STYLE[m].label }))} />
          <div className="small muted">Deterministic baselines enter the Brier score as 0/1 probabilities; the fair probabilistic reference is the no-fit neighbourhood pySTEPS. Axis clipped at −1 (pySTEPS reaches −1.11 at 6 h).</div>
        </Card>
        <Card eyebrow="Yes/no skill" title="CSI at p ≥ 0.5 (BT < 235 K)">
          <LineChart series={series("CSI")} xLabel="lead (min)" yLabel="CSI" yMin={0} yMax={0.7} />
          <Legend items={METHODS.map((m) => ({ color: METHOD_STYLE[m].color, label: METHOD_STYLE[m].label }))} />
          <div className="small muted">ML CSI is 0 from 150 min because its calibrated probability stays below 0.5 there.</div>
        </Card>
      </div>
      <Card eyebrow="Final comparison table" title="Held-out E8 + E10 + E11 pooled, identical pixels for every method (docs/FINAL_RESULTS.md)">
        <table className="tbl"><thead><tr><th>Lead</th>{METHODS.map((m) => <th key={m} colSpan={2}>{METHOD_STYLE[m].label}</th>)}</tr>
          <tr><th /> {METHODS.map((m) => [<th key={`${m}b`}>BSS</th>, <th key={`${m}c`}>CSI</th>])}</tr></thead><tbody>
          {leads.map((L) => <tr key={L}><td className="mono">{leadLabel(L)}</td>{METHODS.map((m) => {
            const r = s.pooled[m].find((x) => x.lead_min === L);
            return [<td key={`${m}b`} className={`mono ${best(L, "BSS") === m ? "best" : ""}`}>{fmt(r?.BSS, 2)}</td>,
                    <td key={`${m}c`} className={`mono ${best(L, "CSI") === m ? "best" : ""}`}>{fmt(r?.CSI, 3)}</td>];
          })}</tr>)}
        </tbody></table>
        <div className="small muted">Bold = best in row. Source: data/processed/ml_eval/ml-v0/metrics_pooled_lead.csv (hash in the freeze manifest). Nothing is computed in the browser.</div>
      </Card>
      <div className="two-col">
        <Card eyebrow="Phase 4 · baselines on 3 events" title="pySTEPS beats persistence on every lead, every event">
          <table className="tbl"><thead><tr><th>Lead</th><th>CSI persistence</th><th>CSI pySTEPS</th><th>events pySTEPS better</th></tr></thead><tbody>
            {s.phase4_cross_event.filter((r) => leads.includes(r.lead_min)).map((r) => <tr key={r.lead_min}><td className="mono">{leadLabel(r.lead_min)}</td>
              <td className="mono">{r.CSI_persistence.toFixed(3)}</td><td className="mono">{r.CSI_pysteps.toFixed(3)}</td><td className="mono">{r.n_events_pysteps_better} / 3</td></tr>)}
          </tbody></table>
          <div className="small muted">Useful FSS (40 km) ends at 90 min (persistence) and 120 min (pySTEPS) on every event.</div>
        </Card>
        <Card eyebrow="Phase 5 · why skill is lost" title="pySTEPS bias growth is mostly the scoring edge">
          <table className="tbl"><thead><tr><th>Event</th><th>Lead</th><th>bias</th><th>edge ×</th><th>advected area ×</th><th>intensity ×</th></tr></thead><tbody>
            {s.phase5_decomposition.filter((r) => [120, 360].includes(Number(r.lead_min))).map((r) => <tr key={`${r.event}${r.lead_min}`}>
              <td className="mono">{String(r.event).split("_")[0]}</td><td className="mono">{leadLabel(Number(r.lead_min))}</td><td className="mono">{fmt(Number(r.bias_V), 2)}</td>
              <td className="mono">{fmt(Number(r.E_edge), 2)}</td><td className="mono">{fmt(Number(r.C_advected_area), 2)}</td><td className="mono">{fmt(Number(r.G_unchanged_intensity), 2)}</td></tr>)}
          </tbody></table>
          <div className="small muted">bias = edge × advected area × intensity (exact). A decay-aware model was not built: lifecycle trends failed the pre-declared persistence test.</div>
        </Card>
      </div>
      <About><p>All numbers come from frozen held-out evaluations (Phases 4–6). The ML advantage is in probability skill, to about 4 h. It is
        mostly a calibrated neighbourhood smoothing of pySTEPS; storm-initiation skill is not demonstrated. Three events, one month and one
        region, tested backward in time: no generalisation is claimed.</p></About>
    </div>
  );
}

// ------------------------------------------------------------------ 7b. Data health
export function HealthScreen({ ctx }: { ctx: Ctx }) {
  const { bundle, frame, setFrame } = ctx;
  const h = bundle.health;
  const [showAll, setShowAll] = useState(false);
  const fr = h.frames[frame];
  return (
    <div className="page">
      <div className="page-head"><div className="eyebrow">Evidence · Data health</div><h1>Sources, gaps and provenance</h1>
        <p className="muted">{h.latency_note}</p></div>
      <div className="two-col">
        <Card eyebrow="Per source" title="Status (matches docs/DATA_REALITY.md)">
          <table className="tbl"><thead><tr><th>Source</th><th>Status</th><th>Role</th></tr></thead><tbody>
            {h.sources.map((s) => <tr key={s.source}><td>{s.source}<div className="small muted">{s.note}</div></td>
              <td><span className={`badge ${s.status.startsWith("AVAILABLE") ? "badge-ok" : "badge-muted"}`}>{s.status}</span></td><td className="small">{s.role}</td></tr>)}
          </tbody></table>
        </Card>
        <Card eyebrow="Frames" title={`${h.frames.length} half-hourly frames · ${h.frames.filter((f) => f.qc_status !== "OK").length} QC-fail (kept, flagged)`}>
          <div className="qc-strip">{h.frames.map((f) => <button key={f.frame} className={`qc ${f.qc_status === "OK" ? "ok" : "fail"} ${f.frame === frame ? "now" : ""}`}
            style={{ height: `${8 + Math.min(40, f.qc_missing_frac * 600)}px` }} title={`${utcIst(f.time_utc).utc} UTC · ${f.qc_status} · ${(f.qc_missing_frac * 100).toFixed(1)} % missing`}
            onClick={() => setFrame(f.frame)} />)}</div>
          <div className="small muted">Bar height = residual missing fraction after small-gap fill; red = frame failed QC (&gt; 5 % missing).</div>
          <div className="grid2 mono small" style={{ marginTop: 8 }}>
            <div><span className="k">Frame</span>{utcIst(fr.time_utc).utc} UTC</div><div><span className="k">QC</span>{fr.qc_status}</div>
            <div><span className="k">Missing (raw)</span>{(fr.raw_missing_frac * 100).toFixed(2)} %</div><div><span className="k">Gap-filled</span>{(fr.gapfilled_frac * 100).toFixed(2)} %</div>
            <div><span className="k">Source file</span>{fr.source_file}</div><div><span className="k">SHA-256</span>{fr.source_sha256.slice(0, 16)}…</div>
          </div>
        </Card>
      </div>
      <div className="two-col">
        <Card eyebrow="Scorable area" title="Fraction of the domain that cannot be scored (inflow edge + gaps)">
          <LineChart series={[{ name: "excluded", color: "#6B6457", points: h.unscorable_frac_by_lead.map((r) => ({ x: r.lead_min, y: r.excluded_frac_mean })) }]}
                     xLabel="lead (min)" yLabel="fraction" yMin={0} yMax={0.5} height={150} />
        </Card>
        <Card eyebrow="Model card" title={`${h.model.version} (frozen)`}>
          <div className="grid2 mono small">
            <div><span className="k">Algorithm</span>HistGradientBoosting + isotonic</div><div><span className="k">Trees</span>{h.model.n_iter}</div>
            <div><span className="k">Train days</span>{h.model.train_days[0]} … {h.model.train_days[h.model.train_days.length - 1]}</div>
            <div><span className="k">Validation</span>{h.model.validation_days[0]} … {h.model.validation_days[h.model.validation_days.length - 1]}</div>
            <div><span className="k">Test (held out)</span>{h.model.test_events.map((e) => e.split("_")[0]).join(", ")}</div>
            <div><span className="k">Yes/no threshold</span>p ≥ {h.model.deterministic_threshold_p}</div>
            {Object.entries(h.model.artifacts).map(([k, v]) => <div key={k}><span className="k">{k}</span>{v.slice(0, 16)}…</div>)}
            <div><span className="k">Evidence freeze</span>{h.freeze_manifest_sha256.slice(0, 16)}…</div>
          </div>
        </Card>
      </div>
      <Card eyebrow="Limitations" title="Must accompany every result">
        <ul className="small">{h.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
      </Card>
      <Card eyebrow="Provenance" title="Bundle inputs (verified against the Phase-7 freeze manifest when the bundle was built)">
        <button onClick={() => setShowAll(!showAll)}>{showAll ? "hide" : "show"} {Object.keys(bundle.manifest.inputs).length} input hashes</button>
        {showAll && <table className="tbl"><tbody>{Object.entries(bundle.manifest.inputs).map(([k, v]) => <tr key={k}><td className="small">{k}</td>
          <td className="mono small">{v.slice(0, 20)}…</td></tr>)}</tbody></table>}
      </Card>
      <About><p>What would change with IMD Doppler radar or lightning access: independent truth for cell tracking and hazard claims
        (none are claimed now), and radar-based nowcasts as an extra baseline.</p></About>
    </div>
  );
}
