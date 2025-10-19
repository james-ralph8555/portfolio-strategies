"""
Integration tests for the equity volatility barbell strategy.

This module tests the integration of the strategy with the broader
portfolio management system and external dependencies.
"""

import os
import sys
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# Add the project root to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.interfaces.strategy import Strategy
from strategies.equity_vol_barbell.strategy import EquityVolBarbellStrategy


class TestEquityVolBarbellIntegration:
    """Integration tests for EquityVolBarbellStrategy class."""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance for integration testing."""
        config = {
            "core_equity_weight": 0.60,
            "vol_sleeve_weight": 0.40,
            "tqqq_base_weight": 0.30,
            "spy_weight": 0.30,
            "svol_weight": 0.25,
            "tail_weight": 0.15,
            "drawdown_threshold": 0.15,
            "volatility_spike_threshold": 2.0,
            "vix_elevated_threshold": 25,
            "vix_stress_threshold": 35,
            "rebalance_threshold": 0.05,
        }
        return EquityVolBarbellStrategy(config)

    def test_strategy_inheritance(self, strategy):
        """Test that strategy properly inherits from base Strategy class."""
        assert isinstance(strategy, Strategy)
        assert hasattr(strategy, "calculate_weights")
        assert hasattr(strategy, "should_rebalance")
        assert hasattr(strategy, "validate_config")

    @patch("yfinance.download")
    def test_real_data_integration(self, mock_yf_download, strategy):
        """Test integration with real market data from yfinance."""
        # Mock yfinance response
        mock_data = pd.DataFrame(
            {
                "TQQQ": np.random.normal(100, 10, 100),
                "VOO": np.random.normal(400, 20, 100),
                "SVOL": np.random.normal(50, 5, 100),
                "TAIL": np.random.normal(60, 8, 100),
                "^VIX": np.random.normal(20, 5, 100),
            },
            index=pd.date_range("2023-01-01", periods=100),
        )

        mock_yf_download.return_value = mock_data

        # Test that strategy can process real data format
        weights = strategy.calculate_weights(mock_data)

        assert set(weights.keys()) == set(strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 0.01
        assert all(w > 0 for w in weights.values())

    def test_portfolio_manager_integration(self, strategy):
        """Test integration with hypothetical portfolio manager."""

        # Mock portfolio manager interface
        class MockPortfolioManager:
            def __init__(self):
                self.strategies = []
                self.current_weights = {}

            def add_strategy(self, strategy):
                self.strategies.append(strategy)

            def get_target_weights(self, market_data):
                weights = {}
                for strategy in self.strategies:
                    strategy_weights = strategy.calculate_weights(market_data)
                    weights.update(strategy_weights)
                return weights

            def should_rebalance_portfolio(self, market_data):
                target_weights = self.get_target_weights(market_data)
                return strategy.should_rebalance(self.current_weights, target_weights)

        # Test integration
        portfolio_manager = MockPortfolioManager()
        portfolio_manager.add_strategy(strategy)

        # Create test market data
        market_data = pd.DataFrame(
            {
                "TQQQ_Returns": [0.01, 0.02, -0.01],
                "VOO_Returns": [0.005, 0.008, -0.003],
                "SVOL_Returns": [0.001, 0.002, 0.0005],
                "TAIL_Returns": [0.0005, 0.001, 0.0008],
                "VIX": [20, 22, 25],
                "VIX_MA20": [20, 21, 22],
                "Drawdown": [0, -0.02, -0.01],
            },
            index=pd.date_range("2023-01-01", periods=3),
        )

        # Test portfolio manager can use strategy
        target_weights = portfolio_manager.get_target_weights(market_data)
        assert set(target_weights.keys()) == set(strategy.assets)

        # Test rebalancing logic
        portfolio_manager.current_weights = target_weights
        assert not portfolio_manager.should_rebalance_portfolio(market_data)

        # Simulate drift - need to exceed 10% drift band (drift_bands = 10)
        portfolio_manager.current_weights["TQQQ"] += (
            0.11  # 11% drift exceeds 10% threshold
        )
        assert portfolio_manager.should_rebalance_portfolio(market_data)

    def test_risk_management_integration(self, strategy):
        """Test integration with risk management systems."""

        # Mock risk manager
        class MockRiskManager:
            def __init__(self):
                self.max_drawdown = 0.20
                self.max_volatility = 0.25

            def check_risk_limits(self, weights, market_data):
                # Simple risk check
                portfolio_volatility = 0.15  # Mock calculation
                current_drawdown = (
                    abs(market_data["Drawdown"].min())
                    if "Drawdown" in market_data
                    else 0
                )

                return {
                    "volatility_ok": portfolio_volatility <= self.max_volatility,
                    "drawdown_ok": current_drawdown <= self.max_drawdown,
                    "overall_risk": portfolio_volatility + current_drawdown,
                }

        risk_manager = MockRiskManager()

        # Create test data
        market_data = pd.DataFrame(
            {
                "TQQQ_Returns": [0.01, -0.02, 0.01],
                "VOO_Returns": [0.005, -0.008, 0.005],
                "SVOL_Returns": [0.001, 0.002, 0.001],
                "TAIL_Returns": [0.0005, 0.001, 0.0005],
                "VIX": [20, 30, 25],
                "VIX_MA20": [20, 22, 23],
                "Drawdown": [0, -0.10, -0.05],
            },
            index=pd.date_range("2023-01-01", periods=3),
        )

        weights = strategy.calculate_weights(market_data)
        risk_check = risk_manager.check_risk_limits(weights, market_data)

        assert "volatility_ok" in risk_check
        assert "drawdown_ok" in risk_check
        assert "overall_risk" in risk_check

    def test_backtesting_integration(self, strategy):
        """Test integration with backtesting framework."""

        # Mock backtester
        class MockBacktester:
            def __init__(self, strategy):
                self.strategy = strategy
                self.results = []

            def run_backtest(self, market_data, start_date, end_date):
                # Simple backtest simulation
                data_slice = market_data.loc[start_date:end_date]

                for date in data_slice.index:
                    # Get data up to current date
                    historical_data = data_slice.loc[:date]

                    # Calculate weights
                    weights = self.strategy.calculate_weights(historical_data)

                    # Store results
                    self.results.append(
                        {
                            "date": date,
                            "weights": weights,
                            "return": historical_data["VOO_Returns"].get(date, 0),
                        }
                    )

                return self.results

        # Create extended test data
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        market_data = pd.DataFrame(
            {
                "TQQQ_Returns": np.random.normal(0.001, 0.02, 30),
                "VOO_Returns": np.random.normal(0.0005, 0.015, 30),
                "SVOL_Returns": np.random.normal(0.0002, 0.008, 30),
                "TAIL_Returns": np.random.normal(0.0001, 0.012, 30),
                "VIX": 20 + np.random.normal(0, 3, 30),
                "VIX_MA20": pd.Series(20 + np.random.normal(0, 3, 30))
                .rolling(window=10, min_periods=1)
                .mean(),
                "Drawdown": np.random.uniform(-0.1, 0, 30),
            },
            index=dates,
        )

        # Run backtest
        backtester = MockBacktester(strategy)
        results = backtester.run_backtest(market_data, dates[0], dates[-1])

        assert len(results) == 30
        assert all("weights" in result for result in results)
        assert all("date" in result for result in results)
        assert all("return" in result for result in results)

    def test_configuration_management_integration(self, strategy):
        """Test integration with configuration management system."""

        # Mock config manager
        class MockConfigManager:
            def __init__(self):
                self.configs = {}

            def load_config(self, strategy_name):
                return self.configs.get(strategy_name, {})

            def save_config(self, strategy_name, config):
                self.configs[strategy_name] = config

            def validate_config(self, config):
                # Simple validation
                required_keys = ["core_equity_weight", "vol_sleeve_weight"]
                return all(key in config for key in required_keys)

        config_manager = MockConfigManager()

        # Test saving and loading configuration
        original_config = strategy.get_config()
        config_manager.save_config("equity_vol_barbell", original_config)

        loaded_config = config_manager.load_config("equity_vol_barbell")
        assert loaded_config == original_config

        # Test configuration validation
        assert config_manager.validate_config(loaded_config)

        # Test invalid configuration
        invalid_config = {"invalid_key": "value"}
        assert not config_manager.validate_config(invalid_config)

    def test_monitoring_integration(self, strategy):
        """Test integration with monitoring and alerting systems."""

        # Mock monitoring system
        class MockMonitoringSystem:
            def __init__(self):
                self.alerts = []

            def check_strategy_health(self, strategy, market_data):
                weights = strategy.calculate_weights(market_data)

                # Simple health checks
                issues = []

                # Check weights sum to 1
                if abs(sum(weights.values()) - 1.0) > 0.01:
                    issues.append("Weights don't sum to 1")

                # Check for negative weights
                if any(w < 0 for w in weights.values()):
                    issues.append("Negative weights detected")

                # Check for extreme weights
                if any(w > 0.8 for w in weights.values()):
                    issues.append("Extreme weights detected")

                return {
                    "healthy": len(issues) == 0,
                    "issues": issues,
                    "timestamp": pd.Timestamp.now(),
                }

            def send_alert(self, message):
                self.alerts.append(
                    {"message": message, "timestamp": pd.Timestamp.now()}
                )

        monitoring = MockMonitoringSystem()

        # Create test data
        market_data = pd.DataFrame(
            {
                "TQQQ_Returns": [0.01, 0.02, -0.01],
                "VOO_Returns": [0.005, 0.008, -0.003],
                "SVOL_Returns": [0.001, 0.002, 0.0005],
                "TAIL_Returns": [0.0005, 0.001, 0.0008],
                "VIX": [20, 22, 25],
                "VIX_MA20": [20, 21, 22],
                "Drawdown": [0, -0.02, -0.01],
            },
            index=pd.date_range("2023-01-01", periods=3),
        )

        # Test health monitoring
        health_check = monitoring.check_strategy_health(strategy, market_data)
        assert "healthy" in health_check
        assert "issues" in health_check
        assert "timestamp" in health_check

        # Test alerting
        if not health_check["healthy"]:
            monitoring.send_alert(f"Strategy health issues: {health_check['issues']}")
            assert len(monitoring.alerts) > 0

    def test_data_pipeline_integration(self, strategy):
        """Test integration with data pipeline systems."""

        # Mock data pipeline
        class MockDataPipeline:
            def __init__(self):
                self.data_sources = {}

            def add_data_source(self, name, source):
                self.data_sources[name] = source

            def fetch_data(self, symbols, start_date, end_date):
                # Mock data fetching
                dates = pd.date_range(start_date, end_date, freq="D")
                data = pd.DataFrame(index=dates)

                for symbol in symbols:
                    if symbol in self.data_sources:
                        data[symbol] = self.data_sources[symbol](len(dates))
                    else:
                        data[symbol] = np.random.normal(0, 0.01, len(dates))

                return data

            def preprocess_data(self, raw_data):
                # Mock preprocessing
                processed = raw_data.copy()

                # Calculate returns if not present
                for col in processed.columns:
                    if not col.endswith("_Returns"):
                        returns_col = f"{col}_Returns"
                        if returns_col not in processed.columns:
                            processed[returns_col] = (
                                processed[col].pct_change().fillna(0)
                            )

                # Add VIX data if missing
                if "VIX" not in processed.columns:
                    processed["VIX"] = 20 + np.random.normal(0, 5, len(processed))

                if "VIX_MA20" not in processed.columns:
                    processed["VIX_MA20"] = (
                        processed["VIX"].rolling(window=20, min_periods=1).mean()
                    )

                # Add drawdown if missing
                if "Drawdown" not in processed.columns:
                    if "VOO_Returns" in processed.columns:
                        cumulative = (1 + processed["VOO_Returns"]).cumprod()
                        peak = cumulative.expanding().max()
                        processed["Drawdown"] = (cumulative - peak) / peak
                    else:
                        processed["Drawdown"] = 0

                return processed

        # Set up data pipeline
        pipeline = MockDataPipeline()

        # Add mock data sources
        pipeline.add_data_source("TQQQ", lambda n: np.random.normal(100, 10, n))
        pipeline.add_data_source("VOO", lambda n: np.random.normal(400, 20, n))
        pipeline.add_data_source("SVOL", lambda n: np.random.normal(50, 5, n))
        pipeline.add_data_source("TAIL", lambda n: np.random.normal(60, 8, n))

        # Fetch and process data
        raw_data = pipeline.fetch_data(
            ["TQQQ", "VOO", "SVOL", "TAIL"], "2023-01-01", "2023-01-31"
        )

        processed_data = pipeline.preprocess_data(raw_data)

        # Test strategy with pipeline data
        weights = strategy.calculate_weights(processed_data)

        assert set(weights.keys()) == set(strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 0.01
        assert all(w > 0 for w in weights.values())
