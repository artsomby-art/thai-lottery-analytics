"""
models/ensemble.py — Ensemble Combiner for Thai Lottery Models
รวมผลการทำนายจาก Frequency, ARIMA, Prophet และ LSTM โดยถ่วงน้ำหนักตาม Backtesting
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .frequency_model import FrequencyModel
from .arima_model import ARIMAModel
from .prophet_model import ProphetModel
from .lstm_model import LSTMModel

logger = logging.getLogger("models.ensemble")

PRIZE_TYPES = ["first_prize", "front_three", "back_three", "last_two"]
DEFAULT_WEIGHTS = {
    "frequency": 0.30,
    "arima": 0.25,
    "prophet": 0.25,
    "lstm": 0.20,
}


class EnsembleModel:
    """
    Combines predictions from multiple distinct ML models.
    รวมผลคะแนนจากแต่ละโมเดลด้วยคะแนนถ่วงน้ำหนัก (Weighted Score)
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.frequency_model = FrequencyModel()
        self.arima_model = ARIMAModel()
        self.prophet_model = ProphetModel()
        self.lstm_model = LSTMModel()
        self._trained = False

    def train_all(self, records: list[dict[str, Any]]) -> None:
        """
        Train all underlying sub-models.
        """
        logger.info("Training all ensemble sub-models on %d records…", len(records))
        self.frequency_model.train(records)
        self.arima_model.train(records)
        self.prophet_model.train(records)
        self.lstm_model.train(records)
        self._trained = True
        logger.info("Ensemble sub-models training complete.")

    def set_weights(self, weights: dict[str, float]) -> None:
        """Update ensemble weights based on backtesting results."""
        total = sum(weights.values())
        if total > 0:
            self.weights = {k: round(v / total, 4) for k, v in weights.items()}

    def predict_prize(
        self, prize_type: str, top_n: int = 10
    ) -> dict[str, Any]:
        """
        Generate predictions for a specific prize type from all models and combined ensemble.
        """
        # Fetch predictions from each individual model
        sub_preds = {
            "frequency": self.frequency_model.predict().get(prize_type, {}).get("top10", []),
            "arima": self.arima_model.predict().get(prize_type, {}).get("top10", []),
            "prophet": self.prophet_model.predict().get(prize_type, {}).get("top10", []),
            "lstm": self.lstm_model.predict().get(prize_type, {}).get("top10", []),
        }

        # Calculate combined weighted score
        combined_scores: dict[str, float] = defaultdict(float)
        model_support: dict[str, list[str]] = defaultdict(list)

        for model_name, preds in sub_preds.items():
            w = self.weights.get(model_name, 0.25)
            for item in preds:
                num = item["number"]
                score = float(item["score"])
                combined_scores[num] += score * w
                if model_name not in model_support[num]:
                    model_support[num].append(model_name)

        # Sort and normalize top ensemble candidates
        sorted_combined = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_combined[0][1] if sorted_combined else 1.0

        ensemble_top = [
            {
                "number": num,
                "score": round(score / max_score, 4),
                "model_votes": model_support.get(num, [list(sub_preds.keys())[0]]),
            }
            for num, score in sorted_combined[:top_n]
        ]

        # Format individual model outputs for schema compliance
        models_output = {}
        for m_name, preds in sub_preds.items():
            models_output[m_name] = {
                "top10": preds[:top_n],
                "weight": self.weights.get(m_name, 0.25),
            }

        return {
            "models": models_output,
            "ensemble": {
                "top10": ensemble_top,
                "weights": self.weights,
            },
        }

    def generate_full_prediction(
        self, records: list[dict[str, Any]], next_draw_date: str
    ) -> dict[str, Any]:
        """
        Generate complete prediction output for all prize types.
        """
        if not self._trained:
            self.train_all(records)

        prize_results = {}
        for pt in PRIZE_TYPES:
            prize_results[pt] = self.predict_prize(pt, top_n=10)

        return {
            "generated_at": records[0].get("date", "2026-10-16") if records else "2026-10-16",
            "next_draw_date": next_draw_date,
            "prize_types": prize_results,
        }
