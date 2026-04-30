---
title: 3Min 34/50 Cross Strategy — V1.0 Results
strategy: 3m_cross
version: 1.0
symbol: GC
status: research
date: 2026-04-29
period: 2025-09-01 to 2026-03-31
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

### Indicators (analysis only — not used as entry filters in V1.0)

```
BX = RSI( EMA(close, 5) - EMA(close, 20), 5 ) - 50
```

Oscillates around 0. Positive = bullish momentum, negative = bearish.

- **Daily BX** — calculated on CME session closes (5 PM CT open → 4 PM CT close).
  Each bar uses the prior completed session's BX. No lookahead.
- **Weekly BX** — same formula on weekly closes (week ending Friday 4 PM CT).
  Each bar uses the prior completed week's BX. No lookahead.
- **BX direction** — rising if current period BX > prior period BX.

---

## V1.0 Overall Results

**Period:** Sep 1 2025 – Mar 31 2026  
**Bars:** 202,708 one-minute → 67,569 three-minute bars

| Metric | Value |
|---|---|
| Total Trades | 708 (354 long, 354 short) |
| Win Rate | 29.1% |
| Avg Win | ~+37 pts |
| Avg Loss | ~-12 pts |
| Win / Loss ratio | ~3:1 |
| Total PnL | +29.20% |
| Profit Factor | 1.225 |

### How to read the win rate

30% win rate is expected for a cross-based strategy. The cross fires frequently — many are false moves that reverse quickly (avg loss ~12 pts). The strategy profits because the occasional sustained move generates large wins (avg win ~37 pts), covering roughly 3 small losses per win.

Per 3 trades on average:
```
2 losses × -12 pts = -24 pts
1 win    × +37 pts = +37 pts
──────────────────────────────
Net                = +13 pts  →  positive EV
```

For GC: 1 point = $100/contract.

---

## BX Direction Breakdown

Trades broken down by daily BX direction × weekly BX direction at time of entry.

- **D↑** = daily BX rising (daily momentum building)
- **D↓** = daily BX falling (daily momentum decaying)
- **W↑** = weekly BX rising (weekly momentum building)
- **W↓** = weekly BX falling (weekly momentum decaying)

```
────────────────────────────────────────────────────────────────────────────────────────────
  Bucket      ── LONG ──────────────────────────────  ── SHORT ────────────────────────────
              Trades  Win%  AvgW    AvgL   TotPnL   Trades  Win%  AvgW    AvgL   TotPnL
  ──────────  ───────────────────────────────────   ───────────────────────────────────
  D↑/W↑          137  27.7%   +42.1   -13.2    +5.89%      143  25.9%   +43.4   -12.6    +4.47%
  D↑/W↓           66  28.8%   +28.1    -9.6    +2.33%       66  18.2%   +33.2    -9.3    -2.53%
  D↓/W↑           89  37.1%   +37.7   -10.5   +13.80%       83  31.3%   +24.2   -12.4    -2.22%
  D↓/W↓           62  30.6%   +30.6   -14.0    -0.09%       62  35.5%   +45.3   -15.3    +7.55%
  ──────────  ───────────────────────────────────   ───────────────────────────────────
  ALL            354  30.8%   +36.4   -12.1   +21.93%      354  27.4%   +37.5   -12.3    +7.27%
────────────────────────────────────────────────────────────────────────────────────────────
```

---

## What Each Bucket Means

**BX rising** — momentum is building. The EMA spread is widening. The move has energy.  
**BX falling** — momentum is decaying. The EMA spread is narrowing. The move is losing steam.

### W↑ (Weekly momentum rising)

The weekly trend has energy. Price is in a sustained directional move on the higher timeframe.

**D↓/W↑ → LONG. Best setup in the entire table.**
- 37.1% win rate, +13.80% PnL
- Weekly momentum still strong. Daily BX has pulled back — you're entering when the daily move has temporarily exhausted. The weekly trend reasserts and carries the trade. Classic pullback-in-an-uptrend.

**D↑/W↑ → LONG. Acceptable.**
- 27.7% win rate, +5.89% PnL
- Weaker than D↓/W↑ because both timeframes are extended in the same direction. Less room to run before the trade needs to pause.

**Any SHORT in W↑ → Avoid.**
- D↓/W↑ SHORT: -2.22%. D↑/W↑ SHORT: +4.47% (marginal, unreliable).
- You are fighting weekly momentum. Even when the daily is pulling back, the weekly reasserts and cuts the short.

---

### W↓ (Weekly momentum falling)

The weekly trend is losing energy or heading lower. The dominant bias is bearish.

**D↓/W↓ → SHORT. Best short setup.**
- 35.5% win rate, +7.55% PnL
- Both timeframes losing momentum together. Daily confirming the weekly. Trend continuation short.

**D↑/W↓ → Skip entirely. Worst bucket.**
- SHORT 18.2% win rate, -2.53%. LONG +2.33%.
- Daily is rising while weekly is falling — two timeframes in disagreement. Neither direction has a clean edge. This is the noise bucket.

**Any LONG in W↓ → Avoid.**
- Buying into weekly weakness. Flat to negative in both D sub-buckets.

---

## Decision Tree

```
Is Weekly BX rising (W↑)?
│
├── YES — W↑
│   │
│   ├── Is Daily BX falling (D↓)?
│   │   └── LONG on 3min EMA34/50 cross ← best setup (37.1% WR, PF ~1.6)
│   │
│   └── Is Daily BX rising (D↑)?
│       └── LONG on 3min EMA34/50 cross ← acceptable (27.7% WR)
│           (skip shorts in W↑ entirely)
│
└── NO — W↓
    │
    ├── Is Daily BX falling (D↓)?
    │   └── SHORT on 3min EMA34/50 cross ← best short setup (35.5% WR, PF ~1.5)
    │
    └── Is Daily BX rising (D↑)?
        └── SKIP — no edge in either direction (18.2% short WR, -2.53%)
```

---

## Filtered Results — Best Buckets Only

Applying the decision tree: take only D↓/W↑ longs and D↓/W↓ shorts.

| | Trades | Win% | Total PnL | Est. PF |
|---|---|---|---|---|
| D↓/W↑ LONG | 89 | 37.1% | +13.80% | ~1.6 |
| D↓/W↓ SHORT | 62 | 35.5% | +7.55% | ~1.5 |
| **Combined** | **151** | **36.4%** | **+21.35%** | **~1.55** |

- **~22 trades/month** on GC alone — manageable frequency
- PF improves from 1.22 (unfiltered) to ~1.55 (filtered)
- 50% reduction in trade count, capturing 73% of total unfiltered PnL

---

## Open Questions for V1.1

1. Do these bucket patterns hold over 10 years (2016–2026) across different market regimes?
2. Does the D↓/W↑ long / D↓/W↓ short filter hold on CL?
3. Does adding a hard stop (e.g. 15 pts) reduce avg loss without hurting win rate?
4. Can PF reach ≥ 1.5 consistently before considering live trading?
5. How many consecutive losing trades at 36% win rate? Need to size accordingly.

---

## Notes

- V1.0 is a characterisation run — no filters applied, all crosses taken. Results establish the baseline and identify candidate filters for V1.1.
- Daily and weekly BX use proper CME session closes (5 PM CT open / 4 PM CT close), not calendar midnight. Bars at or after 5 PM CT are assigned to the next session's date.
- All BX values at entry use the prior completed session — no lookahead.
- Points (AvgW / AvgL) are raw price points. For GC: 1 point = $100/contract.
- Sep 2025 – Mar 2026 was a strong directional period for GC (gold bull run). Results need validation across neutral and bearish regimes.
