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

## Database Access Guide

### Reading Backtest Results Database

The backtest results are stored in `cache/backtest_results.duckdb`. Here's how to query it:

```python
import duckdb
import pandas as pd

# Connect to database
conn = duckdb.connect('/home/james/projects/portfolio/cache/backtest_results.duckdb')

# List all strategies
strategies = conn.execute('SELECT * FROM strategies').fetchdf()
print(strategies)

# Get backtest results for a specific strategy
strategy_name = 'risk_parity'
strategy_id = int(strategies[strategies['name'] == strategy_name]['id'].iloc[0])
results = conn.execute(
    'SELECT * FROM backtest_results WHERE strategy_id = ?',
    [strategy_id]
).fetchdf()
print(results)

# Get portfolio values for the most recent backtest
if not results.empty:
    latest_result_id = int(results.iloc[-1]['id'])
    portfolio_values = conn.execute(
        'SELECT date, portfolio_value FROM portfolio_values WHERE backtest_result_id = ? ORDER BY date',
        [latest_result_id]
    ).fetchdf()
    print(portfolio_values.tail(10))

conn.close()
```

### Important Notes

- Stop any running backend/web servers before accessing the database to avoid lock conflicts
