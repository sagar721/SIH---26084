"""Download NOAA/NCEP-CPC globally merged 4 km IR brightness temperature files.

Source: https://ftp.cpc.ncep.noaa.gov/precip/global_full_res_IR/  (anonymous HTTPS)
Each hourly file ``merg_YYYYMMDDHH_4km-pixel.Z`` holds two half-hourly fields (HH:00, HH:30).
Every downloaded file is recorded in ``data/raw/cpc_merged_ir/manifest.json`` with its URL,
HTTP Last-Modified, byte size and SHA-256, so a re-run can prove it used the same bytes.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import threading
from contextlib import contextmanager
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE_URL = "https://ftp.cpc.ncep.noaa.gov/precip/global_full_res_IR/"
SATID_TEMPLATE = "geomerg_satid_{yyyymm}.Z"
RAW_DIR = Path("data/raw/cpc_merged_ir")
USER_AGENT = "sih26084-phase1/0.1 (research prototype)"
_MANIFEST_LOCK = threading.Lock()


def hourly_filename(t: datetime) -> str:
    return f"merg_{t:%Y%m%d%H}_4km-pixel.Z"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest(raw_dir: Path) -> dict:
    p = raw_dir / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _save_manifest(raw_dir: Path, manifest: dict) -> None:
    tmp = raw_dir / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    os.replace(tmp, raw_dir / "manifest.json")          # atomic: readers never see a half-written manifest


@contextmanager
def _manifest_locked(raw_dir: Path):
    """Thread lock + OS file lock, so parallel threads AND parallel download processes cannot lose entries."""
    with _MANIFEST_LOCK, (raw_dir / ".manifest.lock").open("w") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def download(filename: str, raw_dir: Path = RAW_DIR, retries: int = 8) -> Path:
    """Download one file (idempotent: skip if present with a matching manifest checksum).

    A broken transfer is resumed from the partial ``.part`` file with an HTTP Range request (Phase 6: the server
    dropped long transfers); the finished size must equal the server's total size before the file is accepted.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    with _manifest_locked(raw_dir):
        manifest = _load_manifest(raw_dir)
    dest = raw_dir / filename
    if dest.exists() and filename in manifest and manifest[filename]["sha256"] == sha256_of(dest):
        return dest
    url = BASE_URL + filename
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            offset = tmp.stat().st_size if tmp.exists() else 0
            headers = {"User-Agent": USER_AGENT, **({"Range": f"bytes={offset}-"} if offset else {})}
            with requests.get(url, stream=True, timeout=120, headers=headers) as r:
                if r.status_code == 416:          # partial file already complete (or larger than remote): restart
                    tmp.unlink()
                    raise requests.RequestException("range not satisfiable; restarting")
                r.raise_for_status()
                resumed = r.status_code == 206
                total = (int(r.headers["Content-Range"].split("/")[-1]) if resumed
                         else int(r.headers.get("Content-Length", -1)))
                with tmp.open("ab" if resumed else "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                if total >= 0 and tmp.stat().st_size != total:
                    raise requests.RequestException(f"incomplete: {tmp.stat().st_size} of {total} bytes")
                tmp.rename(dest)
                record = {
                    "source": "NOAA/NCEP/CPC Globally Merged IR (4 km, 30 min)",
                    "url": url,
                    "http_last_modified": r.headers.get("Last-Modified"),
                    "bytes": dest.stat().st_size,
                    "sha256": sha256_of(dest),
                    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "licence": "US Government work (NOAA); no access restriction observed - see docs/FIRST_EVENT.md",
                }
                with _manifest_locked(raw_dir):  # re-read so parallel workers don't overwrite each other's entries
                    manifest = _load_manifest(raw_dir)
                    manifest[filename] = record
                    _save_manifest(raw_dir, manifest)
                return dest
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(min(60, 10 * attempt))
    raise RuntimeError("unreachable")


def download_window(start: datetime, end: datetime, raw_dir: Path = RAW_DIR, workers: int = 6) -> list[Path]:
    t = start.replace(minute=0, second=0, microsecond=0)
    names = []
    while t <= end:
        names.append(hourly_filename(t))
        t += timedelta(hours=1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda n: download(n, raw_dir), names))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", required=True, help="UTC, e.g. 2026-05-14T00:00")
    ap.add_argument("--end", required=True, help="UTC, e.g. 2026-05-14T23:00")
    ap.add_argument("--satid", action="store_true", help="also fetch the monthly satellite-ID file")
    a = ap.parse_args()
    start = datetime.fromisoformat(a.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(a.end).replace(tzinfo=timezone.utc)
    for p in download_window(start, end):
        print(p)
    if a.satid:
        print(download(SATID_TEMPLATE.format(yyyymm=f"{start:%Y%m}")))


if __name__ == "__main__":
    main()
