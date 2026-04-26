---
date: 2026-04-25
title: Thin channels produce noise trades — filter candidate
tags: [entry, channel-width, filter, crm_exit]
strategy: crm_exit
tickers: [TSLA, NVDA, MSFT]
impact: medium
---

Observed consistently across TSLA, NVDA, and MSFT: when the EMA34/EMA50 channel width is very small (< $0.20 for large-cap stocks), the entry signals are noise.

Examples from TSLA:
- T3 (Ch $0.15): +1.86% stock, +17.34% options — accidental winner
- T11 (Ch $0.13): -1.43% stock, -38.71% options
- T13 (Ch $0.74) into T14 (Ch $0.71): back-to-back shorts at the same zone

NVDA examples: T7 ($0.10), T8 ($0.02), T9 ($0.10) — all entered same consolidation zone. T8 loses, T9 wins, both noise.

When EMA34 and EMA50 are nearly flat and compressed, the channel has no directional information. Any close outside it is statistically meaningless — price will snap back inside almost immediately.

**Candidate filter:** Require ch_width >= $X before taking a trade. Threshold TBD — needs to be calibrated per ticker given different price levels. Percentage-based threshold may be better than absolute dollar amount.

Not applied yet — noted for V3.1 testing.
