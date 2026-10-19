"""
processor.py — Feature Engineering for Thai Lottery Data
คำนวณสถิติและ features จากข้อมูลผลรางวัลสลากกินแบ่งย้อนหลัง

Outputs:
    data/statistics.json — computed statistics for all prize types
"""

from __future__ import annotations

import json
import logging
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import ephem  # type: ignore
    HAS_EPHEM = True
except ImportError:
    HAS_EPHEM = False

from scraper import DrawRecord, load_raw, SAMPLE_RECORDS

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("processor")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATS_FILE = DATA_DIR / "statistics.json"
HOT_WINDOW = 24  # number of recent draws for "hot" numbers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _digits_of(number: str, length: int = 6) -> list[str]:
    """Pad/truncate a number string and return a list of single-digit chars."""
    n = number.strip().zfill(length)[-length:]
    return list(n)


def _lunar_phase(iso_date: str) -> Optional[float]:
    """
    Compute moon phase (0=new, 0.5=full) for a given ISO date.
    Returns None if ephem is not available.
    """
    if not HAS_EPHEM:
        return None
    try:
        date = ephem.Date(iso_date.replace("-", "/"))
        moon = ephem.Moon(date)
        return float(moon.phase) / 100.0  # normalize to [0,1]
    except Exception:
        return None


def _digit_sum(number: str) -> int:
    """Return the sum of all digits in a number string."""
    return sum(int(d) for d in number if d.isdigit())


# ---------------------------------------------------------------------------
# Core statistics
# ---------------------------------------------------------------------------

class LotteryProcessor:
    """
    Feature engineering processor for Thai lottery historical data.
    คำนวณสถิติครบถ้วนสำหรับทุก prize type
    """

    PRIZE_TYPES = ["first_prize", "front_three", "back_three", "last_two"]
    FIRST_PRIZE_LEN = 6
    THREE_LEN = 3
    TWO_LEN = 2

    def __init__(self, records: list[DrawRecord]) -> None:
        self.records = sorted(records, key=lambda r: r.get("date", ""))
        self.n = len(self.records)

    # ------------------------------------------------------------------
    # Per-digit position frequency
    # ------------------------------------------------------------------

    def _all_numbers_for_type(self, prize_type: str) -> list[str]:
        """Flatten all number strings for a given prize type."""
        numbers: list[str] = []
        for rec in self.records:
            val = rec.get(prize_type)
            if not val:
                continue
            if isinstance(val, list):
                numbers.extend(val)
            else:
                numbers.append(str(val))
        return numbers

    def digit_frequency(self, prize_type: str) -> dict[str, dict[str, Any]]:
        """
        Per-position digit frequency for each prize type.
        Returns {position_index: {digit: count, ...}} (position as string key).
        """
        numbers = self._all_numbers_for_type(prize_type)
        if not numbers:
            return {}

        length = len(numbers[0]) if numbers else 1
        freq: dict[str, Counter] = {str(i): Counter() for i in range(length)}

        for num in numbers:
            num = num.zfill(length)
            for pos, digit in enumerate(num):
                freq[str(pos)][digit] += 1

        return {
            pos: {d: count for d, count in sorted(counter.items())}
            for pos, counter in freq.items()
        }

    def gap_analysis(self, prize_type: str) -> dict[str, int]:
        """
        For each unique number value in a prize type, compute the gap
        (number of draws since the number last appeared).
        Returns {number_string: gap_draws}.
        """
        last_seen: dict[str, int] = {}
        for idx, rec in enumerate(self.records):
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            for num in nums:
                last_seen[str(num)] = idx

        gap: dict[str, int] = {
            num: (self.n - 1 - last_idx)
            for num, last_idx in last_seen.items()
        }
        return gap

    def hot_cold_numbers(self, prize_type: str) -> dict[str, Any]:
        """
        Hot = top-10 most frequent in last HOT_WINDOW draws.
        Cold = top-10 least frequent overall.
        """
        recent = self.records[-HOT_WINDOW:]
        recent_counter: Counter = Counter()
        for rec in recent:
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            for num in nums:
                recent_counter[str(num)] += 1

        overall_counter: Counter = Counter()
        for rec in self.records:
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            for num in nums:
                overall_counter[str(num)] += 1

        hot = [{"number": n, "count": c} for n, c in recent_counter.most_common(10)]
        # Cold: least frequently appearing (at least once)
        cold_sorted = sorted(overall_counter.items(), key=lambda x: x[1])
        cold = [{"number": n, "count": c} for n, c in cold_sorted[:10]]

        return {"hot": hot, "cold": cold}

    # ------------------------------------------------------------------
    # Intermediate features
    # ------------------------------------------------------------------

    def digit_sum_distribution(self) -> dict[str, int]:
        """Distribution of digit sums for first_prize."""
        counter: Counter = Counter()
        for rec in self.records:
            fp = rec.get("first_prize", "")
            if fp:
                counter[str(_digit_sum(fp))] += 1
        return dict(sorted(counter.items()))

    def even_odd_ratio(self, prize_type: str) -> dict[str, Any]:
        """Even/odd count for each digit position."""
        numbers = self._all_numbers_for_type(prize_type)
        if not numbers:
            return {}
        length = len(numbers[0])
        result: dict[str, dict[str, int]] = {}
        for pos in range(length):
            even_count = sum(1 for n in numbers if int(n.zfill(length)[pos]) % 2 == 0)
            odd_count = len(numbers) - even_count
            result[str(pos)] = {"even": even_count, "odd": odd_count}
        return result

    def high_low_ratio(self, prize_type: str) -> dict[str, Any]:
        """High (5-9) / Low (0-4) ratio per digit position."""
        numbers = self._all_numbers_for_type(prize_type)
        if not numbers:
            return {}
        length = len(numbers[0])
        result: dict[str, dict[str, int]] = {}
        for pos in range(length):
            high = sum(1 for n in numbers if int(n.zfill(length)[pos]) >= 5)
            low = len(numbers) - high
            result[str(pos)] = {"high": high, "low": low}
        return result

    def day_of_month_pattern(self) -> dict[str, Any]:
        """
        Pattern by draw day-of-month (Thai lottery is on 1st and 16th).
        Returns first_prize frequency per day-of-month.
        """
        counter: dict[str, Counter] = {"1": Counter(), "16": Counter()}
        for rec in self.records:
            try:
                day = int(rec["date"].split("-")[2])
            except (KeyError, ValueError, IndexError):
                continue
            key = "1" if day <= 8 else "16"
            fp = rec.get("first_prize", "")
            if fp:
                for d in fp:
                    counter[key][d] += 1
        return {k: dict(v) for k, v in counter.items()}

    def monthly_pattern(self, prize_type: str) -> dict[str, dict[str, int]]:
        """Frequency distribution by month (1-12)."""
        result: dict[str, Counter] = {str(m): Counter() for m in range(1, 13)}
        for rec in self.records:
            try:
                month = int(rec["date"].split("-")[1])
            except (KeyError, ValueError, IndexError):
                continue
            val = rec.get(prize_type)
            nums = val if isinstance(val, list) else [val] if val else []
            for num in nums:
                result[str(month)][str(num)] += 1
        return {k: dict(v) for k, v in result.items()}

    def last_digit_distribution(self, prize_type: str) -> dict[str, int]:
        """Distribution of the last digit for a prize type."""
        counter: Counter = Counter()
        numbers = self._all_numbers_for_type(prize_type)
        for num in numbers:
            if num:
                counter[num[-1]] += 1
        return dict(sorted(counter.items()))

    # ------------------------------------------------------------------
    # Advanced features
    # ------------------------------------------------------------------

    def pair_cooccurrence(self) -> dict[str, dict[str, int]]:
        """
        For last_two prizes: which pair digits appear together.
        Returns {digit: {other_digit: co_occurrence_count}}.
        """
        matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            lt = rec.get("last_two", "")
            if lt and len(lt) >= 2:
                d1, d2 = lt[0], lt[1]
                matrix[d1][d2] += 1
                matrix[d2][d1] += 1
        return {k: dict(v) for k, v in matrix.items()}

    def positional_analysis(self, prize_type: str) -> dict[str, Any]:
        """
        Hundreds/tens/units analysis for 3-digit prizes.
        Returns {hundreds: Counter, tens: Counter, units: Counter}.
        """
        numbers = self._all_numbers_for_type(prize_type)
        if not numbers:
            return {}
        pos_names = ["hundreds", "tens", "units"] if len(numbers[0]) == 3 else [
            f"pos_{i}" for i in range(len(numbers[0]))
        ]
        result: dict[str, Counter] = {name: Counter() for name in pos_names}
        for num in numbers:
            for i, name in enumerate(pos_names):
                if i < len(num):
                    result[name][num[i]] += 1
        return {k: dict(sorted(v.items())) for k, v in result.items()}

    def consecutive_patterns(self) -> dict[str, Any]:
        """
        Detect consecutive (sequential digits, e.g. 1234) and repeated digit patterns.
        Returns counts of how many first_prizes have these patterns.
        """
        sequential_count = 0
        repeated_count = 0
        mirror_count = 0

        for rec in self.records:
            fp = rec.get("first_prize", "")
            if not fp or len(fp) < 2:
                continue
            digits = [int(d) for d in fp]

            # Sequential: all digits differ by 1 (ascending or descending)
            diffs = [digits[i+1] - digits[i] for i in range(len(digits) - 1)]
            if all(d == 1 for d in diffs) or all(d == -1 for d in diffs):
                sequential_count += 1

            # Repeated: any digit appears 3+ times
            c = Counter(fp)
            if max(c.values()) >= 3:
                repeated_count += 1

            # Mirror: number equals its reverse (palindrome)
            if fp == fp[::-1]:
                mirror_count += 1

        total = max(self.n, 1)
        return {
            "sequential": {"count": sequential_count, "rate": sequential_count / total},
            "repeated_digits": {"count": repeated_count, "rate": repeated_count / total},
            "palindrome": {"count": mirror_count, "rate": mirror_count / total},
        }

    def lunar_correlation(self) -> list[dict[str, Any]]:
        """
        Compute moon phase for each draw date (if ephem available).
        Returns list of {date, moon_phase, first_prize}.
        """
        results = []
        for rec in self.records:
            phase = _lunar_phase(rec.get("date", ""))
            results.append(
                {
                    "date": rec.get("date"),
                    "moon_phase": phase,
                    "first_prize": rec.get("first_prize"),
                }
            )
        return results

    # ------------------------------------------------------------------
    # Top-level compute
    # ------------------------------------------------------------------

    def compute_all(self) -> dict[str, Any]:
        """
        Compute ALL statistics and return as a single dict.
        คำนวณสถิติทั้งหมดแล้วคืนค่าเป็น dict
        """
        stats: dict[str, Any] = {
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "total_draws": self.n,
            "date_range": {
                "earliest": self.records[0]["date"] if self.records else None,
                "latest": self.records[-1]["date"] if self.records else None,
            },
        }

        prize_stats: dict[str, Any] = {}
        for pt in self.PRIZE_TYPES:
            logger.info("Computing stats for %s…", pt)
            prize_stats[pt] = {
                "digit_frequency": self.digit_frequency(pt),
                "gap_analysis": self.gap_analysis(pt),
                "hot_cold": self.hot_cold_numbers(pt),
                "even_odd": self.even_odd_ratio(pt),
                "high_low": self.high_low_ratio(pt),
                "monthly_pattern": self.monthly_pattern(pt),
                "last_digit": self.last_digit_distribution(pt),
            }
            if pt in ("front_three", "back_three"):
                prize_stats[pt]["positional"] = self.positional_analysis(pt)

        stats["prize_types"] = prize_stats

        # Global features
        stats["digit_sum_distribution"] = self.digit_sum_distribution()
        stats["day_of_month_pattern"] = self.day_of_month_pattern()
        stats["pair_cooccurrence_last_two"] = self.pair_cooccurrence()
        stats["consecutive_patterns"] = self.consecutive_patterns()
        stats["lunar_correlation"] = self.lunar_correlation()

        # Markov State Transition Matrix
        try:
            from models.markov_model import MarkovChainModel
            markov = MarkovChainModel()
            markov.train(self.records)
            stats["markov_transitions"] = markov.get_last_two_transition_matrix_heatmap()
        except Exception as e:
            logger.warning("Could not compute markov transitions: %s", e)
            stats["markov_transitions"] = {}

        return stats


def run_processor(records: Optional[list[DrawRecord]] = None) -> dict[str, Any]:
    """
    Load records (or use provided), compute statistics, save to disk.
    รันการคำนวณสถิติและบันทึกผล
    """
    if records is None:
        records = load_raw()
    if not records:
        logger.warning("No records found — using sample data")
        records = SAMPLE_RECORDS

    processor = LotteryProcessor(records)
    stats = processor.compute_all()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Saved statistics → %s", STATS_FILE)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    stats = run_processor()
    print(f"✅ Statistics computed ({stats['total_draws']} draws) → {STATS_FILE}")
