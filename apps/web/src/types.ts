// Shapes of the replay bundle written by pipelines/replay/build_bundle.py (frozen ml-v0 evidence).

export interface Bounds { west: number; south: number; east: number; north: number }

export interface Manifest {
  event: string; code: string; name: string; date: string; built_at_utc: string;
  mode: "REPLAY"; data_tier: string;
  envelope: { model: { name: string; version: string; artifacts: Record<string, string> }; baselines: string[];
              evidence_level: string; calibrated: boolean };
  held_out: boolean;
  grid: { width: number; height: number; bounds: Bounds };
  frames: string[];
  issues: { i: number; frame: number; time_utc: string }[];
  leads_min: number[];
  freeze_manifest_sha256: string;
  inputs: Record<string, string>;
  outputs: Record<string, string>;
}

export interface EventCard {
  code: string; event?: string; date: string; place: string; hazard: string;
  status: "BUNDLED" | "EXCLUDED" | "NOT AVAILABLE"; reason: string; held_out?: boolean;
}

export interface CellProps {
  cell: number; feature: number; phase: string; min_bt_K: number; area_km2: number; cold_core_km2: number;
  speed_kmh: number | null; heading_deg: number | null; d_min_bt_30: number | null; age_min: number; family: number;
  touches_missing: boolean; lon: number; lat: number; merges_splits_so_far: number;
}

export interface TrackPoint { frame: number; lon: number; lat: number; min_bt_K: number; area_km2: number;
                              cold_core_km2: number; phase: string }

export interface CellForecast {
  cell: number;
  by_lead: Record<string, { field_advection?: { lon: number; lat: number }; persistence?: { lon: number; lat: number };
                            ml_p_max_10km?: number | null }>;
}

export type Method = "persistence" | "pysteps_advection" | "pysteps_np31" | "ml";

export interface IssueScore { H: number; M: number; F: number; CN: number; n: number; CSI: number | null;
                              POD: number | null; bias: number | null; BS: number }

export interface SkillRow { lead_min: number; CSI: number | null; POD: number | null; FAR: number | null; bias: number | null;
                            BSS: number | null; FSS_40km_event_mean: number | null; n_px: number }

export interface Skill {
  source: string; leads: number[];
  pooled: Record<Method | "ml_raw", SkillRow[]>;
  by_event: Record<string, Record<string, { lead_min: number; CSI: number | null; BSS: number | null;
                                            FSS_40km: number | null; bias: number | null }[]>>;
  bootstrap: Record<string, number | string | null>[];
  reliability_by_bin: { method: string; lead_bin: string; ece: number;
                        bins: { bin: number; n: number; mean_p: number; obs_freq: number }[] }[];
  phase4_cross_event: { lead_min: number; CSI_persistence: number; CSI_pysteps: number; n_events_pysteps_better: number }[];
  phase4_decay: Record<string, string | number>[];
  phase5_decomposition: Record<string, string | number>[];
  claim_guard: string;
}

export interface Health {
  frames: { frame: number; time_utc: string; qc_status: string; qc_missing_frac: number; raw_missing_frac: number;
            gapfilled_frac: number; source_file: string; source_sha256: string }[];
  unscorable_frac_by_lead: { lead_min: number; excluded_frac_mean: number }[];
  sources: { source: string; status: string; role: string; note: string }[];
  latency_note: string;
  model: { version: string; artifacts: Record<string, string>; n_iter: number; train_days: string[]; validation_days: string[];
           test_events: string[]; calibration: string; deterministic_threshold_p: number };
  freeze_manifest_sha256: string;
  limitations: string[];
}

export interface Place { name: string; printed_as: string; lat: number; lon: number; state_hint: string; source: string;
                         report_date: string }

export interface DraftAlert { alert_id: string; place: string; lat: number; lon: number; lead_min: number; p_max: number; prediction_id: string }

export interface Alerts { rule: string; by_issue: Record<string, DraftAlert[]>; place_max_p_60min: Record<string, Record<string, number>> }

export interface Bundle {
  manifest: Manifest; skill: Skill; health: Health; places: Place[]; alerts: Alerts;
  scores: Record<string, Record<string, Partial<Record<Method, IssueScore>>>>;
  tracks: Record<string, TrackPoint[]>;
}
