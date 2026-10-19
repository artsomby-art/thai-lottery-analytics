"""
models/markov_model.py — Hybrid Multiscale Markov Chain Model
โมเดลลูกโซ่มาร์คอฟแบบหลายมิติ: คำนวณความน่าจะเป็นการเปลี่ยนสถานะจากงวดก่อนหน้าสู่งวดถัดไป
- 100-State Transition Matrix (00-99) สำหรับเลขท้าย 2 ตัว
- Positional Transition Matrices (0-9) แยกอิสระแต่ละหลักสำหรับเลข 3 ตัว และรางวัลที่ 1
"""

from __future__ import annotations

import logging
from collections import defaultdict
from itertools import product
from typing import Any

logger = logging.getLogger("models.markov")

PRIZE_LENGTHS = {
    "first_prize": 6,
    "front_three": 3,
    "back_three": 3,
    "last_two": 2,
}


class MarkovChainModel:
    """
    Markov Chain transition probability model with Laplace smoothing.
    โมเดล Markov Chain คำนวณความน่าจะเป็นในการเปลี่ยนสถานะ (State Transitions)
    """

    MODEL_NAME = "markov"

    def __init__(self) -> None:
        # 100-state transition matrix for 2-digit numbers: 100x100
        self._matrix_100: list[list[float]] = [[0.01 for _ in range(100)] for _ in range(100)]
        # Positional transition matrices: prize_type -> position -> 10x10
        self._positional_matrices: dict[str, dict[int, list[list[float]]]] = {}
        self._last_draw: dict[str, Any] = {}
        self._trained = False

    def train(self, records: list[dict[str, Any]]) -> None:
        """
        Train Markov transition matrices from chronological historical records.
        Records are assumed to be sorted latest-first or oldest-first;
        we ensure oldest-first for sequential transition learning.
        """
        logger.info("Training MarkovChainModel on %d records…", len(records))
        if not records or len(records) < 2:
            self._trained = True
            return

        # Ensure oldest-to-newest order for sequential state transitions
        sorted_records = sorted(records, key=lambda x: x.get("date", ""))
        self._last_draw = sorted_records[-1]

        # 1. Train 100-State Matrix for last_two
        counts_100 = [[0 for _ in range(100)] for _ in range(100)]
        for i in range(len(sorted_records) - 1):
            s_curr = int(str(sorted_records[i].get("last_two", "00"))[-2:].zfill(2))
            s_next = int(str(sorted_records[i + 1].get("last_two", "00"))[-2:].zfill(2))
            if 0 <= s_curr < 100 and 0 <= s_next < 100:
                counts_100[s_curr][s_next] += 1

        # Laplace smoothing (alpha = 1.0)
        self._matrix_100 = []
        for i in range(100):
            row_sum = sum(counts_100[i]) + 100
            self._matrix_100.append([(counts_100[i][j] + 1) / row_sum for j in range(100)])

        # 2. Train Positional Matrices for 3-digit and 6-digit prizes
        self._positional_matrices = {}
        for pt, num_len in PRIZE_LENGTHS.items():
            pos_dict = {}
            for pos in range(num_len):
                counts_10 = [[0 for _ in range(10)] for _ in range(10)]
                for i in range(len(sorted_records) - 1):
                    rec_curr = sorted_records[i]
                    rec_next = sorted_records[i + 1]

                    val_curr = rec_curr.get(pt)
                    val_next = rec_next.get(pt)

                    num_c = (val_curr[0] if isinstance(val_curr, list) else val_curr) or "0"
                    num_n = (val_next[0] if isinstance(val_next, list) else val_next) or "0"

                    str_c = str(num_c).zfill(num_len)[-num_len:]
                    str_n = str(num_n).zfill(num_len)[-num_len:]

                    d_c = int(str_c[pos])
                    d_n = int(str_n[pos])
                    counts_10[d_c][d_n] += 1

                # Laplace smoothing
                mat_10 = []
                for d in range(10):
                    row_total = sum(counts_10[d]) + 10
                    mat_10.append([(counts_10[d][next_d] + 1) / row_total for next_d in range(10)])
                pos_dict[pos] = mat_10
            self._positional_matrices[pt] = pos_dict

        self._trained = True
        logger.info("MarkovChainModel training complete.")

    def get_positional_probs(self, prize_type: str) -> dict[int, dict[str, float]]:
        """
        Return the predicted probability distribution for each digit position
        given the latest observed draw state.
        """
        num_len = PRIZE_LENGTHS.get(prize_type, 2)
        pos_matrices = self._positional_matrices.get(prize_type, {})
        val = self._last_draw.get(prize_type, "0")
        num_str = str(val[0] if isinstance(val, list) else val).zfill(num_len)[-num_len:]

        result = {}
        for pos in range(num_len):
            last_digit = int(num_str[pos]) if len(num_str) > pos else 0
            row = pos_matrices.get(pos, [[] for _ in range(10)])[last_digit]
            result[pos] = {str(d): row[d] for d in range(10)}
        return result

    def predict_prize(self, prize_type: str, top_n: int = 10) -> list[dict[str, Any]]:
        """
        Generate top predictions for a prize type based on transition probability.
        """
        num_len = PRIZE_LENGTHS.get(prize_type, 2)

        # For 2 digits: use the 100-state matrix
        if prize_type == "last_two":
            last_val = int(str(self._last_draw.get("last_two", "00"))[-2:].zfill(2))
            probs = self._matrix_100[last_val]
            indexed = [(f"{i:02d}", probs[i]) for i in range(100)]
            indexed.sort(key=lambda x: x[1], reverse=True)
            max_p = indexed[0][1] if indexed else 1.0
            return [
                {"number": num, "score": round(prob / max_p, 4)}
                for num, prob in indexed[:top_n]
            ]

        # For 6 digits & 3 digits: combine positional transition distributions
        pos_probs = self.get_positional_probs(prize_type)
        if num_len == 6:
            # Beam search: take top 3 digits per position
            top_per_pos = []
            for pos in range(6):
                pd = pos_probs[pos]
                top_digits = sorted(pd.keys(), key=lambda d: pd[d], reverse=True)[:3]
                top_per_pos.append(top_digits)

            candidates: list[tuple[str, float]] = []
            for combo in product(*top_per_pos):
                num = "".join(combo)
                prob = 1.0
                for pos, d in enumerate(num):
                    prob *= pos_probs[pos][d]
                candidates.append((num, prob))

            candidates.sort(key=lambda x: x[1], reverse=True)
            max_p = candidates[0][1] if candidates else 1.0
            return [
                {"number": num, "score": round(prob / max_p, 4)}
                for num, prob in candidates[:top_n]
            ]
        else:
            # 3 digits exhaustive search (1,000 combinations)
            candidates = []
            for i in range(1000):
                num = f"{i:03d}"
                prob = pos_probs[0][num[0]] * pos_probs[1][num[1]] * pos_probs[2][num[2]]
                candidates.append((num, prob))
            candidates.sort(key=lambda x: x[1], reverse=True)
            max_p = candidates[0][1] if candidates else 1.0
            return [
                {"number": num, "score": round(prob / max_p, 4)}
                for num, prob in candidates[:top_n]
            ]

    def predict(self) -> dict[str, Any]:
        """Generate predictions for all prize categories."""
        if not self._trained:
            return {}
        return {
            pt: {"top10": self.predict_prize(pt, top_n=10), "model": self.MODEL_NAME}
            for pt in PRIZE_LENGTHS
        }

    def predict_for_backtest(self, prize_type: str) -> list[str]:
        """Return top 10 numbers for backtesting evaluation."""
        preds = self.predict_prize(prize_type, top_n=10)
        return [p["number"] for p in preds]

    def get_last_two_transition_matrix_heatmap(self) -> dict[str, Any]:
        """
        Return the 100-state transition matrix formatted for ECharts Heatmap.
        Returns 10x10 aggregated cluster or top high-probability transitions.
        """
        # Aggregate 100x100 into 10x10 tens-digit cluster for visual clarity
        cluster = [[0.0 for _ in range(10)] for _ in range(10)]
        for i in range(100):
            t_from = i // 10
            for j in range(100):
                t_to = j // 10
                cluster[t_from][t_to] += self._matrix_100[i][j]

        # Normalize
        for r in range(10):
            row_sum = sum(cluster[r]) or 1.0
            cluster[r] = [round(v / row_sum, 4) for v in cluster[r]]

        return {
            "matrix_10x10": cluster,
            "labels": [f"หมวด {i}0" for i in range(10)],
        }
