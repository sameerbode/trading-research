"""
generate_site.py — Trading Research Site Generator
Reads content/ and generates docs/ for GitHub Pages.

Usage:
    python3 generate_site.py

GitHub Pages setup:
    Settings → Pages → Source: GitHub Actions (custom deploy.yml)
    Site: https://sameerbode.github.io/trading-research
"""
import json, re, os
from pathlib import Path
from datetime import datetime

ROOT    = Path(__file__).parent
CONTENT = ROOT / "content"
DOCS    = ROOT / "docs"
TICKERS = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA"]
FUTURES = ["GC", "CL"]
TODAY   = datetime.now().strftime("%b %d, %Y")

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

def load_3m_cross_bt(symbol):
    path = CONTENT / "projects" / "3m_cross" / "backtests"
    files = sorted(path.glob(f"{symbol}_v1_*.json"), reverse=True)
    if not files: return None
    return json.loads(files[0].read_text())

def load_strategy(sid):
    f = CONTENT / "projects" / sid / "meta.json"
    return json.loads(f.read_text()) if f.exists() else None

def load_insights():
    """Aggregate insights from all project insight folders + content/insights/."""
    insights = []
    proj_root = CONTENT / "projects"
    if proj_root.exists():
        for proj_dir in sorted(proj_root.iterdir()):
            if not proj_dir.is_dir(): continue
            ins_dir = proj_dir / "insights"
            if not ins_dir.exists(): continue
            for f in sorted(ins_dir.glob("*.md"), reverse=True):
                text = f.read_text()
                meta = {"strategy": proj_dir.name}
                m = re.search(r'^---\n(.*?)\n---', text, re.DOTALL)
                if m:
                    for line in m.group(1).split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            meta[k.strip()] = v.strip()
                    body_start = text.index('---', 3) + 3
                    meta['body'] = text[body_start:].strip()
                meta['file'] = f.stem
                insights.append(meta)
    shared_dir = CONTENT / "insights"
    if shared_dir.exists():
        for f in sorted(shared_dir.glob("*.md"), reverse=True):
            text = f.read_text()
            meta = {"strategy": "shared"}
            m = re.search(r'^---\n(.*?)\n---', text, re.DOTALL)
            if m:
                for line in m.group(1).split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        meta[k.strip()] = v.strip()
                body_start = text.index('---', 3) + 3
                meta['body'] = text[body_start:].strip()
            meta['file'] = f.stem
            insights.append(meta)
    return sorted(insights, key=lambda x: x.get("date", ""), reverse=True)

def bucket_stats_from_bt(bt, direction=None):
    """Per-bucket PnL stats from a 3m_cross backtest JSON."""
    if not bt: return {}
    closed = [t for t in bt["trades"] if not t.get("open_end")]
    if direction:
        closed = [t for t in closed if t["dir"] == direction]
    result = {}
    for dr in [True, False]:
        for wr in [True, False]:
            label = f"{'D↑' if dr else 'D↓'}/{'W↑' if wr else 'W↓'}"
            bucket = [t for t in closed if t["bx_rising"] == dr and t["wbx_rising"] == wr]
            wins = [t for t in bucket if t["pnl"] > 0]
            result[label] = {
                "n": len(bucket),
                "pnl": round(sum(t["pnl"] for t in bucket), 2),
                "wr": round(len(wins) / len(bucket) * 100, 1) if bucket else 0,
            }
    return result

# ── Interactive equity curve ───────────────────────────────────────────────────

def build_interactive_equity_chart(bt_by_sym, uid="eq0", height=340):
    """
    Embed trade data + JS controls (symbol / direction / bucket) into the page.
    bt_by_sym: {symbol: bt_json}  — works for 1 or 2 symbols.
    uid must be alphanumeric (used as JS identifier prefix and HTML element id prefix).
    When multiple symbols are present a "Both" option renders both traces simultaneously,
    each symbol keeping its own independent direction/bucket settings.
    """
    symbols     = list(bt_by_sym.keys())
    default_sym = symbols[0]
    _COLORS = {"GC": "#3fb950", "CL": "#388bfd", "ES": "#f0883e", "NQ": "#bc8cff"}

    def encode(bt):
        if not bt: return []
        closed = sorted([t for t in bt["trades"] if not t.get("open_end")],
                        key=lambda x: x["entry_ts"])
        return [[1 if t["bx_rising"] else 0,
                 1 if t["wbx_rising"] else 0,
                 1 if t["dir"] == "LONG" else 0,
                 round(t["pnl"], 4)]
                for t in closed]

    data_js   = json.dumps({s: encode(bt) for s, bt in bt_by_sym.items()})
    syms_js   = json.dumps(symbols)
    def_js    = json.dumps(default_sym)
    colors_js = json.dumps({s: _COLORS.get(s, "#58a6ff") for s in symbols})

    # Symbol selector — shown when > 1 symbol; includes a "Both" button
    sym_html = ""
    if len(symbols) > 1:
        btns = "".join(
            f'<button class="filter-btn sym-btn{"  active" if i == 0 else ""}" '
            f"data-sym=\"{sym}\" onclick=\"eqSwitchSym{uid}('{sym}')\">{sym}</button>"
            for i, sym in enumerate(symbols)
        )
        btns += (f'<button class="filter-btn sym-btn" data-sym="both" '
                 f"onclick=\"eqSwitchSym{uid}('both')\">Both</button>")
        sym_html = (f'<div><div class="ctrl-label">Symbol</div>'
                    f'<div style="display:flex;gap:6px">{btns}</div></div>')

    bucket_names = ["D↑/W↑", "D↑/W↓", "D↓/W↑", "D↓/W↓"]
    buckets_html = "".join(
        f'<label class="bucket-label">'
        f'<input type="checkbox" class="bucket-cb" id="{uid}bc{i}" data-bi="{i}" checked '
        f"onchange=\"eqToggleBucket{uid}({i})\"> {bl}</label>"
        for i, bl in enumerate(bucket_names)
    )

    # JS written as a regular string; __PLACEHOLDERS__ replaced afterwards
    # "both" mode: each symbol uses its own stored state; direction/bucket controls
    # update the currently-active symbol's state (or the shared 'both' slot isn't used —
    # the controls are per-symbol, remembered independently).
    js_raw = r"""(function(){
  var UID='__UID__', DATA=__DATA__, SYMS=__SYMS__, COLORS=__COLORS__;
  var state={};
  SYMS.forEach(function(s){ state[s]={dir:'both', buckets:[1,1,1,1]}; });
  // 'both' view uses each symbol's own state — no shared slot needed.
  var cur=__DEF__;

  function bucketIdx(d,w){ return d&&w?0 : d&&!w?1 : !d&&w?2 : 3; }

  function applyFilter(trades, s){
    return trades.filter(function(t){
      if(!s.buckets[bucketIdx(t[0],t[1])]) return false;
      if(s.dir==='long'  && !t[2]) return false;
      if(s.dir==='short' &&  t[2]) return false;
      return true;
    });
  }

  function symStats(sym){
    var t=applyFilter(DATA[sym], state[sym]);
    var n=t.length, w=t.filter(function(x){return x[3]>0;}).length;
    var p=t.reduce(function(s,x){return s+x[3];},0);
    return {trades:t, n:n, wr:n>0?(w/n*100).toFixed(1)+'%':'—',
            pnl:p, pnlStr:(p>=0?'+':'')+p.toFixed(2)+'%',
            pnlColor:p>=0?'#3fb950':'#f85149'};
  }

  var LAYOUT={
    paper_bgcolor:'#161b22', plot_bgcolor:'#161b22',
    font:{family:'Inter,sans-serif', color:'#e6edf3', size:12},
    margin:{l:44, r:16, t:12, b:40},
    xaxis:{title:'Trade #', gridcolor:'#21262d', zerolinecolor:'#30363d'},
    yaxis:{ticksuffix:'%',  gridcolor:'#21262d', zerolinecolor:'#30363d'},
    shapes:[{type:'line', x0:0, x1:1, xref:'paper', y0:0, y1:0,
             line:{color:'#30363d', width:1}}]
  };

  function render(){
    var traces=[], statsHtml='';

    if(cur==='both'){
      SYMS.forEach(function(sym){
        var st=symStats(sym), cum=0;
        var y=st.trades.map(function(t){cum+=t[3];return+cum.toFixed(4);});
        var x=Array.from({length:y.length},function(_,i){return i+1;});
        traces.push({x:x,y:y,type:'scatter',mode:'lines',name:sym,
          line:{color:COLORS[sym],width:2},
          hovertemplate:'Trade %{x}<br>Cum PnL: %{y:.2f}%<extra>'+sym+'</extra>'});
        statsHtml+='<span style="color:#8b949e">'+sym
          +' <strong style="color:#e6edf3">'+st.n.toLocaleString()+'</strong> trades'
          +' · <strong style="color:#e6edf3">'+st.wr+'</strong> WR'
          +' · <strong style="color:'+st.pnlColor+'">'+st.pnlStr+'</strong></span>'
          +'<span style="color:#30363d;padding:0 10px">|</span>';
      });
      statsHtml=statsHtml.replace(/<span[^>]*>\|<\/span>$/,''); // trim trailing |
      LAYOUT.showlegend=true;
      LAYOUT.legend={orientation:'h',y:1.08,bgcolor:'rgba(0,0,0,0)'};
    } else {
      var st=symStats(cur), cum=0;
      var y=st.trades.map(function(t){cum+=t[3];return+cum.toFixed(4);});
      var x=Array.from({length:y.length},function(_,i){return i+1;});
      var col=COLORS[cur];
      traces.push({x:x,y:y,type:'scatter',mode:'lines',name:cur,
        line:{color:col,width:2},fill:'tozeroy',fillcolor:col+'14',
        hovertemplate:'Trade %{x}<br>Cum PnL: %{y:.2f}%<extra>'+cur+'</extra>'});
      statsHtml='<span style="color:#8b949e">Trades <strong style="color:#e6edf3">'+st.n.toLocaleString()+'</strong></span>'
        +'<span style="color:#8b949e">Win Rate <strong style="color:#e6edf3">'+st.wr+'</strong></span>'
        +'<span style="color:#8b949e">PnL <strong style="color:'+st.pnlColor+'">'+st.pnlStr+'</strong></span>';
      LAYOUT.showlegend=false;
      delete LAYOUT.legend;
    }

    Plotly.react(UID+'-chart', traces, LAYOUT, {responsive:true,displayModeBar:false});
    document.getElementById(UID+'-statsrow').innerHTML=statsHtml;
  }

  function curState(){ return cur==='both' ? null : state[cur]; }

  function syncUI(){
    var s=curState();
    var wrap=document.getElementById(UID+'-wrap');
    wrap.querySelectorAll('.sym-btn').forEach(function(b){
      b.classList.toggle('active', b.dataset.sym===cur);
    });
    // In 'both' mode keep the dir/bucket controls showing last single-sym state
    // (controls still work — they update whichever single symbol was last active)
    if(s){
      wrap.querySelectorAll('.dir-btn').forEach(function(b){
        b.classList.toggle('active', b.dataset.dir===s.dir);
      });
      [0,1,2,3].forEach(function(i){
        var cb=document.getElementById(UID+'bc'+i);
        if(cb) cb.checked=!!s.buckets[i];
      });
    }
  }

  // When in 'both' mode, direction/bucket changes affect the LAST selected single symbol
  var lastSingle=__DEF__;

  window['eqSwitchSym'+UID] = function(sym){
    if(sym!=='both') lastSingle=sym;
    cur=sym; syncUI(); render();
  };
  window['eqSetDir'+UID] = function(dir){
    state[lastSingle].dir=dir; syncUI(); render();
  };
  window['eqToggleBucket'+UID] = function(idx){
    state[lastSingle].buckets[idx]=state[lastSingle].buckets[idx]?0:1; render();
  };

  if(typeof Plotly!=='undefined'){ render(); } else { window.addEventListener('load', render); }
})();"""

    js = (js_raw
          .replace("__DATA__",   data_js)
          .replace("__SYMS__",   syms_js)
          .replace("__COLORS__", colors_js)
          .replace("__DEF__",    def_js)
          .replace("__UID__",    uid))

    return f"""<div id="{uid}-wrap">
<style>
.filter-btn{{background:#21262d;border:1px solid #30363d;border-radius:6px;color:#8b949e;font:500 12px 'Inter',sans-serif;padding:5px 12px;cursor:pointer;transition:all .15s}}
.filter-btn:hover{{color:#e6edf3;border-color:#8b949e}}
.filter-btn.active{{background:#388bfd20;border-color:#388bfd;color:#58a6ff}}
.ctrl-label{{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#8b949e;margin-bottom:6px}}
.bucket-label{{display:flex;align-items:center;gap:6px;font-size:13px;color:#8b949e;cursor:pointer;user-select:none}}
.bucket-label input{{cursor:pointer;accent-color:#388bfd;width:14px;height:14px}}
</style>
<div style="display:flex;gap:20px;align-items:flex-start;margin-bottom:16px;flex-wrap:wrap">
  {sym_html}
  <div>
    <div class="ctrl-label">Direction</div>
    <div style="display:flex;gap:6px">
      <button class="filter-btn dir-btn active" data-dir="both"  onclick="eqSetDir{uid}('both')">Both</button>
      <button class="filter-btn dir-btn"        data-dir="long"  onclick="eqSetDir{uid}('long')">Long</button>
      <button class="filter-btn dir-btn"        data-dir="short" onclick="eqSetDir{uid}('short')">Short</button>
    </div>
  </div>
  <div>
    <div class="ctrl-label">Buckets</div>
    <div style="display:flex;gap:14px;flex-wrap:wrap">{buckets_html}</div>
  </div>
  <div style="margin-left:auto;padding-top:2px">
    <div class="ctrl-label">Stats</div>
    <div id="{uid}-statsrow" style="display:flex;gap:20px;flex-wrap:wrap;font-size:13px">—</div>
  </div>
</div>
<div id="{uid}-chart" style="height:{height}px"></div>
<script>{js}</script>
</div>"""

# ── HTML shell ─────────────────────────────────────────────────────────────────

def shell(title, content, active="home", depth=0):
    prefix = "../" * depth

    nav_links = [
        ("home",     f"{prefix}index.html",          "Dashboard"),
        ("insights", f"{prefix}insights/index.html", "Insights"),
    ]
    strategy_links = [
        (f"{prefix}strategy/crm_exit.html",    "CRM Exit"),
        (f"{prefix}strategy/3m_cross.html",    "3Min Cross GC"),
        (f"{prefix}strategy/3m_cross_cl.html", "3Min Cross CL"),
    ]

    nav_html = ""
    for key, href, label in nav_links:
        cls = "active" if key == active else ""
        nav_html += f'<a href="{href}" class="nav-link {cls}">{label}</a>\n'

    strat_active = "active" if active in ("strategy", "3m_cross", "3m_cross_cl") else ""
    strat_items  = "".join(
        f'<a href="{href}" class="dropdown-item">{label}</a>' for href, label in strategy_links
    )

    ticker_items = "".join(
        f'<a href="{prefix}tickers/{t.lower()}.html" class="dropdown-item">{t}</a>' for t in TICKERS
    )
    ticker_items += '<div style="height:1px;background:#30363d;margin:4px 0"></div>'
    ticker_items += "".join(
        f'<a href="{prefix}tickers/{t.lower()}.html" class="dropdown-item">'
        f'{t} <span style="color:#f0883e;font-size:10px">FUT</span></a>'
        for t in FUTURES
    )

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
.dropdown-btn{{background:none;border:none;color:#8b949e;font:500 13px 'Inter',sans-serif;padding:0 12px;height:56px;cursor:pointer;display:inline-flex;align-items:center;gap:4px;border-bottom:2px solid transparent}}
.dropdown-btn:hover{{color:#e6edf3}}
.dropdown-btn.active{{color:#e6edf3;border-bottom-color:#3fb950}}
.dropdown-menu{{display:none;position:absolute;top:56px;left:0;background:#161b22;border:1px solid #30363d;border-radius:6px;min-width:160px;padding:4px 0;z-index:200}}
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
.section-divider{{border:none;border-top:1px solid #21262d;margin:32px 0}}
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
.badge-orange{{background:rgba(240,136,62,.15);color:#f0883e;border:1px solid rgba(240,136,62,.3)}}
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
    <button class="dropdown-btn {strat_active}">Strategies ▾</button>
    <div class="dropdown-menu">{strat_items}</div>
  </div>
  <div class="dropdown">
    <button class="dropdown-btn">Tickers ▾</button>
    <div class="dropdown-menu">{ticker_items}</div>
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

# ── INDEX PAGE (multi-strategy dashboard) ─────────────────────────────────────

def build_index(bt_crm, strategy, gc_bt, cl_bt):
    import plotly.graph_objects as go

    # ── CRM Exit data ─────────────────────────────────────────────────────────
    tickers   = list(bt_crm["tickers"].keys())
    summaries = {t: bt_crm["tickers"][t]["summary"] for t in tickers}
    crm_total = sum(s["trades"] for s in summaries.values())
    crm_avg_wr = sum(s["win_rate"] for s in summaries.values()) / len(summaries)
    crm_best   = max(summaries, key=lambda t: summaries[t]["total_pnl"])

    # ── 3Min Cross data ───────────────────────────────────────────────────────
    gc_s = gc_bt["summary"] if gc_bt else {}
    cl_s = cl_bt["summary"] if cl_bt else {}

    BUCKET_LABELS = ["D↑/W↑", "D↑/W↓", "D↓/W↑", "D↓/W↓"]
    gc_long_b = bucket_stats_from_bt(gc_bt, "LONG")
    cl_long_b = bucket_stats_from_bt(cl_bt, "LONG")

    # ── Chart 1: CRM Exit PnL by ticker ───────────────────────────────────────
    sorted_t  = sorted(tickers, key=lambda t: summaries[t]["total_pnl"])
    stock_pnls = [summaries[t]["total_pnl"] for t in sorted_t]
    opt_pnls   = [summaries[t]["opt_total_pnl"] for t in sorted_t]

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name="Stock PnL %", x=sorted_t, y=stock_pnls,
        marker_color=["#3fb950" if v>=0 else "#f85149" for v in stock_pnls],
        text=[pct(v) for v in stock_pnls], textposition="outside"))
    fig1.add_trace(go.Bar(
        name="Options PnL %", x=sorted_t, y=opt_pnls,
        marker_color=["#388bfd" if v>=0 else "#da3633" for v in opt_pnls],
        opacity=0.75, text=[pct(v) for v in opt_pnls], textposition="outside"))
    fig1.add_hline(y=0, line_color="#30363d", line_width=1)
    fig1.update_layout(barmode="group", yaxis_ticksuffix="%", showlegend=True)
    chart_crm_pnl = fig_to_div(fig1, "chart-crm-pnl", 360)

    # ── Chart 2: CRM Exit win rate ─────────────────────────────────────────────
    sorted_wr = sorted(tickers, key=lambda t: summaries[t]["win_rate"])
    win_rates  = [summaries[t]["win_rate"] for t in sorted_wr]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="Win Rate %", x=sorted_wr, y=win_rates,
        marker_color=["#3fb950" if v>=50 else "#f85149" for v in win_rates],
        text=[f"{v:.1f}%" for v in win_rates], textposition="outside"))
    fig2.add_hline(y=50, line_color="#388bfd", line_dash="dash", line_width=1,
                   annotation_text="50%", annotation_position="right")
    chart_crm_wr = fig_to_div(fig2, "chart-crm-wr", 300)

    # ── Chart 3: CRM Exit profit factor ───────────────────────────────────────
    sorted_pf = sorted(tickers, key=lambda t: summaries[t]["pf"] or 0)
    pf_vals = [summaries[t]["pf"] or 0 for t in sorted_pf]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Profit Factor", x=sorted_pf, y=pf_vals,
        marker_color=["#3fb950" if v>=1 else "#f85149" for v in pf_vals],
        text=[f"{v:.2f}" for v in pf_vals], textposition="outside"))
    fig3.add_hline(y=1, line_color="#388bfd", line_dash="dash", line_width=1,
                   annotation_text="1.0", annotation_position="right")
    chart_crm_pf = fig_to_div(fig3, "chart-crm-pf", 300)

    # ── Chart 4: 3Min Cross — bucket long PnL comparison (GC vs CL) ──────────
    gc_lp = [gc_long_b.get(b, {}).get("pnl", 0) for b in BUCKET_LABELS] if gc_long_b else []
    cl_lp = [cl_long_b.get(b, {}).get("pnl", 0) for b in BUCKET_LABELS] if cl_long_b else []
    fig4 = go.Figure()
    if gc_lp:
        fig4.add_trace(go.Bar(
            name="GC Long PnL", x=BUCKET_LABELS, y=gc_lp,
            marker_color=["#3fb950" if v>=0 else "#f85149" for v in gc_lp],
            text=[pct(v) for v in gc_lp], textposition="outside"))
    if cl_lp:
        fig4.add_trace(go.Bar(
            name="CL Long PnL", x=BUCKET_LABELS, y=cl_lp,
            marker_color=["#388bfd" if v>=0 else "#da3633" for v in cl_lp],
            opacity=0.8, text=[pct(v) for v in cl_lp], textposition="outside"))
    fig4.add_hline(y=0, line_color="#30363d", line_width=1)
    fig4.update_layout(barmode="group", yaxis_ticksuffix="%")
    chart_3m_buckets = fig_to_div(fig4, "chart-3m-buckets", 360)

    # ── Interactive equity curve (GC + CL, filters per symbol) ───────────────
    interactive_eq = build_interactive_equity_chart(
        {sym: bt for sym, bt in [("GC", gc_bt), ("CL", cl_bt)] if bt},
        uid="eqdash", height=340
    )

    # ── CRM Exit summary table ─────────────────────────────────────────────────
    crm_rows = ""
    for t in sorted(tickers, key=lambda t: summaries[t]["total_pnl"], reverse=True):
        s = summaries[t]
        sc  = color(s["total_pnl"]); oc = color(s["opt_total_pnl"])
        wrc = "#3fb950" if s["win_rate"] >= 50 else "#f85149"
        pf_v = s["pf"]
        crm_rows += f"""<tr>
          <td><a href="tickers/{t.lower()}.html" style="font-weight:600;color:#e6edf3">{t}</a></td>
          <td>{s['trades']}</td>
          <td style="color:{wrc};font-weight:600">{s['win_rate']}%</td>
          <td style="color:{sc};font-weight:600">{pct(s['total_pnl'])}</td>
          <td style="color:{'#3fb950' if pf_v and pf_v>=1 else '#f85149'};font-weight:600">{f'{pf_v:.2f}' if pf_v else '—'}</td>
          <td style="color:{oc};font-weight:600">{pct(s['opt_total_pnl'])}</td>
        </tr>"""

    # ── 3Min Cross summary cards ───────────────────────────────────────────────
    def futures_card(sym, s):
        if not s: return '<div class="card"><div class="card-title">—</div></div>'
        sc = color(s.get("total_pnl")); wrc = "#3fb950" if s.get("win_rate",0)>=50 else "#f85149"
        pf_v = s.get("pf")
        return f"""<div class="card">
          <div class="card-title">3Min Cross — {sym}</div>
          <div class="card-value" style="color:{sc}">{pct(s.get('total_pnl'))}</div>
          <div class="card-sub">Win {s.get('win_rate',0):.1f}% · PF {f'{pf_v:.3f}' if pf_v else '—'} · <a href="tickers/{sym.lower()}.html">{s.get('trades',0):,} trades</a></div>
        </div>"""

    content = f"""
<div class="page-title">Trading Research Dashboard</div>
<div class="page-sub">2 Active Strategies · CRM Exit (MAG7 Equities) · 3Min Cross (GC &amp; CL Futures) · {TODAY}</div>

<div class="grid-4">
  <div class="card">
    <div class="card-title">Active Strategies</div>
    <div class="card-value">2</div>
    <div class="card-sub">CRM Exit · 3Min Cross</div>
  </div>
  <div class="card">
    <div class="card-title">CRM Exit — Best Ticker</div>
    <div class="card-value" style="color:#3fb950">{crm_best}</div>
    <div class="card-sub">{pct(summaries[crm_best]['total_pnl'])} stock · {crm_total:,} total trades · Avg WR {crm_avg_wr:.1f}%</div>
  </div>
  {futures_card("GC", gc_s)}
  {futures_card("CL", cl_s)}
</div>

<hr class="section-divider">
<div class="section-title">CRM Exit — MAG7 Equities &nbsp;<span class="badge badge-blue">V3.0</span></div>

<div class="chart-card">
  <div class="chart-title">Stock PnL vs Options PnL by Ticker</div>
  <div class="chart-sub">{bt_crm.get('data_window','')} · Options dramatically amplify winning moves</div>
  {chart_crm_pnl}
</div>

<div class="grid-2">
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Win Rate by Ticker</div>
    <div class="chart-sub">Reference line at 50% — above = statistical edge</div>
    {chart_crm_wr}
  </div>
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Profit Factor by Ticker</div>
    <div class="chart-sub">Reference line at 1.0 — above = profitable</div>
    {chart_crm_pf}
  </div>
</div>
<br>
<div class="chart-card" style="padding:0;overflow:hidden">
<table>
  <thead><tr><th>Ticker</th><th>Trades</th><th>Win%</th><th>Stock PnL</th><th>Profit Factor</th><th>Options PnL</th></tr></thead>
  <tbody>{crm_rows}</tbody>
</table>
</div>

<hr class="section-divider">
<div class="section-title">3Min 34/50 Cross — Futures &nbsp;<span class="badge badge-orange">V1.0</span></div>

<div class="chart-card">
  <div class="chart-title">Long PnL by Bucket — GC vs CL (10-Year)</div>
  <div class="chart-sub">D↑/D↓ = daily BX rising/falling · W↑/W↓ = weekly BX rising/falling · Apr 2016 – Apr 2026</div>
  {chart_3m_buckets}
</div>

<div class="chart-card">
  <div class="chart-title">Cumulative Equity Curve — Interactive</div>
  <div class="chart-sub">Each symbol keeps its own direction &amp; bucket settings independently</div>
  {interactive_eq}
</div>
"""
    return shell("Dashboard", content, active="home", depth=0)

# ── TICKER PAGE (equity: CRM Exit data) ───────────────────────────────────────

def build_ticker(ticker, bt):
    import plotly.graph_objects as go

    data   = bt["tickers"][ticker]
    s      = data["summary"]
    trades = data["trades"]
    valid  = [t for t in trades if not t["open_end"]]
    wins   = [t for t in valid if t["pnl"] > 0]
    losses = [t for t in valid if t["pnl"] <= 0]
    opt_v  = [t for t in valid if t.get("opt_pnl") is not None]

    cumstock = []; cumopt = []; cs = co = 0
    for i, t in enumerate(valid):
        cs += t["pnl"]; cumstock.append(round(cs, 3))
        co += t.get("opt_pnl") or 0; cumopt.append(round(co, 3) if t.get("opt_pnl") is not None else None)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=list(range(1,len(cumstock)+1)), y=cumstock, name="Stock PnL",
        line=dict(color="#3fb950", width=2), fill="tozeroy", fillcolor="rgba(63,185,80,0.08)",
        hovertemplate="Trade %{x}<br>Cumulative: %{y:.2f}%<extra>Stock</extra>"))
    fig1.add_trace(go.Scatter(x=list(range(1,len(cumopt)+1)), y=cumopt, name="Options PnL",
        line=dict(color="#388bfd", width=2), fill="tozeroy", fillcolor="rgba(56,139,253,0.06)",
        hovertemplate="Trade %{x}<br>Cumulative: %{y:.2f}%<extra>Options</extra>"))
    fig1.add_hline(y=0, line_color="#30363d", line_width=1)
    fig1.update_layout(xaxis_title="Trade #", yaxis_ticksuffix="%", showlegend=True,
                       legend=dict(orientation="h", y=1.1))
    chart1 = fig_to_div(fig1, f"chart-equity-{ticker}", 300)

    fig2 = go.Figure()
    for t in valid:
        col = "#3fb950" if t["pnl"]>0 else "#f85149"
        fig2.add_trace(go.Scatter(
            x=[t["days"]], y=[t["pnl"]], mode="markers",
            marker=dict(size=max(8, t["ch_width"]*4), color=col, opacity=0.8,
                        line=dict(width=1, color="#30363d")),
            name="W" if t["pnl"]>0 else "L", showlegend=False,
            hovertemplate=f"<b>T{valid.index(t)+1}</b><br>{t['entry_ts'][:10]}<br>"
                          f"{t['dir']} {pct(t['pnl'])}<br>Days: {t['days']}<br>"
                          f"Ch Width: ${t['ch_width']:.2f}<extra></extra>"))
    fig2.add_hline(y=0, line_color="#30363d", line_width=1)
    fig2.update_layout(xaxis_title="Days Held", yaxis_title="PnL %", yaxis_ticksuffix="%")
    chart2 = fig_to_div(fig2, f"chart-scatter-{ticker}", 300)

    fig3 = go.Figure(go.Pie(
        labels=["Winners","Losers"], values=[len(wins),len(losses)],
        marker=dict(colors=["#3fb950","#f85149"]),
        hole=0.6, textinfo="label+percent", hoverinfo="label+value"))
    fig3.add_annotation(text=f"{s['win_rate']}%<br><span style='font-size:10px'>Win</span>",
                        x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#e6edf3"))
    chart3 = fig_to_div(fig3, f"chart-donut-{ticker}", 260)

    if opt_v:
        fig4 = go.Figure()
        cols  = ["#3fb950" if t["opt_pnl"]>0 else "#f85149" for t in opt_v]
        hover = [f"T{valid.index(t)+1} {t['entry_ts'][:10]}<br>Stock: {pct(t['pnl'])}<br>Options: {pct(t['opt_pnl'])}"
                 for t in opt_v]
        fig4.add_trace(go.Scatter(
            x=[t["pnl"] for t in opt_v], y=[t["opt_pnl"] for t in opt_v],
            mode="markers", marker=dict(size=10, color=cols, opacity=0.85,
                                        line=dict(width=1, color="#30363d")),
            hovertemplate="%{customdata}<extra></extra>", customdata=hover))
        fig4.add_vline(x=0, line_color="#30363d", line_width=1)
        fig4.add_hline(y=0, line_color="#30363d", line_width=1)
        fig4.update_layout(xaxis_title="Stock PnL %", yaxis_title="Options PnL %",
                           xaxis_ticksuffix="%", yaxis_ticksuffix="%", showlegend=False)
        chart4 = fig_to_div(fig4, f"chart-opts-{ticker}", 300)
    else:
        chart4 = "<p style='color:#8b949e;text-align:center;padding:40px'>No options data</p>"

    rows = ""
    for i, t in enumerate(trades):
        pnl_s = pct(t["pnl"]) if not t["open_end"] else "open"
        pnl_c = color(t.get("pnl")) if not t["open_end"] else "#f0883e"
        opt_s = pct(t.get("opt_pnl")) if t.get("opt_pnl") is not None else "—"
        opt_c = color(t.get("opt_pnl"))
        dir_b = f'<span class="badge badge-{"green" if t["dir"]=="LONG" else "red"}">{t["dir"]}</span>'
        entry = t["entry_ts"][5:16].replace("T"," ")
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

    ticker_nav = '<div class="ticker-nav">'
    for t in TICKERS:
        cls = "active" if t == ticker else ""
        ticker_nav += f'<a href="{t.lower()}.html" class="ticker-btn {cls}">{t}</a>'
    ticker_nav += "</div>"

    sc = color(s["total_pnl"]); oc = color(s["opt_total_pnl"])
    wrc = "#3fb950" if s["win_rate"] >= 50 else "#f85149"
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

# ── TICKER PAGE (futures: 3Min Cross data) ────────────────────────────────────

def build_futures_ticker(symbol, bt):
    import plotly.graph_objects as go
    if not bt: return None

    s      = bt["summary"]
    closed = sorted([t for t in bt["trades"] if not t.get("open_end")],
                    key=lambda x: x["entry_ts"])
    winners = [t for t in closed if t["pnl"] > 0]
    losers  = [t for t in closed if t["pnl"] <= 0]

    BUCKET_LABELS = ["D↑/W↑", "D↑/W↓", "D↓/W↑", "D↓/W↓"]

    # ── Interactive equity curve ───────────────────────────────────────────────
    chart1 = build_interactive_equity_chart(
        {symbol: bt}, uid=f"eq{symbol.lower()}", height=320
    )

    # ── Bucket PnL bar chart (longs and shorts side by side) ──────────────────
    long_b  = bucket_stats_from_bt(bt, "LONG")
    short_b = bucket_stats_from_bt(bt, "SHORT")
    lp = [long_b.get(b, {}).get("pnl", 0)  for b in BUCKET_LABELS]
    sp = [short_b.get(b, {}).get("pnl", 0) for b in BUCKET_LABELS]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="Long PnL", x=BUCKET_LABELS, y=lp,
        marker_color=["#3fb950" if v>=0 else "#f85149" for v in lp],
        text=[pct(v) for v in lp], textposition="outside"))
    fig2.add_trace(go.Bar(
        name="Short PnL", x=BUCKET_LABELS, y=sp,
        marker_color=["#388bfd" if v>=0 else "#da3633" for v in sp],
        opacity=0.8, text=[pct(v) for v in sp], textposition="outside"))
    fig2.add_hline(y=0, line_color="#30363d", line_width=1)
    fig2.update_layout(barmode="group", yaxis_ticksuffix="%")
    chart2 = fig_to_div(fig2, f"chart-buckets-{symbol}", 340)

    # ── Win Rate by bucket (longs) ─────────────────────────────────────────────
    long_wrs = [long_b.get(b, {}).get("wr", 0) for b in BUCKET_LABELS]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        name="Long Win Rate", x=BUCKET_LABELS, y=long_wrs,
        marker_color=["#3fb950" if v>=28 else "#f85149" for v in long_wrs],
        text=[f"{v:.1f}%" for v in long_wrs], textposition="outside"))
    fig3.add_hline(y=s.get("win_rate", 28), line_color="#388bfd", line_dash="dash",
                   line_width=1, annotation_text="Avg", annotation_position="right")
    fig3.update_layout(yaxis_title="Win Rate %", yaxis_ticksuffix="%")
    chart3 = fig_to_div(fig3, f"chart-wr-{symbol}", 280)

    # ── Win/Loss donut ─────────────────────────────────────────────────────────
    fig4 = go.Figure(go.Pie(
        labels=["Winners","Losers"], values=[len(winners), len(losers)],
        marker=dict(colors=["#3fb950","#f85149"]),
        hole=0.6, textinfo="label+percent", hoverinfo="label+value"))
    fig4.add_annotation(text=f"{s['win_rate']:.1f}%<br><span style='font-size:10px'>Win</span>",
                        x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#e6edf3"))
    chart4 = fig_to_div(fig4, f"chart-donut-{symbol}", 260)

    # ── Bucket summary table ───────────────────────────────────────────────────
    all_b = bucket_stats_from_bt(bt)
    bucket_rows = ""
    for b in BUCKET_LABELS:
        lb = long_b.get(b, {"n":0,"pnl":0,"wr":0})
        sb = short_b.get(b, {"n":0,"pnl":0,"wr":0})
        combined = round(lb["pnl"] + sb["pnl"], 2)
        lc = color(lb["pnl"]); sc2 = color(sb["pnl"]); cc = color(combined)
        bucket_rows += f"""<tr>
          <td style="font-weight:600">{b}</td>
          <td style="color:#8b949e">{lb['n']}</td>
          <td style="color:#8b949e">{lb['wr']:.1f}%</td>
          <td style="color:{lc};font-weight:600">{pct(lb['pnl'])}</td>
          <td style="color:#8b949e">{sb['n']}</td>
          <td style="color:#8b949e">{sb['wr']:.1f}%</td>
          <td style="color:{sc2};font-weight:600">{pct(sb['pnl'])}</td>
          <td style="color:{cc};font-weight:600">{pct(combined)}</td>
        </tr>"""

    # Futures ticker nav
    futures_nav = '<div class="ticker-nav">'
    for f in FUTURES:
        cls = "active" if f == symbol else ""
        futures_nav += f'<a href="{f.lower()}.html" class="ticker-btn {cls}">{f}</a>'
    futures_nav += "</div>"

    sc_main = color(s["total_pnl"])
    wrc = "#3fb950" if s["win_rate"] >= 50 else "#f85149"
    pf_v = s["pf"]

    content = f"""
<div class="page-title">{symbol} — Futures</div>
<div class="page-sub">3Min 34/50 Cross · V1.0 · {bt.get('data_window','')} · {s['trades']:,} closed trades</div>
{futures_nav}
<div class="grid-4">
  <div class="card"><div class="card-title">Win Rate</div><div class="card-value" style="color:{wrc}">{s['win_rate']:.1f}%</div><div class="card-sub">{s['winners']:,}W / {s['losers']:,}L</div></div>
  <div class="card"><div class="card-title">Total PnL (all trades)</div><div class="card-value" style="color:{sc_main}">{pct(s['total_pnl'])}</div><div class="card-sub">Unfiltered — every cross</div></div>
  <div class="card"><div class="card-title">Profit Factor</div><div class="card-value" style="color:{'#3fb950' if pf_v and pf_v>=1 else '#f85149'}">{f'{pf_v:.3f}' if pf_v else '—'}</div><div class="card-sub">Gross win / gross loss</div></div>
  <div class="card"><div class="card-title">Avg Win / Avg Loss</div><div class="card-value" style="font-size:20px;color:#3fb950">{pct(s['avg_win'])}</div><div class="card-sub">Avg loss: <span style="color:#f85149">{pct(s['avg_loss'])}</span></div></div>
</div>

<div class="chart-card">
  <div class="chart-title">Cumulative Equity Curve — Interactive</div>
  <div class="chart-sub">Filter by direction and bucket combination to explore trade subsets</div>
  {chart1}
</div>

<div class="chart-card">
  <div class="chart-title">Bucket PnL — Long vs Short (10-Year)</div>
  <div class="chart-sub">Total PnL % per daily BX × weekly BX direction bucket</div>
  {chart2}
</div>

<div class="grid-2">
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Long Win Rate by Bucket</div>
    <div class="chart-sub">Dashed line = overall average win rate</div>
    {chart3}
  </div>
  <div class="chart-card" style="margin-bottom:0">
    <div class="chart-title">Win / Loss Split</div>
    <div class="chart-sub">All closed trades</div>
    {chart4}
  </div>
</div>
<br>

<div class="section-title">Bucket Summary — Long &amp; Short</div>
<div class="chart-card" style="padding:0;overflow:hidden">
<table>
  <thead><tr>
    <th>Bucket</th>
    <th>Long Trades</th><th>Long WR</th><th>Long PnL</th>
    <th>Short Trades</th><th>Short WR</th><th>Short PnL</th>
    <th>Combined PnL</th>
  </tr></thead>
  <tbody>{bucket_rows}</tbody>
</table>
</div>
"""
    return shell(f"{symbol} Futures", content, active="tickers", depth=1)

# ── STRATEGY PAGE (CRM Exit detail) ───────────────────────────────────────────

def build_strategy(strategy, bt):
    import plotly.graph_objects as go

    versions = strategy["versions"]
    v_names  = [v["version"] for v in versions]
    v_pnls   = [v.get("tsla_stock_pnl", 0) for v in versions]

    fig1 = go.Figure()
    fig1.add_trace(go.Bar(name="Stock PnL %", x=v_names, y=v_pnls,
        marker_color=["#3fb950" if v>=0 else "#f85149" for v in v_pnls],
        text=[f"{pct(v)}" for v in v_pnls], textposition="outside"))
    fig1.add_hline(y=0, line_color="#30363d", line_width=1)
    fig1.update_layout(xaxis_title="Version", yaxis_ticksuffix="%", showlegend=False)
    chart1 = fig_to_div(fig1, "chart-versions", 320)

    exits = ["34/50 only", "8/21 only (V3)", "5/12 only"]
    stock = [5.28, 11.60, 3.34]
    opts  = [-17.12, 178.13, 57.92]
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Stock PnL %", x=exits, y=stock,
        marker_color=["#3fb950" if v>=0 else "#f85149" for v in stock],
        text=[pct(v) for v in stock], textposition="outside"))
    fig2.add_trace(go.Bar(name="Options PnL %", x=exits, y=opts,
        marker_color=["#388bfd" if v>=0 else "#da3633" for v in opts],
        text=[pct(v) for v in opts], textposition="outside", opacity=0.8))
    fig2.add_hline(y=0, line_color="#30363d", line_width=1)
    fig2.update_layout(barmode="group", yaxis_ticksuffix="%")
    chart2 = fig_to_div(fig2, "chart-exits", 340)

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

# ── INSIGHTS PAGE (aggregated across all strategies) ──────────────────────────

STRATEGY_LABELS = {
    "crm_exit":  ("CRM Exit",    "badge-blue"),
    "3m_cross":  ("3Min Cross",  "badge-orange"),
    "shared":    ("Shared",      "badge-gray"),
}

def build_insights(insights):
    cards = ""
    for ins in insights:
        impact   = ins.get("impact","medium")
        strat_id = ins.get("strategy","")
        strat_label, strat_badge = STRATEGY_LABELS.get(strat_id, (strat_id, "badge-gray"))
        tags     = [t.strip() for t in ins.get("tags","").strip("[]").split(",") if t.strip()]
        tag_html = " ".join(f'<span class="tag">{t}</span>' for t in tags)
        cards += f"""
<div class="insight-card impact-{impact}">
  <div class="insight-title">{ins.get('title','')}</div>
  <div class="insight-meta">
    <span style="color:#8b949e;font-size:12px">📅 {ins.get('date','')}</span>
    <span class="badge badge-{'red' if impact=='high' else 'blue' if impact=='medium' else 'gray'}">{impact} impact</span>
    <span class="badge {strat_badge}">{strat_label}</span>
    {tag_html}
  </div>
  <div class="insight-body">{ins.get('body','').replace(chr(10),'<br>')}</div>
</div>"""

    content = f"""
<div class="page-title">Insights</div>
<div class="page-sub">Lessons learned, observations, and decisions — across all strategies</div>
<div style="max-width:800px">
{cards}
</div>
"""
    return shell("Insights", content, active="insights", depth=1)

# ── PUBLISH PAGE (markdown strategy write-ups) ────────────────────────────────

def build_publish_page(project_id, filename="publish.md", active_key=None):
    import markdown as md
    f = CONTENT / "projects" / project_id / filename
    if not f.exists():
        return None
    if active_key is None:
        active_key = project_id

    raw  = f.read_text()
    body = re.sub(r'^---\n.*?\n---\n', '', raw, flags=re.DOTALL).strip()
    html = md.markdown(body, extensions=["tables", "fenced_code"])
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
    title = raw.split("title:")[1].split("\n")[0].strip() if "title:" in raw else project_id
    return shell(title, content, active=active_key, depth=1)


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    print("\nBuilding site...\n")
    bt_crm   = load_latest_backtest("crm_exit")
    strategy = load_strategy("crm_exit")
    insights = load_insights()
    gc_bt    = load_3m_cross_bt("GC")
    cl_bt    = load_3m_cross_bt("CL")

    if not bt_crm:
        print("  No CRM Exit backtest found in content/projects/crm_exit/backtests/"); return

    # Dashboard
    (DOCS / "index.html").write_text(build_index(bt_crm, strategy, gc_bt, cl_bt))
    print("  ✓ index.html")

    # CRM Exit strategy detail
    if strategy:
        (DOCS / "strategy" / "crm_exit.html").write_text(build_strategy(strategy, bt_crm))
        print("  ✓ strategy/crm_exit.html")

    # Equity ticker pages
    for ticker in TICKERS:
        if ticker in bt_crm["tickers"]:
            (DOCS / "tickers" / f"{ticker.lower()}.html").write_text(build_ticker(ticker, bt_crm))
            print(f"  ✓ tickers/{ticker.lower()}.html")

    # Futures ticker pages
    for sym, bt in [("GC", gc_bt), ("CL", cl_bt)]:
        p = build_futures_ticker(sym, bt)
        if p:
            (DOCS / "tickers" / f"{sym.lower()}.html").write_text(p)
            print(f"  ✓ tickers/{sym.lower()}.html")

    # Insights
    if insights:
        (DOCS / "insights" / "index.html").write_text(build_insights(insights))
        print("  ✓ insights/index.html")

    # Strategy write-up pages
    p = build_publish_page("3m_cross")
    if p:
        (DOCS / "strategy" / "3m_cross.html").write_text(p)
        print("  ✓ strategy/3m_cross.html")

    p_cl = build_publish_page("3m_cross", filename="publish_CL.md", active_key="3m_cross_cl")
    if p_cl:
        (DOCS / "strategy" / "3m_cross_cl.html").write_text(p_cl)
        print("  ✓ strategy/3m_cross_cl.html")

    print(f"\n  Site → {DOCS}/")
    print(f"  Push to GitHub → live at https://sameerbode.github.io/trading-research\n")

if __name__ == "__main__":
    main()
