# 🎰 Thai Lottery Analytics (สลากกินแบ่งรัฐบาล — วิเคราะห์ด้วย AI)

> **⚠️ คำเตือน / Disclaimer**  
> สลากกินแบ่งรัฐบาลไทยเป็น **ระบบการสุ่มแบบสมบูรณ์** (true random system)  
> ผลการวิเคราะห์ทางสถิติและการทำนายจาก AI/ML ในโปรเจกต์นี้ **ไม่สามารถรับประกันความแม่นยำได้**  
> โปรเจกต์นี้จัดทำขึ้นเพื่อ **วัตถุประสงค์ทางการศึกษาและการวิจัยเท่านั้น**  
> Thai Government Lottery is a **completely random system**. All statistical analyses and AI/ML predictions in this project are for **educational and research purposes only** and carry no guarantee of accuracy.

---

## 📋 ภาพรวมโปรเจกต์ / Project Overview

Thai Lottery Analytics คือ static site ที่สร้างขึ้นด้วย GitHub Actions  
โดยสคริปต์ Python จะรันอัตโนมัติทุกงวด เพื่อ:

1. **ดึงข้อมูล** ผลรางวัลสลากกินแบ่งย้อนหลังจากหลายแหล่ง
2. **ประมวลผล** สถิติและ feature engineering
3. **ทำนาย** ด้วยโมเดล ML หลายแบบ (Frequency, ARIMA, Prophet, LSTM)
4. **ส่งออก** ข้อมูลเป็น JSON/CSV เพื่อให้ GitHub Pages แสดงผล

---

## 🚀 การติดตั้ง / Installation

```bash
# Clone the repository
git clone https://github.com/your-username/thai-lottery-analytics.git
cd thai-lottery-analytics

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 🏃 การใช้งาน / Usage

```bash
# Run the full pipeline (scrape → process → ML → export)
python scripts/main.py

# Run individual steps
python scripts/scraper.py        # ดึงข้อมูลเท่านั้น
python scripts/processor.py      # คำนวณสถิติ
python scripts/backtester.py     # ทดสอบย้อนหลัง
python scripts/exporter.py       # ส่งออกไฟล์

# Options
python scripts/main.py --skip-scrape   # ใช้ข้อมูลที่มีอยู่ ไม่ดึงใหม่
python scripts/main.py --skip-ml       # ข้ามขั้นตอน ML
python scripts/main.py --debug         # แสดง log ละเอียด
```

---

## 🗂️ โครงสร้างโปรเจกต์ / Architecture

```
thai-lottery-analytics/
├── scripts/                    # Python backend
│   ├── main.py                 # Pipeline orchestrator
│   ├── scraper.py              # Web scraper (3-source fallback)
│   ├── processor.py            # Feature engineering
│   ├── backtester.py           # Walk-forward validation
│   ├── exporter.py             # JSON/CSV exporter
│   └── models/
│       ├── frequency_model.py  # Statistical frequency model
│       ├── arima_model.py      # ARIMA time-series model
│       ├── prophet_model.py    # Facebook Prophet model
│       ├── lstm_model.py       # LSTM neural network
│       └── ensemble.py         # Ensemble combiner
├── data/                       # Generated data (auto-updated)
│   ├── raw/                    # Raw scraped data
│   ├── results.json            # All historical results
│   ├── results.csv             # All historical results (CSV)
│   ├── statistics.json         # Computed statistics
│   ├── predictions.json        # ML predictions
│   └── backtesting.json        # Backtest accuracy
├── docs/                       # GitHub Pages frontend
├── requirements.txt
└── README.md
```

### Data Flow

```
myhora.com ──┐
sanook.com ──┼──► scraper.py ──► data/raw/results_raw.json
glo.or.th ──┘
                                          │
                                          ▼
                              processor.py (feature engineering)
                                          │
                              ┌───────────┼───────────┐
                              ▼           ▼           ▼
                        frequency     arima      prophet  lstm
                              └───────────┼───────────┘
                                          ▼
                                    ensemble.py
                                          │
                                          ▼
                                   exporter.py
                              ┌────────┴────────┐
                              ▼                  ▼
                        data/*.json         data/*.csv
                              │
                              ▼
                         GitHub Pages
```

---

## 📊 แหล่งข้อมูล / Data Sources

| แหล่งข้อมูล | URL | หมายเหตุ |
|-------------|-----|----------|
| myhora.com | `https://myhora.com/lottery/` | แหล่งหลัก |
| sanook.com | `https://lottery.sanook.com/` | Fallback 1 |
| สำนักงานสลากกินแบ่งรัฐบาล | `https://www.glo.or.th` | Fallback 2 |

ครอบคลุมข้อมูลตั้งแต่ พ.ศ. 2549 (2006) ถึงปัจจุบัน (~480+ งวด)

---

## 🤖 วิธีการทำนาย / ML Methodology

### 1. Frequency Model (โมเดลความถี่)
คำนวณความน่าจะเป็นจากความถี่ในอดีต  
Score = ความถี่ที่สังเกต / ความถี่ที่คาดหวัง (1.0 = เท่ากับค่าเฉลี่ย)

### 2. ARIMA Model
ใช้ ARIMA(2,1,2) จาก statsmodels เพื่อจับแพทเทิร์น time-series  
ในความถี่ของแต่ละหลักตัวเลขในแต่ละตำแหน่ง

### 3. Prophet Model (Facebook)
ใช้ Prophet เพื่อจับ seasonality รายเดือน และ semi-monthly  
(สลากออกวันที่ 1 และ 16 ของทุกเดือน)

### 4. LSTM Neural Network
2-layer LSTM (64 units) รับ input เป็น sequence ของ 24 งวดล่าสุด  
Output คือ probability distribution ของตัวเลขสำหรับงวดถัดไป

### 5. Ensemble
รวม 4 โมเดล ด้วย weighted average  
น้ำหนักปรับตาม backtesting accuracy (walk-forward validation)

---

## 📈 Backtesting

ใช้ **Walk-forward validation**:  
Train บน draws 1..N → ทำนาย N+1 → วัด accuracy → เลื่อน window  
Metric: **Hit Rate** — ตัวเลขจริงอยู่ใน top-10 ที่ทำนายหรือไม่

---

## 📄 License

MIT License — Copyright © 2024 Thai Lottery Analytics Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.** See the full MIT License text for details.
