---
date: 2026-04-25
title: Options amplify big moves dramatically but punish losers equally hard
tags: [options, risk, black-scholes, crm_exit]
strategy: crm_exit
tickers: [TSLA, AAPL, MSFT, AMZN]
impact: high
---

Running Black-Scholes options simulation (ATM, next Friday >= 2 weeks, HV20 as IV) across all MAG7:

**Amplification on winners:**
- TSLA T16: +5.01% stock → +91.00% options
- TSLA T17: +5.90% stock → +93.98% options
- MSFT T15: +13.10% stock → +552.44% options (one outlier driving entire MSFT result)
- AAPL T1: +7.13% stock → +318.57% options
- AMZN T16: +12.82% stock → +377.32% options

**Punishment on losers:**
- TSLA T2: -3.52% stock → -64.28% options
- NVDA T1: -2.66% stock → -71.29% options
- GOOGL T13: -4.99% stock → -70.44% options

**The pattern:** Options are roughly 12-18x leveraged on 5%+ moves. On 1-2% moves, theta eats most of the gain. On losses >= 2.5%, options lose 50-75%.

**Key implication:** This strategy in options is NOT a high-frequency small-winner game. It's a **momentum capture** game — you need the 5%+ moves to make the math work. The 8/21 exit is critical because it holds long enough to catch those moves while small-move trades roughly break even.

**Risk note:** IV was 28-50% across the test period (TSLA). Real options pricing may differ. No bid-ask spread modeled. Results are directionally correct but not exact.
