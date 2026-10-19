"""
scraper.py — Thai Lottery Web Scraper
ดึงข้อมูลผลรางวัลสลากกินแบ่งรัฐบาลจากหลายแหล่ง (3-source fallback)

Sources:
  Primary:   myhora.com/lottery/
  Fallback1: sanook.com/lottery/
  Fallback2: glo.or.th
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPER_DEPS = True
except ImportError:
    requests = None  # type: ignore
    BeautifulSoup = None  # type: ignore
    HAS_SCRAPER_DEPS = False

# Try fake_useragent; fall back to static list if not installed
try:
    from fake_useragent import UserAgent
    _UA = UserAgent()
    def _random_ua() -> str:
        return _UA.random
except Exception:
    _STATIC_UAS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    ]
    import random as _random
    def _random_ua() -> str:
        return _random.choice(_STATIC_UAS)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scraper")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_FILE = RAW_DIR / "results_raw.json"

REQUEST_DELAY_SEC = 1.5   # polite delay between requests
MAX_RETRIES = 3
BACKOFF_BASE = 2          # exponential: 2^attempt seconds


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
DrawRecord = dict[str, Any]
"""
{
    "date": "2024-04-01",          # ISO date
    "date_thai": "1 เมษายน 2567",  # Thai formatted date
    "first_prize": "123456",
    "front_three": ["123", "456"],
    "back_three": ["789", "012"],
    "last_two": "34",
}
"""


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _session() -> Any:
    """Create a requests session with browser-like headers."""
    if not HAS_SCRAPER_DEPS:
        return None
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": _random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return s


def _fetch(url: str, session: requests.Session, timeout: int = 15) -> Optional[str]:
    """
    Fetch a URL with exponential-backoff retry.
    Returns HTML text or None on failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug("GET %s (attempt %d/%d)", url, attempt + 1, MAX_RETRIES)
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 403:
                # Rotate UA and retry
                session.headers["User-Agent"] = _random_ua()
                logger.warning("403 Forbidden from %s — rotating UA", url)
            elif resp.status_code == 200:
                return resp.text
            else:
                logger.warning("HTTP %s from %s", resp.status_code, url)
        except requests.RequestException as exc:
            logger.warning("Request error: %s", exc)

        wait = BACKOFF_BASE ** attempt
        logger.info("Waiting %ss before retry…", wait)
        time.sleep(wait)

    logger.error("Failed to fetch %s after %d attempts", url, MAX_RETRIES)
    return None


def _sleep() -> None:
    time.sleep(REQUEST_DELAY_SEC)


# ---------------------------------------------------------------------------
# Thai date helpers
# ---------------------------------------------------------------------------

THAI_MONTHS = {
    1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
    5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
    9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม",
}

THAI_MONTHS_REV = {v: k for k, v in THAI_MONTHS.items()}
THAI_MONTHS_SHORT = {
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4,
    "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8,
    "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
}


def _thai_to_iso(date_thai: str) -> Optional[str]:
    """
    Convert Thai date string to ISO-8601 (e.g. '1 เมษายน 2567' → '2024-04-01').
    Handles both long and abbreviated month names, and both CE/BE years.
    """
    date_thai = date_thai.strip()
    # Try long month names
    for month_name, month_num in THAI_MONTHS_REV.items():
        if month_name in date_thai:
            parts = date_thai.replace(month_name, "").split()
            if len(parts) >= 2:
                try:
                    day = int(parts[0])
                    year = int(parts[-1])
                    if year > 2500:  # Buddhist Era
                        year -= 543
                    return f"{year:04d}-{month_num:02d}-{day:02d}"
                except ValueError:
                    pass
    # Try short month names
    for abbr, month_num in THAI_MONTHS_SHORT.items():
        if abbr in date_thai:
            parts = date_thai.replace(abbr, "").split()
            if len(parts) >= 2:
                try:
                    day = int(parts[0])
                    year = int(parts[-1])
                    if year > 2500:
                        year -= 543
                    return f"{year:04d}-{month_num:02d}-{day:02d}"
                except ValueError:
                    pass
    # Try numeric (e.g. "01/04/2567" or "01-04-2567")
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_thai)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year > 2500:
            year -= 543
        return f"{year:04d}-{month:02d}-{day:02d}"
    return None


def _iso_to_thai(iso: str) -> str:
    """Convert ISO date to Thai string."""
    try:
        dt = datetime.strptime(iso, "%Y-%m-%d")
        be_year = dt.year + 543
        return f"{dt.day} {THAI_MONTHS[dt.month]} {be_year}"
    except ValueError:
        return iso


# ---------------------------------------------------------------------------
# Source 1: myhora.com
# ---------------------------------------------------------------------------

def _parse_myhora_page(html: str) -> list[DrawRecord]:
    """Parse a single myhora.com lottery result page."""
    records: list[DrawRecord] = []
    soup = BeautifulSoup(html, "lxml")

    # myhora typically wraps each draw in a div/table with class patterns
    # We search for prize data in multiple possible container structures
    containers = (
        soup.select("div.lotto-result") or
        soup.select("div.lottery-result") or
        soup.select("table.lotto") or
        soup.select("div[class*='lotto']") or
        soup.select("article") or
        soup.find_all("div", {"class": re.compile(r"result|lottery|lotto", re.I)})
    )

    for container in containers:
        record = _extract_myhora_record(container)
        if record:
            records.append(record)

    return records


def _extract_myhora_record(tag) -> Optional[DrawRecord]:
    """Extract a single draw record from a myhora.com HTML element."""
    text = tag.get_text(separator=" ", strip=True)

    # Look for 6-digit first prize
    first_prizes = re.findall(r"\b(\d{6})\b", text)
    if not first_prizes:
        return None

    first_prize = first_prizes[0]

    # Date: look for Thai date pattern
    date_match = re.search(
        r"(\d{1,2})\s*(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|"
        r"กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s*(\d{4})",
        text,
    )
    if not date_match:
        return None
    date_thai = date_match.group(0).strip()
    iso_date = _thai_to_iso(date_thai)
    if not iso_date:
        return None

    # 3-digit front/back prizes
    three_digit = re.findall(r"\b(\d{3})\b", text)
    front_three = three_digit[:2] if len(three_digit) >= 2 else ["000", "000"]
    back_three = three_digit[2:4] if len(three_digit) >= 4 else ["000", "000"]

    # 2-digit last prize
    two_digit = re.findall(r"\b(\d{2})\b", text)
    # filter out sub-strings of 6-digit numbers; take first unique 2-digit
    last_two = two_digit[0] if two_digit else "00"

    return {
        "date": iso_date,
        "date_thai": date_thai,
        "first_prize": first_prize,
        "front_three": front_three[:2],
        "back_three": back_three[:2],
        "last_two": last_two,
    }


def scrape_myhora(session: requests.Session) -> list[DrawRecord]:
    """
    Scrape historical lottery results from myhora.com.
    Tries the index page and year-based pages for ~20 years of data.
    """
    logger.info("Scraping myhora.com…")
    records: list[DrawRecord] = []

    # Try the main index page first
    html = _fetch("https://myhora.com/lottery/", session)
    if html:
        records.extend(_parse_myhora_page(html))
        _sleep()

    # Try year-based pages (พ.ศ. 2549 = 2006 up to current year + 543)
    current_be = datetime.now().year + 543
    for be_year in range(2549, current_be + 1):
        url = f"https://myhora.com/lottery/งวด-{be_year}.aspx"
        html = _fetch(url, session)
        if html:
            page_records = _parse_myhora_page(html)
            logger.info("  myhora %d BE: %d records", be_year, len(page_records))
            records.extend(page_records)
        else:
            # Try alternative URL pattern
            url2 = f"https://myhora.com/lottery/{be_year}/"
            html2 = _fetch(url2, session)
            if html2:
                page_records = _parse_myhora_page(html2)
                records.extend(page_records)
        _sleep()

    logger.info("myhora.com: %d raw records", len(records))
    return records


# ---------------------------------------------------------------------------
# Source 2: sanook.com
# ---------------------------------------------------------------------------

def _parse_sanook_page(html: str) -> list[DrawRecord]:
    """Parse sanook.com lottery result page."""
    records: list[DrawRecord] = []
    soup = BeautifulSoup(html, "lxml")

    # sanook lottery results are often in list items or table rows
    items = (
        soup.select("li.lottery-result-item") or
        soup.select("div.lottery-item") or
        soup.select("tr") or
        soup.find_all("div", {"class": re.compile(r"result|item|draw", re.I)})
    )

    for item in items:
        text = item.get_text(separator=" ", strip=True)
        record = _parse_generic_record(text)
        if record:
            records.append(record)

    return records


def scrape_sanook(session: requests.Session) -> list[DrawRecord]:
    """Scrape sanook.com/lotto as Fallback 1."""
    logger.info("Scraping sanook.com (fallback 1)…")
    records: list[DrawRecord] = []

    urls = [
        "https://lottery.sanook.com/",
        "https://www.sanook.com/lottery/",
        "https://lottery.sanook.com/history/",
    ]
    for url in urls:
        html = _fetch(url, session)
        if html:
            page_records = _parse_sanook_page(html)
            records.extend(page_records)
            _sleep()

    logger.info("sanook.com: %d raw records", len(records))
    return records


# ---------------------------------------------------------------------------
# Source 3: glo.or.th
# ---------------------------------------------------------------------------

def _parse_glo_page(html: str) -> list[DrawRecord]:
    """Parse glo.or.th result page."""
    records: list[DrawRecord] = []
    soup = BeautifulSoup(html, "lxml")

    rows = soup.find_all("tr")
    for row in rows:
        text = row.get_text(separator=" ", strip=True)
        record = _parse_generic_record(text)
        if record:
            records.append(record)

    return records


def scrape_glo(session: requests.Session) -> list[DrawRecord]:
    """Scrape glo.or.th as Fallback 2."""
    logger.info("Scraping glo.or.th (fallback 2)…")
    records: list[DrawRecord] = []

    urls = [
        "https://www.glo.or.th/check/result/",
        "https://www.glo.or.th/",
    ]
    for url in urls:
        html = _fetch(url, session)
        if html:
            records.extend(_parse_glo_page(html))
            _sleep()

    logger.info("glo.or.th: %d raw records", len(records))
    return records


# ---------------------------------------------------------------------------
# Generic parser (fallback for unknown HTML structures)
# ---------------------------------------------------------------------------

def _parse_generic_record(text: str) -> Optional[DrawRecord]:
    """
    Attempt to extract a draw record from raw text using regex patterns.
    Useful when site structure is unknown or changes.
    """
    first_prizes = re.findall(r"\b(\d{6})\b", text)
    if not first_prizes:
        return None

    date_match = re.search(
        r"(\d{1,2})\s*(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|"
        r"กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s*(\d{4})",
        text,
    )
    if not date_match:
        return None

    date_thai = date_match.group(0)
    iso_date = _thai_to_iso(date_thai)
    if not iso_date:
        return None

    three_digit = re.findall(r"\b(\d{3})\b", text)
    two_digit = re.findall(r"(?<!\d)(\d{2})(?!\d)", text)

    return {
        "date": iso_date,
        "date_thai": date_thai.strip(),
        "first_prize": first_prizes[0],
        "front_three": three_digit[:2] if len(three_digit) >= 2 else ["000", "000"],
        "back_three": three_digit[2:4] if len(three_digit) >= 4 else ["000", "000"],
        "last_two": two_digit[0] if two_digit else "00",
    }


# ---------------------------------------------------------------------------
# Dedup & sort
# ---------------------------------------------------------------------------

def _deduplicate(records: list[DrawRecord]) -> list[DrawRecord]:
    """Remove duplicate draw records (same date), keeping the most complete."""
    seen: dict[str, DrawRecord] = {}
    for r in records:
        date = r.get("date", "")
        if not date:
            continue
        if date not in seen:
            seen[date] = r
        else:
            # Prefer record with non-zero prizes
            existing = seen[date]
            if (
                existing.get("first_prize", "000000") == "000000"
                and r.get("first_prize", "000000") != "000000"
            ):
                seen[date] = r
    return sorted(seen.values(), key=lambda x: x["date"])


# ---------------------------------------------------------------------------
# Fallback sample data for development / CI without network
# ---------------------------------------------------------------------------

SAMPLE_RECORDS: list[DrawRecord] = [
    {"date": "2026-10-16", "date_thai": "16 ตุลาคม 2569", "first_prize": "011781", "front_three": ["392", "402"], "back_three": ["171", "255"], "last_two": "48"},
    {"date": "2026-10-01", "date_thai": "1 ตุลาคม 2569", "first_prize": "402701", "front_three": ["791", "912"], "back_three": ["058", "396"], "last_two": "70"},
    {"date": "2026-09-16", "date_thai": "16 กันยายน 2569", "first_prize": "730640", "front_three": ["060", "521"], "back_three": ["266", "041"], "last_two": "64"},
    {"date": "2026-09-01", "date_thai": "1 กันยายน 2569", "first_prize": "417212", "front_three": ["257", "346"], "back_three": ["136", "740"], "last_two": "04"},
    {"date": "2026-08-16", "date_thai": "16 สิงหาคม 2569", "first_prize": "004615", "front_three": ["731", "429"], "back_three": ["937", "094"], "last_two": "53"},
    {"date": "2026-08-01", "date_thai": "1 สิงหาคม 2569", "first_prize": "932479", "front_three": ["413", "672"], "back_three": ["154", "039"], "last_two": "69"},
    {"date": "2026-07-16", "date_thai": "16 กรกฎาคม 2569", "first_prize": "639214", "front_three": ["683", "709"], "back_three": ["746", "427"], "last_two": "71"},
    {"date": "2026-07-01", "date_thai": "1 กรกฎาคม 2569", "first_prize": "751495", "front_three": ["001", "980"], "back_three": ["304", "531"], "last_two": "62"},
    {"date": "2026-06-16", "date_thai": "16 มิถุนายน 2569", "first_prize": "287184", "front_three": ["758", "434"], "back_three": ["007", "721"], "last_two": "48"},
    {"date": "2026-06-01", "date_thai": "1 มิถุนายน 2569", "first_prize": "173770", "front_three": ["415", "848"], "back_three": ["410", "938"], "last_two": "95"},
    {"date": "2026-05-16", "date_thai": "16 พฤษภาคม 2569", "first_prize": "107387", "front_three": ["298", "091"], "back_three": ["602", "716"], "last_two": "08"},
    {"date": "2026-05-02", "date_thai": "2 พฤษภาคม 2569", "first_prize": "536077", "front_three": ["267", "318"], "back_three": ["065", "153"], "last_two": "43"},
    {"date": "2026-04-16", "date_thai": "16 เมษายน 2569", "first_prize": "309612", "front_three": ["355", "108"], "back_three": ["868", "424"], "last_two": "77"},
    {"date": "2026-04-01", "date_thai": "1 เมษายน 2569", "first_prize": "292514", "front_three": ["406", "113"], "back_three": ["851", "098"], "last_two": "47"},
    {"date": "2026-03-16", "date_thai": "16 มีนาคม 2569", "first_prize": "833009", "front_three": ["510", "983"], "back_three": ["439", "954"], "last_two": "64"},
    {"date": "2026-03-01", "date_thai": "1 มีนาคม 2569", "first_prize": "820866", "front_three": ["479", "054"], "back_three": ["068", "837"], "last_two": "06"},
    {"date": "2026-02-16", "date_thai": "16 กุมภาพันธ์ 2569", "first_prize": "340563", "front_three": ["527", "241"], "back_three": ["578", "169"], "last_two": "07"},
    {"date": "2026-02-01", "date_thai": "1 กุมภาพันธ์ 2569", "first_prize": "174629", "front_three": ["917", "195"], "back_three": ["408", "041"], "last_two": "48"},
    {"date": "2026-01-17", "date_thai": "17 มกราคม 2569", "first_prize": "807779", "front_three": ["699", "961"], "back_three": ["448", "477"], "last_two": "23"},
    {"date": "2025-12-30", "date_thai": "30 ธันวาคม 2568", "first_prize": "625544", "front_three": ["600", "648"], "back_three": ["882", "456"], "last_two": "89"}
]


# ---------------------------------------------------------------------------
# Main scrape function
# ---------------------------------------------------------------------------

def scrape_all() -> list[DrawRecord]:
    """
    Scrape lottery results from all sources with fallback.
    Returns deduplicated sorted list of draw records.

    เรียงลำดับความสำคัญ: myhora.com → sanook.com → glo.or.th → sample data
    """
    session = _session()
    if session is None:
        logger.warning("Scraper dependencies missing — using built-in sample data")
        return SAMPLE_RECORDS.copy()
    all_records: list[DrawRecord] = []

    # Source 1
    try:
        myhora_records = scrape_myhora(session)
        all_records.extend(myhora_records)
    except Exception as exc:
        logger.error("myhora scrape failed: %s", exc)

    # Source 2 (fallback)
    if len(all_records) < 10:
        try:
            sanook_records = scrape_sanook(session)
            all_records.extend(sanook_records)
        except Exception as exc:
            logger.error("sanook scrape failed: %s", exc)

    # Source 3 (fallback)
    if len(all_records) < 10:
        try:
            glo_records = scrape_glo(session)
            all_records.extend(glo_records)
        except Exception as exc:
            logger.error("glo scrape failed: %s", exc)

    # Final fallback: sample data (for dev/CI)
    if not all_records:
        logger.warning("All scrapers failed — using built-in sample data (5 draws)")
        all_records = SAMPLE_RECORDS.copy()

    deduped = _deduplicate(all_records)
    logger.info("Total unique draw records: %d", len(deduped))
    return deduped


def save_raw(records: list[DrawRecord]) -> Path:
    """Save raw records to data/raw/results_raw.json."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "count": len(records),
        "records": records,
    }
    RAW_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d records → %s", len(records), RAW_FILE)
    return RAW_FILE


def load_raw() -> list[DrawRecord]:
    """Load previously-scraped raw records from disk."""
    if not RAW_FILE.exists():
        return []
    data = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    return data.get("records", [])


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Thai Lottery Scraper")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    records = scrape_all()
    save_raw(records)
    print(f"✅ Scraped {len(records)} draw records → {RAW_FILE}")
