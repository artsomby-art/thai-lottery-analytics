"""
models/prophet_model.py — Facebook Prophet Seasonality Model
โมเดล Prophet สำหรับจับ seasonality รายเดือน และ semi-monthly (วันที่ 1 และ 16)
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("models.prophet")

try:
    from prophet import Prophet  # type: ignore
    HAS_PROPHET = True
except ImportError:
    try:
        from fbprophet import Prophet  # type: ignore
        HAS_PROPHET = True
    except ImportError:
        HAS_PROPHET = False
        logger.warning("prophet not installed — ProphetModel will use trend-based fallback")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}


class ProphetModel:
    """
    Facebook Prophet model with monthly and semi-monthly seasonality.
    Captures the pattern that Thai lottery draws on the 1st and 16th of each month.
    โมเดล Prophet จับ seasonality สำหรับสลากที่ออกทุกวันที่ 1 และ 16
    """

    MODEL_NAME = "prophet"

    def __init__(self) -> None:
        self._predictions: dict[str, dict[str, dict[str, float]]] = {}
        self._next_draw_date: str = ""
        self._trained = False

    def _compute_next_draw_date(self, records: list[dict[str, Any]]) -> str:
        """
        Compute the next lottery draw date (1st or 16th of next applicable month).
        คำนวณวันที่งวดถัดไป
        """
        if not records:
            today = datetime.utcnow()
            next_day = 1 if today.day >= 16 else 16
            if next_day == 1:
                month = today.month + 1
                year = today.year + (1 if month > 12 else 0)
                month = (month - 1) % 12 + 1
            else:
                month = today.month
                year = today.year
            return f"{year:04d}-{month:02d}-{next_day:02d}"

        latest = max(records, key=lambda r: r.get("date", ""))["date"]
        try:
            dt = datetime.strptime(latest, "%Y-%m-%d")
        except ValueError:
            return ""
        if dt.day < 16:
            return f"{dt.year:04d}-{dt.month:02d}-16"
        else:
            # Next month 1st
            if dt.month == 12:
                return f"{dt.year + 1:04d}-01-01"
            return f"{dt.year:04d}-{dt.month + 1:02d}-01"

    def _build_frequency_series(
        self, records: list[dict[str, Any]], prize_type: str, pos: int, digit: str
    ) -> pd.DataFrame:
        """
        Build a pandas DataFrame {ds, y} for Prophet where y is the
        fraction of numbers for this prize_type having `digit` at `pos`.
        """
        num_len = PRIZE_LENGTHS[prize_type]
        rows = []
        for rec in records:
            date_str = rec.get("date", "")
            if not date_str:
                continue
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            if not nums:
                continue
            match = sum(
                1 for n in nums
                if len(str(n).zfill(num_len)) > pos and str(n).zfill(num_len)[pos] == digit
            )
            rows.append({"ds": pd.Timestamp(date_str), "y": match / len(nums)})

        df = pd.DataFrame(rows)
        df = df.sort_values("ds").reset_index(drop=True)
        return df

    def _fit_prophet(self, df: pd.DataFrame, future_date: str) -> float:
        """
        Fit a Prophet model and forecast for future_date.
        Returns predicted probability, clamped to [0,1].
        """
        if not HAS_PROPHET or len(df) < 8:
            return float(df["y"].mean()) if not df.empty else 0.1

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                m = Prophet(
                    yearly_seasonality=True,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    seasonality_mode="additive",
                )
                # Add semi-monthly seasonality (period = 15.2 days)
                m.add_seasonality(name="semi_monthly", period=15.2, fourier_order=3)
                m.fit(df)

                future = pd.DataFrame({"ds": [pd.Timestamp(future_date)]})
                forecast = m.predict(future)
                val = float(forecast["yhat"].iloc[0])
                return max(0.0, min(1.0, val))
            except Exception as exc:
                logger.debug("Prophet fit error: %s", exc)
                return float(df["y"].mean())

    def train(self, records: list[dict[str, Any]]) -> None:
        """
        Fit Prophet models for all prize types and digit positions.
        เทรนโมเดล Prophet สำหรับทุก prize type
        """
        logger.info("Training ProphetModel on %d records…", len(records))
        self._next_draw_date = self._compute_next_draw_date(records)
        logger.info("Next draw date: %s", self._next_draw_date)

        self._predictions = {}
        for prize_type, num_len in PRIZE_LENGTHS.items():
            pos_preds: dict[str, dict[str, float]] = {}
            for pos in range(num_len):
                digit_probs: dict[str, float] = {}
                for digit in [str(d) for d in range(10)]:
                    df = self._build_frequency_series(records, prize_type, pos, digit)
                    digit_probs[digit] = self._fit_prophet(df, self._next_draw_date)

                # Normalize
                total = sum(digit_probs.values()) or 1.0
                pos_preds[str(pos)] = {d: v / total for d, v in digit_probs.items()}

            self._predictions[prize_type] = pos_preds
            logger.info("  Prophet trained: %s", prize_type)

        self._trained = True
        logger.info("ProphetModel training complete")

    def _score_number(self, number: str, prize_type: str) -> float:
        """Score a candidate number using per-position prophet predictions."""
        preds = self._predictions.get(prize_type, {})
        if not preds:
            return 0.0
        num_len = PRIZE_LENGTHS[prize_type]
        number = str(number).zfill(num_len)[-num_len:]
        prob = 1.0
        for pos, digit in enumerate(number):
            pos_pred = preds.get(str(pos), {})
            prob *= pos_pred.get(digit, 0.1)
        return prob

    def _generate_candidates(self, prize_type: str) -> list[tuple[str, float]]:
        """Generate top-10 candidates for a prize type."""
        from itertools import product
        num_len = PRIZE_LENGTHS[prize_type]
        preds = self._predictions.get(prize_type, {})

        if num_len == 6:
            top_per_pos: list[list[str]] = []
            for pos in range(num_len):
                pd_dict = preds.get(str(pos), {d: 0.1 for d in "0123456789"})
                top_per_pos.append(sorted(pd_dict, key=pd_dict.get, reverse=True)[:3])  # type: ignore[arg-type]
            combos = {
                "".join(c): self._score_number("".join(c), prize_type)
                for c in product(*top_per_pos)
            }
            return sorted(combos.items(), key=lambda x: x[1], reverse=True)[:10]
        else:
            max_val = 10 ** num_len
            scored = [
                (str(i).zfill(num_len), self._score_number(str(i).zfill(num_len), prize_type))
                for i in range(max_val)
            ]
            return sorted(scored, key=lambda x: x[1], reverse=True)[:10]

    def predict(self) -> dict[str, Any]:
        """
        Return top-10 predictions for each prize type.
        คืนค่าการทำนายจากโมเดล Prophet
        """
        if not self._trained:
            raise RuntimeError("ProphetModel not trained. Call train() first.")

        result: dict[str, Any] = {}
        for prize_type in PRIZE_LENGTHS:
            candidates = self._generate_candidates(prize_type)
            result[prize_type] = {
                "top10": [
                    {"number": num, "score": round(score, 6)}
                    for num, score in candidates[:10]
                ],
                "model": self.MODEL_NAME,
                "next_draw_date": self._next_draw_date,
            }
        return result

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """Return top-10 predicted numbers for backtesting."""
        if not self._trained:
            return []
        candidates = self._generate_candidates(prize_type)
        return [num for num, _ in candidates[:10]]

    def get_next_draw_date(self) -> str:
        return self._next_draw_date
