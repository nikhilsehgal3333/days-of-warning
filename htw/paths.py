"""Folders and settings of each case.

case/<id>/        hand-made inputs: config.json, nodes.csv, sources.csv, evidence.csv,
                  assumptions.csv, gold_check.csv
results/<id>/     generated results
site/<id>/        generated figures and page
local/<id>/       downloaded texts (ignored by Git)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def cases() -> list[str]:
    return sorted(p.name for p in (ROOT / "case").iterdir() if (p / "config.json").exists())


def case_dir(case: str) -> Path:
    return ROOT / "case" / case


def _made(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def results_dir(case: str) -> Path:
    return _made(ROOT / "results" / case)


def site_dir(case: str) -> Path:
    return _made(ROOT / "site" / case)


def text_dir(case: str) -> Path:
    return _made(ROOT / "local" / case / "text")


def raw_dir(case: str) -> Path:
    return _made(ROOT / "local" / case / "raw")


def config(case: str) -> dict:
    return json.loads((case_dir(case) / "config.json").read_text(encoding="utf-8"))


def selected(argv: list[str] | None = None) -> tuple[list[str], bool]:
    """Read `--case <id>` (may repeat) and `--refresh` from the command line."""
    argv = sys.argv[1:] if argv is None else argv
    chosen = [argv[i + 1] for i, a in enumerate(argv) if a == "--case" and i + 1 < len(argv)]
    return (chosen or cases()), "--refresh" in argv
