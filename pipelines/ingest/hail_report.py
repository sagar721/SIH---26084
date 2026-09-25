"""Archive the IMD RMC New Delhi hail-storm report and geocode the stations for one date.

The PDF is overwritten by IMD as the season progresses, so we keep a dated copy with its
SHA-256. Station coordinates come from OpenStreetMap Nominatim (1 request/second, per its
usage policy) and are cached in ``data/raw/hail_reports/geocoded_<date>.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

REPORT_URL = "https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
RAW_DIR = Path("data/raw/hail_reports")
USER_AGENT = "sih26084-phase1/0.1 (research prototype; contact via project repo)"


def archive_report(raw_dir: Path = RAW_DIR) -> dict:
    raw_dir.mkdir(parents=True, exist_ok=True)
    r = requests.get(REPORT_URL, timeout=60, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    digest = hashlib.sha256(r.content).hexdigest()
    dest = raw_dir / f"hailstorm_report_{digest[:12]}.pdf"
    dest.write_bytes(r.content)
    meta = {
        "source": "IMD Regional Meteorological Centre New Delhi - hail storm report, NW India",
        "url": REPORT_URL,
        "http_last_modified": r.headers.get("Last-Modified"),
        "bytes": len(r.content),
        "sha256": digest,
        "path": str(dest),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "licence": "Public IMD web document; attribution to IMD",
    }
    (raw_dir / "report_manifest.json").write_text(json.dumps(meta, indent=2))
    return meta


def geocode_stations(event_cfg: dict, raw_dir: Path = RAW_DIR) -> list[dict]:
    out_path = raw_dir / f"geocoded_{event_cfg['date']}.json"
    if out_path.exists():
        return json.loads(out_path.read_text())
    results = []
    for st in event_cfg["hail_reports"]:
        q = f"{st['name']}, {st['state_hint']}, India"
        r = requests.get(NOMINATIM, params={"q": q, "format": "json", "limit": 1},
                         headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        hits = r.json()
        rec = {"name": st["name"], "printed_as": st.get("printed_as", st["name"]),
               "state_hint": st["state_hint"], "query": q}
        if hits:
            rec.update(lat=float(hits[0]["lat"]), lon=float(hits[0]["lon"]),
                       osm_display_name=hits[0]["display_name"], status="OK")
        else:
            rec.update(lat=None, lon=None, status="NOT_FOUND")
        results.append(rec)
        time.sleep(1.1)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    a = ap.parse_args()
    cfg = yaml.safe_load(Path("config/events.yaml").read_text())[a.event]
    print(json.dumps(archive_report(), indent=2))
    for rec in geocode_stations(cfg):
        print(rec["name"], rec["status"], rec.get("lat"), rec.get("lon"))


if __name__ == "__main__":
    main()
