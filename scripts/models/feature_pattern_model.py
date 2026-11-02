"""
models/feature_pattern_model.py — Quantitative Feature Pattern & Vectorized Exhaustive Engine
โมเดลวิเคราะห์โครงสร้างกลุ่มตัวเลขเชิงปริมาณ 5 มิติ:
1. ผลรวมแต้ม (Digit Sum) — วิเคราะห์ตาม Gaussian Distribution (μ, σ)
2. สัดส่วน คู่/คี่ (Even/Odd Ratio) — วิเคราะห์ตาม Binomial Distribution
3. การกระจาย สูง/ต่ำ (High/Low Distribution) — สัดส่วน 0-4 vs 5-9
4. รูปแบบเลขซ้ำ/เบิ้ล (Multiplicity Pattern) — ความน่าจะเป็นของจำนวนตัวเลขที่ไม่ซ้ำ
5. ระยะกระจายของตัวเลข (Digit Span) — ค่าสูงสุดลบค่าต่ำสุด (Max - Min)

ประมวลผลด้วย NumPy Vectorized Exhaustive Matrix สำหรับตัวเลข 1,000,000 ชุด (รางวัลที่ 1)
และตัวเลข 100 ชุด (เลขท้าย 2 ตัว) ในระดับเสี้ยววินาทีโดยปราศจากการสุ่มเดา
"""

from __future__ import annotations

import logging
from typing import Any
import numpy as np

logger = logging.getLogger("models.feature_pattern")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}

# Bitcount lookup table for 10-bit integers (0 to 1023)
_POPCOUNT_TABLE = np.array([bin(x).count("1") for x in range(1024)], dtype=np.int8)


class FeaturePatternModel:
    """
    Quantitative Feature Pattern Model using Joint Likelihood Scoring.
    """

    MODEL_NAME = "feature_pattern"

    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, Any]] = {}
        self._top_predictions: dict[str, list[dict[str, Any]]] = {}
        self._radar_profiles: dict[str, dict[str, Any]] = {}
        self._trained = False

    def train(self, records: list[dict[str, Any]]) -> None:
        """
        Learn the empirical distribution parameters for each prize type
        from historical records (700+ draws).
        """
        logger.info("Training FeaturePatternModel on %d records…", len(records))
        if not records:
            self._trained = True
            return

        for ptype, length in PRIZE_LENGTHS.items():
            self._profiles[ptype] = self._learn_distribution(records, ptype, length)

        self._trained = True
        logger.info("FeaturePatternModel distribution learning complete.")

    def _learn_distribution(self, records: list[dict[str, Any]], ptype: str, length: int) -> dict[str, Any]:
        """
        Calculate empirical means, variances, and frequency tables for 5 features.
        """
        all_numbers: list[str] = []
        for r in records:
            val = r.get(ptype)
            if not val:
                continue
            if isinstance(val, list):
                for v in val:
                    s = str(v).zfill(length)[-length:]
                    if s.isdigit():
                        all_numbers.append(s)
            else:
                s = str(val).zfill(length)[-length:]
                if s.isdigit():
                    all_numbers.append(s)

        if not all_numbers:
            # Defaults if no data
            return {
                "mu_sum": length * 4.5,
                "sigma_sum": np.sqrt(length * 8.25),
                "p_even": np.ones(length + 1) / (length + 1),
                "p_high": np.ones(length + 1) / (length + 1),
                "p_unique": np.ones(length + 1) / (length + 1),
                "p_span": np.ones(10) / 10.0,
                "pos_freq": np.ones((length, 10)) / 10.0,
            }

        # Digits array: shape (N, length)
        digits = np.array([[int(c) for c in num] for num in all_numbers], dtype=np.int8)
        N = len(digits)

        # 1. Digit Sum
        d_sums = digits.sum(axis=1)
        mu_sum = float(np.mean(d_sums))
        sigma_sum = float(np.std(d_sums)) if np.std(d_sums) > 0 else 1.0

        # 2. Even count (0 to length)
        evens = (digits % 2 == 0).sum(axis=1)
        p_even = np.zeros(length + 1, dtype=np.float64)
        for k in range(length + 1):
            p_even[k] = (evens == k).sum() + 1.0  # Laplace smoothing
        p_even /= p_even.sum()

        # 3. High count (0 to length)
        highs = (digits >= 5).sum(axis=1)
        p_high = np.zeros(length + 1, dtype=np.float64)
        for k in range(length + 1):
            p_high[k] = (highs == k).sum() + 1.0
        p_high /= p_high.sum()

        # 4. Unique digits (1 to length)
        p_unique = np.zeros(length + 1, dtype=np.float64)
        for row in digits:
            u = len(set(row))
            p_unique[u] += 1.0
        p_unique += 0.5  # smoothing
        p_unique /= p_unique.sum()

        # 5. Span (max - min: 0 to 9)
        spans = digits.max(axis=1) - digits.min(axis=1)
        p_span = np.zeros(10, dtype=np.float64)
        for s in range(10):
            p_span[s] = (spans == s).sum() + 1.0
        p_span /= p_span.sum()

        # Positional Frequency: length x 10
        pos_freq = np.zeros((length, 10), dtype=np.float64)
        for pos in range(length):
            for d in range(10):
                pos_freq[pos, d] = (digits[:, pos] == d).sum() + 1.0
            pos_freq[pos] /= pos_freq[pos].sum()

        return {
            "mu_sum": mu_sum,
            "sigma_sum": sigma_sum,
            "p_even": p_even,
            "p_high": p_high,
            "p_unique": p_unique,
            "p_span": p_span,
            "pos_freq": pos_freq,
        }

    def predict_prize(self, prize_type: str, top_n: int = 10) -> list[dict[str, Any]]:
        """
        Generate top predictions using Vectorized Joint Likelihood Scoring.
        """
        length = PRIZE_LENGTHS.get(prize_type, 2)
        profile = self._profiles.get(prize_type)
        if not profile:
            profile = self._learn_distribution([], prize_type, length)

        mu_sum = profile["mu_sum"]
        sigma_sum = profile["sigma_sum"]
        p_even = profile["p_even"]
        p_high = profile["p_high"]
        p_unique = profile["p_unique"]
        p_span = profile["p_span"]
        pos_freq = profile["pos_freq"]

        if length == 6:
            # 1,000,000 numbers vectorized
            nums = np.arange(1000000, dtype=np.int32)
            d0 = nums // 100000
            d1 = (nums // 10000) % 10
            d2 = (nums // 1000) % 10
            d3 = (nums // 100) % 10
            d4 = (nums // 10) % 10
            d5 = nums % 10

            d_sum = d0 + d1 + d2 + d3 + d4 + d5
            l_sum = np.exp(-0.5 * ((d_sum - mu_sum) / sigma_sum) ** 2)

            even_cnt = (d0 % 2 == 0).astype(np.int8) + (d1 % 2 == 0) + (d2 % 2 == 0) + (d3 % 2 == 0) + (d4 % 2 == 0) + (d5 % 2 == 0)
            l_even = p_even[even_cnt]

            high_cnt = (d0 >= 5).astype(np.int8) + (d1 >= 5) + (d2 >= 5) + (d3 >= 5) + (d4 >= 5) + (d5 >= 5)
            l_high = p_high[high_cnt]

            max_d = np.maximum.reduce([d0, d1, d2, d3, d4, d5])
            min_d = np.minimum.reduce([d0, d1, d2, d3, d4, d5])
            span = max_d - min_d
            l_span = p_span[span]

            mask = (1 << d0) | (1 << d1) | (1 << d2) | (1 << d3) | (1 << d4) | (1 << d5)
            uniq = _POPCOUNT_TABLE[mask]
            l_uniq = p_unique[uniq]

            # Positional likelihood
            l_pos = (
                pos_freq[0, d0]
                * pos_freq[1, d1]
                * pos_freq[2, d2]
                * pos_freq[3, d3]
                * pos_freq[4, d4]
                * pos_freq[5, d5]
            )

            # Combined Joint Score
            joint_scores = l_sum * l_even * l_high * l_span * l_uniq * (l_pos ** 0.5)

            # Top N indices
            top_indices = np.argpartition(joint_scores, -top_n)[-top_n:]
            top_indices = top_indices[np.argsort(joint_scores[top_indices])[::-1]]

            max_score = joint_scores[top_indices[0]] if len(top_indices) > 0 and joint_scores[top_indices[0]] > 0 else 1.0

            results = []
            for idx in top_indices:
                num_str = f"{idx:06d}"
                raw_score = float(joint_scores[idx])
                score = round(raw_score / max_score, 4)
                breakdown = {
                    "digit_sum": int(d_sum[idx]),
                    "even_odd": f"{int(even_cnt[idx])}:{6 - int(even_cnt[idx])}",
                    "high_low": f"{int(high_cnt[idx])}:{6 - int(high_cnt[idx])}",
                    "unique_digits": int(uniq[idx]),
                    "span": int(span[idx]),
                    "pattern_label": f"แต้ม {int(d_sum[idx])} | คู่:คี่ {int(even_cnt[idx])}:{6 - int(even_cnt[idx])} | ห่าง {int(span[idx])}",
                }
                results.append({"number": num_str, "score": score, "feature_breakdown": breakdown})

        elif length == 2:
            nums = np.arange(100, dtype=np.int16)
            d0 = nums // 10
            d1 = nums % 10

            d_sum = d0 + d1
            l_sum = np.exp(-0.5 * ((d_sum - mu_sum) / sigma_sum) ** 2)

            even_cnt = (d0 % 2 == 0).astype(np.int8) + (d1 % 2 == 0)
            l_even = p_even[even_cnt]

            high_cnt = (d0 >= 5).astype(np.int8) + (d1 >= 5)
            l_high = p_high[high_cnt]

            span = np.abs(d0 - d1)
            l_span = p_span[span]

            uniq = np.where(d0 == d1, 1, 2)
            l_uniq = p_unique[uniq]

            l_pos = pos_freq[0, d0] * pos_freq[1, d1]
            joint_scores = l_sum * l_even * l_high * l_span * l_uniq * (l_pos ** 0.5)

            top_indices = np.argsort(joint_scores)[::-1][:top_n]
            max_score = joint_scores[top_indices[0]] if len(top_indices) > 0 and joint_scores[top_indices[0]] > 0 else 1.0

            results = []
            for idx in top_indices:
                num_str = f"{idx:02d}"
                raw_score = float(joint_scores[idx])
                score = round(raw_score / max_score, 4)
                breakdown = {
                    "digit_sum": int(d_sum[idx]),
                    "even_odd": f"{int(even_cnt[idx])}:{2 - int(even_cnt[idx])}",
                    "high_low": f"{int(high_cnt[idx])}:{2 - int(high_cnt[idx])}",
                    "unique_digits": int(uniq[idx]),
                    "span": int(span[idx]),
                    "pattern_label": f"แต้ม {int(d_sum[idx])} | คู่:คี่ {int(even_cnt[idx])}:{2 - int(even_cnt[idx])} | ห่าง {int(span[idx])}",
                }
                results.append({"number": num_str, "score": score, "feature_breakdown": breakdown})

        else:
            # 3 digits (1000 combinations)
            nums = np.arange(1000, dtype=np.int16)
            d0 = nums // 100
            d1 = (nums // 10) % 10
            d2 = nums % 10

            d_sum = d0 + d1 + d2
            l_sum = np.exp(-0.5 * ((d_sum - mu_sum) / sigma_sum) ** 2)

            even_cnt = (d0 % 2 == 0).astype(np.int8) + (d1 % 2 == 0) + (d2 % 2 == 0)
            l_even = p_even[even_cnt]

            high_cnt = (d0 >= 5).astype(np.int8) + (d1 >= 5) + (d2 >= 5)
            l_high = p_high[high_cnt]

            max_d = np.maximum.reduce([d0, d1, d2])
            min_d = np.minimum.reduce([d0, d1, d2])
            span = max_d - min_d
            l_span = p_span[span]

            mask = (1 << d0) | (1 << d1) | (1 << d2)
            uniq = _POPCOUNT_TABLE[mask]
            l_uniq = p_unique[uniq]

            l_pos = pos_freq[0, d0] * pos_freq[1, d1] * pos_freq[2, d2]
            joint_scores = l_sum * l_even * l_high * l_span * l_uniq * (l_pos ** 0.5)

            top_indices = np.argsort(joint_scores)[::-1][:top_n]
            max_score = joint_scores[top_indices[0]] if len(top_indices) > 0 and joint_scores[top_indices[0]] > 0 else 1.0

            results = []
            for idx in top_indices:
                num_str = f"{idx:03d}"
                raw_score = float(joint_scores[idx])
                score = round(raw_score / max_score, 4)
                breakdown = {
                    "digit_sum": int(d_sum[idx]),
                    "even_odd": f"{int(even_cnt[idx])}:{3 - int(even_cnt[idx])}",
                    "high_low": f"{int(high_cnt[idx])}:{3 - int(high_cnt[idx])}",
                    "unique_digits": int(uniq[idx]),
                    "span": int(span[idx]),
                    "pattern_label": f"แต้ม {int(d_sum[idx])} | คู่:คี่ {int(even_cnt[idx])}:{3 - int(even_cnt[idx])} | ห่าง {int(span[idx])}",
                }
                results.append({"number": num_str, "score": score, "feature_breakdown": breakdown})

        self._top_predictions[prize_type] = results
        self._radar_profiles[prize_type] = self._build_radar_profile(results, profile, length)
        return results

    def _build_radar_profile(self, top_results: list[dict[str, Any]], profile: dict[str, Any], length: int) -> dict[str, Any]:
        """
        Build a normalized 5-dimension radar profile comparing Top 1 vs 30-year ideal.
        """
        if not top_results:
            return {
                "dimensions": ["ผลรวมแต้ม", "สัดส่วนคู่-คี่", "สัดส่วนสูง-ต่ำ", "ความหลากหลาย", "ระยะกระจาย"],
                "ideal": [100, 100, 100, 100, 100],
                "top_predicted": [90, 90, 90, 90, 90],
            }

        top1 = top_results[0]
        fb = top1.get("feature_breakdown", {})
        d_sum = fb.get("digit_sum", length * 4.5)
        mu_sum = profile["mu_sum"]
        sigma_sum = profile["sigma_sum"]

        # 1. Sum Match: 100 - (|sum - mu| / (2*sigma)) * 50
        sum_score = max(20, min(100, int(100 - (abs(d_sum - mu_sum) / (2 * sigma_sum)) * 50)))

        # 2. Even/Odd Match
        even_parts = [int(x) for x in fb.get("even_odd", "1:1").split(":")]
        ev_cnt = even_parts[0] if even_parts else length // 2
        p_ev = profile["p_even"][ev_cnt] if ev_cnt < len(profile["p_even"]) else 0.5
        even_score = max(30, min(100, int((p_ev / profile["p_even"].max()) * 100)))

        # 3. High/Low Match
        hl_parts = [int(x) for x in fb.get("high_low", "1:1").split(":")]
        hi_cnt = hl_parts[0] if hl_parts else length // 2
        p_hi = profile["p_high"][hi_cnt] if hi_cnt < len(profile["p_high"]) else 0.5
        high_score = max(30, min(100, int((p_hi / profile["p_high"].max()) * 100)))

        # 4. Unique Match
        u_cnt = fb.get("unique_digits", length)
        p_u = profile["p_unique"][u_cnt] if u_cnt < len(profile["p_unique"]) else 0.5
        uniq_score = max(30, min(100, int((p_u / profile["p_unique"].max()) * 100)))

        # 5. Span Match
        sp_cnt = fb.get("span", 5)
        p_sp = profile["p_span"][sp_cnt] if sp_cnt < len(profile["p_span"]) else 0.5
        span_score = max(30, min(100, int((p_sp / profile["p_span"].max()) * 100)))

        return {
            "dimensions": [
                {"name": "ผลรวมแต้ม (Sum)", "max": 100},
                {"name": "คู่/คี่ (Even/Odd)", "max": 100},
                {"name": "สูง/ต่ำ (High/Low)", "max": 100},
                {"name": "ความหลากหลาย (Unique)", "max": 100},
                {"name": "ระยะกระจาย (Span)", "max": 100},
            ],
            "ideal": [100, 100, 100, 100, 100],
            "top_predicted": [sum_score, even_score, high_score, uniq_score, span_score],
            "top_number": top1.get("number", "------"),
        }

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """
        Standalone prediction for backtesting, returning top 10 predicted numbers.
        """
        preds = self.predict_prize(prize_type, top_n=10)
        return [p["number"] for p in preds]

    def get_radar_profile(self, prize_type: str) -> dict[str, Any]:
        """Get radar profile for the specified prize type."""
        return self._radar_profiles.get(prize_type, {})
