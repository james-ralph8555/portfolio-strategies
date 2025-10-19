# Unified Backtesting Guide

## Overview

The unified backtesting system (`unified_backtest.py`) provides a comprehensive framework for testing all trading strategies with consistent market data and performance metrics.

## Quick Start

```bash
# Enter Nix shell first
nix develop

# Run single strategy backtest
python unified_backtest.py --strategy risk_parity --start-date 2020-01-01 --end-date 2023-12-31

# Run all strategies
python unified_backtest.py --start-date 2020-01-01 --end-date 2023-12-31

# Custom initial capital
python unified_backtest.py --initial-capital 1000000 --start-date 2020-01-01 --end-date 2023-12-31
```

## Features

### Strategy Integration

- **Auto-discovery**: Automatically loads all strategies from `strategies/` directory
- **Config loading**: Reads strategy-specific YAML configurations
- **Market data**: Uses existing `MarketDataManager` for consistent data access

### Database Storage

- **Separate DB**: `backtest_results/backtest_results.duckdb` (isolated from market data)
- **Three tables**:
  - `backtest_results`: Summary metrics and strategy info
  - `portfolio_values`: Daily portfolio values
  - `trades`: Individual trade records

### Performance Metrics

- Total return, annualized return, volatility
- Sharpe ratio, maximum drawdown, win rate
- Average win/loss, profit factor, calmar ratio

## Command Line Options

| Option              | Description                      | Default        |
| ------------------- | -------------------------------- | -------------- |
| `--start-date`      | Backtest start date (YYYY-MM-DD) | 2020-01-01     |
| `--end-date`        | Backtest end date (YYYY-MM-DD)   | 2023-12-31     |
| `--strategy`        | Specific strategy to run         | All strategies |
| `--initial-capital` | Starting capital amount          | 1000000        |

## Output

### Console Output

```
=== Backtest Summary ===
Strategy: risk_parity
Period: 2020-01-01 to 2023-12-31
Initial Capital: $1,000,000.00
Final Value: $1,234,567.89
Total Return: 23.46%
Annualized Return: 5.89%
Sharpe Ratio: 0.82
Max Drawdown: -8.34%
```

### Database Queries

```sql
-- View all backtest results
SELECT * FROM backtest_results ORDER BY end_date DESC;

-- Compare strategy performance
SELECT strategy_name, total_return, sharpe_ratio, max_drawdown
FROM backtest_results WHERE start_date = '2020-01-01';

-- Get portfolio values for a strategy
SELECT date, portfolio_value
FROM portfolio_values
WHERE strategy_name = 'risk_parity'
ORDER BY date;
```

## Implementation Details

### Core Components

1. **StrategyLoader**: Dynamically imports and instantiates strategies
2. **MarketDataManager**: Provides consistent market data access
3. **BacktestEngine**: Executes backtests with proper rebalancing logic
4. **MetricsCalculator**: Computes comprehensive performance metrics

### Data Flow

1. Load strategy configurations from YAML files
2. Fetch market data via `MarketDataManager`
3. Execute strategy logic with monthly rebalancing
4. Calculate performance metrics
5. Store results in DuckDB database

### Error Handling

- Missing market data warnings (continues with available assets)
- Database duplicate prevention
- Graceful handling of strategy initialization failures

## Troubleshooting

### Common Issues

- **Missing assets**: Some strategies reference assets not in market data (PDBC, IAU)
- **Date ranges**: Ensure end date is after start date and within available data
- **Memory usage**: Large date ranges may require significant RAM

### Debug Mode

Add print statements in `BacktestEngine.run_backtest()` to trace:

- Portfolio composition changes
- Individual trade executions
- Daily value calculations

## Architecture

```
unified_backtest.py
├── StrategyLoader (dynamic strategy loading)
├── BacktestEngine (core backtesting logic)
├── MetricsCalculator (performance analysis)
└── DatabaseManager (DuckDB operations)

Integration Points:
├── core/market_data/manager.py (MarketDataManager)
├── core/interfaces/strategy.py (IStrategy interface)
└── strategies/*/ (individual strategy implementations)
```
