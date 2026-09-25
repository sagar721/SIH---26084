import { useMemo, useState } from "react";
import type { Ctx, FcMethod } from "../App";
import MapView from "../components/MapView";
import { About, Card, LineChart, Sparkline } from "../components/Charts";
import { cellList, issueAt, useArrows, useCellFc, useCells, useContours } from "../hooks";
import type { Layer } from "../data";
import { fmt, issueKey, leadLabel, utcIst, addMinutes } from "../format";
import { METHOD_STYLE, PHASE_STYLE, P_BINS, P_COLORS } from "../colors";
import { capXml } from "../cap";
import type { CellProps, DraftAlert, Method } from "../types";

const SKILL_METHOD: Record<FcMethod, Method> = { persistence: "persistence", pysteps: "pysteps_advection", ml: "ml" };

export function layerFor(method: FcMethod, issue: { i: number; frame: number } | null, lead: number, frame: number): Layer {
  if (!issue || method === "persistence") return { kind: "obs", frame: issue ? issue.frame : frame };
  return { kind: method === "ml" ? "ml" : "pysteps", issue: issue.i, lead };
}

function IrLegend() {
  const stops = [[300, "warm"], [273, "273"], [253, "253"], [235, "235"], [221, "221"], [208, "208 K"]];
  return <div className="legend"><div className="eyebrow">IR brightness temperature (K)</div>
    <div className="ir-bar" /><div className="ir-ticks mono">{stops.map(([v, l]) => <span key={String(v)}>{l}</span>)}</div>
    <div className="small muted">Grey = no data (source gap) · deep convection = BT &lt; 235 K</div></div>;
}

export function ProbLegend({ threshold }: { threshold: number }) {
  return <div className="legend"><div className="eyebrow">ML probability · P(BT &lt; 235 K) <span className="badge badge-prob">PROBABILITY</span></div>
    <div className="p-bins">{P_BINS.map((b, i) => <span key={b} style={{ background: `rgba(${P_COLORS[i].slice(0, 3).join(",")},${b < threshold ? 0.15 : 1})` }}
      className="mono">{b.toFixed(1)}+</span>)}</div>
    <div className="small muted">Calibrated probability, not a guaranteed outcome. Bins below the threshold ({threshold.toFixed(1)}) hidden.</div></div>;
}

function PhaseLegend() {
  return <div className="legend"><div className="eyebrow">Cell phase (rules v0 · PROPOSED)</div>
    {Object.entries(PHASE_STYLE).map(([k, v]) => <div key={k} className="phase-row"><svg width="26" height="8"><line x1="0" x2="26" y1="4" y2="4"
      stroke={v.color} strokeWidth={v.width + 0.5} strokeDasharray={v.dash[1] ? v.dash.map((d) => d * 3).join(" ") : undefined} /></svg>{v.label}</div>)}
    <div className="small muted">Phase is shown by colour and line style. Arrows: pySTEPS motion over the next 30 min.</div></div>;
}

// ------------------------------------------------------------------ 1. Situation
export function SituationScreen({ ctx }: { ctx: Ctx }) {
  const { bundle, ev, frame, selectCell, go, basemap } = ctx;
  const issue = issueAt(bundle, frame);
  const cellsFc = useCells(ev, frame);
  const cells = cellList(cellsFc);
  const fc = useCellFc(ev, issue ? issue.i : null);
  const arrows = useArrows(cells, fc);
  const pp = issue ? bundle.alerts.place_max_p_60min[issueKey(issue.time_utc)] ?? {} : {};
  const places = bundle.places.map((p) => ({ ...p, p: issue ? pp[p.name] : undefined }));
  const top = useMemo(() => cells.map((c) => ({ c, p: fc?.[String(c.cell)]?.by_lead?.["60"]?.ml_p_max_10km ?? null }))
    .sort((a, b) => (b.p ?? -1) - (a.p ?? -1)).slice(0, 5), [cells, fc]);
  const qc = bundle.health.frames[frame];
  const hi = Object.values(pp).filter((v) => v >= 0.5).length;
  return (
    <div className="screen">
      <div className="map-area">
        <MapView event={ev} bounds={bundle.manifest.grid.bounds} layer={{ kind: "obs", frame }} cells={cellsFc} arrows={arrows}
                 places={places} onCellClick={(c) => { selectCell(c); go("cells"); }} basemap={basemap} />
        <div className="legend-stack"><IrLegend /><PhaseLegend /></div>
      </div>
      <aside className="context">
        <div className="kpis">
          <div className="kpi"><div className="eyebrow">Active cells</div><div className="big mono">{cells.length}</div><div className="small muted">cold segments &lt; 245 K (v2)</div></div>
          <div className="kpi"><div className="eyebrow">Mature</div><div className="big mono">{cells.filter((c) => c.phase === "Mature").length}</div><div className="small muted">rules v0</div></div>
          <div className="kpi"><div className="eyebrow">Places P ≥ 0.5</div><div className="big mono">{issue ? hi : "—"}</div><div className="small muted">next 60 min (ML)</div></div>
          <div className="kpi"><div className="eyebrow">Frame QC</div><div className={`big mono ${qc.qc_status === "OK" ? "ok-t" : "warn-t"}`}>{qc.qc_status}</div>
            <div className="small muted">{(qc.qc_missing_frac * 100).toFixed(1)} % no data</div></div>
        </div>
        <Card eyebrow="Operate" title="Top 5 cells by ML risk (next 60 min)">
          {!issue && <div className="muted small">No forecast issued at this frame (needs 60 min of history and a future frame).</div>}
          {issue && top.length === 0 && <div className="muted small">No convective cells below 245 K in the domain.</div>}
          {issue && <table className="tbl"><thead><tr><th>Cell</th><th>Phase</th><th>Min BT</th><th>P(60)</th></tr></thead><tbody>
            {top.map(({ c, p }) => <tr key={c.cell} className="click" onClick={() => { selectCell(c.cell); go("cells"); }}>
              <td className="mono">#{c.cell}</td><td>{c.phase}</td><td className="mono">{c.min_bt_K} K</td><td className="mono">{fmt(p)}</td></tr>)}
          </tbody></table>}
          <div className="small muted">P(60) = max calibrated ML probability within 10 km of the pySTEPS-advected cell centre at +60 min (display summary, not a verified cell metric).</div>
        </Card>
        <Card eyebrow="Data health" title="Sources">
          {bundle.health.sources.map((s) => <div key={s.source} className="src-row"><span className={`dot-s ${s.status.startsWith("AVAILABLE") ? "ok" : "off"}`} />
            <span className="small">{s.source}</span><span className="small mono muted">{s.status}</span></div>)}
        </Card>
        <About><p>Observed NOAA CPC merged-IR frame at the timeline time, cells from the frozen Phase-3 v2 tracking (overlap-linked cold
          segments), place markers = IMD hail-report places for this date (context only). Click a cell for its details. Replay of observed data;
          not live.</p></About>
      </aside>
    </div>
  );
}

// ------------------------------------------------------------------ 2 + 4. Storm cells + details + ML probability
function haversineKm(a: { lon: number; lat: number }, b: { lon: number; lat: number }) {
  const R = 6371, r = Math.PI / 180;
  const d = Math.sin(((b.lat - a.lat) * r) / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(((b.lon - a.lon) * r) / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(d));
}

type Row = CellProps & { p60: number | null };
const DESC = new Set(["p60", "area_km2", "age_min", "cold_core_km2"]);
export function sortRows(rows: Row[], key: keyof CellProps | "p60"): Row[] {
  return [...rows].sort((a, b) => {
    const va = a[key as keyof Row], vb = b[key as keyof Row];
    if (va === null || va === undefined) return 1;
    if (vb === null || vb === undefined) return -1;
    const c = typeof va === "string" ? va.localeCompare(String(vb)) : (va as number) - (vb as number);
    return DESC.has(key) ? -c : c;
  });
}

export function CellsScreen({ ctx }: { ctx: Ctx }) {
  const { bundle, ev, frame, selectedCell, selectCell, basemap, lead } = ctx;
  const issue = issueAt(bundle, frame);
  const cellsFc = useCells(ev, frame);
  const cells = cellList(cellsFc);
  const fc = useCellFc(ev, issue ? issue.i : null);
  const arrows = useArrows(cells, fc);
  const [sort, setSort] = useState<keyof CellProps | "p60">("min_bt_K");
  const sel = cells.find((c) => c.cell === selectedCell) ?? null;
  const hist = sel ? (bundle.tracks[String(sel.cell)] ?? []).filter((p) => p.frame <= frame) : [];
  const f = sel ? fc?.[String(sel.cell)] : undefined;
  const leads = bundle.manifest.leads_min;
  const fcTrack = sel && f ? { coords: [[sel.lon, sel.lat] as [number, number], ...leads.filter((L) => f.by_lead[String(L)]?.field_advection)
      .map((L) => [f.by_lead[String(L)].field_advection!.lon, f.by_lead[String(L)].field_advection!.lat] as [number, number])],
      labels: leads.filter((L) => f.by_lead[String(L)]?.field_advection).map((L) => leadLabel(L)) } : null;
  const p30 = f?.by_lead["30"]?.field_advection;
  const speed = sel && p30 ? haversineKm(sel, p30) / 0.5 : null;
  const rows = sortRows(cells.map((c) => ({ ...c, p60: fc?.[String(c.cell)]?.by_lead?.["60"]?.ml_p_max_10km ?? null })), sort);
  return (
    <div className="screen">
      <div className="map-area">
        <MapView event={ev} bounds={bundle.manifest.grid.bounds} layer={{ kind: "obs", frame }} cells={cellsFc} arrows={arrows}
                 selectedCell={selectedCell} onCellClick={selectCell} basemap={basemap}
                 pastTrack={hist.length > 1 ? hist.map((p) => [p.lon, p.lat]) : null} fcTrack={fcTrack} places={bundle.places} />
        <div className="legend-stack"><PhaseLegend />
          <div className="legend"><div className="eyebrow">Tracks</div><div className="small">solid navy = observed track so far · dashed red =
            pySTEPS-advected position (T+30m…T+6h)</div><div className="small warn-t">Cell position skill is verified only as a diagnostic at 30 min.</div></div></div>
      </div>
      <aside className="context">
        {!sel && <Card eyebrow="Storm cells" title="Select a cell"><div className="muted small">Click a cell on the map or in the table below.</div></Card>}
        {sel && <Card eyebrow={`Cell #${sel.cell} · family ${sel.family}`} title={`Phase now: ${sel.phase}`}
                      badge={<span className="badge badge-muted">rules v0 · PROPOSED</span>}>
          <div className="grid2 mono">
            <div><span className="k">Min BT</span>{sel.min_bt_K} K</div>
            <div><span className="k">ΔBT 30 min</span>{sel.d_min_bt_30 === null ? "—" : `${sel.d_min_bt_30 > 0 ? "+" : ""}${sel.d_min_bt_30} K`}</div>
            <div><span className="k">Area &lt; 245 K</span>{sel.area_km2.toLocaleString()} km²</div>
            <div><span className="k">Cold core &lt; 221 K</span>{sel.cold_core_km2.toLocaleString()} km²</div>
            <div><span className="k">Age so far</span>{sel.age_min} min</div>
            <div><span className="k">Merges/splits so far</span>{sel.merges_splits_so_far}</div>
            <div><span className="k">Motion (pySTEPS)</span>{speed === null ? "—" : `${speed.toFixed(0)} km/h`}</div>
            <div><span className="k">Touches data gap</span>{sel.touches_missing ? "yes" : "no"}</div>
          </div>
          <div className="spark-row"><span className="small muted">Min BT (history to now)</span>
            <Sparkline values={hist.map((p) => p.min_bt_K)} color="#1F6FB2" invert /></div>
          <div className="spark-row"><span className="small muted">Area &lt; 245 K</span><Sparkline values={hist.map((p) => p.area_km2)} color="#E9A23B" /></div>
          <div className="envelope small mono">issued {issue ? utcIst(issue.time_utc).utc : "—"} UTC · model {bundle.manifest.envelope.model.version} · {bundle.manifest.data_tier} · REPLAY</div>
        </Card>}
        {sel && <Card eyebrow="Storm details + ML probability" title="P(deep convection) near the forecast cell position" badge={<span className="badge badge-prob">PROBABILITY</span>}>
          {!f && <div className="muted small">No forecast for this cell at this frame (new cell: no motion history yet, or no issue time).</div>}
          {f && <LineChart xLabel="lead (min)" yLabel="max P within 10 km" yMin={0} yMax={1} height={150} marker={lead}
            refLine={{ y: 0.5, label: "p = 0.5" }} series={[{ name: "ML", color: "#B23A2E",
              points: leads.map((L) => ({ x: L, y: f.by_lead[String(L)]?.ml_p_max_10km ?? null })) }]} />}
          <div className="small muted">Display summary of the frozen ML probability field at the pySTEPS-advected cell centre. The ML model
            forecasts the grid (P of BT &lt; 235 K), not cells; beyond 2.5 h its calibrated probabilities stay below 0.5.</div>
        </Card>}
        <Card eyebrow="Cell table" title={`${cells.length} cells at ${utcIst(bundle.manifest.frames[frame]).utc} UTC`}>
          <table className="tbl sortable"><thead><tr>
            {([["cell", "ID"], ["phase", "Phase"], ["age_min", "Age"], ["min_bt_K", "Min BT"], ["d_min_bt_30", "ΔBT30"], ["area_km2", "Area"], ["p60", "P(60)"]] as const)
              .map(([k, l]) => <th key={k} className={sort === k ? "on" : ""} onClick={() => setSort(k as keyof CellProps)}>{l}</th>)}
          </tr></thead><tbody>
            {rows.map((c) => <tr key={c.cell} className={`click ${c.cell === selectedCell ? "sel" : ""}`} onClick={() => selectCell(c.cell)}>
              <td className="mono">#{c.cell}</td><td>{c.phase}</td><td className="mono">{c.age_min}</td><td className="mono">{c.min_bt_K}</td>
              <td className="mono">{fmt(c.d_min_bt_30, 1)}</td><td className="mono">{c.area_km2.toLocaleString()}</td><td className="mono">{fmt(c.p60)}</td></tr>)}
          </tbody></table>
        </Card>
        <About><p>Cells are the frozen Phase-3 v2 tracks (overlap-linked cold segments). Tracking was audited but has no independent truth;
          phases use proposed rules v0. Age, history and merges/splits are shown only up to the current frame. (One exception: cells seen in a
          single frame were dropped offline, which uses the next frame.)</p></About>
      </aside>
    </div>
  );
}

// ------------------------------------------------------------------ 3. 0-6 h Forecast
export function SkillRibbon({ ctx, method, lead }: { ctx: Ctx; method: FcMethod; lead: number }) {
  const s = ctx.bundle.skill;
  const m = SKILL_METHOD[method];
  const row = s.pooled[m]?.find((r) => r.lead_min === lead);
  const decay = s.phase4_decay.filter((d) => d.method === (m === "ml" ? "pysteps_advection" : m));
  // ML: last lead with positive pooled BSS; baselines: useful FSS 40 km on every event (Phase 4). Both from frozen tables.
  const usefulTo = m === "ml" ? Math.max(...s.pooled.ml.filter((r) => (r.BSS ?? -1) > 0).map((r) => r.lead_min))
                              : Math.min(...decay.map((d) => Number(d.useful_FSS_40km_up_to_min)));
  const beyond = lead > usefulTo;
  const small = m === "ml" && !beyond && (row?.BSS ?? 0) < 0.1;
  return (
    <div className={`ribbon ${beyond ? "muted-ribbon" : ""}`}>
      <div className="eyebrow">Validated skill at {leadLabel(lead)} · {METHOD_STYLE[m].label} · held-out E8+E10+E11 pooled</div>
      <div className="ribbon-nums mono">
        <span>CSI {fmt(row?.CSI, 3)}</span><span>BSS {fmt(row?.BSS, 2)}</span><span>FSS40 {fmt(row?.FSS_40km_event_mean, 2)}</span><span>bias {fmt(row?.bias, 2)}</span>
      </div>
      <div className="small">{m === "ml"
          ? (beyond ? <b className="warn-t">No probability skill at this lead (pooled BSS ≤ 0 beyond {usefulTo} min).</b>
                    : small ? <span className="warn-t">Positive but small probability skill (BSS &lt; 0.1). The final claims state useful ML skill to about 4 h.</span>
                            : <span className="ok-t">Positive probability skill (BSS &gt; 0) at this lead.</span>)
          : (beyond ? <b className="warn-t">Beyond validated useful skill (FSS 40 km useful to {usefulTo} min on every event).</b>
                    : <span className="ok-t">Within validated useful skill (FSS 40 km useful to {usefulTo} min on every event).</span>)}
        {m === "ml" && " ML CSI is at p ≥ 0.5; as a yes/no forecast ML does not beat pySTEPS beyond 60 min."}</div>
    </div>
  );
}

export function ForecastScreen({ ctx }: { ctx: Ctx }) {
  const { bundle, ev, frame, lead, method, setMethod, threshold, setThreshold, basemap, setLead } = ctx;
  const issue = issueAt(bundle, frame);
  const [showObs, setShowObs] = useState(false);
  const [showCells, setShowCells] = useState(true);
  const validFrame = issue ? issue.frame + lead / 30 : null;
  const contours = useContours(ev, showObs && validFrame !== null && validFrame < bundle.manifest.frames.length ? validFrame : null);
  const cellsFc = useCells(ev, issue ? issue.frame : frame);
  const layer = layerFor(method, issue, lead, frame);
  const sc = issue ? bundle.scores[issueKey(issue.time_utc)]?.[String(lead)] : undefined;
  return (
    <div className="screen">
      <div className="map-area">
        <MapView event={ev} bounds={bundle.manifest.grid.bounds} layer={layer} threshold={threshold} cells={showCells ? cellsFc : null}
                 contours={contours} basemap={basemap} places={bundle.places} />
        <div className="legend-stack">{method === "ml" ? <ProbLegend threshold={threshold} /> : <IrLegend />}
          {method === "pysteps" && <div className="legend small">Hatched = no pySTEPS forecast (inflow from outside the grid).</div>}
          {showObs && <div className="legend small">Black outline = OBSERVED BT &lt; 235 K at the valid time (replay only).</div>}</div>
      </div>
      <aside className="context">
        {!issue && <Card eyebrow="0–6 h forecast" title="No forecast at this frame"><div className="small muted">Forecasts are issued from 01:00 to 23:00 UTC
          (60 min of history and at least one future frame needed). Move the timeline.</div></Card>}
        <Card eyebrow="0–6 h forecast" title="Method">
          <div className="seg-ctl">{(["persistence", "pysteps", "ml"] as FcMethod[]).map((m) => <button key={m} className={method === m ? "on" : ""}
            onClick={() => setMethod(m)}>{m === "ml" ? "ML probability" : m === "pysteps" ? "pySTEPS" : "Persistence"}</button>)}</div>
          <div className="eyebrow" style={{ marginTop: 10 }}>Lead time</div>
          <div className="seg-ctl">{[0, 15, ...bundle.manifest.leads_min].map((L) => <button key={L} disabled={L === 0 || L === 15}
            className={L === lead ? "on" : ""} title={L === 15 ? "not produced: the source has 30-min frames" : L === 0 ? "analysis = observed frame at issue time" : ""}
            onClick={() => setLead(L)}>{leadLabel(L)}</button>)}</div>
          <div className="small muted">T+15 m is not produced (30-min source cadence). T+0 is the observed issue frame (Situation screen).</div>
          {method === "ml" && <><div className="eyebrow" style={{ marginTop: 10 }}>Probability display threshold</div>
            <input type="range" min={0.1} max={0.9} step={0.2} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
            <span className="mono small"> {threshold.toFixed(1)}</span></>}
          <div className="toggles small">
            <label><input type="checkbox" checked={showObs} onChange={(e) => setShowObs(e.target.checked)} /> show what happened (replay)</label>
            <label><input type="checkbox" checked={showCells} onChange={(e) => setShowCells(e.target.checked)} /> cells at issue time</label>
          </div>
        </Card>
        <SkillRibbon ctx={ctx} method={method} lead={lead} />
        {issue && <Card eyebrow="Envelope" title="This forecast">
          <div className="grid2 mono small">
            <div><span className="k">Issued</span>{utcIst(issue.time_utc).utc} UTC</div><div><span className="k">Valid</span>{utcIst(addMinutes(issue.time_utc, lead)).utc} UTC</div>
            <div><span className="k">Mode</span>REPLAY</div><div><span className="k">Model</span>{method === "ml" ? "ml-v0 (calibrated)" : method === "pysteps" ? "pySTEPS LK+SL" : "persistence"}</div>
            <div><span className="k">Evidence</span>{method === "ml" ? "PROBABILITY" : "DETERMINISTIC BASELINE"}</div><div><span className="k">Data tier</span>SAT (IR only)</div>
          </div>
          {sc && <><div className="eyebrow" style={{ marginTop: 8 }}>Score of this single forecast (E8, p ≥ 0.5)</div>
            <table className="tbl"><thead><tr><th>Method</th><th>CSI</th><th>POD</th><th>bias</th><th>Brier</th></tr></thead><tbody>
              {(["persistence", "pysteps_advection", "pysteps_np31", "ml"] as Method[]).map((m) => sc[m] && <tr key={m}><td>{METHOD_STYLE[m].label}</td>
                <td className="mono">{fmt(sc[m]!.CSI, 3)}</td><td className="mono">{fmt(sc[m]!.POD, 2)}</td><td className="mono">{fmt(sc[m]!.bias, 2)}</td>
                <td className="mono">{fmt(sc[m]!.BS, 4)}</td></tr>)}
            </tbody></table>
            <div className="small muted">One issue time is noisy; the validated numbers are the pooled ribbon above.</div></>}
        </Card>}
        <About><p>Persistence = the observed frame at issue time. pySTEPS = Lucas–Kanade motion + semi-Lagrangian advection of BT (unchanged
          Phase-2 settings). ML = ml-v0 calibrated probability that the cloud top will be colder than 235 K. All three forecasts were computed
          in Phases 2 and 6 and are replayed here unchanged.</p></About>
      </aside>
    </div>
  );
}

// ------------------------------------------------------------------ 8. Alert / status
export function AlertsScreen({ ctx }: { ctx: Ctx }) {
  const { bundle, ev, frame, basemap, decisions, decide, audit } = ctx;
  const issue = issueAt(bundle, frame);
  const drafts: DraftAlert[] = issue ? bundle.alerts.by_issue[issueKey(issue.time_utc)] ?? [] : [];
  const pp = issue ? bundle.alerts.place_max_p_60min[issueKey(issue.time_utc)] ?? {} : {};
  const [preview, setPreview] = useState<DraftAlert | null>(null);
  const xml = preview && issue ? capXml(preview, issue.time_utc, ev, bundle.manifest.envelope.model.version) : "";
  const download = () => {
    const blob = new Blob([xml], { type: "application/xml" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${preview!.alert_id.replace(/[^A-Za-z0-9]/g, "_")}_EXERCISE.xml`;
    a.click();
  };
  const qc = bundle.health.frames[frame];
  return (
    <div className="screen">
      <div className="map-area">
        <MapView event={ev} bounds={bundle.manifest.grid.bounds} layer={issue ? { kind: "ml", issue: issue.i, lead: 60 } : { kind: "obs", frame }}
                 threshold={0.5} places={bundle.places.map((p) => ({ ...p, p: pp[p.name] }))} basemap={basemap} />
        <div className="legend-stack"><ProbLegend threshold={0.5} /><div className="legend small">Map: ML probability at +60 min, p ≥ 0.5 only. Places coloured by max P in the next 60 min.</div></div>
      </div>
      <aside className="context">
        <Card eyebrow="Status" title="System status">
          <div className="grid2 mono small">
            <div><span className="k">Mode</span>REPLAY (not live)</div><div><span className="k">Model</span>{bundle.manifest.envelope.model.version} · frozen</div>
            <div><span className="k">Frame QC</span>{qc.qc_status} · {(qc.qc_missing_frac * 100).toFixed(1)} % gaps</div><div><span className="k">Latency</span>not modelled</div>
            <div><span className="k">Radar</span>unavailable</div><div><span className="k">Lightning</span>unavailable</div>
          </div>
          <div className="small muted">Evidence freeze {bundle.manifest.freeze_manifest_sha256.slice(0, 12)}…</div>
        </Card>
        <Card eyebrow="Alert Center · EXERCISE" title={`Draft advisories at ${issue ? utcIst(issue.time_utc).utc : "—"} UTC`}
              badge={<span className="badge badge-warn">EXERCISE</span>}>
          <div className="small muted">Rule: {bundle.alerts.rule}. Nothing is issued without forecaster approval.</div>
          {!issue && <div className="small muted">No forecast at this frame.</div>}
          {issue && drafts.length === 0 && <div className="small">No draft advisories at this issue time.</div>}
          {drafts.map((a) => {
            const d = decisions[a.alert_id];
            return <div key={a.alert_id} className={`alert-row ${d ? d.toLowerCase() : ""}`}>
              <div><b>{a.place}</b> · P {a.p_max.toFixed(2)} within 10 km at +{a.lead_min} min
                <div className="mono small muted">{a.prediction_id}</div></div>
              <div className="alert-btns">
                {d ? <span className={`badge ${d === "APPROVED" ? "badge-ok" : "badge-muted"}`}>{d}</span> : <>
                  <button onClick={() => decide(a.alert_id, "APPROVED")}>Approve</button>
                  <button onClick={() => decide(a.alert_id, "REJECTED")}>Reject</button></>}
                <button onClick={() => setPreview(a)} disabled={d !== "APPROVED"} title={d !== "APPROVED" ? "approve first" : ""}>CAP</button>
              </div>
            </div>;
          })}
        </Card>
        {preview && <Card eyebrow="CAP 1.2 preview" title={`${preview.place} · status=Exercise`}>
          <pre className="cap">{xml}</pre><button onClick={download}>Download XML</button></Card>}
        <Card eyebrow="Audit log" title="Forecaster actions (this browser)">
          {audit.length === 0 ? <div className="small muted">No actions yet.</div> :
            <ul className="audit mono small">{audit.slice(0, 12).map((x, i) => <li key={i}>{x.t.slice(11, 19)} {x.msg}</li>)}</ul>}
        </Card>
        <About><p>Draft advisories apply the frozen p ≥ 0.5 threshold to the ml-v0 probability near each IMD-report place. They are exercises:
          no hail, lightning or rainfall forecast is implied, alert skill has not been verified, and this is not an official IMD warning.</p></About>
      </aside>
    </div>
  );
}
