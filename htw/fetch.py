"""Download the web sources in case/sources.csv and extract their text.

Texts go to local/text/<source_id>.txt (ignored by Git). The repository stores only the address,
the snapshot timestamp, the SHA-256 value and the date of each download, in case/sources_lock.csv.

    py -3.12 -m htw.fetch            download sources that have no local text yet
    py -3.12 -m htw.fetch --refresh  download all sources again
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from . import net

ROOT = Path(__file__).resolve().parent.parent
CASE = ROOT / "case"
TEXT = ROOT / "local" / "text"
RAW = ROOT / "local" / "raw"


def newest_snapshot_before(url: str, before: str) -> str | None:
    query = urlencode({"url": url, "to": before, "output": "json",
                       "filter": "statuscode:200", "fl": "timestamp"})
    body, _ = net.get("https://web.archive.org/cdx/search/cdx?" + query)
    rows = json.loads(body or b"[]")
    return rows[-1][0] if len(rows) > 1 else None


def extract(body: bytes) -> str:
    if body[:4] == b"%PDF":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(body)).pages)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ")


def main() -> None:
    refresh = "--refresh" in sys.argv
    TEXT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    lock_path = CASE / "sources_lock.csv"
    lock = {}
    if lock_path.exists():
        lock = {r["source_id"]: r for r in csv.DictReader(open(lock_path, encoding="utf-8"))}
    for row in csv.DictReader(open(CASE / "sources.csv", encoding="utf-8")):
        sid = row["source_id"]
        if row["kind"] == "api":
            continue  # written by the signal scripts
        target = TEXT / f"{sid}.txt"
        if target.exists() and not refresh:
            continue
        status, final, ts = "ok", "", row["snapshot_ts"]
        try:
            if not ts and row["snapshot_before"]:
                ts = newest_snapshot_before(row["url"], row["snapshot_before"]) or ""
                if not ts:
                    raise ValueError(f"no snapshot before {row['snapshot_before']}")
            url = f"https://web.archive.org/web/{ts}id_/{row['url']}" if ts else row["url"]
            body, final = net.get(url)
            text = extract(body)
        except Exception as error:  # the list continues when one site refuses
            lock[sid] = {"source_id": sid, "final_url": final, "snapshot_ts": ts, "sha256": "",
                         "bytes": 0, "chars": 0, "retrieved": date.today().isoformat(),
                         "status": f"failed: {error}"}
            print(f"{sid}: failed ({error})")
            continue
        (RAW / f"{sid}.bin").write_bytes(body)
        target.write_text(text, encoding="utf-8")
        lock[sid] = {"source_id": sid, "final_url": final, "snapshot_ts": ts,
                     "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                     "chars": len(text), "retrieved": date.today().isoformat(), "status": status}
        print(f"{sid}: {len(text):,} characters" + (f" (snapshot {ts})" if ts else ""))
    fields = ["source_id", "final_url", "snapshot_ts", "sha256", "bytes", "chars", "retrieved", "status"]
    with open(lock_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(lock[k] for k in sorted(lock))


if __name__ == "__main__":
    main()
