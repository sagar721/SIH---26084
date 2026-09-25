import type { EventCard } from "../types";
import { About } from "../components/Charts";

export function EventsScreen({ cards, current, onPick }: { cards: EventCard[]; current: string; onPick: (e: string) => void }) {
  return (
    <div className="page">
      <div className="page-head">
        <div className="eyebrow">Start · Historical replay of real events</div>
        <h1>Select an event</h1>
        <p className="muted">Every playable event is a <b>held-out test day</b>: it was never used for training or calibration of
          model <span className="mono">ml-v0</span>. The main demo is <b>E8 · 14 May 2026</b> (NW-India multi-station hail day).</p>
      </div>
      <div className="event-grid">
        {cards.map((c) => (
          <button key={c.code} className={`event-card ${c.status !== "BUNDLED" ? "unavailable" : ""} ${c.event === current ? "current" : ""}`}
                  disabled={c.status !== "BUNDLED"} onClick={() => c.event && onPick(c.event)}>
            <div className="ev-top"><span className="mono ev-code">{c.code}</span>
              <span className={`badge ${c.status === "BUNDLED" ? "badge-replay" : c.status === "EXCLUDED" ? "badge-warn" : "badge-muted"}`}>
                {c.status === "BUNDLED" ? "REPLAY" : c.status}</span></div>
            <div className="ev-date">{c.date}</div>
            <div className="ev-place">{c.place}</div>
            <div className="small muted">{c.hazard}</div>
            <div className="small ev-reason">{c.reason}</div>
            {c.event === "E8_20260514" && <div className="small ev-main">★ main demo</div>}
          </button>))}
      </div>
      <About>
        <p>Events E1–E9 come from the project replay plan; E10 and E11 were added in Phase 4 by a rule fixed before scoring.
          Events without a bundle are shown with the reason, rather than hidden: some are before the approved NOAA archive
          (which starts 2026), April 2026 is missing from it, and E8a failed the pre-declared suitability rule.
          Hail reports (IMD RMC New Delhi PDF) are used only to choose days; the verification truth is satellite cloud-top
          temperature below 235 K.</p>
      </About>
    </div>
  );
}
