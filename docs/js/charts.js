/**
 * charts.js — All ECharts chart configurations and initialization
 * Thai Lottery Analytics Dashboard
 */

'use strict';

// ─── Chart Registry ─────────────────────────────────────────────────────────
const ChartRegistry = {};

const GOLD = '#f0b429';
const RED  = '#ef4444';
const BLUE = '#3b82f6';
const GREEN = '#22c55e';
const PURPLE = '#a855f7';

const MODEL_COLORS = {
  frequency:   '#f0b429',
  markov:      '#06b6d4',
  arima:       '#3b82f6',
  prophet:     '#22c55e',
  lstm:        '#a855f7',
  monte_carlo: '#ec4899'
};

const CHART_BG = '#161b22';

function getOrInitChart(id) {
  if (ChartRegistry[id]) {
    ChartRegistry[id].dispose();
    delete ChartRegistry[id];
  }
  const el = document.getElementById(id);
  if (!el) return null;
  const chart = echarts.init(el, 'dark');
  ChartRegistry[id] = chart;
  return chart;
}

// Resize all charts on window resize
window.addEventListener('resize', () => {
  Object.values(ChartRegistry).forEach(c => {
    try { c.resize(); } catch (e) {}
  });
});

// Helper to normalize prizeType key
function normalizePrizeKey(pt) {
  if (pt === 'last_three_b' || pt === 'back_three') return { standard: 'back_three', alt: 'last_three_b' };
  if (pt === 'last_three_f' || pt === 'front_three') return { standard: 'front_three', alt: 'last_three_f' };
  if (pt === 'first' || pt === 'first_prize') return { standard: 'first_prize', alt: 'first' };
  return { standard: 'last_two', alt: 'last_two' };
}

// ─── Hot/Cold Horizontal Bar Chart ──────────────────────────────────────────
function initHotColdChart(data) {
  const chart = getOrInitChart('chart-hotcold');
  if (!chart) return;

  const hotNums  = (data?.hot_cold?.last_two?.hot  || data?.prize_types?.last_two?.hot_cold?.hot || []).slice(0, 10);
  const coldNums = (data?.hot_cold?.last_two?.cold || data?.prize_types?.last_two?.hot_cold?.cold || []).slice(0, 10);

  const hotLabels  = hotNums.map(n => n.number);
  const hotValues  = hotNums.map(n => n.count);
  const coldLabels = coldNums.map(n => n.number);
  const coldValues = coldNums.map(n => n.count);

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: {
      data: ['เลขร้อน (Hot)', 'เลขเย็น (Cold)'],
      textStyle: { color: '#e6edf3' },
      top: 8
    },
    grid: [
      { left: 60, right: '52%', top: 40, bottom: 30 },
      { left: '52%', right: 20, top: 40, bottom: 30 }
    ],
    xAxis: [
      {
        gridIndex: 0, type: 'value', inverse: true,
        axisLabel: { color: '#8b949e' },
        splitLine: { lineStyle: { color: '#30363d' } }
      },
      {
        gridIndex: 1, type: 'value',
        axisLabel: { color: '#8b949e' },
        splitLine: { lineStyle: { color: '#30363d' } }
      }
    ],
    yAxis: [
      {
        gridIndex: 0, type: 'category', data: hotLabels,
        inverse: false,
        axisLabel: { color: '#e6edf3', fontFamily: 'monospace', fontWeight: 'bold' }
      },
      {
        gridIndex: 1, type: 'category', data: coldLabels,
        axisLabel: { color: '#e6edf3', fontFamily: 'monospace', fontWeight: 'bold' },
        position: 'right'
      }
    ],
    series: [
      {
        name: 'เลขร้อน (Hot)',
        type: 'bar',
        xAxisIndex: 0, yAxisIndex: 0,
        data: hotValues,
        itemStyle: { color: RED, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'insideRight', color: '#fff', fontWeight: 'bold' }
      },
      {
        name: 'เลขเย็น (Cold)',
        type: 'bar',
        xAxisIndex: 1, yAxisIndex: 1,
        data: coldValues,
        itemStyle: { color: BLUE, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'insideLeft', color: '#fff', fontWeight: 'bold' }
      }
    ]
  };
  chart.setOption(option);
}

// ─── Frequency Heatmap ───────────────────────────────────────────────────────
function initFrequencyHeatmap(data, prizeType) {
  const chart = getOrInitChart('chart-heatmap');
  if (!chart) return;

  const { standard, alt } = normalizePrizeKey(prizeType);

  const digitPos = data?.prize_types?.[standard]?.digit_frequency ||
                   data?.prize_types?.[alt]?.digit_frequency ||
                   data?.digit_position?.[standard] ||
                   data?.digit_position?.[alt];

  if (!digitPos) { chart.clear(); return; }

  const positions = Object.keys(digitPos);
  const digits = ['0','1','2','3','4','5','6','7','8','9'];
  const heatData = [];
  let maxVal = 0;

  positions.forEach((pos, posIdx) => {
    digits.forEach((d, dIdx) => {
      const v = digitPos[pos]?.[d] || 0;
      if (v > maxVal) maxVal = v;
      heatData.push([dIdx, posIdx, v]);
    });
  });

  const getPositionLabel = (pos, totalLen) => {
    const numPos = Number(pos);
    if (isNaN(numPos)) {
      const dict = {
        units: 'หลักหน่วย', tens: 'หลักสิบ', hundreds: 'หลักร้อย',
        thousands: 'หลักพัน', ten_thousands: 'หลักหมื่น', hundred_thousands: 'หลักแสน'
      };
      return dict[pos] || pos;
    }
    if (totalLen === 6) {
      return ['หลักแสน', 'หลักหมื่น', 'หลักพัน', 'หลักร้อย', 'หลักสิบ', 'หลักหน่วย'][numPos] || `หลักที่ ${numPos + 1}`;
    }
    if (totalLen === 3) {
      return ['หลักร้อย', 'หลักสิบ', 'หลักหน่วย'][numPos] || `หลักที่ ${numPos + 1}`;
    }
    return ['หลักสิบ', 'หลักหน่วย'][numPos] || `หลักที่ ${numPos + 1}`;
  };

  const labels = positions.map(p => getPositionLabel(p, positions.length));

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: p => `ตำแหน่ง: ${labels[p.data[1]]}<br>ตัวเลข: ${digits[p.data[0]]}<br>ความถี่: ${p.data[2]} ครั้ง`
    },
    grid: { left: 90, right: 20, top: 20, bottom: 60 },
    xAxis: {
      type: 'category', data: digits,
      name: 'ตัวเลข (0-9)', nameLocation: 'center', nameGap: 30,
      axisLabel: { color: '#e6edf3', fontWeight: 'bold' },
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#e6edf3' },
      splitArea: { show: true }
    },
    visualMap: {
      min: 0, max: maxVal || 10,
      calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#0d1117', '#1d4e89', GOLD] },
      textStyle: { color: '#e6edf3' }
    },
    series: [{
      type: 'heatmap', data: heatData,
      label: { show: true, color: '#fff', fontSize: 10 },
      emphasis: { itemStyle: { shadowBlur: 10 } }
    }]
  };
  chart.setOption(option);
}

// ─── Gap Analysis Bar Chart ──────────────────────────────────────────────────
function initGapAnalysis(data, prizeType) {
  const chart = getOrInitChart('chart-gap');
  if (!chart) return;

  const { standard, alt } = normalizePrizeKey(prizeType);

  const gapData = data?.prize_types?.[standard]?.gap_analysis ||
                  data?.prize_types?.[alt]?.gap_analysis ||
                  data?.gap_analysis?.[standard] ||
                  data?.gap_analysis?.[alt];

  if (!gapData) { chart.clear(); return; }

  const entries = Object.entries(gapData).sort((a, b) => Number(b[1]) - Number(a[1])).slice(0, 30);
  const labels = entries.map(e => e[0]);
  const values = entries.map(e => e[1]);

  const maxGap = Math.max(...values, 1);
  const colors = values.map(v => {
    const ratio = v / maxGap;
    if (ratio > 0.8) return RED;
    if (ratio > 0.5) return '#f97316';
    if (ratio < 0.2) return BLUE;
    return GOLD;
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: p => `เลข ${p[0].name}<br>ไม่ออกมาแล้ว: ${p[0].value} งวด`
    },
    grid: { left: 50, right: 20, top: 20, bottom: 80 },
    xAxis: {
      type: 'category', data: labels,
      axisLabel: {
        color: '#e6edf3', fontFamily: 'monospace', fontWeight: 'bold',
        rotate: 45, fontSize: 10
      }
    },
    yAxis: {
      type: 'value', name: 'จำนวนงวดที่ไม่ออก',
      nameTextStyle: { color: '#8b949e' },
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#30363d' } }
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [3,3,0,0] } })),
      label: { show: false }
    }]
  };
  chart.setOption(option);
}

// ─── Pattern by Month Line Chart ─────────────────────────────────────────────
function initPatternByMonth(data, prizeType) {
  const chart = getOrInitChart('chart-month');
  if (!chart) return;

  const { standard, alt } = normalizePrizeKey(prizeType);

  const monthData = data?.prize_types?.[standard]?.monthly_pattern ||
                    data?.prize_types?.[alt]?.monthly_pattern ||
                    data?.pattern_by_month?.[standard] ||
                    data?.pattern_by_month?.[alt];

  if (!monthData) { chart.clear(); return; }

  const months = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.'];
  const values = months.map((_, i) => monthData[String(i + 1)] || 0);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: p => `${p[0].name}<br>ความถี่เฉลี่ย: ${Number(p[0].value).toFixed(2)}`
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category', data: months,
      axisLabel: { color: '#e6edf3' },
      splitLine: { lineStyle: { color: '#30363d' } }
    },
    yAxis: {
      type: 'value', name: 'ความถี่เฉลี่ย',
      nameTextStyle: { color: '#8b949e' },
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#30363d' } }
    },
    series: [{
      type: 'line', data: values, smooth: true,
      lineStyle: { color: GOLD, width: 2 },
      itemStyle: { color: GOLD },
      areaStyle: {
        color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(240,180,41,0.3)' }, { offset: 1, color: 'rgba(240,180,41,0.02)' }] }
      },
      symbol: 'circle', symbolSize: 6
    }]
  };
  chart.setOption(option);
}

// ─── Even/Odd Donut ──────────────────────────────────────────────────────────
function initEvenOddChart(data, prizeType) {
  const chartEO = getOrInitChart('chart-evenodd');
  const chartHL = getOrInitChart('chart-highlow');

  const { standard, alt } = normalizePrizeKey(prizeType);

  const eo = data?.prize_types?.[standard]?.even_odd ||
             data?.prize_types?.[alt]?.even_odd ||
             data?.even_odd?.[standard] ||
             data?.even_odd?.[alt];

  const hl = data?.prize_types?.[standard]?.high_low ||
             data?.prize_types?.[alt]?.high_low ||
             data?.high_low?.[standard] ||
             data?.high_low?.[alt];

  if (chartEO) {
    const eoOption = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 10, textStyle: { color: '#e6edf3' } },
      series: [{
        type: 'pie', radius: ['40%', '70%'], center: ['40%', '50%'],
        label: { color: '#e6edf3' },
        data: [
          { value: eo?.even || 50, name: 'คู่ (Even)', itemStyle: { color: GOLD } },
          { value: eo?.odd  || 50, name: 'คี่ (Odd)',  itemStyle: { color: BLUE } }
        ]
      }]
    };
    chartEO.setOption(eoOption);
  }

  if (chartHL) {
    const hlOption = {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 10, textStyle: { color: '#e6edf3' } },
      series: [{
        type: 'pie', radius: ['40%', '70%'], center: ['40%', '50%'],
        label: { color: '#e6edf3' },
        data: [
          { value: hl?.high || 50, name: 'สูง (High)', itemStyle: { color: RED } },
          { value: hl?.low  || 50, name: 'ต่ำ (Low)',  itemStyle: { color: GREEN } }
        ]
      }]
    };
    chartHL.setOption(hlOption);
  }
}

// ─── Accuracy Gauges ─────────────────────────────────────────────────────────
function initAccuracyGauges(backtestData, prizeType) {
  const models = ['frequency', 'markov', 'arima', 'prophet', 'lstm', 'monte_carlo'];
  const { standard, alt } = normalizePrizeKey(prizeType);

  models.forEach(model => {
    const chart = getOrInitChart(`chart-gauge-${model}`);
    if (!chart) return;

    const accDict = backtestData?.models?.[model]?.overall_accuracy || {};
    const accuracy = accDict[standard] ?? accDict[alt] ?? accDict['last_two'] ?? 0.20;
    const pct = Math.round(accuracy * 100);
    const color = MODEL_COLORS[model] || GOLD;

    const option = {
      backgroundColor: 'transparent',
      series: [{
        type: 'gauge',
        startAngle: 200, endAngle: -20,
        min: 0, max: 100,
        pointer: { show: false },
        progress: {
          show: true, overlap: false, roundCap: true,
          itemStyle: { color }
        },
        axisLine: {
          lineStyle: { width: 10, color: [[1, '#30363d']] }
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true, fontSize: 16, fontWeight: 'bold',
          color, formatter: '{value}%', offsetCenter: [0, '15%']
        },
        title: { show: false },
        data: [{ value: pct }]
      }]
    };
    chart.setOption(option);
  });
}

// ─── Model Comparison Bar ─────────────────────────────────────────────────────
function initModelComparisonChart(predData, prizeType) {
  const chart = getOrInitChart('chart-model-compare');
  if (!chart) return;

  const models = ['frequency', 'markov', 'arima', 'prophet', 'lstm', 'monte_carlo'];
  const modelNames = {
    frequency: 'Frequency',
    markov: 'Markov Chain',
    arima: 'ARIMA',
    prophet: 'Prophet',
    lstm: 'LSTM',
    monte_carlo: 'Monte Carlo'
  };
  const { standard, alt } = normalizePrizeKey(prizeType);

  const allNums = new Set();
  models.forEach(m => {
    const list = predData?.prize_types?.[standard]?.models?.[m]?.top10 ||
                 predData?.prize_types?.[alt]?.models?.[m]?.top10 ||
                 predData?.models?.[m]?.predictions?.[standard] ||
                 predData?.models?.[m]?.predictions?.[alt] || [];
    list.slice(0, 5).forEach(p => allNums.add(p.number));
  });

  const nums = [...allNums].slice(0, 10);

  const series = models.map(m => {
    const preds = predData?.prize_types?.[standard]?.models?.[m]?.top10 ||
                  predData?.prize_types?.[alt]?.models?.[m]?.top10 ||
                  predData?.models?.[m]?.predictions?.[standard] ||
                  predData?.models?.[m]?.predictions?.[alt] || [];

    return {
      name: modelNames[m],
      type: 'bar',
      barGap: '5%',
      itemStyle: { color: MODEL_COLORS[m], borderRadius: [3,3,0,0] },
      data: nums.map(n => {
        const found = preds.find(p => p.number === n);
        return found ? Math.round(found.score * 100) : 0;
      })
    };
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', formatter: p => p.map(s => `${s.seriesName}: ${s.value}%`).join('<br>') },
    legend: {
      data: Object.values(modelNames),
      textStyle: { color: '#e6edf3' }, top: 8
    },
    grid: { left: 50, right: 20, top: 50, bottom: 50 },
    xAxis: {
      type: 'category', data: nums,
      axisLabel: { color: '#e6edf3', fontFamily: 'monospace', fontWeight: 'bold' }
    },
    yAxis: {
      type: 'value', name: 'คะแนน (%)', max: 100,
      nameTextStyle: { color: '#8b949e' },
      axisLabel: { color: '#8b949e', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#30363d' } }
    },
    series
  };
  chart.setOption(option);
}

// ─── Historical Accuracy Line Chart ─────────────────────────────────────────
function initHistoricalAccuracyChart(backtestData, prizeType) {
  const chart = getOrInitChart('chart-hist-accuracy');
  if (!chart) return;

  const models = ['frequency', 'markov', 'arima', 'prophet', 'lstm', 'monte_carlo'];
  const modelNames = {
    frequency: 'Frequency',
    markov: 'Markov Chain',
    arima: 'ARIMA',
    prophet: 'Prophet',
    lstm: 'LSTM',
    monte_carlo: 'Monte Carlo'
  };
  const { standard } = normalizePrizeKey(prizeType);

  const hitKey = standard === 'first_prize' ? 'first_prize_hit'
               : standard === 'last_two' ? 'last_two_hit'
               : standard === 'back_three' ? 'last_three_b_hit'
               : 'last_three_f_hit';

  let allDates = new Set();
  models.forEach(m => {
    (backtestData?.models?.[m]?.history || []).forEach(h => allDates.add(h.draw));
  });
  const dates = [...allDates].sort();

  const series = models.map(m => {
    const history = backtestData?.models?.[m]?.history || [];
    // Rolling 3-draw accuracy
    const values = dates.map((d, i) => {
      const windowSlice = dates.slice(Math.max(0, i - 2), i + 1);
      const hits = windowSlice.filter(wd => {
        const h = history.find(x => x.draw === wd);
        return h && (h[hitKey] ?? h['last_two_hit']);
      }).length;
      return Math.round((hits / windowSlice.length) * 100);
    });
    return {
      name: modelNames[m],
      type: 'line', smooth: true,
      lineStyle: { color: MODEL_COLORS[m], width: 2 },
      itemStyle: { color: MODEL_COLORS[m] },
      data: values, symbol: 'circle', symbolSize: 5
    };
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: { data: Object.values(modelNames), textStyle: { color: '#e6edf3' }, top: 8 },
    grid: { left: 50, right: 20, top: 50, bottom: 60 },
    xAxis: {
      type: 'category',
      data: dates.map(d => formatThaiDateShort(d)),
      axisLabel: { color: '#8b949e', rotate: 30, fontSize: 10 }
    },
    yAxis: {
      type: 'value', name: 'ความแม่นยำ (%)', min: 0, max: 100,
      nameTextStyle: { color: '#8b949e' },
      axisLabel: { color: '#8b949e', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#30363d' } }
    },
    series
  };
  chart.setOption(option);
}

// ─── Ensemble Weights Pie ─────────────────────────────────────────────────────
function initEnsembleWeightsChart(predData, prizeType) {
  const chart = getOrInitChart('chart-weights');
  if (!chart) return;

  const models = ['frequency', 'markov', 'arima', 'prophet', 'lstm', 'monte_carlo'];
  const modelNames = {
    frequency: 'Frequency',
    markov: 'Markov Chain',
    arima: 'ARIMA',
    prophet: 'Prophet',
    lstm: 'LSTM',
    monte_carlo: 'Monte Carlo'
  };
  const { standard, alt } = normalizePrizeKey(prizeType || 'last_two');

  const weights = predData?.prize_types?.[standard]?.ensemble?.weights ||
                  predData?.prize_types?.[alt]?.ensemble?.weights ||
                  predData?.ensemble?.weights || {};

  const pieData = models.map(m => {
    const w = weights[m] ?? predData?.models?.[m]?.weight ?? 0.16;
    return {
      name: modelNames[m],
      value: Math.round(w * 100),
      itemStyle: { color: MODEL_COLORS[m] }
    };
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
    legend: { orient: 'vertical', right: 10, textStyle: { color: '#e6edf3' } },
    series: [{
      type: 'pie', radius: ['35%', '65%'], center: ['40%', '50%'],
      label: { color: '#e6edf3', formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: '#8b949e' } },
      data: pieData
    }]
  };
  chart.setOption(option);
}

// ─── Markov State Transition Heatmap (Tab 2) ───────────────────────────────────
function initMarkovTransitionHeatmap(stats) {
  const chart = getOrInitChart('chart-markov-transition');
  if (!chart) return;

  const trans = stats?.markov_transitions || {};
  const matrix = trans.matrix_10x10 || [];
  const labels = trans.labels || ['หมวด 00', 'หมวด 10', 'หมวด 20', 'หมวด 30', 'หมวด 40', 'หมวด 50', 'หมวด 60', 'หมวด 70', 'หมวด 80', 'หมวด 90'];

  if (!matrix.length) {
    chart.clear();
    return;
  }

  const heatData = [];
  let maxVal = 0;
  for (let r = 0; r < matrix.length; r++) {
    for (let c = 0; c < matrix[r].length; c++) {
      const val = matrix[r][c];
      if (val > maxVal) maxVal = val;
      heatData.push([c, r, val]);
    }
  }

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: p => `จาก: ${labels[p.data[1]]}<br>ไปสู่: ${labels[p.data[0]]}<br>ความน่าจะเป็น: ${(p.data[2] * 100).toFixed(1)}%`
    },
    grid: { left: 80, right: 30, top: 30, bottom: 60 },
    xAxis: {
      type: 'category', data: labels,
      name: 'สถานะงวดถัดไป', nameLocation: 'center', nameGap: 35,
      axisLabel: { color: '#e6edf3', fontSize: 10, rotate: 30 }
    },
    yAxis: {
      type: 'category', data: labels,
      name: 'สถานะงวดก่อนหน้า',
      axisLabel: { color: '#e6edf3', fontSize: 10 }
    },
    visualMap: {
      min: 0, max: maxVal || 0.25,
      calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#0d1117', '#0891b2', '#f0b429'] },
      textStyle: { color: '#e6edf3' },
      formatter: v => `${(v * 100).toFixed(0)}%`
    },
    series: [{
      type: 'heatmap', data: heatData,
      label: {
        show: true,
        formatter: p => `${(p.data[2] * 100).toFixed(0)}%`,
        color: '#fff', fontSize: 10
      }
    }]
  };
  chart.setOption(option);
}
