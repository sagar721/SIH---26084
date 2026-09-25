import { useMemo } from "react";
import type { Ctx, FcMethod } from "../App";
import MapView, { MapSync } from "../components/MapView";
import { About, Card, Reliability } from "../components/Charts";
import { issueAt, useCells, useContours } from "../hooks";
import { fmt, issueKey, leadLabel, utcIst, addMinutes } from "../format";
import { METHOD_STYLE } from "../colors";
import { layerFor, ProbLegend } from "./Operate";
import type { Method } from "../types";

// ------------------------------------------------------------------ 5. Historical replay (REPLAY_SPEC §5)
export function ReplayScreen({ ctx }: { ctx: Ctx }) {
  const { bundle, ev, frame, lead, setLead, method, setMethod, threshold, basemap } = ctx;
  const sync = useMemo(() => new MapSync(), []);
  const issue = issueAt(bundle, frame);
  const nF = bundle.manifest.frames.length;
  const validFrame = issue ? issue.frame + lead / 30 : null;
  const inRange = validFrame !== null && validFrame < nF;
  const knewCells = useCells(ev, frame);
  const happenedCells = useCells(ev, inRange ? validFrame! : frame);
  const happenedContour = useContours(ev, inRange ? validFrame : null);
  const drafts = issue ? bundle.alerts.by_issue[issueKey(issue.time_utc)] ?? [] : [];
  const sc = issue ? bundle.scores[issueKey(issue.time_utc)]?.[String(lead)] : undefined;
  const b = bundle.manifest.grid.bounds;
  const qc = bundle.health.frames[frame];
  return (
    <div className="screen replay">
      <div className="replay-banner">Replay of observed data. This event was excluded from model training and calibration
        (held-out test day). Inputs at issue time use only frames up to the issue time; product latency is not modelled.</div>
      <div className="replay-panes">
        <MapView event={ev} bounds={b} layer={{ kind: "obs", frame }} cells={knewCells} sync={sync} basemap={basemap}
                 title={`WHAT THE SYSTEM KNEW · ${utcIst(bundle.manifest.frames[frame]).utc} UTC`} badge="observed input" />
        <MapView event={ev} bounds={b} layer={issue ? layerFor(method, issue, lead, frame) : null} threshold={threshold} sync={sync}
                 basemap={basemap} contours={null}
                 title={`WHAT IT PREDICTED · ${method === "ml" ? "ML probability" : method === "pysteps" ? "pySTEPS" : "persistence"} ${leadLabel(lead)}`}
                 badge={method === "ml" ? "PROBABILITY" : "BASELINE"} />
        <MapView event={ev} bounds={b} layer={inRange ? { kind: "obs", frame: validFrame! } : null} cells={inRange ? happenedCells : null}
                 contours={happenedContour} places={bundle.places} sync={sync} basemap={basemap}
                 title={`WHAT ACTUALLY HAPPENED · ${inRange ? utcIst(bundle.manifest.frames[validFrame!]).utc + " UTC" : "outside the day"}`}
                 badge="observed + IMD report places" />
      </div>
      <div className="replay-controls">
        <div className="seg-ctl"><span className="eyebrow">Predicted pane (B)</span>{(["ml", "pysteps", "persistence"] as FcMethod[]).map((m) =>
          <button key={m} className={method === m ? "on" : ""} onClick={() => setMethod(m)}>{m === "ml" ? "ML" : m === "pysteps" ? "pySTEPS" : "Persistence"}</button>)}</div>
        <div className="seg-ctl"><span className="eyebrow">Lead Δ</span>{bundle.manifest.leads_min.map((L) =>
          <button key={L} className={L === lead ? "on" : ""} onClick={() => setLead(L)}>{leadLabel(L)}</button>)}</div>
        <div className="avail small"><span className="eyebrow">Data at issue time</span>
          <span className={`pill ${qc.qc_status === "OK" ? "ok" : "warn"}`}>CPC merged IR {qc.qc_status}</span>
          <span className="pill off">INSAT-3DS NOT AVAILABLE OPERATIONALLY</span><span className="pill off">Meteosat-9 NOT CONNECTED</span>
          <span className="pill off">DWR UNAVAILABLE</span><span className="pill off">Lightning UNAVAILABLE</span></div>
      </div>
      <div className="replay-bottom">
        <Card eyebrow="Scorecard" title={issue ? `This issue time, ${leadLabel(lead)} (E8 frozen per-issue scores)` : "No forecast at this frame"}>
          {sc && <table className="tbl"><thead><tr><th>Method</th><th>CSI (p≥0.5)</th><th>POD</th><th>bias</th><th>Brier</th></tr></thead><tbody>
            {(["persistence", "pysteps_advection", "pysteps_np31", "ml"] as Method[]).map((m) => sc[m] && <tr key={m}><td>{METHOD_STYLE[m].label}</td>
              <td className="mono">{fmt(sc[m]!.CSI, 3)}</td><td className="mono">{fmt(sc[m]!.POD, 2)}</td><td className="mono">{fmt(sc[m]!.bias, 2)}</td>
              <td className="mono">{fmt(sc[m]!.BS, 4)}</td></tr>)}</tbody></table>}
          {issue && !sc && <div className="small muted">Valid time is beyond the end of the day; no verifying observation.</div>}
        </Card>
        <Card eyebrow="Would-have-issued" title="Draft advisories at this issue time (EXERCISE)">
          {drafts.length === 0 ? <div className="small muted">None.</div> :
            <ul className="small">{drafts.map((a) => <li key={a.alert_id}><b>{a.place}</b> — P {a.p_max.toFixed(2)} at +{a.lead_min} min
              <span className="mono muted"> {a.prediction_id}</span></li>)}</ul>}
          <div className="small muted">IMD hail reports give a date only (no time), so alert lead time relative to the reported impact cannot be computed.</div>
        </Card>
        {method === "ml" && <ProbLegend threshold={threshold} />}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ 7a. Confidence
export function ConfidenceScreen({ ctx }: { ctx: Ctx }) {
  const s = ctx.bundle.skill;
  const bins = ["30-30", "60-60", "90-120", "150-360"];
  const boot = s.bootstrap;
  const evs = Array.from(new Set(boot.map((r) => String(r.event))));
  return (
    <div className="page">
      <div className="page-head"><div className="eyebrow">Investigate · Confidence</div><h1>How far can the ML probability be trusted?</h1>
        <p className="muted">Held-out test days E8, E10, E11 pooled; isotonic calibration fitted on validation days only (6–12 May 2026).</p></div>
      <div className="rel-grid">
        {bins.map((lb) => {
          const curves = s.reliability_by_bin.filter((r) => r.lead_bin === lb && (r.method === "ml" || r.method === "pysteps_np31"));
          return <Card key={lb} eyebrow={`Lead ${lb.replace("-", "–")} min`} title="Reliability">
            <Reliability title="observed vs forecast" curves={curves.map((c) => ({ name: c.method, color: c.method === "ml" ? "#B23A2E" : "#8FB8DE", bins: c.bins }))} />
            <div className="small mono">{curves.map((c) => <div key={c.method}>{c.method === "ml" ? "ML" : "Neighbourhood pySTEPS"}: ECE {c.ece.toFixed(4)}
              · n={c.bins.reduce((a, b) => a + b.n, 0).toLocaleString()} px</div>)}</div>
          </Card>;
        })}
      </div>
      <Card eyebrow="Per held-out event" title="ML minus references, 95 % block-bootstrap intervals (within-event)">
        <table className="tbl"><thead><tr><th>Event</th><th>Lead</th><th>BSS(ML) − BSS(neighbourhood pySTEPS)</th><th>CSI(ML) − CSI(pySTEPS)</th></tr></thead><tbody>
          {evs.flatMap((e) => [30, 60, 120, 180].map((L) => {
            const r = boot.find((x) => x.event === e && Number(x.lead_min) === L);
            if (!r) return null;
            const bss = [Number(r.BSS_diff_ml_minus_np31), Number(r.BSS_diff_np31_lo95), Number(r.BSS_diff_np31_hi95)];
            const csi = [Number(r.CSI_diff_ml_minus_pysteps), Number(r.CSI_diff_lo95), Number(r.CSI_diff_hi95)];
            const tag = (v: number[]) => (v[1] > 0 ? "ok-t" : v[2] < 0 ? "warn-t" : "muted");
            return <tr key={`${e}${L}`}><td className="mono">{e.split("_")[0]}</td><td className="mono">{leadLabel(L)}</td>
              <td className={`mono ${tag(bss)}`}>{bss[0] >= 0 ? "+" : ""}{bss[0].toFixed(3)} [{bss[1].toFixed(3)}, {bss[2].toFixed(3)}]</td>
              <td className={`mono ${tag(csi)}`}>{csi[0] >= 0 ? "+" : ""}{csi[0].toFixed(3)} [{csi[1].toFixed(3)}, {csi[2].toFixed(3)}]</td></tr>;
          }))}
        </tbody></table>
        <div className="small muted">Green = interval above 0, amber = below 0. Intervals describe variability within one day; three days cannot establish generalisation.</div>
      </Card>
      <About><p>How to read this: a point on the diagonal means "when the model says 30 %, it happened 30 % of the time". The ML
        probabilities are close to the diagonal at every lead bin; the no-fit neighbourhood probability is over-confident from 60 min on.
        Beyond 2.5 h the calibrated ML probability never reaches 0.5, which is honest calibration rather than a failure to display.
        Data tier: satellite IR only; no radar or lightning validation.</p></About>
    </div>
  );
}

export { addMinutes };
