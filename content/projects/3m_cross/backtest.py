"""
backtest.py — 3Min 34/50 Cross Strategy
Data  : data/futures/<SYM>_1m.parquet  (UTC, tz-aware)
Output: content/projects/3m_cross/backtests/<SYM>_v1_<YYYYMMDD>.json

Usage:
    python backtest.py           # runs GC
    python backtest.py GC
    python backtest.py CL
    python backtest.py GC 2024-01-01 2026-04-10
"""

import bisect
import json
import sys
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]   # trading-research/
DATA = ROOT / "data" / "futures"
OUT  = Path(__file__).parent / "backtests"
ET   = ZoneInfo("America/New_York")
CT   = ZoneInfo("America/Chicago")

# ── strategy params ────────────────────────────────────────────────────────────
BX_L1, BX_L2, BX_L3 = 5, 20, 5
EMA_FAST, EMA_SLOW   = 34, 50


# ── indicators ─────────────────────────────────────────────────────────────────

def wilder_rsi(series: pd.Series, period: int) -> pd.Series:
    delta  = series.diff()
    gain   = delta.clip(lower=0)
    loss   = (-delta).clip(lower=0)
    avg_g  = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_l  = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs     = avg_g / avg_l.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_bx(series: pd.Series) -> pd.Series:
    e1 = series.ewm(span=BX_L1, adjust=False).mean()
    e2 = series.ewm(span=BX_L2, adjust=False).mean()
    return wilder_rsi(e1 - e2, BX_L3) - 50


def cme_session_dates(index_utc: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """
    Assign each bar to its CME trading session date.
    CME rule: bar at or after 5 PM CT belongs to the NEXT calendar day's session.
    e.g. Sunday 6 PM CT → Monday's session date.
    """
    ct = index_utc.tz_convert(CT)
    dates = ct.normalize()                              # midnight CT of calendar day
    after_close = ct.hour >= 17
    dates = dates + pd.to_timedelta(after_close.astype(int), unit="D")
    return dates.tz_localize(None)                      # plain dates, no tz


def session_close(df_1m: pd.DataFrame, freq: str) -> pd.Series:
    """
    Last price of each CME session period (daily or weekly).
    freq: 'D' for daily, 'W-FRI' for weekly (week ending Friday).
    """
    ct_close = df_1m["close"].tz_convert(CT)
    s_dates  = cme_session_dates(df_1m.index)
    # daily: last bar of each session date
    daily    = ct_close.groupby(s_dates).last()
    daily.index = pd.to_datetime(daily.index)
    if freq == "D":
        return daily
    # weekly: last session close of the week ending Friday
    return daily.resample("W-FRI").last().dropna()


def calc_daily_bx(df_1m: pd.DataFrame) -> pd.Series:
    """Daily BX on proper CME session closes (5 PM CT open → 4 PM CT close)."""
    return calc_bx(session_close(df_1m, "D"))


def calc_weekly_bx(df_1m: pd.DataFrame) -> pd.Series:
    """Weekly BX — week closes on Friday 4 PM CT."""
    return calc_bx(session_close(df_1m, "W-FRI"))


# ── simulation ─────────────────────────────────────────────────────────────────

def simulate(bars: pd.DataFrame, use_bx: bool = True) -> list[dict]:
    """
    Find all valid entry bars and pair each with its next opposite cross exit.
    Only one position at a time — next entry must be after the prior exit.
    use_bx=False: take every cross regardless of daily BX direction.
    """
    cross_up_times   = sorted(bars.index[bars["cross_up"]].tolist())
    cross_down_times = sorted(bars.index[bars["cross_down"]].tolist())

    if use_bx:
        entry_mask = (
            (bars["cross_up"]   & (bars["bx"] > 0)) |
            (bars["cross_down"] & (bars["bx"] < 0))
        )
    else:
        entry_mask = bars["cross_up"] | bars["cross_down"]

    entries = bars[entry_mask]

    trades      = []
    last_exit   = pd.Timestamp.min.tz_localize(ET)

    for ts, row in entries.iterrows():
        if ts < last_exit:
            continue

        if row["cross_up"]:
            direction  = "LONG"
            exit_pool  = cross_down_times
        else:
            direction  = "SHORT"
            exit_pool  = cross_up_times

        idx = bisect.bisect_right(exit_pool, ts)
        if idx < len(exit_pool):
            exit_ts    = exit_pool[idx]
            exit_price = bars.loc[exit_ts, "close"]
            open_end   = False
        else:
            exit_ts    = bars.index[-1]
            exit_price = bars.iloc[-1]["close"]
            open_end   = True

        last_exit = exit_ts

        raw_pnl = (exit_price - row["close"]) / row["close"] * 100
        pnl     = raw_pnl if direction == "LONG" else -raw_pnl
        hours   = (exit_ts - ts).total_seconds() / 3600

        trades.append({
            "entry_ts":   ts.isoformat(),
            "exit_ts":    exit_ts.isoformat(),
            "dir":        direction,
            "entry":      round(float(row["close"]),      4),
            "exit":       round(float(exit_price),        4),
            "pnl":        round(float(pnl),               4),
            "hours":      round(float(hours),             2),
            "bx_entry":   round(float(row["bx"]),         2),
            "wbx_entry":  round(float(row["weekly_bx"]),  2),
            "bx_rising":  bool(row["bx_rising"]),
            "wbx_rising": bool(row["wbx_rising"]),
            "open_end":   open_end,
        })

    return trades


# ── main ───────────────────────────────────────────────────────────────────────

def run(symbol: str, start: str = None, end: str = None, use_bx: bool = True):
    print(f"\nLoading {symbol} 1m data...")
    df = pd.read_parquet(DATA / f"{symbol}_1m.parquet")

    if start:
        df = df[df.index >= pd.Timestamp(start, tz="UTC")]
    if end:
        df = df[df.index <= pd.Timestamp(end, tz="UTC")]

    print(f"  {len(df):,} bars  |  {df.index[0].date()} → {df.index[-1].date()}")

    # Daily + weekly BX
    daily_bx  = calc_daily_bx(df)
    weekly_bx = calc_weekly_bx(df)

    # 3-minute bars
    print("Building 3-min bars...")
    bars = (
        df.resample("3min")
          .agg(open=("open", "first"), high=("high", "max"),
               low=("low", "min"),    close=("close", "last"),
               volume=("volume", "sum"))
          .dropna()
    )

    bars["ema34"] = bars["close"].ewm(span=EMA_FAST, adjust=False).mean()
    bars["ema50"] = bars["close"].ewm(span=EMA_SLOW, adjust=False).mean()

    prev34 = bars["ema34"].shift(1)
    prev50 = bars["ema50"].shift(1)
    bars["cross_up"]   = (bars["ema34"] > bars["ema50"]) & (prev34 <= prev50)
    bars["cross_down"] = (bars["ema34"] < bars["ema50"]) & (prev34 >= prev50)

    # Map prior completed daily and weekly BX onto each 3-min bar
    # Use CME session dates so bars after 5 PM CT are assigned to next day's session
    print("Mapping daily + weekly BX to 3-min bars...")
    bars_et       = bars.tz_convert(ET)
    bar_sdates    = cme_session_dates(bars_et.index)   # session date per 3-min bar

    def map_bx(bx_series: pd.Series) -> np.ndarray:
        bx_dates_list = bx_series.index.normalize().tolist()
        bx_arr        = bx_series.values
        out           = np.full(len(bars_et), np.nan)
        for d in bar_sdates.unique():
            idx = bisect.bisect_left(bx_dates_list, d) - 1
            if idx < 0:
                continue
            out[bar_sdates == d] = bx_arr[idx]
        return out

    bars_et = bars_et.copy()
    bars_et["bx"]        = map_bx(daily_bx)
    bars_et["bx_prev"]   = map_bx(daily_bx.shift(1))
    bars_et["weekly_bx"] = map_bx(weekly_bx)
    bars_et["wbx_prev"]  = map_bx(weekly_bx.shift(1))
    bars_et["bx_rising"]  = bars_et["bx"] > bars_et["bx_prev"]
    bars_et["wbx_rising"] = bars_et["weekly_bx"] > bars_et["wbx_prev"]
    bars_et = bars_et.dropna(subset=["bx", "bx_prev", "weekly_bx", "wbx_prev"])

    print("Running simulation...")
    trades = simulate(bars_et, use_bx=use_bx)

    # Summary stats
    closed   = [t for t in trades if not t["open_end"]]
    winners  = [t for t in closed if t["pnl"] > 0]
    losers   = [t for t in closed if t["pnl"] <= 0]

    total_pnl  = sum(t["pnl"] for t in closed)
    win_rate   = len(winners) / len(closed) * 100 if closed else 0
    gross_win  = sum(t["pnl"] for t in winners)
    gross_loss = abs(sum(t["pnl"] for t in losers))
    pf         = round(gross_win / gross_loss, 3) if gross_loss else None
    avg_win    = round(gross_win  / len(winners), 4) if winners else 0
    avg_loss   = round(-gross_loss / len(losers), 4) if losers else 0

    result = {
        "id":       f"{symbol}_v1_{date.today().strftime('%Y%m%d')}",
        "strategy": "3m_cross",
        "version":  "1.0",
        "symbol":   symbol,
        "run_date": date.today().isoformat(),
        "data_window": f"{df.index[0].date()} to {df.index[-1].date()}",
        "params": {
            "bx_l1": BX_L1, "bx_l2": BX_L2, "bx_l3": BX_L3,
            "ema_fast": EMA_FAST, "ema_slow": EMA_SLOW,
        },
        "summary": {
            "trades":    len(closed),
            "open":      sum(1 for t in trades if t["open_end"]),
            "winners":   len(winners),
            "losers":    len(losers),
            "win_rate":  round(win_rate, 1),
            "total_pnl": round(total_pnl, 4),
            "pf":        pf,
            "avg_win":   avg_win,
            "avg_loss":  avg_loss,
        },
        "trades": trades,
    }

    OUT.mkdir(exist_ok=True)
    fname = OUT / f"{symbol}_v1_{date.today().strftime('%Y%m%d')}.json"
    fname.write_text(json.dumps(result, indent=2, default=str))

    print(f"\n── {symbol} V1.0 ──────────────────────────────")
    print(f"  Trades    : {len(closed)}")
    print(f"  Win Rate  : {win_rate:.1f}%")
    print(f"  Total PnL : {total_pnl:.2f}%")
    print(f"  Profit Factor : {pf}")
    print(f"  Avg Win   : {avg_win:.2f}%  |  Avg Loss: {avg_loss:.2f}%")
    print(f"  Saved → {fname.relative_to(ROOT)}")

    bx_breakdown(trades)

    return result


def _side_stats(ts: list[dict]) -> dict:
    if not ts:
        return None
    wins   = [t for t in ts if t["pnl"] > 0]
    losses = [t for t in ts if t["pnl"] <= 0]
    wr     = len(wins) / len(ts) * 100
    total_pnl = sum(t["pnl"] for t in ts)

    def pts(t):
        raw = t["exit"] - t["entry"]
        return raw if t["dir"] == "LONG" else -raw

    win_pts  = [pts(t) for t in wins]
    loss_pts = [pts(t) for t in losses]
    avg_w_pts = sum(win_pts)  / len(win_pts)  if win_pts  else 0
    avg_l_pts = sum(loss_pts) / len(loss_pts) if loss_pts else 0

    return {
        "n":        len(ts),
        "wr":       wr,
        "avg_w":    avg_w_pts,
        "avg_l":    avg_l_pts,
        "total_pnl": total_pnl,
    }


def _fmt(s) -> str:
    if s is None:
        return f"{'—':>6} {'—':>6} {'—':>7} {'—':>7} {'—':>8}"
    return (
        f"{s['n']:>6} "
        f"{s['wr']:>5.1f}% "
        f"{s['avg_w']:>+7.1f} "
        f"{s['avg_l']:>+7.1f} "
        f"{s['total_pnl']:>+8.2f}%"
    )


def bx_breakdown(trades: list[dict]):
    """Side-by-side LONG vs SHORT broken down by daily BX direction × weekly BX direction."""
    closed = [t for t in trades if not t.get("open_end")]
    longs  = [t for t in closed if t["dir"] == "LONG"]
    shorts = [t for t in closed if t["dir"] == "SHORT"]

    # (daily_rising, weekly_rising) -> label
    keys = [
        (True,  True,  "D↑/W↑"),
        (True,  False, "D↑/W↓"),
        (False, True,  "D↓/W↑"),
        (False, False, "D↓/W↓"),
    ]

    def get_bucket(ts, dr, wr):
        return [t for t in ts if t["bx_rising"] == dr and t["wbx_rising"] == wr]

    col = "Trades  Win%  AvgW    AvgL   TotPnL"
    div = "─" * len(col)
    print(f"\n{'─'*92}")
    print(f"  {'Bucket':<10}  {'── LONG ' + '─'*30:<38}  {'── SHORT ' + '─'*28}")
    print(f"  {'':10}  {col}   {col}")
    print(f"  {'─'*10}  {div}   {div}")

    for (dr, wr, label) in keys:
        lb = get_bucket(longs,  dr, wr)
        sb = get_bucket(shorts, dr, wr)
        print(f"  {label:<10}  {_fmt(_side_stats(lb))}   {_fmt(_side_stats(sb))}")

    print(f"  {'─'*10}  {div}   {div}")
    print(f"  {'ALL':<10}  {_fmt(_side_stats(longs))}   {_fmt(_side_stats(shorts))}")
    print(f"{'─'*92}\n")


if __name__ == "__main__":
    args   = sys.argv[1:]
    sym    = args[0] if args else "GC"
    start  = args[1] if len(args) > 1 else None
    end    = args[2] if len(args) > 2 else None
    use_bx = "--no-bx" not in args
    run(sym, start, end, use_bx=use_bx)
