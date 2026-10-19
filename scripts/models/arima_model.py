"""
models/arima_model.py — ARIMA Time-Series Model
โมเดล ARIMA(2,1,2) สำหรับทำนายความถี่ของแต่ละหลักตัวเลขในแต่ละตำแหน่ง
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np

logger = logging.getLogger("models.arima")

try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logger.warning("statsmodels not available — ARIMA model will produce fallback output")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}

ARIMA_ORDER = (2, 1, 2)


class ARIMAModel:
    """
    ARIMA(2,1,2) model fitted independently on the time-series of each
    digit-position frequency across historical draws.
    โมเดล ARIMA สำหรับแต่ละ position ของแต่ละ prize type
    """

    MODEL_NAME = "arima"

    def __init__(self) -> None:
        # Stores predicted probability distribution per prize_type → position → digit
        self._predictions: dict[str, dict[str, dict[str, float]]] = {}
        self._trained = False

    def _build_series(
        self, records: list[dict[str, Any]], prize_type: str, pos: int, digit: str
    ) -> list[float]:
        """
        Build a time series: for each draw, what fraction of numbers for this
        prize_type had `digit` at position `pos`?
        """
        series: list[float] = []
        num_len = PRIZE_LENGTHS[prize_type]
        for rec in records:
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            if not nums:
                series.append(0.0)
                continue
            match_count = sum(
                1 for n in nums
                if len(str(n).zfill(num_len)) > pos and str(n).zfill(num_len)[pos] == digit
            )
            series.append(match_count / len(nums))
        return series

    def _fit_arima(self, series: list[float]) -> float:
        """
        Fit ARIMA and forecast one step ahead.
        Returns the predicted probability (clamped to [0,1]).
        """
        if not HAS_STATSMODELS or len(series) < 10:
            return float(np.mean(series)) if series else 0.1

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                model = ARIMA(series, order=ARIMA_ORDER)
                result = model.fit()
                forecast = float(result.forecast(steps=1)[0])
                return max(0.0, min(1.0, forecast))
            except Exception as exc:
                logger.debug("ARIMA fit error: %s — using mean", exc)
                return float(np.mean(series))

    def train(self, records: list[dict[str, Any]]) -> None:
        """
        Fit ARIMA models for all prize types and positions.
        เทรน ARIMA สำหรับทุก prize type และทุก position
        """
        logger.info("Training ARIMAModel on %d records…", len(records))
        self._predictions = {}

        for prize_type, num_len in PRIZE_LENGTHS.items():
            pos_preds: dict[str, dict[str, float]] = {}
            for pos in range(num_len):
                digit_probs: dict[str, float] = {}
                for digit in [str(d) for d in range(10)]:
                    series = self._build_series(records, prize_type, pos, digit)
                    digit_probs[digit] = self._fit_arima(series)

                # Normalize to sum to 1
                total = sum(digit_probs.values()) or 1.0
                pos_preds[str(pos)] = {d: v / total for d, v in digit_probs.items()}

            self._predictions[prize_type] = pos_preds
            logger.info("  ARIMA trained: %s", prize_type)

        self._trained = True
        logger.info("ARIMAModel training complete")

    def _score_number(self, number: str, prize_type: str) -> float:
        """Score a number as the product of per-position predicted probabilities."""
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
        """Generate top-10 candidates for a prize type using ARIMA predictions."""
        from itertools import product
        num_len = PRIZE_LENGTHS[prize_type]
        preds = self._predictions.get(prize_type, {})

        # For 6-digit: take top 3 digits per position then score combinations
        if num_len == 6:
            top_per_pos: list[list[str]] = []
            for pos in range(num_len):
                pd = preds.get(str(pos), {d: 0.1 for d in "0123456789"})
                top_per_pos.append(sorted(pd, key=pd.get, reverse=True)[:3])  # type: ignore[arg-type]
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
        คืนค่าการทำนายสำหรับแต่ละ prize type
        """
        if not self._trained:
            raise RuntimeError("ARIMAModel not trained. Call train() first.")

        result: dict[str, Any] = {}
        for prize_type in PRIZE_LENGTHS:
            candidates = self._generate_candidates(prize_type)
            result[prize_type] = {
                "top10": [
                    {"number": num, "score": round(score, 6)}
                    for num, score in candidates[:10]
                ],
                "model": self.MODEL_NAME,
            }
        return result

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """Return top-10 predicted numbers for backtesting."""
        if not self._trained:
            return []
        candidates = self._generate_candidates(prize_type)
        return [num for num, _ in candidates[:10]]
