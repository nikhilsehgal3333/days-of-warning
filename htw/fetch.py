"""Download the web sources of a case and extract their text.

Texts go to local/<case>/text/<source_id>.txt (ignored by Git). The repository stores only the
address, the snapshot timestamp, the SHA-256 value and the date of each download, in
case/<case>/sources_lock.csv.

    py -3.12 -m htw.fetch [--case <id>] [--refresh]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date
from urllib.parse import urlencode

from . import net, paths


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


def run(case: str, refresh: bool = False) -> None:
    text_dir, raw_dir = paths.text_dir(case), paths.raw_dir(case)
    lock_path = paths.case_dir(case) / "sources_lock.csv"
    lock = {}
    if lock_path.exists():
        lock = {r["source_id"]: r for r in csv.DictReader(open(lock_path, encoding="utf-8"))}
    for row in csv.DictReader(open(paths.case_dir(case) / "sources.csv", encoding="utf-8")):
        sid = row["source_id"]
        if row["kind"] == "api":
            continue  # written by htw/signals.py
        target = text_dir / f"{sid}.txt"
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
            print(f"[{case}] {sid}: failed ({error})")
            continue
        (raw_dir / f"{sid}.bin").write_bytes(body)
        target.write_text(text, encoding="utf-8")
        lock[sid] = {"source_id": sid, "final_url": final, "snapshot_ts": ts,
                     "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
                     "chars": len(text), "retrieved": date.today().isoformat(), "status": status}
        print(f"[{case}] {sid}: {len(text):,} characters" + (f" (snapshot {ts})" if ts else ""))
    fields = ["source_id", "final_url", "snapshot_ts", "sha256", "bytes", "chars", "retrieved", "status"]
    with open(lock_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(lock[k] for k in sorted(lock))


def main() -> None:
    chosen, refresh = paths.selected()
    for case in chosen:
        run(case, refresh)


if __name__ == "__main__":
    main()
