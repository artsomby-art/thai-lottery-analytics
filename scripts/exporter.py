"""
exporter.py — Export Engine for Thai Lottery Data
ส่งออกข้อมูลเป็น JSON และ CSV สำหรับ Frontend และ Data Analysis
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("exporter")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def export_results_json(records: list[dict[str, Any]]) -> Path:
    """Export all draw records to data/results.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "results.json"

    # Normalize draws for dual compatibility (draws + results keys, field aliases)
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

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info("Exported results to %s (%d records)", out_path, len(normalized_draws))
    return out_path


def export_results_csv(records: list[dict[str, Any]]) -> Path:
    """Export all draw records to data/results.csv."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "results.csv"

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

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
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

    logger.info("Exported CSV to %s (%d records)", out_path, len(records))
    return out_path


def export_statistics(stats: dict[str, Any]) -> Path:
    """Save processed statistics to data/statistics.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "statistics.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    logger.info("Exported statistics to %s", out_path)
    return out_path


def export_predictions(predictions: dict[str, Any]) -> Path:
    """Save ML predictions to data/predictions.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "predictions.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)

    logger.info("Exported predictions to %s", out_path)
    return out_path


def export_backtesting(backtest_data: dict[str, Any]) -> Path:
    """Save backtesting accuracy metrics to data/backtesting.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / "backtesting.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(backtest_data, f, ensure_ascii=False, indent=2)

    logger.info("Exported backtesting metrics to %s", out_path)
    return out_path
