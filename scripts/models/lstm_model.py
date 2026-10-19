"""
models/lstm_model.py — LSTM Deep Learning Model
โมเดล LSTM สำหรับการตรวจจับลำดับตัวเลข (Sequential Pattern Recognition)
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

import numpy as np

logger = logging.getLogger("models.lstm")

try:
    import tensorflow as tf
    from tensorflow.keras.layers import Dense, Dropout, LSTM
    from tensorflow.keras.models import Sequential
    HAS_TF = True
    # Suppress verbose TensorFlow warnings
    tf.get_logger().setLevel(logging.ERROR)
except ImportError:
    HAS_TF = False
    logger.warning("TensorFlow not available — LSTM model will use statistical fallback")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}

SEQUENCE_LENGTH = 24  # Lookback window (last 24 draws)


class LSTMModel:
    """
    LSTM-based sequential pattern model.
    ใช้โครงข่ายประสาทเทียมแบบ LSTM 2 ชั้น เพื่อทำนายการแจกแจงความน่าจะเป็นของตัวเลข
    """

    MODEL_NAME = "lstm"

    def __init__(self) -> None:
        self._predictions: dict[str, dict[str, dict[str, float]]] = {}
        self._trained = False

    def train(self, records: list[dict[str, Any]]) -> None:
        """
        Train LSTM models for each prize type and digit position.
        เทรนโมเดล LSTM จากข้อมูลลำดับงวดย้อนหลัง
        """
        logger.info("Training LSTMModel on %d records…", len(records))
        self._predictions = {}

        if not records:
            logger.warning("No records to train LSTM")
            return

        for prize_type, num_len in PRIZE_LENGTHS.items():
            self._predictions[prize_type] = {}
            for pos in range(num_len):
                dist = self._train_and_predict_position(records, prize_type, pos)
                self._predictions[prize_type][str(pos)] = dist

        self._trained = True
        logger.info("LSTMModel training complete.")

    def _train_and_predict_position(
        self, records: list[dict[str, Any]], prize_type: str, pos: int
    ) -> dict[str, float]:
        """
        Build sequential data for a single digit position and predict next draw.
        """
        num_len = PRIZE_LENGTHS[prize_type]
        series: list[int] = []

        # Chronological order (oldest to newest)
        for rec in reversed(records):
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            if nums:
                n_str = str(nums[0]).zfill(num_len)[-num_len:]
                series.append(int(n_str[pos]))

        if len(series) < SEQUENCE_LENGTH + 5 or not HAS_TF:
            # Fallback to empirical frequency if insufficient data or no TF
            return self._fallback_distribution(series)

        try:
            # One-hot encode sequence
            X, y = [], []
            for i in range(len(series) - SEQUENCE_LENGTH):
                seq = series[i : i + SEQUENCE_LENGTH]
                target = series[i + SEQUENCE_LENGTH]
                X.append(seq)
                y.append(target)

            X_arr = np.zeros((len(X), SEQUENCE_LENGTH, 10), dtype=np.float32)
            y_arr = np.zeros((len(y), 10), dtype=np.float32)

            for i, seq in enumerate(X):
                for t, digit in enumerate(seq):
                    X_arr[i, t, digit] = 1.0
                y_arr[i, y[i]] = 1.0

            # Build small efficient LSTM
            model = Sequential([
                LSTM(32, input_shape=(SEQUENCE_LENGTH, 10), return_sequences=False),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(10, activation='softmax')
            ])

            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            # Quick training with early stopping
            model.fit(
                X_arr,
                y_arr,
                epochs=15,
                batch_size=16,
                verbose=0,
                shuffle=False
            )

            # Predict next step using latest window
            latest_seq = series[-SEQUENCE_LENGTH:]
            next_X = np.zeros((1, SEQUENCE_LENGTH, 10), dtype=np.float32)
            for t, digit in enumerate(latest_seq):
                next_X[0, t, digit] = 1.0

            preds = model.predict(next_X, verbose=0)[0]
            # Normalize and return
            total = float(np.sum(preds))
            return {str(d): float(preds[d] / total) for d in range(10)}

        except Exception as e:
            logger.debug("LSTM training error for %s pos %d: %s", prize_type, pos, e)
            return self._fallback_distribution(series)

    def _fallback_distribution(self, series: list[int]) -> dict[str, float]:
        """Empirical frequency fallback with Laplace smoothing."""
        counts = {str(d): 1.0 for d in range(10)}
        for d in series[-50:]:  # recent 50 draws
            if 0 <= d <= 9:
                counts[str(d)] += 1.0
        total = sum(counts.values())
        return {k: round(v / total, 4) for k, v in counts.items()}

    def predict_prize(
        self, prize_type: str, top_n: int = 10
    ) -> list[dict[str, Any]]:
        """Predict top candidate numbers with probability scores for a prize type."""
        if not self._trained:
            logger.warning("Model not trained yet.")
            return []

        pos_dist = self._predictions.get(prize_type, {})
        num_len = PRIZE_LENGTHS[prize_type]

        if prize_type == "last_two":
            candidates: list[tuple[str, float]] = []
            for d0 in range(10):
                for d1 in range(10):
                    s0 = pos_dist.get("0", {}).get(str(d0), 0.1)
                    s1 = pos_dist.get("1", {}).get(str(d1), 0.1)
                    score = s0 * s1
                    candidates.append((f"{d0}{d1}", score))
            candidates.sort(key=lambda x: x[1], reverse=True)
            max_s = candidates[0][1] if candidates else 1.0
            return [
                {"number": num, "score": round(sc / max_s, 4)}
                for num, sc in candidates[:top_n]
            ]

        results = []
        for rank in range(top_n):
            digits = []
            score_prod = 1.0
            for pos in range(num_len):
                d_scores = pos_dist.get(str(pos), {str(d): 0.1 for d in range(10)})
                sorted_digits = sorted(d_scores.items(), key=lambda x: x[1], reverse=True)
                pick_idx = min(rank % 3, len(sorted_digits) - 1)
                chosen_digit, sc = sorted_digits[pick_idx]
                digits.append(chosen_digit)
                score_prod *= sc
            num_str = "".join(digits)
            results.append({"number": num_str, "score": round(score_prod ** (1.0 / num_len), 4)})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def predict(self) -> dict[str, Any]:
        """Return top-10 predictions for each prize type."""
        result: dict[str, Any] = {}
        for pt in PRIZE_LENGTHS:
            result[pt] = {
                "top10": self.predict_prize(pt, top_n=10),
                "model": self.MODEL_NAME,
            }
        return result

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """Return top-10 predicted numbers for backtesting."""
        return [x["number"] for x in self.predict_prize(prize_type, top_n=10)]
