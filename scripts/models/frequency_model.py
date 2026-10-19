"""
models/frequency_model.py — Statistical Frequency Model
โมเดลความถี่ทางสถิติ: คำนวณความน่าจะเป็นจากความถี่ในอดีต

Score = observed_frequency / expected_frequency
  1.0 = exactly average
  >1.0 = above average (hot)
  <1.0 = below average (cold)
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

logger = logging.getLogger("models.frequency")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}


class FrequencyModel:
    """
    Frequency-based probability model.
    คำนวณ score จากความถี่สัมพัทธ์ของแต่ละตำแหน่งหลัก
    """

    MODEL_NAME = "frequency"

    def __init__(self) -> None:
        self._distributions: dict[str, dict[str, dict[str, float]]] = {}
        self._trained = False

    def train(self, records: list[dict[str, Any]]) -> None:
        """
        Fit model on historical draw records.
        เทรนโมเดลด้วยข้อมูลย้อนหลัง
        """
        logger.info("Training FrequencyModel on %d records…", len(records))
        self._distributions = {}

        for prize_type, num_len in PRIZE_LENGTHS.items():
            pos_counters: dict[str, Counter] = {str(i): Counter() for i in range(num_len)}

            for rec in records:
                val = rec.get(prize_type)
                nums = val if isinstance(val, list) else [val] if val else []
                for num in nums:
                    num_str = str(num).zfill(num_len)[-num_len:]
                    for pos, digit in enumerate(num_str):
                        pos_counters[str(pos)][digit] += 1

            # Convert to relative frequency (score vs uniform expectation)
            pos_scores: dict[str, dict[str, float]] = {}
            for pos, counter in pos_counters.items():
                total = sum(counter.values()) or 1
                expected = total / 10.0  # uniform over digits 0-9
                pos_scores[pos] = {
                    d: counter.get(d, 0) / expected
                    for d in [str(i) for i in range(10)]
                }

            self._distributions[prize_type] = pos_scores

        self._trained = True
        logger.info("FrequencyModel training complete")

    def _score_number(self, number: str, prize_type: str) -> float:
        """Compute the average positional score for a number string."""
        dist = self._distributions.get(prize_type, {})
        if not dist:
            return 1.0
        scores = []
        num_len = PRIZE_LENGTHS[prize_type]
        number = str(number).zfill(num_len)[-num_len:]
        for pos, digit in enumerate(number):
            pos_dist = dist.get(str(pos), {})
            scores.append(pos_dist.get(digit, 1.0))
        return sum(scores) / len(scores) if scores else 1.0

    def _generate_candidates(self, prize_type: str) -> list[tuple[str, float]]:
        """
        Generate top-N candidate numbers by enumerating all possible values
        and scoring them using positional frequencies.
        """
        num_len = PRIZE_LENGTHS[prize_type]
        dist = self._distributions.get(prize_type, {})

        # For 6-digit numbers, exhaustive is 1M — use greedy assembly instead
        if num_len == 6:
            # Greedy: pick the top 3 digits per position, then permute
            top_digits_per_pos: list[list[str]] = []
            for pos in range(num_len):
                pd = dist.get(str(pos), {})
                sorted_digits = sorted(pd.keys(), key=lambda d: pd.get(d, 0), reverse=True)
                top_digits_per_pos.append(sorted_digits[:3])

            candidates: dict[str, float] = {}
            # Sample combinations
            from itertools import product
            for combo in product(*top_digits_per_pos):
                num = "".join(combo)
                candidates[num] = self._score_number(num, prize_type)
            return sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:10]
        else:
            # Full enumeration for 2-3 digit numbers
            max_val = 10 ** num_len
            all_scored: list[tuple[str, float]] = []
            for i in range(max_val):
                num = str(i).zfill(num_len)
                score = self._score_number(num, prize_type)
                all_scored.append((num, score))
            all_scored.sort(key=lambda x: x[1], reverse=True)
            return all_scored[:10]

    def predict(self) -> dict[str, Any]:
        """
        Generate top-10 predictions for each prize type.
        คืนค่า predictions สำหรับแต่ละ prize type
        """
        if not self._trained:
            raise RuntimeError("Model has not been trained. Call train() first.")

        result: dict[str, Any] = {}
        for prize_type in PRIZE_LENGTHS:
            candidates = self._generate_candidates(prize_type)
            result[prize_type] = {
                "top10": [
                    {"number": num, "score": round(score, 4)}
                    for num, score in candidates[:10]
                ],
                "model": self.MODEL_NAME,
            }

        return result

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """Return top-10 predicted numbers for a single prize type (for backtesting)."""
        if not self._trained:
            return []
        candidates = self._generate_candidates(prize_type)
        return [num for num, _ in candidates[:10]]
