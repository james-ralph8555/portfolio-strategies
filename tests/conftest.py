"""
Pytest configuration and fixtures for strategy testing.

This module provides common fixtures and configuration that can be used
across all test modules to ensure consistency and reduce duplication.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import pytest

# Add the project root to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strategies.equity_crisis_alpha.strategy import EquityCrisisAlphaStrategy
from strategies.equity_inflation_beta.strategy import EquityInflationBetaStrategy
from strategies.equity_vol_barbell.strategy import EquityVolBarbellStrategy


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample configuration for equity crisis alpha strategy."""
    return {
        "risk_budget": {
            "tqqq_weight": 0.6,
            "diversifier_weight": 0.3,
            "cash_weight": 0.1,
        },
        "volatility_targeting": {"target_vol": 0.15, "lookback_period": 60},
        "rebalancing": {"frequency": "monthly", "drift_bands": 10},
        "black_litterman": {
            "views": [{"assets": ["TQQQ"], "confidence": 0.7, "expected_return": 0.12}]
        },
        "risk_controls": {
            "max_leverage": 3.0,
            "max_single_asset_weight": 0.8,
            "correlation_regime_guard": True,
        },
    }


@pytest.fixture
def equity_inflation_beta_config() -> dict[str, Any]:
    """Sample configuration for equity inflation beta strategy."""
    return {
        "assets": {
            "core": "TQQQ",
            "commodities": "PDBC",
            "gold": "IAU",
            "cash": "SGOV",
        },
        "signals": {
            "trend": {"weight": 0.6, "lookback_periods": [20, 60, 120]},
            "carry": {"weight": 0.4},
        },
        "risk_parity": {"commodities_gold_ratio": 0.5, "lookback_period": 60},
        "tqqq_overweight": {"base_weight": 0.6, "scaling_factor": 1.2},
        "volatility_targeting": {"target_vol": 0.15, "lookback_period": 60},
        "rebalancing": {"frequency": "monthly", "drift_bands": 10},
    }


@pytest.fixture
def equity_vol_barbell_config() -> dict[str, Any]:
    """Default strategy configuration for testing."""
    return {
        "barbell_allocation": {
            "tqqq_base_weight": 0.7,
            "short_vol_weight": 0.15,
            "tail_hedge_weight": 0.1,
            "cash_weight": 0.05,
        },
        "drawdown_triggers": {
            "volatility_spike_threshold": 2.0,
            "max_drawdown_threshold": 0.15,
            "tqqq_scaling_factor": 0.5,
        },
        "vol_sizing": {
            "vix_term_structure_threshold": 0.1,
            "svol_max_weight": 0.2,
            "tail_max_weight": 0.15,
        },
        "rebalancing": {"frequency": "monthly", "drift_bands": 5},
    }


@pytest.fixture
def sample_price_data() -> pd.DataFrame:
    """Create sample price data for testing."""
    assets = ["TQQQ", "DBMF", "IAU", "SGOV"]
    days = 252

    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    # Create price data with different characteristics for each asset
    np.random.seed(42)  # For reproducible tests

    price_data = {}

    for asset in assets:
        if asset == "TQQQ":
            # High volatility, upward trend
            returns = np.random.normal(0.001, 0.04, len(dates))
            cumulative_returns = np.cumprod(1 + returns)
            price_data[asset] = 100 * cumulative_returns

        elif asset == "DBMF":
            # Low volatility, stable
            returns = np.random.normal(0.0003, 0.01, len(dates))
            cumulative_returns = np.cumprod(1 + returns)
            price_data[asset] = 100 * cumulative_returns

        elif asset == "IAU":
            # Medium volatility, slight upward trend
            returns = np.random.normal(0.0005, 0.015, len(dates))
            cumulative_returns = np.cumprod(1 + returns)
            price_data[asset] = 100 * cumulative_returns

        elif asset == "SGOV":
            # Very low volatility, stable returns
            returns = np.random.normal(0.0002, 0.002, len(dates))
            cumulative_returns = np.cumprod(1 + returns)
            price_data[asset] = 100 * cumulative_returns

    return pd.DataFrame(price_data, index=dates)


@pytest.fixture
def inflation_beta_price_data() -> pd.DataFrame:
    """Sample price data for inflation beta strategy testing."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=200, freq="D")

    # Create realistic price series with some trends
    tqqq_prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 200))
    pdbc_prices = np.cumprod(1 + np.random.normal(0.0005, 0.015, 200))
    iau_prices = np.cumprod(1 + np.random.normal(0.0003, 0.01, 200))
    sgov_prices = np.cumprod(1 + np.random.normal(0.0001, 0.002, 200))

    return pd.DataFrame(
        {
            "TQQQ": tqqq_prices,
            "PDBC": pdbc_prices,
            "IAU": iau_prices,
            "SGOV": sgov_prices,
        },
        index=dates,
    )


@pytest.fixture
def vol_barbell_price_data() -> pd.DataFrame:
    """Sample price data for volatility barbell strategy testing."""
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=200, freq="D")

    # Create realistic price series for vol barbell assets
    tqqq_prices = np.cumprod(1 + np.random.normal(0.001, 0.03, 200))
    svol_prices = np.cumprod(1 + np.random.normal(0.0002, 0.01, 200))
    tail_prices = np.cumprod(1 + np.random.normal(0.0003, 0.015, 200))
    cash_prices = np.cumprod(1 + np.random.normal(0.0001, 0.001, 200))

    return pd.DataFrame(
        {
            "TQQQ": tqqq_prices,
            "SVOL": svol_prices,
            "TAIL": tail_prices,
            "CASH": cash_prices,
        },
        index=dates,
    )


@pytest.fixture
def trending_data() -> pd.DataFrame:
    """Price data with clear trends for signal testing."""
    np.random.seed(123)
    dates = pd.date_range("2020-01-01", periods=150, freq="D")

    # Create trending data
    tqqq_trend = np.linspace(100, 150, 150) + np.random.normal(0, 2, 150)
    pdbc_trend = np.linspace(50, 60, 150) + np.random.normal(0, 1, 150)
    iau_trend = np.linspace(30, 35, 150) + np.random.normal(0, 0.5, 150)
    sgov_trend = np.linspace(10, 11, 150) + np.random.normal(0, 0.1, 150)

    return pd.DataFrame(
        {"TQQQ": tqqq_trend, "PDBC": pdbc_trend, "IAU": iau_trend, "SGOV": sgov_trend},
        index=dates,
    )


@pytest.fixture
def equity_crisis_alpha_strategy(sample_config):
    """Create EquityCrisisAlphaStrategy instance for testing."""
    return EquityCrisisAlphaStrategy(sample_config)


@pytest.fixture
def equity_inflation_beta_strategy(equity_inflation_beta_config):
    """Create EquityInflationBetaStrategy instance for testing."""
    return EquityInflationBetaStrategy(equity_inflation_beta_config)


@pytest.fixture
def equity_vol_barbell_strategy(equity_vol_barbell_config):
    """Create EquityVolBarbellStrategy instance for testing."""
    return EquityVolBarbellStrategy(equity_vol_barbell_config)


@pytest.fixture
def strategy(equity_inflation_beta_config):
    """Generic strategy fixture for testing - defaults to equity inflation beta."""
    return EquityInflationBetaStrategy(equity_inflation_beta_config)


@pytest.fixture
def invalid_config():
    """Create invalid configuration for testing validation."""
    return {
        "risk_budget": {
            "tqqq_weight": 0.8,
            "diversifier_weight": 0.4,  # Sum > 1.0
            "cash_weight": 0.1,
        },
        "volatility_targeting": {
            "target_vol": 0.8,  # Too high
            "lookback_period": 60,
        },
        # Missing rebalancing section
    }


@pytest.fixture
def minimal_config() -> dict[str, Any]:
    """Minimal valid configuration."""
    return {
        "assets": {
            "core": "TQQQ",
            "commodities": "PDBC",
            "gold": "IAU",
            "cash": "SGOV",
        },
        "signals": {"trend": {"weight": 0.6}, "carry": {"weight": 0.4}},
        "risk_parity": {"lookback_period": 60},
        "tqqq_overweight": {"base_weight": 0.6, "scaling_factor": 1.2},
        "volatility_targeting": {"lookback_period": 60},
        "rebalancing": {"frequency": "monthly", "drift_bands": 10},
    }


# Volatility barbell specific fixtures
@pytest.fixture
def minimal_market_data():
    """Basic market data with required columns for testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=60, freq="D")

    return pd.DataFrame(
        {
            "TQQQ": np.cumprod(1 + np.random.normal(0.001, 0.02, 60)),
            "SVOL": np.cumprod(1 + np.random.normal(0.0002, 0.008, 60)),
            "TAIL": np.cumprod(1 + np.random.normal(0.0003, 0.01, 60)),
            "CASH": np.cumprod(1 + np.random.normal(0.0001, 0.001, 60)),
        },
        index=dates,
    )


@pytest.fixture
def extended_market_data():
    """Full year of realistic market data."""
    np.random.seed(123)
    dates = pd.date_range("2023-01-01", periods=252, freq="D")

    # Simulate different market conditions throughout the year
    tqqq_returns = np.random.normal(0.001, 0.025, 252)
    tqqq_returns[50:100] = np.random.normal(-0.002, 0.04, 50)  # Stress period

    return pd.DataFrame(
        {
            "TQQQ": 100 * np.cumprod(1 + tqqq_returns),
            "SVOL": 50 * np.cumprod(1 + np.random.normal(0.0002, 0.008, 252)),
            "TAIL": 30 * np.cumprod(1 + np.random.normal(0.0003, 0.01, 252)),
            "CASH": 10 * np.cumprod(1 + np.random.normal(0.0001, 0.001, 252)),
        },
        index=dates,
    )


@pytest.fixture
def crisis_market_data():
    """Market data simulating crisis conditions."""
    np.random.seed(999)
    dates = pd.date_range("2023-01-01", periods=90, freq="D")

    # Severe drawdown period
    crisis_returns = np.random.normal(-0.01, 0.05, 90)

    return pd.DataFrame(
        {
            "TQQQ": 100 * np.cumprod(1 + crisis_returns),
            "SVOL": 50 * np.cumprod(1 + np.random.normal(0.002, 0.02, 90)),
            "TAIL": 30 * np.cumprod(1 + np.random.normal(0.01, 0.03, 90)),
            "CASH": 10 * np.cumprod(1 + np.random.normal(0.0001, 0.001, 90)),
        },
        index=dates,
    )


@pytest.fixture
def low_volatility_data():
    """Market data with low volatility conditions."""
    np.random.seed(555)
    dates = pd.date_range("2023-01-01", periods=120, freq="D")

    return pd.DataFrame(
        {
            "TQQQ": np.cumprod(1 + np.random.normal(0.0005, 0.008, 120)),
            "SVOL": np.cumprod(1 + np.random.normal(0.0001, 0.003, 120)),
            "TAIL": np.cumprod(1 + np.random.normal(0.0002, 0.004, 120)),
            "CASH": np.cumprod(1 + np.random.normal(0.0001, 0.0005, 120)),
        },
        index=dates,
    )


# Fixtures for EquityConvexRateHedgeStrategy tests
@pytest.fixture
def custom_strategy_config() -> dict[str, Any]:
    """Custom configuration for equity convex rate hedge strategy."""
    return {
        "target_volatility": 0.12,
        "tqqq_base_weight": 0.55,
        "pfix_base_weight": 0.25,
        "gold_base_weight": 0.15,
        "cash_base_weight": 0.05,
        "correlation_threshold": 0.0,
        "volatility_lookback": 60,
        "correlation_lookback": 252,
        "drift_bands": 5,
    }


@pytest.fixture
def sample_market_data() -> pd.DataFrame:
    """Sample market data for equity convex rate hedge strategy testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=300, freq="D")

    return pd.DataFrame(
        {
            "TQQQ": np.cumprod(1 + np.random.normal(0.001, 0.03, 300)),
            "PFIX": np.cumprod(1 + np.random.normal(0.0003, 0.01, 300)),
            "IAU": np.cumprod(1 + np.random.normal(0.0005, 0.015, 300)),
            "SGOV": np.cumprod(1 + np.random.normal(0.0002, 0.002, 300)),
        },
        index=dates,
    )


@pytest.fixture
def minimal_data() -> pd.DataFrame:
    """Minimal market data for testing edge cases."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=50, freq="D")

    return pd.DataFrame(
        {
            "TQQQ": np.cumprod(1 + np.random.normal(0.001, 0.02, 50)),
            "PFIX": np.cumprod(1 + np.random.normal(0.0003, 0.008, 50)),
            "IAU": np.cumprod(1 + np.random.normal(0.0005, 0.01, 50)),
            "SGOV": np.cumprod(1 + np.random.normal(0.0002, 0.001, 50)),
        },
        index=dates,
    )


@pytest.fixture
def strategy_config() -> dict[str, Any]:
    """Complete strategy configuration for testing."""
    return {
        "target_volatility": 0.15,
        "tqqq_base_weight": 0.60,
        "pfix_base_weight": 0.20,
        "gold_base_weight": 0.15,
        "cash_base_weight": 0.05,
        "correlation_threshold": 0.0,
        "volatility_lookback": 60,
        "correlation_lookback": 252,
        "drift_bands": 10,
    }
