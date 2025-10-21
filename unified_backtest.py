#!/usr/bin/env python3
"""
Unified Backtesting Script

Runs all strategies with configurable start/end periods using the core market data system.
Stores results in a separate DuckDB database from the market data cache.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import yaml

from core.market_data.manager import MarketDataManager


class UnifiedBacktester:
    """
    Unified backtesting system for all portfolio strategies.

    Uses the core market data manager for data fetching/caching and stores
    backtest results in a separate DuckDB database.
    """

    def __init__(self, results_db_path: str | None = None):
        """
        Initialize the unified backtester.

        Args:
            results_db_path: Path to results DuckDB database
        """
        self.logger = self._setup_logging()

        # Initialize results database
        if results_db_path is None:
            results_dir = Path("backtest_results")
            results_dir.mkdir(exist_ok=True)
            results_db_path = str(results_dir / "backtest_results.duckdb")

        self.results_db_path = results_db_path
        self.results_conn = duckdb.connect(self.results_db_path)
        self._initialize_results_db()

        # Initialize market data manager (with error handling)
        try:
            self.market_data_manager = MarketDataManager()
        except Exception as e:
            self.logger.warning(f"Could not initialize market data manager: {e}")
            self.market_data_manager = None

        # Load all strategies
        self.strategies = self._load_all_strategies()

        self.logger.info(
            f"Initialized unified backtester with {len(self.strategies)} strategies"
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(__name__)

    def _initialize_results_db(self) -> None:
        """Initialize the results database schema."""
        self.results_conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                strategy_name VARCHAR,
                start_date DATE,
                end_date DATE,
                total_return FLOAT,
                annualized_return FLOAT,
                volatility FLOAT,
                sharpe_ratio FLOAT,
                max_drawdown FLOAT,
                calmar_ratio FLOAT,
                win_rate FLOAT,
                profit_factor FLOAT,
                avg_trade_return FLOAT,
                num_trades INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (strategy_name, start_date, end_date)
            )
        """)

        self.results_conn.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_values (
                strategy_name VARCHAR,
                date DATE,
                portfolio_value FLOAT,
                cash FLOAT,
                weights VARCHAR,  -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (strategy_name, date)
            )
        """)

        self.results_conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                strategy_name VARCHAR,
                trade_date DATE,
                symbol VARCHAR,
                action VARCHAR,  -- 'BUY' or 'SELL'
                quantity FLOAT,
                price FLOAT,
                value FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (strategy_name, trade_date, symbol, action)
            )
        """)

        self.results_conn.execute("""
            CREATE TABLE IF NOT EXISTS backtest_traces (
                strategy_name VARCHAR,
                start_date DATE,
                end_date DATE,
                trace_timestamp TIMESTAMP,
                level VARCHAR,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                category VARCHAR,  -- 'REBALANCE', 'WEIGHT_CALC', 'PORTFOLIO', 'TRADE', 'PERFORMANCE'
                message TEXT,
                data JSON,  -- Additional structured data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better performance
        self.results_conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_backtest_strategy_dates ON backtest_results(strategy_name, start_date, end_date)"
        )
        self.results_conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_strategy_date ON portfolio_values(strategy_name, date)"
        )
        self.results_conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_trades_strategy_date ON trades(strategy_name, trade_date)"
        )
        self.results_conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_strategy_date ON backtest_traces(strategy_name, start_date, end_date)"
        )
        self.results_conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON backtest_traces(trace_timestamp)"
        )

    def _load_all_strategies(self) -> dict[str, Any]:
        """Load all available strategies from the strategies directory."""
        strategies = {}
        # Try to find strategies directory from current location or project root
        strategies_dir = Path("strategies")
        if not strategies_dir.exists():
            # Try from the project root (assuming we're in backend/)
            strategies_dir = Path(__file__).parent / "strategies"
        if not strategies_dir.exists():
            # Try one level up from backend
            strategies_dir = Path(__file__).parent.parent / "strategies"

        if not strategies_dir.exists():
            self.logger.error(f"Strategies directory {strategies_dir} not found")
            return strategies

        for strategy_dir in strategies_dir.iterdir():
            if strategy_dir.is_dir() and (strategy_dir / "strategy.py").exists():
                strategy_name = strategy_dir.name

                try:
                    # Load strategy configuration
                    config_path = strategy_dir / "config.yaml"
                    config = {}
                    if config_path.exists():
                        with open(config_path) as f:
                            config = yaml.safe_load(f)

                    # Import strategy class
                    module_name = f"strategies.{strategy_name}.strategy"
                    module = __import__(module_name, fromlist=["strategy"])

                    # Find strategy class (assumes one strategy class per file)
                    strategy_class = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and hasattr(attr, "calculate_weights")
                            and attr_name.endswith("Strategy")
                        ):
                            strategy_class = attr
                            break

                    if strategy_class:
                        try:
                            strategy_instance = strategy_class(config)
                            strategies[strategy_name] = strategy_instance
                            self.logger.info(f"Loaded strategy: {strategy_name}")
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to instantiate {strategy_name}: {e}"
                            )
                            # Still add the strategy class but note the error
                            strategies[strategy_name] = None
                    else:
                        self.logger.warning(
                            f"No strategy class found in {strategy_name}"
                        )

                except Exception as e:
                    self.logger.error(f"Error loading strategy {strategy_name}: {e}")

        return strategies

    def _initialize_backtest_trace(
        self, strategy_name: str, start_date: str, end_date: str
    ) -> str:
        """Initialize trace logging for a backtest run."""
        trace_id = f"{strategy_name}_{start_date}_{end_date}_{int(pd.Timestamp.now().timestamp())}"

        # Log initialization
        self._log_trace_event(
            strategy_name,
            start_date,
            end_date,
            "INFO",
            "BACKTEST",
            f"Starting backtest for {strategy_name}",
            {"trace_id": trace_id, "initial_capital": 100000.0},
        )

        return trace_id

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Sanitize object for JSON serialization."""
        import numpy as np

        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        else:
            return obj

    def _log_trace_event(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        level: str,
        category: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log a trace event for the backtest."""
        try:
            import json

            sanitized_data = self._sanitize_for_json(data) if data else None
            self.results_conn.execute(
                """
                INSERT INTO backtest_traces
                (strategy_name, start_date, end_date, trace_timestamp, level, category, message, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    strategy_name,
                    start_date,
                    end_date,
                    pd.Timestamp.now(),
                    level,
                    category,
                    message,
                    json.dumps(sanitized_data) if sanitized_data else None,
                ],
            )
        except Exception as e:
            self.logger.warning(f"Failed to log trace event: {e}")

    def run_backtest(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
    ) -> dict[str, Any]:
        """
        Run backtest for a specific strategy.

        Args:
            strategy_name: Name of strategy to backtest
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Starting capital for the backtest

        Returns:
            Dictionary with backtest results
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy {strategy_name} not found")

        strategy = self.strategies[strategy_name]
        self.logger.info(
            f"Running backtest for {strategy_name} from {start_date} to {end_date}"
        )

        # Get market data for strategy assets
        assets = strategy.get_assets()
        if not self.market_data_manager:
            raise ValueError("Market data manager not available")
        price_data = self.market_data_manager.get_price_data(
            assets, start_date, end_date
        )

        if price_data.empty:
            raise ValueError(f"No price data available for assets {assets}")

        # Initialize trace logging for this backtest
        self._initialize_backtest_trace(strategy_name, start_date, end_date)

        # Run the backtest simulation
        results = self._simulate_backtest(
            strategy, price_data, start_date, end_date, initial_capital
        )

        # Store results in database
        self._store_backtest_results(strategy_name, results)

        return results

    def _simulate_backtest(
        self,
        strategy: Any,
        price_data: pd.DataFrame,
        start_date: str,
        end_date: str,
        initial_capital: float,
    ) -> dict[str, Any]:
        """
        Simulate the backtest for a strategy.

        Args:
            strategy: Strategy instance
            price_data: Price data for all assets
            start_date: Start date
            end_date: End date
            initial_capital: Starting capital

        Returns:
            Dictionary with backtest results
        """
        # Initialize portfolio tracking
        portfolio_values = []
        trades = []
        current_weights = {}
        cash = initial_capital
        portfolio_value = initial_capital

        # Initialize trace logging for this backtest
        strategy_name = strategy.get_name()
        self._log_trace_event(
            strategy_name,
            start_date,
            end_date,
            "INFO",
            "PORTFOLIO",
            f"Initializing portfolio with ${initial_capital:,.2f}",
            {"initial_capital": initial_capital, "assets": strategy.get_assets()},
        )

        # Get rebalancing frequency (currently unused but kept for future implementation)
        # rebalance_freq = strategy.rebalance_frequency
        # drift_bands = getattr(strategy, "drift_bands", 10) / 100

        # Convert to datetime for easier date handling
        dates = pd.date_range(start_date, end_date, freq="D")
        dates = [d for d in dates if d in price_data.index]  # Only trading days

        for i, date in enumerate(dates):
            # Get current prices
            current_prices = price_data.loc[date].dropna()

            # Check if we need to rebalance
            should_rebalance = False

            if i == 0:  # First day - always rebalance
                should_rebalance = True
                self._log_trace_event(
                    strategy_name,
                    start_date,
                    end_date,
                    "INFO",
                    "REBALANCE",
                    f"First day rebalancing on {date.strftime('%Y-%m-%d')}",
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "portfolio_value": portfolio_value,
                    },
                )
            else:
                # Check drift bands
                target_weights = strategy.calculate_weights(price_data.loc[:date])
                should_rebalance = strategy.should_rebalance(
                    current_weights, target_weights
                )

                if should_rebalance:
                    self._log_trace_event(
                        strategy_name,
                        start_date,
                        end_date,
                        "INFO",
                        "REBALANCE",
                        f"Drift-based rebalancing triggered on {date.strftime('%Y-%m-%d')}",
                        {
                            "date": date.strftime("%Y-%m-%d"),
                            "current_weights": current_weights,
                            "target_weights": target_weights,
                            "portfolio_value": portfolio_value,
                        },
                    )

            if should_rebalance:
                # Calculate new target weights
                target_weights = strategy.calculate_weights(price_data.loc[:date])

                self._log_trace_event(
                    strategy_name,
                    start_date,
                    end_date,
                    "DEBUG",
                    "WEIGHT_CALC",
                    f"Calculated target weights for {date.strftime('%Y-%m-%d')}",
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "target_weights": target_weights,
                        "portfolio_value": portfolio_value,
                    },
                )

                # Execute trades to reach target weights
                new_portfolio_value, new_cash, new_weights, day_trades = (
                    self._execute_rebalance(
                        portfolio_value,
                        cash,
                        current_weights,
                        target_weights,
                        current_prices,
                        date.strftime("%Y-%m-%d"),
                    )
                )

                portfolio_value = new_portfolio_value
                cash = new_cash
                current_weights = new_weights
                trades.extend(day_trades)

                # Log trade execution
                self._log_trace_event(
                    strategy_name,
                    start_date,
                    end_date,
                    "INFO",
                    "TRADE",
                    f"Executed {len(day_trades)} trades on {date.strftime('%Y-%m-%d')}",
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "num_trades": len(day_trades),
                        "trades": day_trades,
                        "new_portfolio_value": new_portfolio_value,
                        "cash": new_cash,
                    },
                )

            # Update portfolio value based on price changes
            if len(current_weights) > 0:
                asset_values = {
                    asset: weight * portfolio_value
                    for asset, weight in current_weights.items()
                }
                portfolio_value = sum(asset_values.values()) + cash

            # Record portfolio value
            portfolio_values.append(
                {
                    "date": date,
                    "portfolio_value": portfolio_value,
                    "cash": cash,
                    "weights": current_weights.copy(),
                }
            )

        # Calculate performance metrics
        portfolio_df = pd.DataFrame(portfolio_values).set_index("date")
        returns_series = portfolio_df["portfolio_value"].pct_change().dropna()

        metrics = self._calculate_performance_metrics(
            returns_series,
            float(portfolio_df["portfolio_value"].iloc[0]),
            float(portfolio_df["portfolio_value"].iloc[-1]),
        )

        # Log completion
        self._log_trace_event(
            strategy_name,
            start_date,
            end_date,
            "INFO",
            "PERFORMANCE",
            f"Backtest completed with {len(trades)} trades",
            {
                "final_portfolio_value": portfolio_value,
                "total_return": metrics.get("total_return", 0),
                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                "max_drawdown": metrics.get("max_drawdown", 0),
                "num_trades": len(trades),
            },
        )

        return {
            "strategy_name": strategy.get_name(),
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_value": portfolio_value,
            "portfolio_values": portfolio_df,
            "trades": trades,
            "metrics": metrics,
        }

    def _execute_rebalance(
        self,
        portfolio_value: float,
        cash: float,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
        prices: pd.Series,
        trade_date: str,
    ) -> tuple[float, float, dict[str, float], list[dict[str, Any]]]:
        """
        Execute rebalancing trades.

        Args:
            portfolio_value: Current portfolio value
            cash: Available cash
            current_weights: Current asset weights
            target_weights: Target asset weights
            prices: Current asset prices

        Returns:
            Tuple of (new_portfolio_value, new_cash, new_weights, trades)
        """
        trades = []
        new_weights = {}

        # Calculate target values for each asset
        target_values = {
            asset: weight * portfolio_value for asset, weight in target_weights.items()
        }

        # Calculate current values for each asset
        current_values = {
            asset: weight * portfolio_value for asset, weight in current_weights.items()
        }

        # Calculate trades needed
        for asset, target_value in target_values.items():
            current_value = current_values.get(asset, 0)
            trade_value = target_value - current_value

            if abs(trade_value) > 1.0:  # Only trade if significant
                if asset in prices:
                    price = prices[asset]
                    quantity = trade_value / price

                    trade = {
                        "symbol": asset,
                        "action": "BUY" if quantity > 0 else "SELL",
                        "quantity": abs(quantity),
                        "price": price,
                        "value": abs(trade_value),
                        "trade_date": trade_date,
                    }
                    trades.append(trade)

                    # Update cash
                    if quantity > 0:  # Buy
                        cash -= abs(trade_value)
                    else:  # Sell
                        cash += abs(trade_value)

                    # Update weights
                    new_weights[asset] = target_value / portfolio_value
                else:
                    self.logger.warning(f"No price available for {asset}")

        # Normalize weights to ensure they sum to 1
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            new_weights = {k: v / total_weight for k, v in new_weights.items()}

        return portfolio_value, cash, new_weights, trades

    def _sanitize_float(self, value: float) -> float:
        """Sanitize float values for JSON serialization."""
        if value == float("inf") or value == float("-inf"):
            return 999.0  # Large finite value
        if value != value:  # Check for NaN
            return 0.0
        return value

    def _calculate_performance_metrics(
        self,
        returns: pd.Series | pd.DataFrame,
        initial_value: float,
        final_value: float,
    ) -> dict[str, float]:
        """Calculate performance metrics for the backtest."""
        if len(returns) == 0:
            return {
                "total_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "calmar_ratio": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_trade_return": 0.0,
                "num_trades": 0,
            }

        # Basic return metrics
        total_return = (final_value / initial_value) - 1
        annualized_return = (
            (final_value / initial_value) ** (252 / len(returns)) - 1
            if len(returns) > 0
            and final_value != float("inf")
            and final_value != float("-inf")
            and initial_value != 0
            else 0
        )
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = (
            annualized_return / volatility
            if volatility > 0
            and volatility != float("inf")
            and volatility != float("-inf")
            else 0
        )

        # Drawdown metrics
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        calmar_ratio = (
            annualized_return / abs(max_drawdown)
            if max_drawdown != 0
            and max_drawdown != float("inf")
            and max_drawdown != float("-inf")
            else 0
        )

        # Trade metrics
        win_rate = float((returns > 0).mean())
        avg_trade_return = float(returns.mean())
        num_trades = len(returns)

        # Profit factor
        positive_returns = float(returns[returns > 0].sum())
        negative_returns = float(abs(returns[returns < 0].sum()))
        profit_factor = (
            positive_returns / negative_returns
            if negative_returns > 0
            else 999.0  # Use large finite value instead of inf for JSON compatibility
        )

        return {
            "total_return": self._sanitize_float(total_return),
            "annualized_return": self._sanitize_float(annualized_return),
            "volatility": self._sanitize_float(volatility),
            "sharpe_ratio": self._sanitize_float(sharpe_ratio),
            "max_drawdown": self._sanitize_float(max_drawdown),
            "calmar_ratio": self._sanitize_float(calmar_ratio),
            "win_rate": self._sanitize_float(win_rate),
            "profit_factor": self._sanitize_float(profit_factor),
            "avg_trade_return": self._sanitize_float(avg_trade_return),
            "num_trades": int(num_trades),
        }

    def _store_backtest_results(
        self, strategy_name: str, results: dict[str, Any]
    ) -> None:
        """Store backtest results in the database."""
        # Store summary metrics
        metrics = results["metrics"]
        # Check if result already exists
        existing = self.results_conn.execute(
            "SELECT 1 FROM backtest_results WHERE strategy_name = ? AND start_date = ? AND end_date = ?",
            [strategy_name, results["start_date"], results["end_date"]],
        ).fetchone()

        if not existing:
            self.results_conn.execute(
                """
                INSERT INTO backtest_results (
                    strategy_name, start_date, end_date, total_return,
                    annualized_return, volatility, sharpe_ratio, max_drawdown,
                    calmar_ratio, win_rate, profit_factor, avg_trade_return, num_trades
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    strategy_name,
                    results["start_date"],
                    results["end_date"],
                    float(metrics["total_return"]),
                    float(metrics["annualized_return"]),
                    float(metrics["volatility"]),
                    float(metrics["sharpe_ratio"]),
                    float(metrics["max_drawdown"]),
                    float(metrics["calmar_ratio"]),
                    float(metrics["win_rate"]),
                    float(metrics["profit_factor"]),
                    float(metrics["avg_trade_return"]),
                    int(metrics["num_trades"]),
                ],
            )

        # Store portfolio values
        portfolio_df = results["portfolio_values"]
        for date, row in portfolio_df.iterrows():
            # Check if record already exists
            existing = self.results_conn.execute(
                "SELECT 1 FROM portfolio_values WHERE strategy_name = ? AND date = ?",
                [strategy_name, date],
            ).fetchone()

            if not existing:
                self.results_conn.execute(
                    """
                    INSERT INTO portfolio_values (strategy_name, date, portfolio_value, cash, weights)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        strategy_name,
                        date,
                        float(row["portfolio_value"]),
                        float(row["cash"]),
                        str(row["weights"]),  # Convert dict to string for storage
                    ],
                )

        # Store trades
        for trade in results["trades"]:
            trade_date = trade.get("trade_date", results["start_date"])
            # Check if trade already exists
            existing = self.results_conn.execute(
                "SELECT 1 FROM trades WHERE strategy_name = ? AND trade_date = ? AND symbol = ? AND action = ?",
                [strategy_name, trade_date, trade["symbol"], trade["action"]],
            ).fetchone()

            if not existing:
                self.results_conn.execute(
                    """
                    INSERT INTO trades (strategy_name, trade_date, symbol, action, quantity, price, value)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    [
                        strategy_name,
                        trade_date,
                        trade["symbol"],
                        trade["action"],
                        float(trade["quantity"]),
                        float(trade["price"]),
                        float(trade["value"]),
                    ],
                )

    def run_all_strategies(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
    ) -> dict[str, dict[str, Any]]:
        """
        Run backtests for all strategies.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            initial_capital: Starting capital for each backtest

        Returns:
            Dictionary mapping strategy names to their results
        """
        all_results = {}

        for strategy_name in self.strategies:
            try:
                self.logger.info(f"Running backtest for {strategy_name}")
                results = self.run_backtest(
                    strategy_name, start_date, end_date, initial_capital
                )
                all_results[strategy_name] = results
                self.logger.info(f"Completed backtest for {strategy_name}")
            except Exception as e:
                self.logger.error(f"Error running backtest for {strategy_name}: {e}")
                all_results[strategy_name] = {"error": str(e)}

        return all_results

    def get_results_summary(self) -> pd.DataFrame:
        """Get a summary of all backtest results."""
        try:
            return self.results_conn.execute("""
                SELECT
                    strategy_name,
                    start_date,
                    end_date,
                    total_return,
                    annualized_return,
                    volatility,
                    sharpe_ratio,
                    max_drawdown,
                    calmar_ratio,
                    win_rate,
                    profit_factor,
                    num_trades,
                    created_at
                FROM backtest_results
                ORDER BY strategy_name, start_date DESC
            """).fetchdf()
        except Exception as e:
            self.logger.error(f"Error getting results summary: {e}")
            return pd.DataFrame()

    def compare_strategies(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Compare strategy performance over a specific period.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with strategy comparison
        """
        try:
            return self.results_conn.execute(
                """
                SELECT
                    strategy_name,
                    total_return,
                    annualized_return,
                    volatility,
                    sharpe_ratio,
                    max_drawdown,
                    calmar_ratio,
                    win_rate,
                    profit_factor
                FROM backtest_results
                WHERE start_date = ? AND end_date = ?
                ORDER BY sharpe_ratio DESC
            """,
                [start_date, end_date],
            ).fetchdf()
        except Exception as e:
            self.logger.error(f"Error comparing strategies: {e}")
            return pd.DataFrame()

    def close(self) -> None:
        """Close database connections."""
        if self.market_data_manager:
            self.market_data_manager.close()
        if self.results_conn:
            self.results_conn.close()

    def __enter__(self) -> "UnifiedBacktester":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def main():
    """Main function to run the unified backtester."""
    parser = argparse.ArgumentParser(description="Unified Backtesting System")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2020-01-01",
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-12-31",
        help="End date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        help="Specific strategy to backtest (default: all strategies)",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=100000.0,
        help="Initial capital for backtest",
    )
    parser.add_argument(
        "--results-db",
        type=str,
        help="Path to results database (default: ~/.portfolio_backtest/backtest_results.duckdb)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show results summary after backtesting"
    )

    args = parser.parse_args()

    try:
        with UnifiedBacktester(args.results_db) as backtester:
            if args.strategy:
                # Run single strategy
                results = backtester.run_backtest(
                    args.strategy, args.start_date, args.end_date, args.initial_capital
                )
                print(f"\nBacktest completed for {args.strategy}:")
                print(f"Total Return: {results['metrics']['total_return']:.2%}")
                print(
                    f"Annualized Return: {results['metrics']['annualized_return']:.2%}"
                )
                print(f"Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
                print(f"Max Drawdown: {results['metrics']['max_drawdown']:.2%}")
            else:
                # Run all strategies
                all_results = backtester.run_all_strategies(
                    args.start_date, args.end_date, args.initial_capital
                )

                print(f"\nBacktest completed for {len(all_results)} strategies")
                for strategy_name, results in all_results.items():
                    if "error" in results:
                        print(f"{strategy_name}: ERROR - {results['error']}")
                    else:
                        metrics = results["metrics"]
                        print(
                            f"{strategy_name}: {metrics['total_return']:.2%} return, "
                            f"{metrics['sharpe_ratio']:.2f} Sharpe"
                        )

            # Show summary if requested
            if args.summary:
                print("\n" + "=" * 80)
                print("RESULTS SUMMARY")
                print("=" * 80)
                summary = backtester.get_results_summary()
                if not summary.empty:
                    print(summary.to_string(index=False))
                else:
                    print("No results found")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
