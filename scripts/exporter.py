"""
exporter.py — Export Engine for Thai Lottery Data
ส่งออกข้อมูลเป็น JSON และ CSV สำหรับ Frontend (docs/data) และ Data Analysis (data)
"""

from __future__ import annotations

import csv
import json
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger("exporter")

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DATA_DIR = ROOT_DIR / "docs" / "data"


def _write_dual(filename: str, content: str) -> Path:
    """Write content to both data/ and docs/data/ directories."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    p1 = DATA_DIR / filename
    p2 = DOCS_DATA_DIR / filename

    with open(p1, "w", encoding="utf-8") as f:
        f.write(content)
    with open(p2, "w", encoding="utf-8") as f:
        f.write(content)

    return p1


def export_results_json(records: list[dict[str, Any]]) -> Path:
    """Export all draw records to data/results.json and docs/data/results.json."""
    normalized_draws = []
    for r in records:
        f3 = r.get("front_three") or r.get("last_three_f") or []
        b3 = r.get("back_three") or r.get("last_three_b") or []
        first = r.get("first_prize") or r.get("first") or ""
        l2 = r.get("last_two") or ""
        d = r.get("date") or ""
        dt = r.get("date_thai") or ""

        normalized_draws.append({
            "date": d,
            "date_thai": dt,
            "draw_id": d,
            "first_prize": first,
            "first": first,
            "front_three": f3,
            "last_three_f": f3,
            "back_three": b3,
            "last_three_b": b3,
            "last_two": l2,
        })

    payload = {
        "last_updated": records[0].get("date", "") if records else "",
        "total_draws": len(normalized_draws),
        "results": normalized_draws,
        "draws": normalized_draws,
    }

    content = json.dumps(payload, ensure_ascii=False, indent=2)
    p = _write_dual("results.json", content)
    logger.info("Exported results.json to data/ and docs/data/ (%d records)", len(normalized_draws))
    return p


def export_results_csv(records: list[dict[str, Any]]) -> Path:
    """Export all draw records to data/results.csv and docs/data/results.csv."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)

    p1 = DATA_DIR / "results.csv"
    p2 = DOCS_DATA_DIR / "results.csv"

    fieldnames = [
        "date",
        "date_thai",
        "first_prize",
        "front_three_1",
        "front_three_2",
        "back_three_1",
        "back_three_2",
        "last_two",
    ]

    for p in (p1, p2):
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                f3 = r.get("front_three") or r.get("last_three_f") or []
                b3 = r.get("back_three") or r.get("last_three_b") or []
                writer.writerow({
                    "date": r.get("date", ""),
                    "date_thai": r.get("date_thai", ""),
                    "first_prize": r.get("first_prize") or r.get("first", ""),
                    "front_three_1": f3[0] if len(f3) > 0 else "",
                    "front_three_2": f3[1] if len(f3) > 1 else "",
                    "back_three_1": b3[0] if len(b3) > 0 else "",
                    "back_three_2": b3[1] if len(b3) > 1 else "",
                    "last_two": r.get("last_two", ""),
                })

    logger.info("Exported results.csv to data/ and docs/data/ (%d records)", len(records))
    return p1


def export_statistics(stats: dict[str, Any]) -> Path:
    """Save processed statistics to data/statistics.json and docs/data/statistics.json."""
    content = json.dumps(stats, ensure_ascii=False, indent=2)
    p = _write_dual("statistics.json", content)
    logger.info("Exported statistics.json to data/ and docs/data/")
    return p


def export_predictions(predictions: dict[str, Any]) -> Path:
    """Save ML predictions to data/predictions.json and docs/data/predictions.json."""
    content = json.dumps(predictions, ensure_ascii=False, indent=2)
    p = _write_dual("predictions.json", content)
    logger.info("Exported predictions.json to data/ and docs/data/")
    return p


def export_backtesting(backtest_data: dict[str, Any]) -> Path:
    """Save backtesting accuracy metrics to data/backtesting.json and docs/data/backtesting.json."""
    content = json.dumps(backtest_data, ensure_ascii=False, indent=2)
    p = _write_dual("backtesting.json", content)
    logger.info("Exported backtesting.json to data/ and docs/data/")
    return p
