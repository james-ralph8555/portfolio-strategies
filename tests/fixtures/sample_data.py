"""
Sample market data for testing.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def create_sample_price_data(days=252, assets=None):
    """
    Create sample price data for testing.

    Args:
        days: Number of days of price data
        assets: List of asset symbols

    Returns:
        DataFrame with price data
    """
    if assets is None:
        assets = ["TQQQ", "DBMF", "IAU", "SGOV"]

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


def create_sample_config():
    """
    Create sample configuration for testing.

    Returns:
        Dictionary with sample configuration
    """
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


def create_invalid_config():
    """
    Create invalid configuration for testing validation.

    Returns:
        Dictionary with invalid configuration
    """
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
