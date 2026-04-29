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

### Indicators (analysis only — not used as entry filters)
**Daily BX** and **Weekly BX** were calculated and attached to each trade for post-trade analysis.

```
BX = RSI( EMA(close, 5) - EMA(close, 20), 5 ) - 50
```

- Oscillates around 0. Positive = bullish momentum, negative = bearish.
- **Daily BX** — calculated on CME session closes (5 PM CT open → 4 PM CT close).
  Each bar uses the prior completed session's BX. No lookahead.
- **Weekly BX** — same formula on weekly closes (week ending Friday 4 PM CT).
  Each bar uses the prior completed week's BX. No lookahead.
- **BX direction** — rising if current period BX > prior period BX.

---

## V1.0 Overall Results

**Period:** Sep 1 2025 – Mar 31 2026
**Bars:** 202,708 one-minute bars (67,569 three-minute bars)

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
30% win rate is expected for this type of strategy. The cross fires frequently —
many are false moves that get stopped by the next cross quickly (-12 pts avg).
The strategy profits because the occasional sustained move generates large wins
(+37 pts avg), covering roughly 3 small losses per win.

Per 3 trades on average:
```
2 losses × -12 pts = -24 pts
1 win    × +37 pts = +37 pts
──────────────────────────────
Net                = +13 pts  →  positive EV
```

---

## BX Direction Breakdown

Trades broken down by daily BX direction × weekly BX direction at time of entry.
**D↑** = daily BX rising, **D↓** = daily BX falling, **W↑** = weekly BX rising, **W↓** = weekly BX falling.

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

## Key Observations

**1. Weekly BX direction is the primary signal**
The clearest pattern: weekly BX direction determines which side to trade.
- **W↑ → longs only.** D↓/W↑ longs: 37.1% win rate, +13.80% PnL. Best bucket overall.
  D↓/W↑ shorts: -2.22% PnL. Same setup, wrong direction.
- **W↓ → shorts only.** D↓/W↓ shorts: 35.5% win rate, +7.55% PnL.
  D↓/W↓ longs: essentially flat (-0.09%).

**2. Daily BX refines timing**
Within the weekly direction, D↓ (daily BX falling = daily pullback) produces better entries
than D↑ (daily BX rising = daily momentum extended).
- D↓/W↑ longs: 37.1% win rate vs D↑/W↑ longs: 27.7%
- D↓/W↓ shorts: 35.5% win rate vs D↑/W↓ shorts: 18.2%

**3. D↑/W↓ shorts are the worst setup**
Shorting when daily momentum is building against the weekly downtrend: 18.2% win rate, -2.53% PnL. Clear avoid.

---

## Open Questions for V1.1

- Does filtering entries to W↑ longs / W↓ shorts improve PF to a tradeable level (≥ 1.5)?
- How many trades per month does a W-direction filter leave?
- Does adding a hard stop (e.g. 15 pts) reduce avg loss without hurting win rate?
- How do these results hold on CL?
- Does this pattern hold across different market regimes (test 2022–2024)?

---

## Notes

- V1.0 is a characterisation run — no filters applied, all crosses taken.
  Results establish the baseline and identify candidate filters for V1.1.
- Daily and weekly BX use proper CME session closes (5 PM CT open / 4 PM CT close),
  not calendar midnight. Bars at or after 5 PM CT are assigned to the next session.
- All BX values at entry use the prior completed session — no lookahead.
- Points (AvgW / AvgL) are raw price points. For GC: 1 point = $100/contract.
