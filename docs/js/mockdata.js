/**
 * mockdata.js — Realistic sample data for Thai Lottery Analytics
 * Used as fallback when real JSON data files are unavailable.
 */

'use strict';

const MOCK_RESULTS = {
  last_updated: "2026-10-16",
  total_draws: 10,
  draws: [
    {
      date: "2026-10-16",
      draw_id: "2026-10-16",
      first: "543219",
      last_three_f: ["123", "456"],
      last_three_b: ["789", "012"],
      last_two: "19"
    },
    {
      date: "2026-10-01",
      draw_id: "2026-10-01",
      first: "287654",
      last_three_f: ["234", "567"],
      last_three_b: ["890", "123"],
      last_two: "54"
    },
    {
      date: "2026-09-16",
      draw_id: "2026-09-16",
      first: "761234",
      last_three_f: ["345", "678"],
      last_three_b: ["901", "234"],
      last_two: "34"
    },
    {
      date: "2026-09-01",
      draw_id: "2026-09-01",
      first: "439876",
      last_three_f: ["456", "789"],
      last_three_b: ["012", "345"],
      last_two: "76"
    },
    {
      date: "2026-08-16",
      draw_id: "2026-08-16",
      first: "158423",
      last_three_f: ["567", "890"],
      last_three_b: ["123", "456"],
      last_two: "23"
    },
    {
      date: "2026-08-01",
      draw_id: "2026-08-01",
      first: "672189",
      last_three_f: ["678", "901"],
      last_three_b: ["234", "567"],
      last_two: "89"
    },
    {
      date: "2026-07-16",
      draw_id: "2026-07-16",
      first: "304567",
      last_three_f: ["789", "012"],
      last_three_b: ["345", "678"],
      last_two: "67"
    },
    {
      date: "2026-07-01",
      draw_id: "2026-07-01",
      first: "891234",
      last_three_f: ["890", "123"],
      last_three_b: ["456", "789"],
      last_two: "34"
    },
    {
      date: "2026-06-16",
      draw_id: "2026-06-16",
      first: "526789",
      last_three_f: ["901", "234"],
      last_three_b: ["567", "890"],
      last_two: "89"
    },
    {
      date: "2026-06-01",
      draw_id: "2026-06-01",
      first: "148963",
      last_three_f: ["012", "345"],
      last_three_b: ["678", "901"],
      last_two: "63"
    }
  ]
};

const MOCK_STATISTICS = {
  generated_at: "2026-10-16",
  prize_types: ["first", "last_three_f", "last_three_b", "last_two"],
  summary: {
    total_draws: 10,
    date_range_years: 0.42,
    last_updated: "2026-10-16",
    next_draw: "2026-11-01"
  },
  frequency: {
    last_two: {
      "00": 1, "01": 0, "02": 2, "03": 1, "04": 3, "05": 1, "06": 0, "07": 2,
      "08": 1, "09": 0, "10": 1, "11": 2, "12": 0, "13": 1, "14": 2, "15": 3,
      "16": 1, "17": 0, "18": 2, "19": 3, "20": 1, "21": 0, "22": 2, "23": 2,
      "24": 1, "25": 0, "26": 3, "27": 1, "28": 2, "29": 0, "30": 1, "31": 2,
      "32": 0, "33": 1, "34": 4, "35": 2, "36": 1, "37": 0, "38": 2, "39": 1,
      "40": 0, "41": 2, "42": 1, "43": 3, "44": 1, "45": 0, "46": 2, "47": 1,
      "48": 3, "49": 0, "50": 1, "51": 2, "52": 0, "53": 1, "54": 3, "55": 2,
      "56": 1, "57": 0, "58": 2, "59": 1, "60": 3, "61": 0, "62": 2, "63": 2,
      "64": 1, "65": 0, "66": 2, "67": 3, "68": 1, "69": 0, "70": 2, "71": 1,
      "72": 3, "73": 0, "74": 2, "75": 1, "76": 2, "77": 0, "78": 1, "79": 2,
      "80": 0, "81": 2, "82": 1, "83": 3, "84": 0, "85": 2, "86": 1, "87": 0,
      "88": 2, "89": 3, "90": 1, "91": 0, "92": 2, "93": 1, "94": 3, "95": 0,
      "96": 2, "97": 1, "98": 0, "99": 2
    },
    last_three_b: {
      "012": 2, "123": 2, "234": 2, "345": 2, "456": 2, "567": 2, "678": 2, "789": 2, "890": 2, "901": 2
    },
    last_three_f: {
      "012": 1, "123": 2, "234": 1, "345": 2, "456": 2, "567": 1, "678": 2, "789": 2, "890": 1, "901": 2
    },
    first: {
      "543219": 1, "287654": 1, "761234": 1, "439876": 1, "158423": 1,
      "672189": 1, "304567": 1, "891234": 1, "526789": 1, "148963": 1
    }
  },
  hot_cold: {
    last_two: {
      hot: [
        {"number": "34", "count": 4},
        {"number": "19", "count": 3},
        {"number": "54", "count": 3},
        {"number": "43", "count": 3},
        {"number": "04", "count": 3},
        {"number": "26", "count": 3},
        {"number": "15", "count": 3},
        {"number": "48", "count": 3},
        {"number": "60", "count": 3},
        {"number": "67", "count": 3}
      ],
      cold: [
        {"number": "01", "count": 0},
        {"number": "06", "count": 0},
        {"number": "09", "count": 0},
        {"number": "12", "count": 0},
        {"number": "17", "count": 0},
        {"number": "21", "count": 0},
        {"number": "25", "count": 0},
        {"number": "29", "count": 0},
        {"number": "32", "count": 0},
        {"number": "37", "count": 0}
      ]
    }
  },
  gap_analysis: {
    last_two: {
      "00": 8, "01": 10, "02": 5, "03": 7, "04": 2, "05": 9, "06": 10, "07": 4,
      "08": 6, "09": 10, "10": 7, "11": 3, "12": 10, "13": 8, "14": 4, "15": 2,
      "16": 6, "17": 10, "18": 5, "19": 1, "20": 7, "21": 10, "22": 4, "23": 3,
      "24": 8, "25": 10, "26": 2, "27": 6, "28": 4, "29": 10, "30": 9, "31": 5,
      "32": 10, "33": 7, "34": 1, "35": 3, "36": 8, "37": 10, "38": 5, "39": 9,
      "40": 10, "41": 4, "42": 7, "43": 2, "44": 8, "45": 10, "46": 5, "47": 9,
      "48": 2, "49": 10, "50": 8, "51": 5, "52": 10, "53": 7, "54": 1, "55": 4,
      "56": 8, "57": 10, "58": 5, "59": 9, "60": 2, "61": 10, "62": 6, "63": 3,
      "64": 8, "65": 10, "66": 5, "67": 2, "68": 9, "69": 10, "70": 6, "71": 8,
      "72": 3, "73": 10, "74": 5, "75": 9, "76": 4, "77": 10, "78": 8, "79": 5,
      "80": 10, "81": 6, "82": 9, "83": 3, "84": 10, "85": 7, "86": 9, "87": 10,
      "88": 5, "89": 2, "90": 8, "91": 10, "92": 6, "93": 9, "94": 3, "95": 10,
      "96": 7, "97": 9, "98": 10, "99": 6
    }
  },
  pattern_by_month: {
    last_two: {
      "1": 1.8, "2": 2.1, "3": 1.9, "4": 2.3, "5": 2.0,
      "6": 1.7, "7": 2.2, "8": 1.9, "9": 2.1, "10": 2.0,
      "11": 1.8, "12": 2.3
    }
  },
  even_odd: {
    last_two: {"even": 52, "odd": 48},
    last_three_f: {"even": 49, "odd": 51},
    last_three_b: {"even": 51, "odd": 49},
    first: {"even": 50, "odd": 50}
  },
  high_low: {
    last_two: {"high": 47, "low": 53},
    last_three_f: {"high": 52, "low": 48},
    last_three_b: {"high": 48, "low": 52},
    first: {"high": 51, "low": 49}
  },
  digit_position: {
    last_two: {
      "tens": {"0":8,"1":12,"2":11,"3":9,"4":10,"5":13,"6":8,"7":9,"8":10,"9":10},
      "units": {"0":9,"1":11,"2":10,"3":12,"4":8,"5":9,"6":11,"7":10,"8":10,"9":10}
    },
    last_three_b: {
      "hundreds": {"0":3,"1":4,"2":3,"3":3,"4":3,"5":3,"6":3,"7":3,"8":3,"9":3},
      "tens": {"0":3,"1":3,"2":3,"3":3,"4":3,"5":3,"6":3,"7":3,"8":4,"9":3},
      "units": {"0":3,"1":3,"2":4,"3":3,"4":3,"5":3,"6":3,"7":3,"8":3,"9":3}
    }
  }
};

const MOCK_PREDICTIONS = {
  generated_at: "2026-10-16",
  next_draw_date: "2026-11-01",
  models: {
    frequency: {
      name: "Frequency Analysis",
      name_th: "การวิเคราะห์ความถี่",
      weight: 0.25,
      predictions: {
        last_two: [
          {"number": "34", "score": 0.87, "rank": 1},
          {"number": "67", "score": 0.82, "rank": 2},
          {"number": "19", "score": 0.78, "rank": 3},
          {"number": "54", "score": 0.74, "rank": 4},
          {"number": "43", "score": 0.71, "rank": 5},
          {"number": "89", "score": 0.69, "rank": 6},
          {"number": "26", "score": 0.65, "rank": 7},
          {"number": "72", "score": 0.61, "rank": 8},
          {"number": "15", "score": 0.58, "rank": 9},
          {"number": "60", "score": 0.55, "rank": 10}
        ],
        last_three_b: [
          {"number": "234", "score": 0.81, "rank": 1},
          {"number": "567", "score": 0.76, "rank": 2},
          {"number": "123", "score": 0.72, "rank": 3},
          {"number": "890", "score": 0.68, "rank": 4},
          {"number": "456", "score": 0.64, "rank": 5}
        ],
        last_three_f: [
          {"number": "345", "score": 0.79, "rank": 1},
          {"number": "678", "score": 0.74, "rank": 2},
          {"number": "789", "score": 0.70, "rank": 3},
          {"number": "456", "score": 0.66, "rank": 4},
          {"number": "901", "score": 0.62, "rank": 5}
        ]
      }
    },
    arima: {
      name: "ARIMA",
      name_th: "ARIMA",
      weight: 0.25,
      predictions: {
        last_two: [
          {"number": "48", "score": 0.84, "rank": 1},
          {"number": "23", "score": 0.79, "rank": 2},
          {"number": "76", "score": 0.75, "rank": 3},
          {"number": "34", "score": 0.71, "rank": 4},
          {"number": "89", "score": 0.68, "rank": 5},
          {"number": "12", "score": 0.63, "rank": 6},
          {"number": "56", "score": 0.59, "rank": 7},
          {"number": "67", "score": 0.55, "rank": 8},
          {"number": "04", "score": 0.52, "rank": 9},
          {"number": "91", "score": 0.48, "rank": 10}
        ],
        last_three_b: [
          {"number": "789", "score": 0.78, "rank": 1},
          {"number": "012", "score": 0.73, "rank": 2},
          {"number": "345", "score": 0.69, "rank": 3},
          {"number": "678", "score": 0.65, "rank": 4},
          {"number": "901", "score": 0.61, "rank": 5}
        ],
        last_three_f: [
          {"number": "012", "score": 0.76, "rank": 1},
          {"number": "234", "score": 0.71, "rank": 2},
          {"number": "567", "score": 0.67, "rank": 3},
          {"number": "890", "score": 0.63, "rank": 4},
          {"number": "123", "score": 0.59, "rank": 5}
        ]
      }
    },
    prophet: {
      name: "Prophet",
      name_th: "Prophet",
      weight: 0.25,
      predictions: {
        last_two: [
          {"number": "19", "score": 0.91, "rank": 1},
          {"number": "34", "score": 0.86, "rank": 2},
          {"number": "60", "score": 0.81, "rank": 3},
          {"number": "43", "score": 0.76, "rank": 4},
          {"number": "72", "score": 0.72, "rank": 5},
          {"number": "26", "score": 0.67, "rank": 6},
          {"number": "89", "score": 0.63, "rank": 7},
          {"number": "15", "score": 0.59, "rank": 8},
          {"number": "54", "score": 0.55, "rank": 9},
          {"number": "48", "score": 0.51, "rank": 10}
        ],
        last_three_b: [
          {"number": "456", "score": 0.83, "rank": 1},
          {"number": "123", "score": 0.78, "rank": 2},
          {"number": "789", "score": 0.74, "rank": 3},
          {"number": "234", "score": 0.70, "rank": 4},
          {"number": "567", "score": 0.66, "rank": 5}
        ],
        last_three_f: [
          {"number": "678", "score": 0.80, "rank": 1},
          {"number": "901", "score": 0.75, "rank": 2},
          {"number": "345", "score": 0.71, "rank": 3},
          {"number": "012", "score": 0.67, "rank": 4},
          {"number": "789", "score": 0.63, "rank": 5}
        ]
      }
    },
    lstm: {
      name: "LSTM",
      name_th: "LSTM (Deep Learning)",
      weight: 0.25,
      predictions: {
        last_two: [
          {"number": "67", "score": 0.88, "rank": 1},
          {"number": "34", "score": 0.83, "rank": 2},
          {"number": "89", "score": 0.79, "rank": 3},
          {"number": "19", "score": 0.74, "rank": 4},
          {"number": "54", "score": 0.70, "rank": 5},
          {"number": "43", "score": 0.66, "rank": 6},
          {"number": "26", "score": 0.62, "rank": 7},
          {"number": "72", "score": 0.58, "rank": 8},
          {"number": "48", "score": 0.54, "rank": 9},
          {"number": "60", "score": 0.50, "rank": 10}
        ],
        last_three_b: [
          {"number": "890", "score": 0.85, "rank": 1},
          {"number": "234", "score": 0.80, "rank": 2},
          {"number": "567", "score": 0.76, "rank": 3},
          {"number": "901", "score": 0.72, "rank": 4},
          {"number": "123", "score": 0.68, "rank": 5}
        ],
        last_three_f: [
          {"number": "789", "score": 0.82, "rank": 1},
          {"number": "456", "score": 0.77, "rank": 2},
          {"number": "123", "score": 0.73, "rank": 3},
          {"number": "678", "score": 0.69, "rank": 4},
          {"number": "345", "score": 0.65, "rank": 5}
        ]
      }
    }
  },
  ensemble: {
    last_two: [
      {"number": "34", "score": 0.917, "rank": 1, "model_votes": ["frequency","arima","prophet","lstm"]},
      {"number": "19", "score": 0.876, "rank": 2, "model_votes": ["frequency","prophet","lstm"]},
      {"number": "67", "score": 0.852, "rank": 3, "model_votes": ["frequency","lstm"]},
      {"number": "89", "score": 0.798, "rank": 4, "model_votes": ["arima","lstm"]},
      {"number": "54", "score": 0.764, "rank": 5, "model_votes": ["frequency","lstm"]},
      {"number": "43", "score": 0.731, "rank": 6, "model_votes": ["frequency","prophet"]},
      {"number": "48", "score": 0.712, "rank": 7, "model_votes": ["arima","lstm"]},
      {"number": "72", "score": 0.695, "rank": 8, "model_votes": ["frequency","prophet"]},
      {"number": "26", "score": 0.678, "rank": 9, "model_votes": ["frequency","prophet"]},
      {"number": "60", "score": 0.654, "rank": 10, "model_votes": ["frequency","prophet"]}
    ],
    last_three_b: [
      {"number": "234", "score": 0.889, "rank": 1, "model_votes": ["frequency","prophet","lstm"]},
      {"number": "789", "score": 0.851, "rank": 2, "model_votes": ["arima","prophet"]},
      {"number": "567", "score": 0.823, "rank": 3, "model_votes": ["frequency","arima","lstm"]},
      {"number": "456", "score": 0.794, "rank": 4, "model_votes": ["frequency","prophet"]},
      {"number": "123", "score": 0.762, "rank": 5, "model_votes": ["frequency","prophet","lstm"]}
    ],
    last_three_f: [
      {"number": "678", "score": 0.882, "rank": 1, "model_votes": ["frequency","prophet","lstm"]},
      {"number": "345", "score": 0.847, "rank": 2, "model_votes": ["frequency","arima","prophet","lstm"]},
      {"number": "789", "score": 0.815, "rank": 3, "model_votes": ["frequency","lstm"]},
      {"number": "901", "score": 0.783, "rank": 4, "model_votes": ["arima","prophet"]},
      {"number": "012", "score": 0.751, "rank": 5, "model_votes": ["arima"]}
    ]
  }
};

const MOCK_BACKTESTING = {
  generated_at: "2026-10-16",
  methodology: "walk_forward",
  window_size: 24,
  models: {
    frequency: {
      overall_accuracy: {
        last_two: 0.312,
        last_three_b: 0.148,
        last_three_f: 0.156
      },
      history: [
        {"draw": "2026-06-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-06-16", "last_two_hit": false, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-07-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-07-16", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-08-01", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-08-16", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-09-01", "last_two_hit": false, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-09-16", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-10-01", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-10-16", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false}
      ]
    },
    arima: {
      overall_accuracy: {
        last_two: 0.278,
        last_three_b: 0.134,
        last_three_f: 0.142
      },
      history: [
        {"draw": "2026-06-01", "last_two_hit": false, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-06-16", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-07-01", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-07-16", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-08-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-08-16", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-09-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-09-16", "last_two_hit": false, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-10-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-10-16", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false}
      ]
    },
    prophet: {
      overall_accuracy: {
        last_two: 0.334,
        last_three_b: 0.162,
        last_three_f: 0.171
      },
      history: [
        {"draw": "2026-06-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-06-16", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-07-01", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-07-16", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-08-01", "last_two_hit": false, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-08-16", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-09-01", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-09-16", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-10-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-10-16", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": true}
      ]
    },
    lstm: {
      overall_accuracy: {
        last_two: 0.298,
        last_three_b: 0.151,
        last_three_f: 0.158
      },
      history: [
        {"draw": "2026-06-01", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-06-16", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-07-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-07-16", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-08-01", "last_two_hit": false, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-08-16", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": true},
        {"draw": "2026-09-01", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-09-16", "last_two_hit": true, "last_three_b_hit": true, "last_three_f_hit": false},
        {"draw": "2026-10-01", "last_two_hit": true, "last_three_b_hit": false, "last_three_f_hit": false},
        {"draw": "2026-10-16", "last_two_hit": false, "last_three_b_hit": false, "last_three_f_hit": true}
      ]
    }
  }
};
