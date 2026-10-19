"""
main.py — Thai Lottery Analytics Pipeline Orchestrator
ผู้ประสานงานไปป์ไลน์การวิเคราะห์สลากกินแบ่งรัฐบาลแบบครบวงจร
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output across Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure local modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scraper import scrape_all, save_raw, load_raw, SAMPLE_RECORDS
from processor import LotteryProcessor, run_processor
from models.ensemble import EnsembleModel
from backtester import Backtester
from exporter import (
    export_results_json,
    export_results_csv,
    export_statistics,
    export_predictions,
    export_backtesting,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main_pipeline")


def calculate_next_draw_date(last_date_str: str) -> str:
    """Calculate the next Thai lottery draw date (normally 1st or 16th)."""
    try:
        last_dt = datetime.strptime(last_date_str, "%Y-%m-%d")
        year = last_dt.year
        month = last_dt.month
        day = last_dt.day

        if day < 16:
            next_day = 16
            next_month = month
            next_year = year
        else:
            next_day = 1
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year

        # Special cases: Jan 1 is New Year (moved to Dec 30 or Jan 17), May 1 Labour day (May 2)
        if next_month == 1 and next_day == 1:
            next_day = 17
        elif next_month == 5 and next_day == 1:
            next_day = 2

        return f"{next_year:04d}-{next_month:02d}-{next_day:02d}"
    except Exception:
        return "2026-11-01"


def run_pipeline(force_scrape: bool = False, skip_scraper: bool = False) -> None:
    """Run the entire end-to-end data pipeline."""
    print("=" * 70)
    print("🎰 THAI LOTTERY ANALYTICS — PIPELINE EXECUTION")
    print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. Scraping Step
    records = []
    if not skip_scraper:
        logger.info("Step 1/5: Running data scraper (3-source fallback)...")
        try:
            records = scrape_all()
            if records:
                save_raw(records)
                logger.info("Successfully scraped %d draw records", len(records))
        except Exception as e:
            logger.warning("Scraper encountered issue: %s. Falling back to cached data.", e)

    if not records:
        logger.info("Loading existing cached records from data/raw/...")
        records = load_raw()

    if not records:
        logger.warning("No scraped or cached records found. Using calibrated historical sample dataset.")
        records = SAMPLE_RECORDS

    logger.info("Using %d total draw records for analysis", len(records))

    # 2. Processing & Feature Engineering
    logger.info("Step 2/5: Computing statistical features & gap analysis...")
    processor = LotteryProcessor(records)
    stats = processor.compute_all()
    logger.info("Feature engineering complete across %d draws", stats.get("total_draws", len(records)))

    # 3. Backtesting Step
    logger.info("Step 3/5: Running walk-forward model backtesting across 6 models (48 draws window)...")
    backtester = Backtester(window_size=48)
    backtest_data = backtester.run(records, test_draws=48)

    # Derive ensemble weights dynamically from backtesting accuracy
    model_weights = {}
    for m_name, m_info in backtest_data.get("models", {}).items():
        acc = m_info.get("overall_accuracy", {}).get("last_two", 0.20)
        model_weights[m_name] = max(0.08, acc)

    # 4. ML Model Training & Ensemble Prediction
    logger.info("Step 4/5: Fitting 6 ML Models & Two-Stage Monte Carlo Stacking Ensemble...")
    ensemble = EnsembleModel(weights=model_weights)
    ensemble.train_all(records)

    latest_date = records[0].get("date", "2026-10-16") if records else "2026-10-16"
    next_draw_date = calculate_next_draw_date(latest_date)
    predictions = ensemble.generate_full_prediction(records, next_draw_date=next_draw_date)

    # 5. Exporting Artifacts
    logger.info("Step 5/5: Exporting JSON & CSV data files for frontend and analysis...")
    p_res_json = export_results_json(records)
    p_res_csv = export_results_csv(records)
    p_stats = export_statistics(stats)
    p_preds = export_predictions(predictions)
    p_backtest = export_backtesting(backtest_data)

    print("\n" + "=" * 70)
    print("✅ PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"📦 Total Draws Processed: {len(records)}")
    print(f"📅 Latest Draw Date:     {latest_date}")
    print(f"🎯 Next Predicted Draw:   {next_draw_date}")
    print("-" * 70)
    print("📁 Exported Artifacts:")
    print(f"   • {p_res_json}")
    print(f"   • {p_res_csv}")
    print(f"   • {p_stats}")
    print(f"   • {p_preds}")
    print(f"   • {p_backtest}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thai Lottery Analytics Runner")
    parser.add_argument("--force-scrape", action="store_true", help="Force re-scraping from web")
    parser.add_argument("--skip-scraper", action="store_true", help="Skip web scraping and use local data")
    args = parser.parse_args()

    run_pipeline(force_scrape=args.force_scrape, skip_scraper=args.skip_scraper)
