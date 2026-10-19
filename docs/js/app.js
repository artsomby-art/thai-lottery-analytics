/**
 * app.js — Main Application Coordinator
 * Thai Lottery Analytics Dashboard
 */

'use strict';

window.APP_DATA = {
  results: null,
  statistics: null,
  predictions: null,
  backtesting: null
};

// Pagination state for Tab 4 (History)
let historyCurrentPage = 1;
const ITEMS_PER_PAGE = 25;
let filteredHistoryDraws = [];

document.addEventListener('DOMContentLoaded', async () => {
  console.log('🎰 Thai Lottery Analytics Dashboard initializing...');
  await loadAllData();
  setupUI();
  initTabs();
  renderOverviewTab();
  initHistoryTab();
});

/**
 * Fetch all 4 JSON files in parallel with graceful fallback to mock data
 */
async function loadAllData() {
  const fetchWithFallback = async (primaryUrl, fallbackUrl, fallbackObj) => {
    try {
      const res = await fetch(primaryUrl);
      if (res.ok) return await res.json();
    } catch (e) {}

    try {
      if (fallbackUrl) {
        const res2 = await fetch(fallbackUrl);
        if (res2.ok) return await res2.json();
      }
    } catch (e) {}

    console.warn(`Could not load ${primaryUrl} or ${fallbackUrl} — using mock data fallback.`);
    return fallbackObj;
  };

  const [results, statistics, predictions, backtesting] = await Promise.all([
    fetchWithFallback('data/results.json', '../data/results.json', typeof MOCK_RESULTS !== 'undefined' ? MOCK_RESULTS : null),
    fetchWithFallback('data/statistics.json', '../data/statistics.json', typeof MOCK_STATISTICS !== 'undefined' ? MOCK_STATISTICS : null),
    fetchWithFallback('data/predictions.json', '../data/predictions.json', typeof MOCK_PREDICTIONS !== 'undefined' ? MOCK_PREDICTIONS : null),
    fetchWithFallback('data/backtesting.json', '../data/backtesting.json', typeof MOCK_BACKTESTING !== 'undefined' ? MOCK_BACKTESTING : null)
  ]);

  window.APP_DATA.results = results;
  window.APP_DATA.statistics = statistics;
  window.APP_DATA.predictions = predictions;
  window.APP_DATA.backtesting = backtesting;

  console.log('Data loaded successfully:', {
    draws: results?.total_draws || results?.draws?.length || 0,
    hasStats: !!statistics,
    hasPreds: !!predictions,
    hasBacktest: !!backtesting
  });
}

/**
 * Populate navbar badge, next draw date, and quick stats
 */
function setupUI() {
  const results = window.APP_DATA.results;
  const preds = window.APP_DATA.predictions;

  const draws = results?.draws || results?.results || [];
  const latestDraw = draws[0] || {};

  // Last updated & next draw
  const lastUpdatedEl = document.getElementById('navbar-last-updated');
  if (lastUpdatedEl && latestDraw.date) {
    lastUpdatedEl.textContent = `งวดล่าสุด: ${formatThaiDate(latestDraw.date)}`;
  }

  const nextDrawEl = document.getElementById('navbar-next-draw');
  if (nextDrawEl) {
    const nextDate = preds?.next_draw_date || getNextDrawDate(latestDraw.date);
    nextDrawEl.textContent = `งวดถัดไป: ${formatThaiDate(nextDate)}`;
  }

  // Quick Stats row
  const statDrawsCount = document.getElementById('stat-total-draws');
  if (statDrawsCount) {
    statDrawsCount.textContent = (results?.total_draws || draws.length || 0).toLocaleString();
  }

  const statYears = document.getElementById('stat-years-span');
  if (statYears && draws.length > 0) {
    const oldest = draws[draws.length - 1]?.date;
    const newest = draws[0]?.date;
    if (oldest && newest) {
      const ySpan = Math.max(1, Math.round((new Date(newest) - new Date(oldest)) / (1000 * 3600 * 24 * 365.25)));
      statYears.textContent = `${ySpan}+ ปี`;
    }
  }

  const statNextDateBadge = document.getElementById('stat-next-date');
  if (statNextDateBadge) {
    statNextDateBadge.textContent = formatThaiDate(preds?.next_draw_date || getNextDrawDate(latestDraw.date));
  }
}

/**
 * Tab 1: Render Overview Tab components
 */
function renderOverviewTab() {
  const results = window.APP_DATA.results;
  const stats = window.APP_DATA.statistics;
  const preds = window.APP_DATA.predictions;

  const draws = results?.draws || results?.results || [];
  const latest = draws[0] || {};

  // 1. Hero Cards: Latest Results
  const firstPrizeEl = document.getElementById('hero-first-prize');
  if (firstPrizeEl) firstPrizeEl.textContent = latest.first_prize || latest.first || '------';

  const frontThreeEl = document.getElementById('hero-front-three');
  if (frontThreeEl) {
    const f3 = latest.front_three || latest.last_three_f || [];
    frontThreeEl.textContent = f3.join('   ') || '---   ---';
  }

  const backThreeEl = document.getElementById('hero-back-three');
  if (backThreeEl) {
    const b3 = latest.back_three || latest.last_three_b || [];
    backThreeEl.textContent = b3.join('   ') || '---   ---';
  }

  const lastTwoEl = document.getElementById('hero-last-two');
  if (lastTwoEl) lastTwoEl.textContent = latest.last_two || '--';

  const drawDateLabel = document.getElementById('hero-draw-date');
  if (drawDateLabel && latest.date) {
    drawDateLabel.textContent = `ผลรางวัลประจำงวดวันที่ ${formatThaiDate(latest.date)}`;
  }

  // 2. Hot / Cold Horizontal Bar Chart
  if (typeof initHotColdChart === 'function' && stats) {
    initHotColdChart(stats);
  }

  // 3. Hot / Cold Badges summary
  const hotListEl = document.getElementById('overview-hot-list');
  const coldListEl = document.getElementById('overview-cold-list');
  const hotCold = stats?.hot_cold?.last_two || {};

  if (hotListEl && hotCold.hot) {
    hotListEl.innerHTML = hotCold.hot.slice(0, 8).map(item =>
      `<span class="badge badge-hot me-1 mb-1 fs-6">${item.number} <small class="text-muted">(${item.count}ครั้ง)</small></span>`
    ).join('');
  }
  if (coldListEl && hotCold.cold) {
    coldListEl.innerHTML = hotCold.cold.slice(0, 8).map(item =>
      `<span class="badge badge-cold me-1 mb-1 fs-6">${item.number} <small class="text-muted">(${item.count}ครั้ง)</small></span>`
    ).join('');
  }

  // 4. Ensemble Top Predictions Preview
  renderOverviewPredictions(preds);
}

function renderOverviewPredictions(preds) {
  const container = document.getElementById('overview-top-predictions');
  if (!container || !preds) return;

  const prizeTypes = [
    { key: 'last_two', altKey: 'last_two', name: 'เลขท้าย 2 ตัว' },
    { key: 'last_three_b', altKey: 'back_three', name: 'เลขท้าย 3 ตัว' },
    { key: 'last_three_f', altKey: 'front_three', name: 'เลขหน้า 3 ตัว' },
    { key: 'first_prize', altKey: 'first', name: 'รางวัลที่ 1' }
  ];

  let html = '<div class="row g-3">';
  prizeTypes.forEach(pt => {
    let topList = preds?.prize_types?.[pt.key]?.ensemble?.top10 ||
                  preds?.prize_types?.[pt.altKey]?.ensemble?.top10 ||
                  preds?.ensemble?.[pt.key] ||
                  preds?.ensemble?.[pt.altKey] || [];

    html += `
      <div class="col-md-6 col-lg-3">
        <div class="dash-card p-3 h-100">
          <div class="text-muted small mb-2 fw-bold text-uppercase">${pt.name}</div>
          <div class="d-flex flex-column gap-2">
            ${topList.length === 0 ? '<div class="text-muted small text-center py-2">ไม่มีข้อมูล</div>' : topList.slice(0, 5).map((item, idx) => `
              <div class="d-flex align-items-center justify-content-between p-2 rounded" style="background: var(--bg-tertiary);">
                <div class="d-flex align-items-center gap-2">
                  <span class="badge ${idx === 0 ? 'bg-warning text-dark' : 'bg-secondary'} rounded-pill">${idx + 1}</span>
                  <span class="prize-number fs-5 text-light">${item.number}</span>
                </div>
                <div class="text-end">
                  <span class="text-warning small fw-bold">${formatScore(item.score)}</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

/**
 * Tab 3: Render Predictions Tables for specific prize type
 */
function renderPredictionsTables(prizeType) {
  const preds = window.APP_DATA.predictions;
  if (!preds) return;

  // Resolve normalized keys
  const altKey = prizeType === 'last_three_b' ? 'back_three'
               : prizeType === 'last_three_f' ? 'front_three'
               : (prizeType === 'first_prize' ? 'first' : (prizeType === 'first' ? 'first_prize' : prizeType));

  // Render Positional Breakdown for First Prize
  renderPositionalBreakdown(preds, prizeType);

  // 1. Combined Ensemble Table
  const ensembleList = preds?.prize_types?.[prizeType]?.ensemble?.top10 ||
                       preds?.prize_types?.[altKey]?.ensemble?.top10 ||
                       preds?.ensemble?.[prizeType] ||
                       preds?.ensemble?.[altKey] || [];

  const ensembleTableBody = document.getElementById('pred-ensemble-table-body');
  if (ensembleTableBody) {
    if (ensembleList.length === 0) {
      ensembleTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">ไม่มีข้อมูลคาดการณ์</td></tr>';
    } else {
      ensembleTableBody.innerHTML = ensembleList.slice(0, 10).map((item, idx) => {
        const pct = Math.round((item.score || 0) * 100);
        const votes = (item.model_votes && item.model_votes.length > 0)
          ? item.model_votes.join(', ')
          : 'Ensemble Consensus';
        return `
          <tr>
            <td class="text-center"><span class="badge ${idx === 0 ? 'bg-warning text-dark' : 'bg-dark border border-secondary'} rounded-pill">${idx + 1}</span></td>
            <td><span class="prize-number fs-5 text-warning">${item.number}</span></td>
            <td style="width: 40%;">
              <div class="d-flex align-items-center gap-2">
                <div class="confidence-bar-bg flex-grow-1">
                  <div class="confidence-bar-fill" style="width: ${pct}%;"></div>
                </div>
                <span class="small text-muted font-monospace">${pct}%</span>
              </div>
            </td>
            <td class="text-muted small">${votes}</td>
          </tr>
        `;
      }).join('');
    }
  }

  // 2. Per-Model Predictions Comparison (6 Models)
  const models = ['frequency', 'markov', 'arima', 'prophet', 'lstm', 'monte_carlo'];
  models.forEach(m => {
    const listEl = document.getElementById(`pred-list-${m}`);
    if (!listEl) return;

    let subList = preds?.prize_types?.[prizeType]?.models?.[m]?.top10 ||
                  preds?.prize_types?.[altKey]?.models?.[m]?.top10 ||
                  preds?.models?.[m]?.predictions?.[prizeType] ||
                  preds?.models?.[m]?.predictions?.[altKey] || [];

    if (subList.length === 0) {
      listEl.innerHTML = '<div class="text-muted small text-center py-2">ไม่มีข้อมูล</div>';
    } else {
      listEl.innerHTML = subList.slice(0, 7).map((item, idx) => `
        <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-dark">
          <span class="text-muted small">#${idx + 1}</span>
          <span class="prize-number fs-6 text-light">${item.number}</span>
          <span class="small font-monospace text-secondary">${formatScore(item.score)}</span>
        </div>
      `).join('');
    }
  });
}

function renderPositionalBreakdown(preds, prizeType) {
  const container = document.getElementById('pred-positional-breakdown');
  const target = document.getElementById('positional-breakdown-container');
  const digitSumBadge = document.getElementById('digit-sum-badge');
  if (!container || !target) return;

  if (prizeType !== 'first_prize') {
    container.classList.add('d-none');
    return;
  }

  const breakdown = preds?.prize_types?.first_prize?.ensemble?.positional_breakdown ||
                    preds?.ensemble?.positional_breakdown || [];
  const digitSum = preds?.prize_types?.first_prize?.ensemble?.digit_sum_analysis ||
                   preds?.ensemble?.digit_sum_analysis || {};

  if (!breakdown.length) {
    container.classList.add('d-none');
    return;
  }

  container.classList.remove('d-none');
  if (digitSumBadge && digitSum.average_sum) {
    digitSumBadge.textContent = `แต้มรวมเฉลี่ย: ${digitSum.average_sum} (ช่วงปกติ: ${digitSum.expected_range || '20-34'})`;
  }

  target.innerHTML = breakdown.map(pos => {
    return `
      <div class="col-6 col-md-4 col-lg-2">
        <div class="p-3 rounded h-100" style="background: var(--bg-tertiary); border: 1px solid var(--border-color);">
          <div class="text-warning fw-bold small mb-2 text-center border-bottom border-dark pb-1">${pos.position_name}</div>
          <div class="d-flex flex-column gap-2">
            ${pos.top_digits.map((td, i) => `
              <div class="d-flex align-items-center justify-content-between">
                <span class="badge ${i === 0 ? 'bg-warning text-dark' : 'bg-dark border border-secondary'} rounded-circle" style="width: 24px; height: 24px; line-height: 16px;">${td.digit}</span>
                <div class="progress flex-grow-1 mx-2" style="height: 6px; background: rgba(255,255,255,0.08);">
                  <div class="progress-bar ${i === 0 ? 'bg-warning' : 'bg-info'}" style="width: ${td.probability}%;"></div>
                </div>
                <span class="small font-monospace text-muted">${td.probability}%</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Tab 4: Historical Results Search, Filters & Pagination
 */
function initHistoryTab() {
  const results = window.APP_DATA.results;
  const draws = results?.draws || results?.results || [];
  filteredHistoryDraws = [...draws];

  renderHistoryTable();

  // Search input
  const searchInput = document.getElementById('history-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim();
      filterHistory(q);
    });
  }

  // Pagination buttons
  const prevBtn = document.getElementById('history-prev-btn');
  const nextBtn = document.getElementById('history-next-btn');

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (historyCurrentPage > 1) {
        historyCurrentPage--;
        renderHistoryTable();
      }
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      const maxPages = Math.ceil(filteredHistoryDraws.length / ITEMS_PER_PAGE);
      if (historyCurrentPage < maxPages) {
        historyCurrentPage++;
        renderHistoryTable();
      }
    });
  }

  // Export CSV Button
  const exportBtn = document.getElementById('history-export-btn');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      downloadCSV(filteredHistoryDraws, `thai-lottery-results-${new Date().toISOString().split('T')[0]}.csv`);
    });
  }
}

function filterHistory(query) {
  const results = window.APP_DATA.results;
  const draws = results?.draws || results?.results || [];

  if (!query) {
    filteredHistoryDraws = [...draws];
  } else {
    filteredHistoryDraws = draws.filter(d => {
      const first = String(d.first_prize || d.first || '');
      const l2 = String(d.last_two || '');
      const f3 = (d.front_three || d.last_three_f || []).join(' ');
      const b3 = (d.back_three || d.last_three_b || []).join(' ');
      const dt = String(d.date || '') + ' ' + String(d.date_thai || '');

      return first.includes(query) ||
             l2.includes(query) ||
             f3.includes(query) ||
             b3.includes(query) ||
             dt.includes(query);
    });
  }

  historyCurrentPage = 1;
  renderHistoryTable();
}

function renderHistoryTable() {
  const tableBody = document.getElementById('history-table-body');
  const pageInfo = document.getElementById('history-page-info');
  const prevBtn = document.getElementById('history-prev-btn');
  const nextBtn = document.getElementById('history-next-btn');

  if (!tableBody) return;

  const total = filteredHistoryDraws.length;
  const maxPages = Math.max(1, Math.ceil(total / ITEMS_PER_PAGE));
  const startIdx = (historyCurrentPage - 1) * ITEMS_PER_PAGE;
  const endIdx = Math.min(startIdx + ITEMS_PER_PAGE, total);
  const pageItems = filteredHistoryDraws.slice(startIdx, endIdx);

  if (pageInfo) {
    pageInfo.textContent = `หน้า ${historyCurrentPage} / ${maxPages} (ทั้งหมด ${total.toLocaleString()} งวด)`;
  }
  if (prevBtn) prevBtn.disabled = historyCurrentPage <= 1;
  if (nextBtn) nextBtn.disabled = historyCurrentPage >= maxPages;

  if (pageItems.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">ไม่พบผลรางวัลที่ค้นหา</td></tr>';
    return;
  }

  tableBody.innerHTML = pageItems.map(d => {
    const f3 = (d.front_three || d.last_three_f || []).join(' , ') || '-';
    const b3 = (d.back_three || d.last_three_b || []).join(' , ') || '-';
    const first = d.first_prize || d.first || '-';
    const l2 = d.last_two || '-';

    return `
      <tr>
        <td class="fw-semibold text-light">${formatThaiDate(d.date)}</td>
        <td><span class="prize-number fs-6 text-warning">${first}</span></td>
        <td><span class="prize-number text-light">${f3}</span></td>
        <td><span class="prize-number text-light">${b3}</span></td>
        <td><span class="prize-number fs-6 text-info">${l2}</span></td>
      </tr>
    `;
  }).join('');
}
