---
date: 2026-04-25
title: 8/21 EMA exit dominates all other exits — especially for options
tags: [exit, options, theta, crm_exit]
strategy: crm_exit
tickers: [TSLA]
impact: high
---

Tested three exits on identical TSLA entry points (no opposite side close):

| Exit  | Trades | Win% | Stock PnL | Options PnL |
|-------|--------|------|-----------|-------------|
| 34/50 | 9      | 55.6%| +5.28%    | -17.12%     |
| 8/21  | 20     | 65.0%| +11.60%   | +178.13%    |
| 5/12  | 25     | 52.0%| +3.34%    | +57.92%     |

**8/21 wins on every metric.** The key reasons:

- **vs 34/50**: Holds too long. Theta eats options premium even on winning stock trades. T2 in V2.3a held 18 days for +0.80% stock move — option lost 64.56%.
- **vs 5/12**: Too fast. Fires on the first leg and misses the continuation. More trades but smaller average winners. Re-entry noise inflates trade count.

The 8/21 cross sits in the sweet spot — exits fast enough to preserve options premium, slow enough to ride the real directional moves (3–7 day holds).

**For options specifically:** 14–18 DTE at entry + 8/21 exit = enough time for a real move to develop before theta dominates.
