"""
models/monte_carlo.py — Monte Carlo Simulation & Stacking Engine
เครื่องยนต์จำลองมอนเตการ์โล 50,000 รอบ:
- สุ่มตัวอย่างจาก Probability Density Function (PDF) รวมของทุกโมเดล
- สังเคราะห์ตัวเลข Top 10
- วิเคราะห์ความน่าจะเป็นของเลขเด่นแยกรายหลัก 6 หลัก (Positional Breakdown)
- วิเคราะห์การแจกแจงผลรวมแต้ม (Digit Sum Distribution)
"""

from __future__ import annotations

import logging
import random
from collections import Counter
from typing import Any

logger = logging.getLogger("models.monte_carlo")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}

POSITION_NAMES_6 = ["หลักแสน", "หลักหมื่น", "หลักพัน", "หลักร้อย", "หลักสิบ", "หลักหน่วย"]


class MonteCarloEngine:
    """
    Monte Carlo Simulation Engine for Two-Stage Ensemble Stacking.
    จำลองการออกรางวัล 50,000 ครั้งเพื่อสังเคราะห์ผลรวมความน่าจะเป็น
    """

    MODEL_NAME = "monte_carlo"

    def __init__(self, simulations: int = 50000) -> None:
        self.simulations = simulations
        self._trained = False
        self._records: list[dict[str, Any]] = []

    def train(self, records: list[dict[str, Any]]) -> None:
        """Cache records for simulation baseline."""
        self._records = records
        self._trained = True

    def simulate_prize(
        self,
        prize_type: str,
        combined_pos_probs: dict[int, dict[str, float]],
        top_n: int = 10,
    ) -> dict[str, Any]:
        """
        Run Monte Carlo simulation for a given prize type.
        Returns Top N candidates, positional breakdown, and digit sum analysis.
        """
        num_len = PRIZE_LENGTHS.get(prize_type, 2)
        digits = [str(d) for d in range(10)]

        # Precompute cumulative probabilities for fast inverse transform sampling
        cumulative_per_pos: list[list[tuple[float, str]]] = []
        for pos in range(num_len):
            probs = combined_pos_probs.get(pos, {d: 0.1 for d in digits})
            total = sum(probs.values()) or 1.0
            cum = 0.0
            pos_cum = []
            for d in digits:
                cum += probs.get(d, 0.1) / total
                pos_cum.append((cum, d))
            cumulative_per_pos.append(pos_cum)

        # Monte Carlo Simulation Loop
        sim_counts: Counter[str] = Counter()
        sum_counts: Counter[int] = Counter()
        pos_digit_counts: list[Counter[str]] = [Counter() for _ in range(num_len)]

        rng = random.Random(42)  # Deterministic seed for reproducible results

        for _ in range(self.simulations):
            drawn_digits = []
            digit_sum = 0
            for pos in range(num_len):
                r = rng.random()
                chosen = "0"
                for threshold, d in cumulative_per_pos[pos]:
                    if r <= threshold:
                        chosen = d
                        break
                drawn_digits.append(chosen)
                digit_sum += int(chosen)
                pos_digit_counts[pos][chosen] += 1

            num_str = "".join(drawn_digits)
            sim_counts[num_str] += 1
            sum_counts[digit_sum] += 1

        # Select Top N
        most_common = sim_counts.most_common(top_n)
        max_freq = most_common[0][1] if most_common else 1

        top_candidates = [
            {
                "number": num,
                "score": round(count / max_freq, 4),
                "sim_hits": count,
                "percentage": round((count / self.simulations) * 100, 2),
            }
            for num, count in most_common
        ]

        # Positional Breakdown (top 3 digits per position)
        positional_breakdown = []
        for pos in range(num_len):
            total_pos = sum(pos_digit_counts[pos].values()) or 1
            pos_name = POSITION_NAMES_6[pos] if num_len == 6 else f"หลักที่ {pos + 1}"
            top_digits = [
                {
                    "digit": d,
                    "probability": round((c / total_pos) * 100, 1),
                }
                for d, c in pos_digit_counts[pos].most_common(3)
            ]
            positional_breakdown.append({
                "position_index": pos,
                "position_name": pos_name,
                "top_digits": top_digits,
            })

        # Digit Sum Statistics
        total_sums = sum(sum_counts.values()) or 1
        avg_sum = round(sum(s * c for s, c in sum_counts.items()) / total_sums, 1)

        return {
            "top10": top_candidates,
            "positional_breakdown": positional_breakdown,
            "digit_sum_analysis": {
                "average_sum": avg_sum,
                "expected_range": f"{int(avg_sum - 7)} - {int(avg_sum + 7)}",
            },
        }

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """
        Standalone simulation predict for backtest using empirical historical frequencies.
        """
        num_len = PRIZE_LENGTHS.get(prize_type, 2)
        pos_counts: dict[int, Counter[str]] = {p: Counter() for p in range(num_len)}
        for rec in self._records:
            val = rec.get(prize_type)
            num = str(val[0] if isinstance(val, list) else val).zfill(num_len)[-num_len:]
            for pos, d in enumerate(num):
                pos_counts[pos][d] += 1

        pos_probs = {}
        for pos in range(num_len):
            tot = sum(pos_counts[pos].values()) or 1
            pos_probs[pos] = {str(d): pos_counts[pos][str(d)] / tot for d in range(10)}

        res = self.simulate_prize(prize_type, pos_probs, top_n=10)
        return [c["number"] for c in res["top10"]]
