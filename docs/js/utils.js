/**
 * utils.js — Utility functions for Thai Lottery Analytics
 */

'use strict';

// Thai month names (short)
const THAI_MONTHS_SHORT = [
  'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
  'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
];

// Thai month names (full)
const THAI_MONTHS_FULL = [
  'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
  'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
];

/**
 * Convert month index (0-based) to Thai short name
 * @param {number} monthIndex — 0-based month index
 * @returns {string} Thai short month name
 */
function thaiMonthName(monthIndex) {
  if (monthIndex < 0 || monthIndex > 11) return '?';
  return THAI_MONTHS_SHORT[monthIndex];
}

/**
 * Format ISO date string to Thai date with Buddhist Era year
 * @param {string} isoDate — ISO 8601 date string (e.g. "2026-10-16")
 * @returns {string} Thai date string (e.g. "16 ตุลาคม 2569")
 */
function formatThaiDate(isoDate) {
  if (!isoDate) return '-';
  try {
    const date = new Date(isoDate + (isoDate.includes('T') ? '' : 'T00:00:00'));
    const day = date.getDate();
    const month = THAI_MONTHS_FULL[date.getMonth()];
    const year = date.getFullYear() + 543; // Convert CE to BE
    return `${day} ${month} ${year}`;
  } catch (e) {
    return isoDate;
  }
}

/**
 * Format ISO date to short Thai format
 * @param {string} isoDate
 * @returns {string} e.g. "16 ต.ค. 69"
 */
function formatThaiDateShort(isoDate) {
  if (!isoDate) return '-';
  try {
    const date = new Date(isoDate + (isoDate.includes('T') ? '' : 'T00:00:00'));
    const day = date.getDate();
    const month = THAI_MONTHS_SHORT[date.getMonth()];
    const year = String(date.getFullYear() + 543).slice(-2);
    return `${day} ${month} ${year}`;
  } catch (e) {
    return isoDate;
  }
}

/**
 * Calculate the next draw date (1st or 16th of each month)
 * @param {string} lastDate — ISO date string of last draw
 * @returns {string} ISO date string of next draw
 */
function getNextDrawDate(lastDate) {
  if (!lastDate) return null;
  try {
    const date = new Date(lastDate + (lastDate.includes('T') ? '' : 'T00:00:00'));
    const day = date.getDate();
    const month = date.getMonth();
    const year = date.getFullYear();

    let nextDate;
    if (day < 16) {
      nextDate = new Date(year, month, 16);
    } else {
      // Next month's 1st
      nextDate = new Date(year, month + 1, 1);
    }
    return nextDate.toISOString().split('T')[0];
  } catch (e) {
    return null;
  }
}

/**
 * Format a lottery number by prize type
 * @param {string|number} num
 * @param {string} type — 'first', 'last_three_f', 'last_three_b', 'last_two'
 * @returns {string} zero-padded number string
 */
function numberToPrizeDisplay(num, type) {
  if (num === null || num === undefined) return '-';
  const n = String(num);
  const padMap = {
    first: 6,
    last_three_f: 3,
    last_three_b: 3,
    last_two: 2
  };
  const pad = padMap[type] || n.length;
  return n.padStart(pad, '0');
}

/**
 * Format ML score as percentage string
 * @param {number} score — raw score (0-1 or 0-100)
 * @returns {string} e.g. "87.3%"
 */
function formatScore(score) {
  if (score === null || score === undefined || isNaN(score)) return '-';
  const pct = score <= 1 ? score * 100 : score;
  return pct.toFixed(1) + '%';
}

/**
 * Check if a prize number is "hot" (above-average frequency)
 * @param {string|number} number
 * @param {object} statistics — statistics data object
 * @param {string} prizeType — prize type key
 * @returns {boolean}
 */
function isPrizeNumberHot(number, statistics, prizeType) {
  if (!statistics || !prizeType) return false;
  try {
    const freqMap = statistics.frequency?.[prizeType];
    if (!freqMap) return false;
    const numStr = String(number);
    const freq = freqMap[numStr] || 0;
    const values = Object.values(freqMap).filter(v => v > 0);
    if (!values.length) return false;
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    return freq > avg;
  } catch (e) {
    return false;
  }
}

/**
 * Download data as a CSV file
 * @param {Array<Array<string>>} rows — array of row arrays (first row = headers)
 * @param {string} filename — desired filename (without .csv)
 */
function downloadCSV(rows, filename) {
  const csvContent = rows
    .map(row =>
      row.map(cell => {
        const s = String(cell == null ? '' : cell);
        // Quote cells containing comma, quote, or newline
        if (s.includes(',') || s.includes('"') || s.includes('\n')) {
          return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
      }).join(',')
    )
    .join('\r\n');

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = (filename || 'export') + '.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Clamp a number between min and max
 */
function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

/**
 * Debounce a function
 */
function debounce(fn, delay) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Deep-get a nested property safely
 */
function safeGet(obj, path, defaultVal) {
  try {
    return path.split('.').reduce((o, k) => o[k], obj) ?? defaultVal;
  } catch {
    return defaultVal;
  }
}
