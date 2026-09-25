import { useCallback, useEffect, useMemo, useState } from "react";
import type { Bundle, EventCard } from "./types";
import { loadBundle, loadIndex } from "./data";
import { leadLabel, utcIst, addMinutes } from "./format";
import { issueAt, useCells, cellList } from "./hooks";
import { EventsScreen } from "./screens/Events";
import { SituationScreen, CellsScreen, ForecastScreen, AlertsScreen } from "./screens/Operate";
import { ReplayScreen, ConfidenceScreen } from "./screens/Investigate";
import { PerformanceScreen, HealthScreen } from "./screens/Evidence";
import { DISCLAIMER } from "./cap";

export type ScreenId = "events" | "situation" | "cells" | "forecast" | "alerts" | "replay" | "confidence" | "performance" | "health";
export type FcMethod = "persistence" | "pysteps" | "ml";

export interface Ctx {
  bundle: Bundle; ev: string; frame: number; setFrame: (f: number) => void; lead: number; setLead: (l: number) => void;
  method: FcMethod; setMethod: (m: FcMethod) => void; threshold: number; setThreshold: (t: number) => void;
  selectedCell: number | null; selectCell: (c: number | null) => void; basemap: boolean; go: (s: ScreenId) => void;
  decisions: Record<string, "APPROVED" | "REJECTED">; decide: (id: string, d: "APPROVED" | "REJECTED") => void;
  audit: { t: string; msg: string }[];
}

const NAV: { group: string; items: { id: ScreenId; label: string }[] }[] = [
  { group: "START", items: [{ id: "events", label: "Event selection" }] },
  { group: "OPERATE", items: [{ id: "situation", label: "Situation" }, { id: "cells", label: "Storm Cells" },
                              { id: "forecast", label: "0–6 h Forecast" }, { id: "alerts", label: "Alert Center" }] },
  { group: "INVESTIGATE", items: [{ id: "replay", label: "Historical Replay" }, { id: "confidence", label: "Confidence" }] },
  { group: "EVIDENCE", items: [{ id: "performance", label: "Model Performance" }, { id: "health", label: "Data Health" }] },
];
const ORDER = NAV.flatMap((g) => g.items.map((i) => i.id));
const LEAD_SCREENS: ScreenId[] = ["forecast", "replay", "cells"];

export default function App() {
  const [index, setIndex] = useState<EventCard[] | null>(null);
  const [ev, setEv] = useState<string>("E8_20260514");
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [screen, setScreen] = useState<ScreenId>("events");
  const [frame, setFrame] = useState(28);
  const [lead, setLead] = useState(60);
  const [method, setMethod] = useState<FcMethod>("ml");
  const [threshold, setThreshold] = useState(0.1);
  const [selectedCell, selectCell] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [basemap, setBasemap] = useState(true);
  const [decisions, setDecisions] = useState<Record<string, "APPROVED" | "REJECTED">>({});
  const [audit, setAudit] = useState<{ t: string; msg: string }[]>([]);

  useEffect(() => { loadIndex().then((i) => { setIndex(i.events); setEv(i.default); }).catch((e) => setErr(String(e))); }, []);
  useEffect(() => {
    setBundle(null);
    loadBundle(ev).then((b) => { setBundle(b); setFrame(Math.min(28, b.manifest.frames.length - 1)); selectCell(null); })
      .catch((e) => setErr(String(e)));
    try {
      setDecisions(JSON.parse(localStorage.getItem(`decisions-${ev}`) ?? "{}"));
      setAudit(JSON.parse(localStorage.getItem(`audit-${ev}`) ?? "[]"));
    } catch { setDecisions({}); setAudit([]); }
  }, [ev]);

  const decide = useCallback((id: string, d: "APPROVED" | "REJECTED") => {
    setDecisions((prev) => {
      const next = { ...prev, [id]: d };
      try { localStorage.setItem(`decisions-${ev}`, JSON.stringify(next)); } catch { /* per-viewer convenience only */ }
      return next;
    });
    setAudit((prev) => {
      const next = [{ t: new Date().toISOString(), msg: `${d} ${id} (exercise; forecaster action in UI)` }, ...prev].slice(0, 200);
      try { localStorage.setItem(`audit-${ev}`, JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });
  }, [ev]);

  // playback: 1x = one 30-min step per 2 s (REPLAY_SPEC §5)
  useEffect(() => {
    if (!playing || !bundle) return;
    const id = setInterval(() => setFrame((f) => (f + 1 >= bundle.manifest.frames.length ? 0 : f + 1)), 2000 / speed);
    return () => clearInterval(id);
  }, [playing, speed, bundle]);

  const go = useCallback((s: ScreenId) => setScreen(s), []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT" || (e.target as HTMLElement)?.tagName === "SELECT") return;
      if (!bundle) return;
      if (e.key === "ArrowRight") setFrame((f) => Math.min(f + 1, bundle.manifest.frames.length - 1));
      else if (e.key === "ArrowLeft") setFrame((f) => Math.max(f - 1, 0));
      else if (e.key === " ") { e.preventDefault(); setPlaying((p) => !p); }
      else if (e.key.toLowerCase() === "b") setMethod((m) => (m === "ml" ? "pysteps" : m === "pysteps" ? "persistence" : "ml"));
      else if (/^[1-9]$/.test(e.key)) setScreen(ORDER[Number(e.key) - 1] ?? screen);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [bundle, screen]);

  const cellsFc = useCells(ev, frame);
  const nCells = cellList(cellsFc).length;

  if (err) return <div className="fatal">Could not load the replay bundle: {err}. Run <code>python -m pipelines.replay.build_bundle</code>.</div>;
  if (!bundle || !index) return <div className="loading"><div className="skeleton" />Loading replay bundle…</div>;

  const m = bundle.manifest;
  const issue = issueAt(bundle, frame);
  const t = m.frames[frame];
  const showLead = LEAD_SCREENS.includes(screen) && issue !== null;
  const valid = showLead ? addMinutes(t, lead) : t;
  const vt = utcIst(valid);
  const drafts = issue ? (bundle.alerts.by_issue[issue.time_utc.replace("T", " ").replace("Z", "")] ?? []).length : 0;
  const ctx: Ctx = { bundle, ev, frame, setFrame, lead, setLead, method, setMethod, threshold, setThreshold, selectedCell,
                     selectCell, basemap, go, decisions, decide, audit };
  const qc = bundle.health.frames[frame];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><div className="logo">SL</div><div><b>StormLife Nowcast</b><div className="muted small">SIH26084 · research prototype</div></div></div>
        {NAV.map((g) => (
          <nav key={g.group}>
            <div className="eyebrow">{g.group}</div>
            {g.items.map((it) => (
              <button key={it.id} className={`nav ${screen === it.id ? "active" : ""}`} onClick={() => setScreen(it.id)}>
                <span>{ORDER.indexOf(it.id) + 1}. {it.label}</span>
                {it.id === "cells" && <span className="count">{nCells}</span>}
                {it.id === "alerts" && drafts > 0 && <span className="count warn">{drafts}</span>}
              </button>))}
          </nav>))}
        <div className="side-foot small muted">
          <label className="toggle"><input type="checkbox" checked={basemap} onChange={(e) => setBasemap(e.target.checked)} /> Basemap (online tiles)</label>
          <div>Keys: ←/→ frame · Space play · 1–9 screens · B method</div>
        </div>
      </aside>

      <header className="topbar">
        <span className="badge badge-replay">REPLAY</span>
        <span className="mono">{m.code} · {m.date}</span>
        <span className="mono">Valid {vt.utc} UTC · {vt.ist} IST{showLead ? ` · issued ${utcIst(t).utc} ${leadLabel(lead)}` : ""}</span>
        <span className="chip">{m.data_tier}</span>
        <span className="chip mono">model {m.envelope.model.version}</span>
        <span className={`chip ${qc?.qc_status === "OK" ? "ok" : "warn"}`}>frame QC {qc?.qc_status}</span>
        <span className="chip muted-chip">latency not modelled</span>
        {m.held_out && <span className="chip ok">held-out event</span>}
      </header>

      <main className="main">
        {screen === "events" && <EventsScreen cards={index} current={ev} onPick={(e) => { setEv(e); setScreen("situation"); }} />}
        {screen === "situation" && <SituationScreen ctx={ctx} />}
        {screen === "cells" && <CellsScreen ctx={ctx} />}
        {screen === "forecast" && <ForecastScreen ctx={ctx} />}
        {screen === "alerts" && <AlertsScreen ctx={ctx} />}
        {screen === "replay" && <ReplayScreen ctx={ctx} />}
        {screen === "confidence" && <ConfidenceScreen ctx={ctx} />}
        {screen === "performance" && <PerformanceScreen ctx={ctx} />}
        {screen === "health" && <HealthScreen ctx={ctx} />}
      </main>

      {screen !== "events" && <Timeline ctx={ctx} showLead={showLead} playing={playing} setPlaying={setPlaying} speed={speed}
                                         setSpeed={setSpeed} />}
      <footer className="footer">{DISCLAIMER} Source: NOAA/NCEP/CPC merged IR. ML output is a calibrated probability, not a guaranteed prediction.</footer>
    </div>
  );
}

function Timeline({ ctx, showLead, playing, setPlaying, speed, setSpeed }: { ctx: Ctx; showLead: boolean; playing: boolean;
  setPlaying: (p: boolean) => void; speed: number; setSpeed: (s: number) => void }) {
  const { bundle, frame, setFrame, lead, setLead } = ctx;
  const m = bundle.manifest;
  const issueFrames = useMemo(() => new Set(m.issues.map((i) => i.frame)), [m]);
  const t = utcIst(m.frames[frame]);
  return (
    <div className="timeline">
      <div className="tl-label"><div className="eyebrow">Active view</div><div className="mono">{t.utc} UTC · {t.ist} IST</div>
        <div className="small muted">{issueFrames.has(frame) ? "forecast issued at this frame" : "no forecast at this frame"}</div></div>
      <div className="tl-controls">
        <button className="play" onClick={() => setPlaying(!playing)} aria-label={playing ? "pause" : "play"}>{playing ? "❚❚" : "▶"}</button>
        <button onClick={() => { setPlaying(false); setFrame(28); }} aria-label="reset">⟲</button>
        {[1, 2, 5].map((s) => <button key={s} className={speed === s ? "on" : ""} onClick={() => setSpeed(s)}>{s}×</button>)}
      </div>
      <div className="tl-frames">
        {m.frames.map((f, k) => {
          const q = bundle.health.frames[k]?.qc_status;
          return <button key={f} className={`seg ${k === frame ? "now" : ""} ${k < frame ? "past" : ""} ${q !== "OK" ? "qcfail" : ""} ${issueFrames.has(k) ? "" : "noissue"}`}
                         title={`${utcIst(f).utc} UTC · QC ${q}${issueFrames.has(k) ? "" : " · no forecast issued"}`} onClick={() => setFrame(k)} />;
        })}
        <div className="tl-hours mono">{[0, 6, 12, 18, 23].map((h) => <span key={h} style={{ left: `${(h * 2 / m.frames.length) * 100}%` }}>{String(h).padStart(2, "0")}:00</span>)}</div>
      </div>
      <div className={`tl-leads ${showLead ? "" : "disabled"}`}>
        <div className="eyebrow">Lead → +6 h</div>
        <div className="leads">{m.leads_min.map((L) => <button key={L} className={L === lead ? "on" : ""} disabled={!showLead}
                                                            onClick={() => setLead(L)}>{leadLabel(L)}</button>)}</div>
      </div>
    </div>
  );
}
