---
title: 3Min 34/50 Cross Strategy — V1.0 Results
strategy: 3m_cross
version: 1.0
symbol: GC
status: research
date: 2026-04-29
---

## Strategy Rules

**Instrument:** GC (Gold Futures, CME)
**Data:** 1-minute Databento bars resampled to 3-minute
**Session:** All hours — CME Globex (no session filter)

### Entry
3-minute EMA34 crosses EMA50 in either direction.
- EMA34 crosses **above** EMA50 → **LONG**
- EMA34 crosses **below** EMA50 → **SHORT**

No additional entry filter applied in V1.0. Always in market — every cross flips the position.

### Exit
Opposite 3-minute EMA34/50 cross.

### Indicators (analysis only — not used as filters in V1.0)

```
BX = RSI( EMA(close, 5) - EMA(close, 20), 5 ) - 50
```

Oscillates around 0. Positive = bullish momentum, negative = bearish.

- **Daily BX** — calculated on CME session closes (5 PM CT open → 4 PM CT close). Each bar uses the prior completed session's BX. No lookahead.
- **Weekly BX** — same formula on weekly closes (week ending Friday 4 PM CT). Each bar uses the prior completed week's BX. No lookahead.
- **BX direction** — rising if current period BX > prior period BX.

Bucket labels:
- **D↑** = daily BX rising, **D↓** = daily BX falling
- **W↑** = weekly BX rising, **W↓** = weekly BX falling

---

## Overall Results

| Metric | 7-Month Window | 10-Year Window |
|---|---|---|
| Period | Sep 2025 – Mar 2026 | Apr 2016 – Apr 2026 |
| Total Trades | 708 | 17,722 |
| Win Rate | 29.1% | 28.0% |
| Avg Win (pts) | +37 | +8.5 |
| Avg Loss (pts) | -12 | -3.0 |
| Total PnL | +29.20% | +71.55% |
| Profit Factor | 1.225 | 1.04 |

---

## Bucket Returns — 7 Month (Sep 2025 – Mar 2026)

### Longs

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 137 | 27.7% | +42.1 pts | -13.2 pts | +5.89% |
| D↑/W↓ | 66 | 28.8% | +28.1 pts | -9.6 pts | +2.33% |
| **D↓/W↑** | **89** | **37.1%** | **+37.7 pts** | **-10.5 pts** | **+13.80%** |
| D↓/W↓ | 62 | 30.6% | +30.6 pts | -14.0 pts | -0.09% |
| **ALL** | **354** | **30.8%** | **+36.4 pts** | **-12.1 pts** | **+21.93%** |

### Shorts

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 143 | 25.9% | +43.4 pts | -12.6 pts | +4.47% |
| D↑/W↓ | 66 | 18.2% | +33.2 pts | -9.3 pts | -2.53% |
| D↓/W↑ | 83 | 31.3% | +24.2 pts | -12.4 pts | -2.22% |
| **D↓/W↓** | **62** | **35.5%** | **+45.3 pts** | **-15.3 pts** | **+7.55%** |
| **ALL** | **354** | **27.4%** | **+37.5 pts** | **-12.3 pts** | **+7.27%** |

### Combined (Long + Short)

| Bucket | Total Trades | Long PnL | Short PnL | Combined PnL |
|---|---|---|---|---|
| D↑/W↑ | 280 | +5.89% | +4.47% | +10.36% |
| D↑/W↓ | 132 | +2.33% | -2.53% | -0.20% |
| **D↓/W↑** | **172** | **+13.80%** | **-2.22%** | **+11.58%** |
| D↓/W↓ | 124 | -0.09% | +7.55% | +7.46% |
| **ALL** | **708** | **+21.93%** | **+7.27%** | **+29.20%** |

---

## Bucket Returns — 10 Year (Apr 2016 – Apr 2026)

### Longs

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 2,330 | 28.8% | +9.2 pts | -3.3 pts | +29.20% |
| D↑/W↓ | 2,126 | 29.2% | +8.1 pts | -2.9 pts | +23.49% |
| **D↓/W↑** | **2,054** | **29.9%** | **+9.2 pts** | **-2.9 pts** | **+51.13%** |
| D↓/W↓ | 2,351 | 27.9% | +7.5 pts | -2.8 pts | +3.78% |
| **ALL** | **8,861** | **28.9%** | **+8.5 pts** | **-3.0 pts** | **+107.61%** |

### Shorts

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 2,402 | 26.4% | +9.4 pts | -3.2 pts | -2.25% |
| D↑/W↓ | 2,185 | 26.4% | +6.3 pts | -2.8 pts | -32.00% |
| D↓/W↑ | 1,993 | 27.8% | +7.4 pts | -3.1 pts | -14.19% |
| **D↓/W↓** | **2,281** | **27.7%** | **+8.5 pts** | **-3.0 pts** | **+12.38%** |
| **ALL** | **8,861** | **27.1%** | **+8.0 pts** | **-3.0 pts** | **-36.05%** |

### Combined (Long + Short)

| Bucket | Total Trades | Long PnL | Short PnL | Combined PnL |
|---|---|---|---|---|
| D↑/W↑ | 4,732 | +29.20% | -2.25% | +26.95% |
| D↑/W↓ | 4,311 | +23.49% | -32.00% | -8.51% |
| **D↓/W↑** | **4,047** | **+51.13%** | **-14.19%** | **+36.94%** |
| D↓/W↓ | 4,632 | +3.78% | +12.38% | +16.16% |
| **ALL** | **17,722** | **+107.61%** | **-36.05%** | **+71.56%** |

---

## What the 10-Year Data Confirms vs Challenges

### Confirmed
- **D↓/W↑ longs are the best bucket in both windows** — +13.80% over 7 months, +51.13% over 10 years. Consistent pullback-in-uptrend edge.
- **D↑/W↓ shorts are consistently the worst** — -2.53% over 7 months, -32.00% over 10 years. Shorting when daily is rising against weekly weakness destroys capital.
- **Weekly BX direction separates longs from shorts** — longs in W↑ generated +52.69% combined over 10 years vs -16.44% for shorts in W↑.

### Challenged
- **D↓/W↓ longs showed strength in 7 months (+0% roughly) but only +3.78% over 10 years** — marginal, not reliable.
- **D↑/W↓ longs looked weak in 7 months (+2.33%) but generated +23.49% over 10 years** — the secular gold bull run gave these long tailwind. Not structurally sound.
- **Overall PF dropped from 1.22 to 1.04 on 10 years** — the 7-month window was during an unusually strong directional period for GC. Not representative of average conditions.

---

## Decision Tree

```
Is Weekly BX rising (W↑)?
│
├── YES — W↑
│   │
│   ├── Is Daily BX falling (D↓)?
│   │   └── LONG on 3min EMA34/50 cross ← best setup (37.1% WR 7m / 29.9% WR 10y)
│   │
│   └── Is Daily BX rising (D↑)?
│       └── LONG on 3min EMA34/50 cross ← acceptable (27.7% WR 7m / 28.8% WR 10y)
│           (skip all shorts when W↑)
│
└── NO — W↓
    │
    ├── Is Daily BX falling (D↓)?
    │   └── SHORT on 3min EMA34/50 cross ← best short setup (35.5% WR 7m / 27.7% WR 10y)
    │
    └── Is Daily BX rising (D↑)?
        └── SKIP — worst bucket in both windows (18.2% WR 7m, -32.00% PnL 10y)
```

---

## Filtered Results — Best Buckets Only (D↓ direction)

Taking only D↓/W↑ longs and D↓/W↓ shorts:

| | 7-Month | 10-Year |
|---|---|---|
| Trades | 151 | 4,335 |
| Win% | 36.4% | 28.8% |
| Long PnL | +13.80% | +51.13% |
| Short PnL | +7.55% | +12.38% |
| **Combined PnL** | **+21.35%** | **+63.51%** |
| Est. PF | ~1.55 | ~1.3 |

- Removes 57% of trades vs unfiltered
- Captures 89% of total 10-year PnL
- ~22 trades/month on GC (7-month window), ~36/month over 10 years

---

## Open Questions for V1.1

1. Does adding a hard stop (e.g. 15 pts) reduce avg loss without hurting win rate?
2. How do results hold on CL across the same periods?
3. What does the year-by-year PnL look like — are there losing years?
4. At 28% win rate, expect runs of 8-10 consecutive losses — what does position sizing look like?
5. Can PF reach ≥ 1.5 consistently before considering live trading?

---

## Notes

- V1.0 is a characterisation run — no filters applied, all crosses taken.
- Daily and weekly BX use proper CME session closes (5 PM CT → 4 PM CT), not calendar midnight.
- All BX values at entry use the prior completed session — no lookahead.
- Points (Avg Win / Avg Loss) are raw price points. For GC: 1 point = $100/contract.
- The 7-month window (Sep 2025 – Mar 2026) coincided with a strong GC bull run. 10-year results are more representative of average market conditions.
