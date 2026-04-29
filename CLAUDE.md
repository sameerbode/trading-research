# Trading Research

Centralized site for backtests, strategy definitions, and insights across trading projects. Generates a static GitHub Pages site from `content/`.

## Repo Structure

```
content/
  projects/
    <project_id>/
      meta.json       — strategy definition, versions, key insights, open questions
      backtests/      — backtest result JSONs (<id>_<YYYYMMDD>.json)
      insights/       — markdown write-ups (<YYYY-MM-DD>_<slug>.md)
  shared/
    universes/        — reusable ticker lists (mag7.json, etc.)
data/
  futures/            — git submodule: sameerbode/futures-data-cache
docs/                 — generated HTML (GitHub Pages, do not edit manually)
generate_site.py      — builds docs/ from content/
```

## Data

Futures data lives in a separate private repo added as a submodule at `data/futures/`.

**Symbols:** ES, NQ, GC, CL  
**Frequency:** 1-minute OHLCV  
**Range:** 2016-04-11 → 2026-04-10  
**Timezone:** UTC (tz-aware index)  
**Source:** Databento (private, do not redistribute)

**Files per symbol:**
- `<SYM>_1m.parquet` — OHLCV bars with `contract` column (active front-month symbol at each bar)
- `<SYM>_rolls.csv` — roll dates (`d0`, `d1`, `raw_symbol`, `instrument_id`)

**Loading data:**
```python
import pandas as pd

es  = pd.read_parquet("data/futures/ES_1m.parquet")
nq  = pd.read_parquet("data/futures/NQ_1m.parquet")
gc  = pd.read_parquet("data/futures/GC_1m.parquet")
cl  = pd.read_parquet("data/futures/CL_1m.parquet")

rolls = pd.read_csv("data/futures/ES_rolls.csv")
```

**Updating the data cache** (when new data is available in futures-data-cache):
```bash
git submodule update --remote data/futures
git commit -am "Update futures data cache to <new end date>"
```

**First-time clone of this repo** (submodule won't auto-clone):
```bash
git clone --recurse-submodules <repo-url>
# or if already cloned:
git submodule update --init data/futures
```

## Adding a New Project

1. `mkdir -p content/projects/<project_id>/backtests content/projects/<project_id>/insights`
2. Create `content/projects/<project_id>/meta.json` with strategy definition
3. Drop backtest results into `backtests/` and insight notes into `insights/`
4. Run `python3 generate_site.py`

## Adding a Backtest

Drop a JSON file into `content/projects/<project_id>/backtests/<id>_<YYYYMMDD>.json`.  
The generator uses the most recent file (sorted by filename) as the active result.

## Adding an Insight

Drop a markdown file into `content/projects/<project_id>/insights/<YYYY-MM-DD>_<slug>.md` with frontmatter:
```markdown
---
date: YYYY-MM-DD
title: ...
tags: [tag1, tag2]
strategy: <project_id>
tickers: [SYM1, SYM2]
impact: high | medium | low
---

Body text here.
```

## Generating the Site

```bash
python3 generate_site.py
```

Push to GitHub → live at https://sameerbode.github.io/trading-research
