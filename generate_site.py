"""
generate_site.py — Trading Research Site Generator
Reads content/ and generates docs/ for GitHub Pages.

Usage:
    python3 generate_site.py

GitHub Pages setup:
    Settings → Pages → Source: Deploy from branch → main → /docs
    Site: https://sameerbode.github.io/trading-research
"""
import json, re, os
from pathlib import Path
from datetime import datetime

ROOT     = Path(__file__).parent
CONTENT  = ROOT / "content"
DOCS     = ROOT / "docs"
TICKERS  = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA"]
TODAY    = datetime.now().strftime("%b %d, %Y")

DOCS.mkdir(exist_ok=True)
(DOCS / "tickers").mkdir(exist_ok=True)
(DOCS / "strategy").mkdir(exist_ok=True)
(DOCS / "insights").mkdir(exist_ok=True)
(DOCS / ".nojekyll").touch()

# ── helpers ────────────────────────────────────────────────────────────────────

def color(v, positive_good=True):
    if v is None: return "#8b949e"
    if positive_good: return "#3fb950" if v >= 0 else "#f85149"
    return "#f85149" if v >= 0 else "#3fb950"

def pct(v, dec=2):
    if v is None: return "—"
    return f"{'+' if v>=0 else ''}{v:.{dec}f}%"

def load_latest_backtest(project_id):
    path = CONTENT / "projects" / project_id / "backtests"
    files = sorted(path.glob("*.json"), reverse=True)
    if not files: return None
    return json.loads(files[0].read_text())

def load_strategy(sid):
    f = CONTENT / "projects" / sid / "meta.json"
    return json.loads(f.read_text()) if f.exists() else None

def load_insights(project_id):
    insights = []
    for f in sorted((CONTENT / "projects" / project_id / "insights").glob("*.md"), reverse=True):
        text = f.read_text()
        meta = {}
        m = re.search(r'^---\n(.*?)\n---', text, re.DOTALL)
        if m:
            for line in m.group(1).split('\n'):
                if ':' in line:
                    k,v = line.split(':',1)
                    meta[k.strip()] = v.strip()
            body_start = text.index('---', 3) + 3
            meta['body'] = text[body_start:].strip()
        meta['file'] = f.stem
        insights.append(meta)
    return insights

# ── HTML shell ─────────────────────────────────────────────────────────────────

def shell(title, content, active="home", depth=0):
    prefix = "../" * depth
    nav_items = [
        ("home",     f"{prefix}index.html",             "Dashboard"),
        ("strategy", f"{prefix}strategy/crm_exit.html", "CRM Exit"),
        ("3m_cross", f"{prefix}strategy/3m_cross.html", "3Min Cross"),
        ("insights", f"{prefix}insights/index.html",    "Insights"),
    ]
    nav_html = ""
    for key, href, label in nav_items:
        cls = "active" if key == active else ""
        nav_html += f'<a href="{href}" class="nav-link {cls}">{label}</a>\n'

    ticker_links = ""
    for t in TICKERS:
        ticker_links += f'<a href="{prefix}tickers/{t.lower()}.html" class="dropdown-item">{t}</a>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Trading Research</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:'Inter',sans-serif;font-size:14px;line-height:1.6}}
a{{color:#58a6ff;text-decoration:none}}
a:hover{{color:#79c0ff}}
.navbar{{background:#161b22;border-bottom:1px solid #30363d;padding:0 24px;display:flex;align-items:center;height:56px;position:sticky;top:0;z-index:100}}
.brand{{font-weight:700;font-size:15px;color:#e6edf3;margin-right:32px;letter-spacing:-0.3px}}
.brand span{{color:#3fb950}}
.nav-link{{color:#8b949e;padding:0 12px;height:56px;display:inline-flex;align-items:center;font-size:13px;font-weight:500;border-bottom:2px solid transparent;transition:color .15s}}
.nav-link:hover{{color:#e6edf3}}
.nav-link.active{{color:#e6edf3;border-bottom-color:#3fb950}}
.dropdown{{position:relative;display:inline-block}}
.dropdown-btn{{background:none;border:none;color:#8b949e;font:500 13px 'Inter',sans-serif;padding:0 12px;height:56px;cursor:pointer;display:inline-flex;align-items:center;gap:4px}}
.dropdown-btn:hover{{color:#e6edf3}}
.dropdown-menu{{display:none;position:absolute;top:56px;left:0;background:#161b22;border:1px solid #30363d;border-radius:6px;min-width:120px;padding:4px 0;z-index:200}}
.dropdown:hover .dropdown-menu{{display:block}}
.dropdown-item{{display:block;padding:7px 14px;color:#8b949e;font-size:13px}}
.dropdown-item:hover{{color:#e6edf3;background:#21262d}}
.container{{max-width:1280px;margin:0 auto;padding:32px 24px}}
.page-title{{font-size:24px;font-weight:700;letter-spacing:-0.5px;margin-bottom:4px}}
.page-sub{{color:#8b949e;font-size:13px;margin-bottom:32px}}
.grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px}}
.grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px}}
.grid-2{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px;margin-bottom:32px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px}}
.card-title{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:#8b949e;margin-bottom:8px}}
.card-value{{font-size:28px;font-weight:700;letter-spacing:-1px}}
.card-sub{{font-size:12px;color:#8b949e;margin-top:4px}}
.section-title{{font-size:15px;font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #21262d}}
.chart-card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:24px;margin-bottom:24px}}
.chart-title{{font-size:13px;font-weight:600;color:#e6edf3;margin-bottom:4px}}
.chart-sub{{font-size:12px;color:#8b949e;margin-bottom:16px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#21262d;color:#8b949e;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;padding:10px 12px;text-align:left;border-bottom:1px solid #30363d}}
td{{padding:10px 12px;border-bottom:1px solid #21262d}}
tr:hover td{{background:#1c2128}}
tr:last-child td{{border-bottom:none}}
.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}}
.badge-green{{background:rgba(63,185,80,.15);color:#3fb950;border:1px solid rgba(63,185,80,.3)}}
.badge-red{{background:rgba(248,81,73,.15);color:#f85149;border:1px solid rgba(248,81,73,.3)}}
.badge-blue{{background:rgba(88,166,255,.15);color:#58a6ff;border:1px solid rgba(88,166,255,.3)}}
.badge-gray{{background:rgba(139,148,158,.15);color:#8b949e;border:1px solid rgba(139,148,158,.3)}}
.insight-card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;margin-bottom:16px}}
.insight-title{{font-size:15px;font-weight:600;margin-bottom:8px}}
.insight-meta{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}}
.insight-body{{color:#8b949e;font-size:13px;line-height:1.7}}
.tag{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;background:#21262d;color:#8b949e}}
.impact-high{{border-left:3px solid #f85149}}
.impact-medium{{border-left:3px solid #f0883e}}
.impact-low{{border-left:3px solid #3fb950}}
.rule-block{{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:16px;margin-bottom:12px;font-size:13px}}
.rule-label{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#8b949e;margin-bottom:6px}}
.rule-value{{color:#e6edf3;line-height:1.6}}
.ticker-nav{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}}
.ticker-btn{{padding:6px 14px;border-radius:6px;font-size:13px;font-weight:600;border:1px solid #30363d;background:#21262d;color:#8b949e;text-decoration:none}}
.ticker-btn:hover,.ticker-btn.active{{background:#388bfd20;border-color:#388bfd;color:#58a6ff}}
footer{{text-align:center;padding:32px;color:#484f58;font-size:12px;border-top:1px solid #21262d;margin-top:48px}}
@media(max-width:768px){{.grid-4{{grid-template-columns:repeat(2,1fr)}}.grid-3{{grid-template-columns:1fr}}.grid-2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<nav class="navbar">
  <div class="brand">Trading<span>Research</span></div>
  {nav_html}
  <div class="dropdown">
    <button class="dropdown-btn">Tickers ▾</button>
    <div class="dropdown-menu">{ticker_links}</div>
  </div>
  <div style="margin-left:auto;color:#484f58;font-size:12px">Updated {TODAY}</div>
</nav>
<div class="container">
{content}
</div>
<footer>sameerbode.github.io/trading-research · Built with Python + Plotly · {TODAY}</footer>
</body>
</html>"""

# ── chart helpers ──────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    font=dict(family="Inter, sans-serif", color="#e6edf3", size=12),
    margin=dict(l=16, r=16, t=24, b=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d"),
)

def fig_to_div(fig, div_id, height=360):
    import plotly.io as pio
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id=div_id,
                       config={"responsive": True, "displayModeBar": False})

# ── INDEX PAGE ─────────────────────────────────────────────────────────────────

def build_index(bt, strategy):
    import plotly.graph_objects as go

    tickers  = list(bt["tickers"].keys())
    summaries = {t: bt["tickers"][t]["summary"] for t in tickers}

    # summary stats
    total_trades  = sum(s["trades"] for s in summaries.values())
    avg_win_rate  = sum(s["win_rate"] for s in summaries.values()) / len(summaries)
    best_stock    = max(summaries, key=lambda t: summaries[t]["total_pnl"])
    best_opts     = max(summaries, key=lambda t: summaries[t]["opt_total_pnl"])

    # ── Chart 1: PnL comparison ───────────────────────────────────────────────
    sorted_t = sorted(tickers, key=lambda t: summaries[t]["total_pnl"])
    stock_pnls = [summaries[t]["total_pnl"] for t in sorted_t]
    opt_pnls   = [summaries[t]["opt_total_pnl"] for t in sorted_t]

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(name="Stock PnL %", x=sorted_t, y=stock_pnls, marker_color=["#3fb950" if v>=0 else "#f85149" for v in stock_pnls], text=[pct(v) for v in stock_pnls], textposition="outside"))
    fig1.add_trace(go.Bar(name="Options PnL %", x=sorted_t, y=opt_pnls, marker_color=["#388bfd" if v>=0 else "#da3633" for v in opt_pnls], opacity=0.75, text=[pct(v) for v in opt_pnls], textposition="outside"))
    fig1.add_hline(y=0, line_color="#30363d", line_width=1)
    fig1.update_layout(barmode="group", yaxis_ticksuffix="%", showlegend=True)
    chart1 = fig_to_div(fig1, "chart-pnl", 380)

    # ── Chart 2: Win Rate + PF ────────────────────────────────────────────────
    sorted_wr = sorted(tickers, key=lambda t: summaries[t]["win_rate"])
    win_rates  = [summaries[t]["win_rate"] for t in sorted_wr]
    pfs        = [summaries[t]["pf"] or 0 for t in sorted_wr]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Win Rate %", x=sorted_wr, y=win_rates, marker_color=["#3fb950" if v>=50 else "#f85149" for v in win_rates], text=[f"{v:.1f}%" for v in win_rates], textposition="outside", yaxis="y"))
    fig2.add_hline(y=50, line_color="#388bfd", line_dash="dash", line_width=1, annotation_text="50%", annotation_position="right")
    chart2 = fig_to_div(fig2, "chart-wr", 320)

    # ── Chart 3: Profit Factor ────────────────────────────────────────────────
    sorted_pf = sorted(tickers, key=lambda t: summaries[t]["pf"] or 0)
    pf_vals = [summaries[t]["pf"] or 0 for t in sorted_pf]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name="Profit Factor", x=sorted_pf, y=pf_vals, marker_color=["#3fb950" if v>=1 else "#f85149" for v in pf_vals], text=[f"{v:.2f}" for v in pf_vals], textposition="outside"))
    fig3.add_hline(y=1, line_color="#388bfd", line_dash="dash", line_width=1, annotation_text="1.0", annotation_position="right")
    chart3 = fig_to_div(fig3, "chart-pf", 320)

    # ── Chart 4: Stock vs Options scatter ─────────────────────────────────────
    fig4 = go.Figure()
    for t in tickers:
        s = summaries[t]
        fig4.add_trace(go.Scatter(
            x=[s["total_pnl"]], y=[s["opt_total_pnl"]],
            mode="markers+text", name=t,
            text=[t], textposition="top center",
            marker=dict(size=14, line=dict(width=1, color="#30363d")),
            hovertemplate=f"<b>{t}</b><br>Stock: {pct(s['total_pnl'])}<br>Options: {pct(s['opt_total_pnl'])}<extra></extra>"
        ))
    fig4.add_vline(x=0, line_color="#30363d", line_width=1)
    fig4.add_hline(y=0, line_color="#30363d", line_width=1)
    fig4.update_layout(xaxis_title="Stock PnL %", yaxis_title="Options PnL %", showlegend=False, xaxis_ticksuffix="%", yaxis_ticksuffix="%")
    chart4 = fig_to_div(fig4, "chart-scatter", 360)

    # ── Summary table ─────────────────────────────────────────────────────────
    rows = ""
    for t in sorted(tickers, key=lambda t: summaries[t]["total_pnl"], reverse=True):
        s = summaries[t]
        sc = color(s["total_pnl"]); oc = color(s["opt_total_pnl"])
        wrc = "#3fb950" if s["win_rate"]>=50 else "#f85149"
        pf_v = s["pf"]; pfc = "#3fb950" if pf_v and pf_v>=1 else "#f85149"
        pf_str = f"{pf_v:.2f}" if pf_v else "—"
        rows += f"""<tr>
          <td><a href="tickers/{t.lower()}.html" style="font-weight:600;color:#e6edf3">{t}</a></td>
          <td>{s['trades']}</td>
          <td style="color:{wrc};font-weight:600">{s['win_rate']}%</td>
          <td style="color:{sc};font-weight:600">{pct(s['total_pnl'])}</td>
          <td style="color:{pfc};font-weight:600">{pf_str}</td>
          <td>{s['opt_trades']}</td>
          <td style="color:{oc};font-weight:600">{pct(s['opt_total_pnl'])}</td>
        </tr>"""

    content = f"""
<div class="page-title">MAG7 Strategy Dashboard</div>
<div class="page-sub">V3.0 CRM Exit · {bt['data_window']} · CST RTH · Updated {TODAY}</div>

<div class="grid-4">
  <div class="card">
    <div class="card-title">Total Trades</div>
    <div class="card-value">{total_trades}</div>
    <div class="card-sub">Across all 7 tickers</div>
  </div>
  <div class="card">
    <div class="card-title">Avg Win Rate</div>
    <div class="card-value" style="color:{'#3fb950' if avg_win_rate>=50 else '#f85149'}">{avg_win_rate:.1f}%</div>
    <div class="card-sub">Across all tickers</div>
  </div>
  <div class="card">
    <div class="card-title">Best Stock PnL</div>
    <div class="card-value" style="color:#3fb950">{best_stock}</div>
    <div class="card-sub">{pct(summaries[best_stock]['total_pnl'])} stock return</div>
  </div>
  <div class="card">
    <div class="card-title">Best Options PnL</div>
    <div class="card-value" style="color:#388bfd">{best_opts}</div>
    <div class="card-sub">{pct(summaries[best_opts]['opt_total_pnl'])} options return</div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Stock PnL vs Options PnL by Ticker</div>
  <div class="chart-sub">Options dramatically amplify winning moves — and losing ones</div>
  {chart1}
</div>

<div class="grid-2">
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Win Rate by Ticker</div>
    <div class="chart-sub">Reference line at 50% — above = statistical edge</div>
    {chart2}
  </div>
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Profit Factor by Ticker</div>
    <div class="chart-sub">Reference line at 1.0 — above = profitable</div>
    {chart3}
  </div>
</div>
<br>

<div class="chart-card">
  <div class="chart-title">Stock PnL vs Options PnL — Quadrant View</div>
  <div class="chart-sub">Top-right = winning both. Top-left = options beat stock. Bottom = avoid.</div>
  {chart4}
</div>

<div class="section-title">All Tickers Summary</div>
<div class="chart-card" style="padding:0;overflow:hidden">
<table>
  <thead><tr>
    <th>Ticker</th><th>Trades</th><th>Win %</th><th>Stock PnL</th><th>Profit Factor</th><th>Opt Trades</th><th>Options PnL</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>
"""
    return shell("Dashboard", content, active="home", depth=0)

# ── TICKER PAGE ────────────────────────────────────────────────────────────────

def build_ticker(ticker, bt):
    import plotly.graph_objects as go

    data     = bt["tickers"][ticker]
    s        = data["summary"]
    trades   = data["trades"]
    valid    = [t for t in trades if not t["open_end"]]
    wins     = [t for t in valid if t["pnl"] > 0]
    losses   = [t for t in valid if t["pnl"] <= 0]
    opt_v    = [t for t in valid if t.get("opt_pnl") is not None]

    # ── Chart 1: Equity curve ─────────────────────────────────────────────────
    cumstock = []; cumopt = []; labels = []
    cs = co = 0
    for i, t in enumerate(valid):
        cs += t["pnl"]; cumstock.append(round(cs, 3))
        if t.get("opt_pnl") is not None:
            co += t["opt_pnl"]; cumopt.append(round(co, 3))
        else:
            cumopt.append(None)
        labels.append(f"T{i+1} {t['entry_ts'][:10]}")

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=list(range(1,len(cumstock)+1)), y=cumstock, name="Stock PnL", line=dict(color="#3fb950", width=2), fill="tozeroy", fillcolor="rgba(63,185,80,0.08)", hovertemplate="Trade %{x}<br>Cumulative: %{y:.2f}%<extra>Stock</extra>"))
    fig1.add_trace(go.Scatter(x=list(range(1,len(cumopt)+1)), y=cumopt, name="Options PnL", line=dict(color="#388bfd", width=2), fill="tozeroy", fillcolor="rgba(56,139,253,0.06)", hovertemplate="Trade %{x}<br>Cumulative: %{y:.2f}%<extra>Options</extra>"))
    fig1.add_hline(y=0, line_color="#30363d", line_width=1)
    fig1.update_layout(xaxis_title="Trade #", yaxis_ticksuffix="%", showlegend=True, legend=dict(orientation="h", y=1.1))
    chart1 = fig_to_div(fig1, f"chart-equity-{ticker}", 300)

    # ── Chart 2: Trade scatter (duration vs PnL) ──────────────────────────────
    fig2 = go.Figure()
    for t in valid:
        col  = "#3fb950" if t["pnl"]>0 else "#f85149"
        fig2.add_trace(go.Scatter(
            x=[t["days"]], y=[t["pnl"]],
            mode="markers",
            marker=dict(size=max(8, t["ch_width"]*4), color=col, opacity=0.8, line=dict(width=1, color="#30363d")),
            name="W" if t["pnl"]>0 else "L",
            showlegend=False,
            hovertemplate=f"<b>T{valid.index(t)+1}</b><br>{t['entry_ts'][:10]}<br>{t['dir']} {pct(t['pnl'])}<br>Days: {t['days']}<br>Ch Width: ${t['ch_width']:.2f}<extra></extra>"
        ))
    fig2.add_hline(y=0, line_color="#30363d", line_width=1)
    fig2.update_layout(xaxis_title="Days Held", yaxis_title="PnL %", yaxis_ticksuffix="%", showlegend=False)
    chart2 = fig_to_div(fig2, f"chart-scatter-{ticker}", 300)

    # ── Chart 3: Win/Loss donut ───────────────────────────────────────────────
    fig3 = go.Figure(go.Pie(
        labels=["Winners","Losers"], values=[len(wins),len(losses)],
        marker=dict(colors=["#3fb950","#f85149"]),
        hole=0.6, textinfo="label+percent", hoverinfo="label+value"
    ))
    fig3.add_annotation(text=f"{s['win_rate']}%<br><span style='font-size:10px'>Win</span>", x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#e6edf3"))
    chart3 = fig_to_div(fig3, f"chart-donut-{ticker}", 260)

    # ── Chart 4: Options vs Stock per trade ───────────────────────────────────
    if opt_v:
        fig4 = go.Figure()
        cols = ["#3fb950" if t["opt_pnl"]>0 else "#f85149" for t in opt_v]
        hover = [f"T{valid.index(t)+1} {t['entry_ts'][:10]}<br>Stock: {pct(t['pnl'])}<br>Options: {pct(t['opt_pnl'])}" for t in opt_v]
        fig4.add_trace(go.Scatter(
            x=[t["pnl"] for t in opt_v], y=[t["opt_pnl"] for t in opt_v],
            mode="markers", marker=dict(size=10, color=cols, opacity=0.85, line=dict(width=1,color="#30363d")),
            hovertemplate="%{customdata}<extra></extra>", customdata=hover
        ))
        fig4.add_vline(x=0, line_color="#30363d", line_width=1)
        fig4.add_hline(y=0, line_color="#30363d", line_width=1)
        fig4.update_layout(xaxis_title="Stock PnL %", yaxis_title="Options PnL %", xaxis_ticksuffix="%", yaxis_ticksuffix="%", showlegend=False)
        chart4 = fig_to_div(fig4, f"chart-opts-{ticker}", 300)
    else:
        chart4 = "<p style='color:#8b949e;text-align:center;padding:40px'>No options data</p>"

    # ── Trade table ───────────────────────────────────────────────────────────
    rows = ""
    for i, t in enumerate(trades):
        pnl_s  = pct(t["pnl"]) if not t["open_end"] else "open"
        pnl_c  = color(t.get("pnl")) if not t["open_end"] else "#f0883e"
        opt_s  = pct(t.get("opt_pnl")) if t.get("opt_pnl") is not None else "—"
        opt_c  = color(t.get("opt_pnl"))
        dir_b  = f'<span class="badge badge-{"green" if t["dir"]=="LONG" else "red"}">{t["dir"]}</span>'
        entry  = t["entry_ts"][5:16].replace("T"," ")
        exit_s = t["exit_ts"][5:16].replace("T"," ") if not t["open_end"] else '<span style="color:#f0883e">open</span>'
        rows += f"""<tr>
          <td style="color:#8b949e">{i+1}</td>
          <td>{entry}</td><td>{exit_s}</td>
          <td style="color:#8b949e">{t['days']}d</td>
          <td>{dir_b}</td>
          <td>${t['entry']:.2f}</td><td>${t['exit']:.2f}</td>
          <td style="color:{pnl_c};font-weight:600">{pnl_s}</td>
          <td style="color:#3fb950">{pct(t.get('mfe')) if not t['open_end'] else '—'}</td>
          <td style="color:#f85149">{pct(t.get('mae')) if not t['open_end'] else '—'}</td>
          <td style="color:#8b949e">${t['ch_width']:.2f}</td>
          <td style="color:{opt_c};font-weight:600">{opt_s}</td>
        </tr>"""

    # ticker nav
    ticker_nav = '<div class="ticker-nav">'
    for t in TICKERS:
        cls = "active" if t == ticker else ""
        ticker_nav += f'<a href="{t.lower()}.html" class="ticker-btn {cls}">{t}</a>'
    ticker_nav += "</div>"

    sc = color(s["total_pnl"]); oc = color(s["opt_total_pnl"])
    wrc = "#3fb950" if s["win_rate"]>=50 else "#f85149"
    pf_v = s["pf"]

    content = f"""
<div class="page-title">{ticker}</div>
<div class="page-sub">V3.0 CRM Exit · {bt['data_window']} · {s['trades']} trades</div>

{ticker_nav}

<div class="grid-4">
  <div class="card"><div class="card-title">Win Rate</div><div class="card-value" style="color:{wrc}">{s['win_rate']}%</div><div class="card-sub">{s['winners']}W / {s['losers']}L</div></div>
  <div class="card"><div class="card-title">Stock PnL</div><div class="card-value" style="color:{sc}">{pct(s['total_pnl'])}</div><div class="card-sub">Avg W: {pct(s['avg_win'])} / L: {pct(s['avg_loss'])}</div></div>
  <div class="card"><div class="card-title">Profit Factor</div><div class="card-value" style="color:{'#3fb950' if pf_v and pf_v>=1 else '#f85149'}">{f'{pf_v:.2f}' if pf_v else '—'}</div><div class="card-sub">Gross win / gross loss</div></div>
  <div class="card"><div class="card-title">Options PnL</div><div class="card-value" style="color:{oc}">{pct(s['opt_total_pnl'])}</div><div class="card-sub">{s['opt_winners']}W / {s['opt_trades']-s['opt_winners']}L · {s['opt_win_rate']}% win</div></div>
</div>

<div class="chart-card">
  <div class="chart-title">Cumulative Equity Curve</div>
  <div class="chart-sub">Stock and options PnL accumulated trade by trade</div>
  {chart1}
</div>

<div class="grid-2">
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Trade Duration vs PnL</div>
    <div class="chart-sub">Bubble size = channel width · Green = winner · Red = loser</div>
    {chart2}
  </div>
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Win / Loss Split</div>
    <div class="chart-sub">Stock trade outcomes</div>
    {chart3}
  </div>
</div>
<br>
<div class="chart-card">
  <div class="chart-title">Options PnL vs Stock PnL per Trade</div>
  <div class="chart-sub">Shows amplification — big stock moves = outsized options wins (and losses)</div>
  {chart4}
</div>

<div class="section-title">All Trades</div>
<div class="chart-card" style="padding:0;overflow:hidden;overflow-x:auto">
<table>
  <thead><tr><th>#</th><th>Entry</th><th>Exit</th><th>Days</th><th>Dir</th><th>Entry $</th><th>Exit $</th><th>PnL</th><th>Max Profit</th><th>Max Loss</th><th>Ch Width</th><th>Opt PnL</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>
"""
    return shell(ticker, content, active="tickers", depth=1)

# ── STRATEGY PAGE ──────────────────────────────────────────────────────────────

def build_strategy(strategy, bt):
    import plotly.graph_objects as go

    versions = strategy["versions"]
    v_names  = [v["version"] for v in versions]
    v_pnls   = [v.get("tsla_stock_pnl", 0) for v in versions]
    v_wrs    = [v.get("tsla_win_rate", 0) for v in versions]
    v_trades = [v.get("tsla_trades", 0) for v in versions]

    # ── Chart: Version evolution ──────────────────────────────────────────────
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(name="Stock PnL %", x=v_names, y=v_pnls, marker_color=["#3fb950" if v>=0 else "#f85149" for v in v_pnls], text=[f"{pct(v)}" for v in v_pnls], textposition="outside"))
    fig1.add_hline(y=0, line_color="#30363d", line_width=1)
    fig1.update_layout(xaxis_title="Version", yaxis_ticksuffix="%", showlegend=False)
    chart1 = fig_to_div(fig1, "chart-versions", 320)

    # ── Exit comparison chart ─────────────────────────────────────────────────
    exits = ["34/50 only", "8/21 only (V3)", "5/12 only"]
    stock = [5.28, 11.60, 3.34]
    opts  = [-17.12, 178.13, 57.92]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Stock PnL %", x=exits, y=stock, marker_color=["#3fb950" if v>=0 else "#f85149" for v in stock], text=[pct(v) for v in stock], textposition="outside"))
    fig2.add_trace(go.Bar(name="Options PnL %", x=exits, y=opts, marker_color=["#388bfd" if v>=0 else "#da3633" for v in opts], text=[pct(v) for v in opts], textposition="outside", opacity=0.8))
    fig2.add_hline(y=0, line_color="#30363d", line_width=1)
    fig2.update_layout(barmode="group", yaxis_ticksuffix="%")
    chart2 = fig_to_div(fig2, "chart-exits", 340)

    # ── Version cards ─────────────────────────────────────────────────────────
    version_rows = ""
    for v in versions:
        pnl_c = "#3fb950" if v.get("tsla_stock_pnl",0)>=0 else "#f85149"
        badge = '<span class="badge badge-green">Current</span>' if v["version"]=="3.0" else ""
        version_rows += f"""<tr>
          <td style="font-weight:600">V{v['version']} {badge}</td>
          <td>{v['name']}</td>
          <td style="color:#8b949e;font-size:12px">{v['entry'][:60]}...</td>
          <td style="color:#8b949e;font-size:12px">{v['exit']}</td>
          <td style="color:{pnl_c};font-weight:600">{pct(v.get('tsla_stock_pnl'))}</td>
          <td style="color:#8b949e">{v.get('tsla_win_rate',0):.1f}%</td>
          <td style="color:#8b949e">{v.get('tsla_trades',0)}</td>
        </tr>"""

    rules = strategy["current_rules"]
    insight_html = ""
    for ins in strategy["key_insights"]:
        insight_html += f'<div style="padding:8px 0;border-bottom:1px solid #21262d;font-size:13px;color:#8b949e">💡 {ins}</div>\n'

    question_html = ""
    for q in strategy["open_questions"]:
        question_html += f'<div style="padding:8px 0;border-bottom:1px solid #21262d;font-size:13px;color:#8b949e">❓ {q}</div>\n'

    content = f"""
<div class="page-title">CRM Exit Strategy</div>
<div class="page-sub">Channel Rejection + Momentum Exit · V3.0 · Active</div>

<div class="grid-2">
  <div>
    <div class="section-title">Current Rules — V3.0</div>
    <div class="rule-block"><div class="rule-label">Bias</div><div class="rule-value">{rules['bias']}</div></div>
    <div class="rule-block"><div class="rule-label">Entry</div><div class="rule-value">{rules['entry']}</div></div>
    <div class="rule-block"><div class="rule-label">Exit</div><div class="rule-value">{rules['exit']}</div></div>
    <div class="rule-block"><div class="rule-label">Session</div><div class="rule-value">{rules['session']}</div></div>
    <div class="rule-block"><div class="rule-label">Options</div><div class="rule-value">{rules['options']}</div></div>
  </div>
  <div>
    <div class="section-title">Key Insights</div>
    <div class="chart-card" style="padding:12px">{insight_html}</div>
    <div class="section-title" style="margin-top:20px">Open Questions</div>
    <div class="chart-card" style="padding:12px">{question_html}</div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">TSLA Stock PnL — Strategy Version Evolution</div>
  <div class="chart-sub">Every version tested on the same TSLA 60-day window</div>
  {chart1}
</div>

<div class="chart-card">
  <div class="chart-title">Exit EMA Comparison (V3.0 entry rules, no opposite side close)</div>
  <div class="chart-sub">8/21 exit dominates — best stock PnL and by far best options PnL</div>
  {chart2}
</div>

<div class="section-title">Version History</div>
<div class="chart-card" style="padding:0;overflow:hidden;overflow-x:auto">
<table>
  <thead><tr><th>Version</th><th>Name</th><th>Entry</th><th>Exit</th><th>TSLA PnL</th><th>Win%</th><th>Trades</th></tr></thead>
  <tbody>{version_rows}</tbody>
</table>
</div>
"""
    return shell("Strategy — CRM Exit", content, active="strategy", depth=1)

# ── INSIGHTS PAGE ──────────────────────────────────────────────────────────────

def build_insights(insights):
    cards = ""
    for ins in insights:
        impact = ins.get("impact","medium")
        tags   = [t.strip() for t in ins.get("tags","").strip("[]").split(",") if t.strip()]
        tag_html = " ".join(f'<span class="tag">{t}</span>' for t in tags)
        cards += f"""
<div class="insight-card impact-{impact}">
  <div class="insight-title">{ins.get('title','')}</div>
  <div class="insight-meta">
    <span style="color:#8b949e;font-size:12px">📅 {ins.get('date','')}</span>
    <span class="badge badge-{'red' if impact=='high' else 'blue' if impact=='medium' else 'gray'}">{impact} impact</span>
    {tag_html}
  </div>
  <div class="insight-body">{ins.get('body','').replace(chr(10),'<br>')}</div>
</div>"""

    content = f"""
<div class="page-title">Insights</div>
<div class="page-sub">Lessons learned, observations, and decisions — captured as they happen</div>
<div style="max-width:800px">
{cards}
</div>
"""
    return shell("Insights", content, active="insights", depth=1)

# ── PUBLISH PAGE ──────────────────────────────────────────────────────────────

def build_publish_page(project_id):
    import markdown as md
    f = CONTENT / "projects" / project_id / "publish.md"
    if not f.exists():
        return None

    raw  = f.read_text()
    # strip frontmatter
    body = re.sub(r'^---\n.*?\n---\n', '', raw, flags=re.DOTALL).strip()

    html = md.markdown(body, extensions=["tables", "fenced_code"])

    # inject site styling onto generated elements
    html = html.replace('<table>', '<table class="publish-table">')
    html = html.replace('<blockquote>', '<blockquote class="publish-quote">')

    content = f"""
<style>
.publish-wrap{{max-width:900px}}
.publish-wrap h2{{font-size:18px;font-weight:700;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #21262d}}
.publish-wrap h3{{font-size:14px;font-weight:600;margin:24px 0 10px;color:#8b949e;text-transform:uppercase;letter-spacing:.6px}}
.publish-wrap p{{color:#8b949e;font-size:13px;line-height:1.8;margin-bottom:12px}}
.publish-wrap ul,.publish-wrap ol{{color:#8b949e;font-size:13px;line-height:1.8;padding-left:20px;margin-bottom:12px}}
.publish-wrap li{{margin-bottom:4px}}
.publish-wrap code{{background:#21262d;border-radius:4px;padding:2px 6px;font-size:12px;color:#79c0ff}}
.publish-wrap pre{{background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:16px;overflow-x:auto;margin-bottom:16px}}
.publish-wrap pre code{{background:none;padding:0;color:#e6edf3;font-size:12px}}
.publish-table{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px}}
.publish-table th{{background:#21262d;color:#8b949e;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;padding:10px 14px;text-align:left;border-bottom:1px solid #30363d}}
.publish-table td{{padding:12px 14px;border-bottom:1px solid #21262d;vertical-align:top;color:#e6edf3;line-height:1.7}}
.publish-table tr:hover td{{background:#1c2128}}
.publish-table tr:last-child td{{border-bottom:none}}
.publish-quote{{border-left:3px solid #388bfd;margin:16px 0;padding:12px 16px;background:#161b22;border-radius:0 6px 6px 0}}
.publish-quote p{{margin:0;color:#8b949e;font-size:13px;line-height:1.7}}
strong{{color:#e6edf3}}
</style>
<div class="publish-wrap">
{html}
</div>
"""
    title = f.read_text().split("title:")[1].split("\n")[0].strip() if "title:" in f.read_text() else project_id
    return shell(title, content, active=project_id, depth=1)


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    print("\nBuilding site...\n")
    bt       = load_latest_backtest("crm_exit")
    strategy = load_strategy("crm_exit")
    insights = load_insights("crm_exit")

    if not bt:
        print("  No backtest data found in content/projects/crm_exit/backtests/"); return

    # Index
    (DOCS / "index.html").write_text(build_index(bt, strategy))
    print("  ✓ index.html")

    # Strategy
    if strategy:
        (DOCS / "strategy" / "crm_exit.html").write_text(build_strategy(strategy, bt))
        print("  ✓ strategy/crm_exit.html")

    # Tickers
    for ticker in TICKERS:
        if ticker in bt["tickers"]:
            (DOCS / "tickers" / f"{ticker.lower()}.html").write_text(build_ticker(ticker, bt))
            print(f"  ✓ tickers/{ticker.lower()}.html")

    # Insights
    if insights:
        (DOCS / "insights" / "index.html").write_text(build_insights(insights))
        print("  ✓ insights/index.html")

    # Publish pages
    p = build_publish_page("3m_cross")
    if p:
        (DOCS / "strategy" / "3m_cross.html").write_text(p)
        print("  ✓ strategy/3m_cross.html")

    print(f"\n  Site → {DOCS}/")
    print(f"  Push to GitHub → live at https://sameerbode.github.io/trading-research\n")

if __name__ == "__main__":
    main()
