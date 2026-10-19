/**
 * tabs.js — Tab Navigation and Filter Controls
 * Thai Lottery Analytics Dashboard
 */

'use strict';

let currentStatsPrize = 'last_two';
let currentPredPrize = 'last_two';

function initTabs() {
  // Listen for Bootstrap tab changes to trigger chart resizing
  const tabElements = document.querySelectorAll('button[data-bs-toggle="pill"]');
  tabElements.forEach(tabEl => {
    tabEl.addEventListener('shown.bs.tab', (event) => {
      const targetId = event.target.getAttribute('data-bs-target');
      
      // Allow DOM to update dimensions then resize charts
      setTimeout(() => {
        Object.values(ChartRegistry).forEach(chart => {
          try {
            chart.resize();
          } catch (e) {}
        });
      }, 50);

      // Lazy load tab specific views if necessary
      if (targetId === '#tab-stats') {
        updateStatsView(currentStatsPrize);
      } else if (targetId === '#tab-predictions') {
        updatePredictionsView(currentPredPrize);
      }
    });
  });

  // Tab 2: Statistics Sub-filter buttons
  const statsFilterBtns = document.querySelectorAll('.stats-filter-btn');
  statsFilterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      statsFilterBtns.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentStatsPrize = e.target.getAttribute('data-prize');
      updateStatsView(currentStatsPrize);
    });
  });

  // Tab 3: Predictions Sub-filter buttons
  const predFilterBtns = document.querySelectorAll('.pred-filter-btn');
  predFilterBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      predFilterBtns.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentPredPrize = e.target.getAttribute('data-prize');
      updatePredictionsView(currentPredPrize);
    });
  });
}

function updateStatsView(prizeType) {
  if (!window.APP_DATA || !window.APP_DATA.statistics) return;
  const stats = window.APP_DATA.statistics;

  // Initialize/Update stats charts
  if (typeof initFrequencyHeatmap === 'function') {
    initFrequencyHeatmap(stats, prizeType);
  }
  if (typeof initGapAnalysis === 'function') {
    initGapAnalysis(stats, prizeType);
  }
  if (typeof initPatternByMonth === 'function') {
    initPatternByMonth(stats, prizeType);
  }
  if (typeof initEvenOddChart === 'function') {
    initEvenOddChart(stats, prizeType);
  }
  if (typeof initPositionalChart === 'function') {
    initPositionalChart(stats, prizeType);
  }
}

function updatePredictionsView(prizeType) {
  if (!window.APP_DATA) return;
  const preds = window.APP_DATA.predictions;
  const backtest = window.APP_DATA.backtesting;

  // Render prediction tables for this prize type
  if (typeof renderPredictionsTables === 'function') {
    renderPredictionsTables(prizeType);
  }

  // Update ML charts
  if (typeof initAccuracyGauges === 'function' && backtest) {
    initAccuracyGauges(backtest, prizeType);
  }
  if (typeof initHistoricalAccuracyChart === 'function' && backtest) {
    initHistoricalAccuracyChart(backtest, prizeType);
  }
  if (typeof initEnsembleWeightsChart === 'function' && preds) {
    initEnsembleWeightsChart(preds, prizeType);
  }
}
