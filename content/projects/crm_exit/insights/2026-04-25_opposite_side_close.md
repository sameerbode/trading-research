---
date: 2026-04-25
title: Removing the opposite side close exit was the single biggest improvement
tags: [exit, v2, v3, crm_exit, rule-change]
strategy: crm_exit
tickers: [TSLA]
impact: high
---

When V2.0 introduced the rejection candle entry, it also added an "opposite side close" exit — if price closed back through the channel in the wrong direction, exit the trade.

This felt conservative but destroyed performance. V2.0 with opposite side close: **-2.84%, 26% win rate**.

The rule was exiting trades that were temporarily pulling back through the channel, then continuing in the bias direction. The exit fired on noise, not on real invalidation.

Proof: controlled test with identical V2.0 entry points, only changing the exit — 8/21 cross alone produced **+3.57%** vs **-2.85%** with the opposite side close rule on the same entries.

**Lesson:** A stop rule that exits you from good trades is worse than no stop at all. The 1H bias is the filter — if bias is intact, the trade is intact. Let the momentum exit (8/21 cross) do its job.
