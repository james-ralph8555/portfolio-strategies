"""
Pytest fixtures for test data generation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_market_data():
    """Generate sample market data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    
    # Generate correlated price series
    n_days = 300
    
    # Base returns with some correlation structure
    tqqq_returns = np.random.normal(0.001, 0.03, n_days)  # Higher vol for leveraged ETF
    pfix_returns = np.random.normal(0.0005, 0.015, n_days)  # Lower vol for rate hedge
    iau_returns = np.random.normal(0.0003, 0.012, n_days)   # Gold returns
    sgov_returns = np.random.normal(0.0001, 0.002, n_days)  # Very low vol for cash
    
    # Add some correlation between TQQQ and PFIX
    correlation_factor = 0.3
    pfix_returns += correlation_factor * tqqq_returns
    
    # Generate price series
    data = pd.DataFrame({
        'TQQQ': 100 * np.exp(np.cumsum(tqqq_returns)),
        'PFIX': 50 * np.exp(np.cumsum(pfix_returns)),
        'IAU': 30 * np.exp(np.cumsum(iau_returns)),
        'SGOV': 20 * np.exp(np.cumsum(sgov_returns))
    }, index=dates)
    
    return data


@pytest.fixture
def positive_correlation_data():
    """Generate data with positive stock-bond correlation."""
    np.random.seed(123)
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    
    # Create positively correlated returns
    base_returns = np.random.normal(0.001, 0.02, 300)
    
    data = pd.DataFrame({
        'TQQQ': 100 * np.exp(np.cumsum(base_returns * 1.5)),  # Higher vol for TQQQ
        'PFIX': 50 * np.exp(np.cumsum(base_returns * 0.8)),   # Positive correlation
        'IAU': 30 * np.exp(np.cumsum(np.random.normal(0.0002, 0.01, 300))),
        'SGOV': 20 * np.exp(np.cumsum(np.random.normal(0.0001, 0.002, 300)))
    }, index=dates)
    
    return data


@pytest.fixture
def negative_correlation_data():
    """Generate data with negative stock-bond correlation."""
    np.random.seed(456)
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    
    # Create negatively correlated returns
    stock_returns = np.random.normal(0.001, 0.02, 300)
    bond_returns = -stock_returns * 0.5 + np.random.normal(0.0005, 0.01, 300)
    
    data = pd.DataFrame({
        'TQQQ': 100 * np.exp(np.cumsum(stock_returns * 1.5)),
        'PFIX': 50 * np.exp(np.cumsum(bond_returns)),
        'IAU': 30 * np.exp(np.cumsum(np.random.normal(0.0002, 0.01, 300))),
        'SGOV': 20 * np.exp(np.cumsum(np.random.normal(0.0001, 0.002, 300)))
    }, index=dates)
    
    return data


@pytest.fixture
def high_volatility_data():
    """Generate data with high volatility period."""
    np.random.seed(789)
    dates = pd.date_range('2023-01-01', periods=300, freq='D')
    
    # Normal volatility for first 200 days, high volatility for last 100 days
    normal_returns = np.random.normal(0.001, 0.02, 200)
    high_vol_returns = np.random.normal(0.001, 0.06, 100)  # 3x volatility
    
    all_returns = np.concatenate([normal_returns, high_vol_returns])
    
    data = pd.DataFrame({
        'TQQQ': 100 * np.exp(np.cumsum(all_returns * 1.5)),
        'PFIX': 50 * np.exp(np.cumsum(all_returns * 0.8)),
        'IAU': 30 * np.exp(np.cumsum(np.random.normal(0.0002, 0.01, 300))),
        'SGOV': 20 * np.exp(np.cumsum(np.random.normal(0.0001, 0.002, 300)))
    }, index=dates)
    
    return data


@pytest.fixture
def minimal_data():
    """Generate minimal dataset for edge case testing."""
    dates = pd.date_range('2023-01-01', periods=60, freq='D')
    
    data = pd.DataFrame({
        'TQQQ': [100 + i for i in range(60)],
        'PFIX': [50 + i * 0.5 for i in range(60)],
        'IAU': [30 + i * 0.3 for i in range(60)],
        'SGOV': [20 + i * 0.1 for i in range(60)]
    }, index=dates)
    
    return data


@pytest.fixture
def strategy_config():
    """Default strategy configuration for testing."""
    return {
        "target_volatility": 0.15,
        "tqqq_base_weight": 0.60,
        "pfix_base_weight": 0.20,
        "gold_base_weight": 0.15,
        "cash_base_weight": 0.05,
        "correlation_threshold": 0.0,
        "volatility_lookback": 60,
        "correlation_lookback": 252,
        "drift_bands": 10
    }


@pytest.fixture
def custom_strategy_config():
    """Custom strategy configuration for testing."""
    return {
        "target_volatility": 0.12,
        "tqqq_base_weight": 0.55,
        "pfix_base_weight": 0.25,
        "gold_base_weight": 0.15,
        "cash_base_weight": 0.05,
        "correlation_threshold": 0.1,
        "volatility_lookback": 45,
        "correlation_lookback": 180,
        "drift_bands": 5
    }