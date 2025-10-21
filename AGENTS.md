# Repository Guidelines

## Build, Test, and Development Commands

Always enter the Nix shell before running Python: `nix develop` for an interactive session or prefix commands with `nix develop --command …`.

## NEVER RUN THE DEV SERVER

NEVER RUN npm dev

## Backend Server

NEVER RUN THE BACKEND SERVER - Tell the user to run it manually if needed:

```bash
nix develop --command python backend/main.py
```

## Debug Trace Logs

The debug trace logs functionality requires:

1. Running backtests to generate trace data in the database
2. The backend server to be running to serve the trace data via API
3. Trace logs are stored in the `backtest_traces` table in `backtest_results/backtest_results.duckdb`

If trace logs show "No debug trace logs available", run a backtest first:

```bash
nix develop --command python -c "
from unified_backtest import UnifiedBacktester
backtester = UnifiedBacktester()
backtester.run_backtest('equity_vol_barbell', '2023-01-01', '2023-01-31', 100000.0)
backtester.close()
"
```
