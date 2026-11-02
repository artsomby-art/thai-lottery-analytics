"""
models/ensemble.py — Two-Stage Monte Carlo Stacking Ensemble
สถาปัตยกรรม 2 ชั้น:
Stage 1: Frequency, Markov Chain, ARIMA, Prophet, LSTM คำนวณความน่าจะเป็น
Stage 2: Monte Carlo Simulation (50,000 รอบ) สังเคราะห์ตัวเลข Top 10 พร้อมเลขเด่น 6 หลัก
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from .frequency_model import FrequencyModel
from .markov_model import MarkovChainModel
from .arima_model import ARIMAModel
from .prophet_model import ProphetModel
from .lstm_model import LSTMModel
from .monte_carlo import MonteCarloEngine
from .feature_pattern_model import FeaturePatternModel

logger = logging.getLogger("models.ensemble")

PRIZE_TYPES = ["first_prize", "front_three", "back_three", "last_two"]
PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}

DEFAULT_WEIGHTS = {
    "feature_pattern": 0.25,
    "markov": 0.20,
    "frequency": 0.15,
    "monte_carlo": 0.15,
    "arima": 0.10,
    "prophet": 0.08,
    "lstm": 0.07,
}


class EnsembleModel:
    """
    Two-Stage Stacking Ensemble Combiner with Monte Carlo Synthesis & Feature Pattern Engine.
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.frequency_model = FrequencyModel()
        self.markov_model = MarkovChainModel()
        self.arima_model = ARIMAModel()
        self.prophet_model = ProphetModel()
        self.lstm_model = LSTMModel()
        self.monte_carlo_engine = MonteCarloEngine(simulations=50000)
        self.feature_pattern_model = FeaturePatternModel()
        self._trained = False

    def train_all(self, records: list[dict[str, Any]]) -> None:
        """
        Train all underlying sub-models.
        """
        logger.info("Training all 7 ensemble sub-models on %d records…", len(records))
        self.frequency_model.train(records)
        self.markov_model.train(records)
        self.arima_model.train(records)
        self.prophet_model.train(records)
        self.lstm_model.train(records)
        self.monte_carlo_engine.train(records)
        self.feature_pattern_model.train(records)
        self._trained = True
        logger.info("All 7 sub-models trained successfully.")

    def set_weights(self, weights: dict[str, float]) -> None:
        """Update ensemble weights based on backtesting results."""
        total = sum(weights.values())
        if total > 0:
            self.weights = {k: round(v / total, 4) for k, v in weights.items()}

    def _build_combined_pos_probs(self, prize_type: str) -> dict[int, dict[str, float]]:
        """
        Synthesize weighted combined probability density function (PDF) per digit position.
        """
        num_len = PRIZE_LENGTHS.get(prize_type, 2)
        digits = [str(d) for d in range(10)]

        # Get distributions from sub-models
        freq_dist = self.frequency_model._distributions.get(prize_type, {})
        markov_pos = self.markov_model.get_positional_probs(prize_type)
        arima_preds = self.arima_model._predictions.get(prize_type, {})

        combined_probs: dict[int, dict[str, float]] = {}

        w_freq = self.weights.get("frequency", 0.20)
        w_markov = self.weights.get("markov", 0.25)
        w_arima = self.weights.get("arima", 0.15)
        w_prophet = self.weights.get("prophet", 0.15)
        w_lstm = self.weights.get("lstm", 0.15)

        for pos in range(num_len):
            pos_p: dict[str, float] = {}
            for d in digits:
                # Frequency component
                f_score = freq_dist.get(str(pos), {}).get(d, 1.0) / 10.0
                # Markov transition component
                m_score = markov_pos.get(pos, {}).get(d, 0.1)
                # ARIMA component
                a_score = arima_preds.get(str(pos), {}).get(d, 0.1)

                val = (
                    (f_score * w_freq)
                    + (m_score * w_markov)
                    + (a_score * (w_arima + w_prophet + w_lstm))
                )
                pos_p[d] = max(0.001, val)

            # Normalize to sum to 1
            tot = sum(pos_p.values()) or 1.0
            combined_probs[pos] = {d: v / tot for d, v in pos_p.items()}

        return combined_probs

    def predict_prize(
        self, prize_type: str, top_n: int = 10
    ) -> dict[str, Any]:
        """
        Generate predictions using Two-Stage Monte Carlo Stacking.
        """
        # Stage 1: Gather top predictions from individual sub-models
        sub_preds = {
            "feature_pattern": self.feature_pattern_model.predict_prize(prize_type, top_n=top_n),
            "frequency": self.frequency_model.predict().get(prize_type, {}).get("top10", []),
            "markov": self.markov_model.predict().get(prize_type, {}).get("top10", []),
            "arima": self.arima_model.predict().get(prize_type, {}).get("top10", []),
            "prophet": self.prophet_model.predict().get(prize_type, {}).get("top10", []),
            "lstm": self.lstm_model.predict().get(prize_type, {}).get("top10", []),
        }

        radar_profile = self.feature_pattern_model.get_radar_profile(prize_type)

        # Stage 2: Combine probability distributions & run Monte Carlo Simulation (50,000 draws)
        combined_pos_probs = self._build_combined_pos_probs(prize_type)
        mc_result = self.monte_carlo_engine.simulate_prize(prize_type, combined_pos_probs, top_n=top_n)
        sub_preds["monte_carlo"] = mc_result.get("top10", [])

        # Blend candidate scores from both simulation and direct voting
        combined_scores: dict[str, float] = defaultdict(float)
        model_support: dict[str, list[str]] = defaultdict(list)

        # 1. Weights from Stage 1 direct model rankings
        for model_name, preds in sub_preds.items():
            w = self.weights.get(model_name, 0.15)
            for item in preds:
                num = item["number"]
                score = float(item["score"])
                combined_scores[num] += score * w
                if model_name not in model_support[num]:
                    model_support[num].append(model_name)

        # 2. Boost from Monte Carlo simulation frequency
        for item in mc_result.get("top10", []):
            num = item["number"]
            score = float(item["score"])
            w_mc = self.weights.get("monte_carlo", 0.15)
            combined_scores[num] += score * w_mc * 1.5

        # Sort and normalize top candidates
        sorted_combined = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_combined[0][1] if sorted_combined else 1.0

        num_len = PRIZE_LENGTHS.get(prize_type, 2)
        def _get_feature_breakdown(num_str: str) -> dict[str, Any]:
            digits = [int(c) for c in num_str if c.isdigit()]
            if not digits:
                return {}
            d_sum = sum(digits)
            ev_cnt = sum(1 for d in digits if d % 2 == 0)
            hi_cnt = sum(1 for d in digits if d >= 5)
            u_cnt = len(set(digits))
            span = max(digits) - min(digits)
            return {
                "digit_sum": d_sum,
                "even_odd": f"{ev_cnt}:{num_len - ev_cnt}",
                "high_low": f"{hi_cnt}:{num_len - hi_cnt}",
                "unique_digits": u_cnt,
                "span": span,
                "pattern_label": f"แต้ม {d_sum} | คู่:คี่ {ev_cnt}:{num_len - ev_cnt} | ห่าง {span}",
            }

        ensemble_top = [
            {
                "number": num,
                "score": round(score / max_score, 4),
                "model_votes": model_support.get(num, ["monte_carlo"]),
                "feature_breakdown": _get_feature_breakdown(num),
            }
            for num, score in sorted_combined[:top_n]
        ]

        # Format individual model outputs
        models_output = {}
        for m_name, preds in sub_preds.items():
            models_output[m_name] = {
                "top10": preds[:top_n],
                "weight": self.weights.get(m_name, 0.15),
            }

        return {
            "models": models_output,
            "ensemble": {
                "top10": ensemble_top,
                "weights": self.weights,
                "positional_breakdown": mc_result.get("positional_breakdown", []),
                "digit_sum_analysis": mc_result.get("digit_sum_analysis", {}),
                "radar_profile": radar_profile,
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
