---
title: 3Min 34/50 Cross Strategy — V1.0 CL Results
strategy: 3m_cross
version: 1.0
symbol: CL
status: research
date: 2026-04-29
---

## Strategy Rules

**Instrument:** CL (WTI Crude Oil Futures, CME)
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

- **Daily BX** — CME session closes (5 PM CT open → 4 PM CT close). Prior completed session only. No lookahead.
- **Weekly BX** — week ending Friday 4 PM CT. Prior completed week only. No lookahead.
- **BX direction** — rising if current period BX > prior period BX.

Bucket labels: **D↑** = daily rising · **D↓** = daily falling · **W↑** = weekly rising · **W↓** = weekly falling

---

## Overall Results

| Metric | 7-Month Window | 10-Year Window |
|---|---|---|
| Period | Sep 2025 – Mar 2026 | Apr 2016 – Apr 2026 |
| Total Trades | 846 | 17,728 |
| Win Rate | 28.1% | 27.2% |
| Avg Win (pts) | +1.0 | +0.6 |
| Avg Loss (pts) | -0.3 | -0.2 |
| Total PnL | +23.93% | +19.29% |
| Profit Factor | 1.096 | 1.004 |

> CL is harder than GC. PF of 1.004 over 10 years means the unfiltered strategy barely covers costs. Bucket filtering is essential.

---

## Quick Reference — When to Trade CL

Stats from 10-year backtest (Apr 2016 – Apr 2026). ✅ = take · ⚠️ = caution · ❌ = skip

| Bucket | Long | Short |
|:---:|:---|:---|
| **D↑ / W↑**<br>Daily momentum building<br>Weekly momentum building | ❌<br>Win Rate: 25.5%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: -29.53% | ❌<br>Win Rate: 26.7%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: -14.24% |
| **D↑ / W↓**<br>Daily momentum building<br>Weekly momentum falling | ⚠️<br>Win Rate: 30.1%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: +11.99% | ❌<br>Win Rate: 26.8%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: -10.83% |
| **D↓ / W↑**<br>Daily momentum falling<br>Weekly momentum building | ✅<br>Win Rate: 29.0%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: +41.45% | ❌<br>Win Rate: 25.3%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: -66.93% |
| **D↓ / W↓**<br>Daily momentum falling<br>Weekly momentum falling | ✅<br>Win Rate: 28.7%<br>Avg Win: +0.6 pts<br>Avg Loss: -0.2 pts<br>Total PnL: +75.38% | ⚠️<br>Win Rate: 26.0%<br>Avg Win: +0.7 pts<br>Avg Loss: -0.2 pts<br>Total PnL: +12.00% |

> **CL rule:** Daily BX falling (D↓) = take longs. Weekly direction is secondary.
> D↓/W↑ and D↓/W↓ longs are both strong. D↑/W↑ longs are a trap — positive in short windows, -29.53% over 10 years.
> ❌ D↓/W↑ shorts = worst bucket in the entire table (-66.93%). Never short into a rising weekly trend on CL.

---

## Bucket Returns — 7 Month (Sep 2025 – Mar 2026)

### Longs

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 142 | 21.1% | +2.0 pts | -0.4 pts | +18.21% |
| D↑/W↓ | 60 | 35.0% | +0.4 pts | -0.2 pts | +2.82% |
| **D↓/W↑** | **127** | **33.9%** | **+1.0 pts** | **-0.3 pts** | **+22.12%** |
| D↓/W↓ | 94 | 29.8% | +0.4 pts | -0.2 pts | +0.86% |
| **ALL** | **423** | **28.8%** | **+1.0 pts** | **-0.3 pts** | **+44.01%** |

### Shorts

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 143 | 34.3% | +0.9 pts | -0.4 pts | +2.66% |
| D↑/W↓ | 67 | 26.9% | +0.4 pts | -0.2 pts | -2.54% |
| D↓/W↑ | 126 | 25.4% | +0.7 pts | -0.3 pts | -14.83% |
| D↓/W↓ | 87 | 19.5% | +0.5 pts | -0.2 pts | -5.36% |
| **ALL** | **423** | **27.4%** | **+0.7 pts** | **-0.3 pts** | **-20.07%** |

### Combined (Long + Short)

| Bucket | Total Trades | Long PnL | Short PnL | Combined PnL |
|---|---|---|---|---|
| D↑/W↑ | 285 | +18.21% | +2.66% | +20.87% |
| D↑/W↓ | 127 | +2.82% | -2.54% | +0.28% |
| **D↓/W↑** | **253** | **+22.12%** | **-14.83%** | **+7.29%** |
| D↓/W↓ | 181 | +0.86% | -5.36% | -4.50% |
| **ALL** | **846** | **+44.01%** | **-20.07%** | **+23.93%** |

---

## Bucket Returns — 10 Year (Apr 2016 – Apr 2026)

### Longs

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 2,413 | 25.5% | +0.6 pts | -0.2 pts | -29.53% |
| D↑/W↓ | 2,139 | 30.1% | +0.6 pts | -0.2 pts | +11.99% |
| **D↓/W↑** | **2,346** | **29.0%** | **+0.6 pts** | **-0.2 pts** | **+41.45%** |
| **D↓/W↓** | **1,966** | **28.7%** | **+0.6 pts** | **-0.2 pts** | **+75.38%** |
| **ALL** | **8,864** | **28.2%** | **+0.6 pts** | **-0.2 pts** | **+99.29%** |

### Shorts

| Bucket | Trades | Win% | Avg Win | Avg Loss | Total PnL |
|---|---|---|---|---|---|
| D↑/W↑ | 2,500 | 26.7% | +0.6 pts | -0.2 pts | -14.24% |
| D↑/W↓ | 2,194 | 26.8% | +0.6 pts | -0.2 pts | -10.83% |
| D↓/W↑ | 2,270 | 25.3% | +0.6 pts | -0.2 pts | -66.93% |
| **D↓/W↓** | **1,900** | **26.0%** | **+0.7 pts** | **-0.2 pts** | **+12.00%** |
| **ALL** | **8,864** | **26.2%** | **+0.6 pts** | **-0.2 pts** | **-79.99%** |

### Combined (Long + Short)

| Bucket | Total Trades | Long PnL | Short PnL | Combined PnL |
|---|---|---|---|---|
| D↑/W↑ | 4,913 | -29.53% | -14.24% | -43.77% |
| D↑/W↓ | 4,333 | +11.99% | -10.83% | +1.16% |
| **D↓/W↑** | **4,616** | **+41.45%** | **-66.93%** | **-25.48%** |
| **D↓/W↓** | **3,866** | **+75.38%** | **+12.00%** | **+87.38%** |
| **ALL** | **17,728** | **+99.29%** | **-79.99%** | **+19.29%** |

---

## CL vs GC — Key Differences

| | GC (Gold) | CL (Crude Oil) |
|---|---|---|
| Best long bucket | D↓/W↑ (+51.13%) | D↓/W↓ (+75.38%) |
| Weekly BX as filter | Strong — W↑ = longs only | Weak — D↓ matters more than W |
| Shorts overall | -36.05% | -79.99% — much worse |
| Worst bucket | D↑/W↓ short (-32%) | D↓/W↑ short (-66.93%) |
| D↑/W↑ longs | +29.20% (ok) | -29.53% (avoid) |
| 10-year PF | 1.04 | 1.004 |

**GC:** Weekly BX direction drives the trade direction. W↑ = longs, W↓ = shorts.
**CL:** Daily BX falling (D↓) drives longs regardless of weekly direction. Shorts rarely work.

---

## Decision Tree — CL

```
Is Daily BX falling (D↓)?
│
├── YES — D↓
│   ├── W↑? → LONG on 3min EMA34/50 cross ← strong (29.0% WR, +41.45% 10y)
│   └── W↓? → LONG on 3min EMA34/50 cross ← best (28.7% WR, +75.38% 10y)
│             (skip all D↓ shorts — D↓/W↑ short is -66.93%)
│
└── NO — D↑
    ├── W↓? → ⚠️ LONG with caution (30.1% WR, +11.99% 10y)
    └── W↑? → ❌ SKIP longs (-29.53% 10y — trap bucket)
              ❌ SKIP shorts too (-14.24% 10y)
```

---

## Filtered Results — Best Buckets Only

Taking D↓ longs only (both W↑ and W↓):

| | 7-Month | 10-Year |
|---|---|---|
| Trades | 221 | 4,312 |
| D↓/W↑ Long PnL | +22.12% | +41.45% |
| D↓/W↓ Long PnL | +0.86% | +75.38% |
| **Combined PnL** | **+22.98%** | **+116.83%** |

- Removes 48% of trades
- Captures 118% of unfiltered 10-year PnL (filtered outperforms unfiltered by removing losing buckets)

---

## Open Questions for V1.1

1. Why does D↑/W↑ long work short-term (+18.21% in 7 months) but fail long-term (-29.53%)? Regime-dependent?
2. Why are CL shorts so much worse than GC shorts overall?
3. Does adding a hard stop improve CL more than GC given the higher volatility?
4. Year-by-year PnL — which years are losing years for the D↓ long filter?
5. Can PF reach ≥ 1.5 on D↓ longs with an additional stop rule?

---

## Notes

- V1.0 characterisation run — no filters applied, all crosses taken.
- CME session closes used: 5 PM CT open → 4 PM CT close. No lookahead.
- Points are raw price points. For CL: 1 point = $1,000/contract.
- CL is structurally different from GC — crude oil is more mean-reverting and driven by supply/demand shocks. The secular bull trend that helped GC longs does not exist in CL over this period.
