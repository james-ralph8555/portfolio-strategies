"""
Pytest configuration and shared fixtures for the test suite.

This module provides common fixtures and configuration that can be used
across all test modules to ensure consistency and reduce duplication.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add the project root to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from strategies.equity_vol_barbell.strategy import EquityVolBarbellStrategy


@pytest.fixture
def default_strategy_config():
    """Default strategy configuration for testing."""
    return {
        'barbell_allocation': {
            'tqqq_base_weight': 0.7,
            'short_vol_weight': 0.15,
            'tail_hedge_weight': 0.1,
            'cash_weight': 0.05
        },
        'drawdown_triggers': {
            'volatility_spike_threshold': 2.0,
            'max_drawdown_threshold': 0.15,
            'tqqq_scaling_factor': 0.5
        },
        'vol_sizing': {
            'vix_term_structure_threshold': 0.1,
            'svol_max_weight': 0.2,
            'tail_max_weight': 0.15
        },
        'rebalancing': {
            'frequency': 'monthly',
            'drift_bands': 5
        }
    }


@pytest.fixture
def strategy(default_strategy_config):
    """Create a strategy instance with default configuration."""
    return EquityVolBarbellStrategy(default_strategy_config)


@pytest.fixture
def minimal_market_data():
    """Minimal market data with required columns."""
    dates = pd.date_range('2023-01-01', periods=10, freq='D')
    np.random.seed(42)
    
    data = pd.DataFrame(index=dates)
    data['TQQQ_Returns'] = np.random.normal(0.001, 0.02, 10)
    data['SPY_Returns'] = np.random.normal(0.0005, 0.015, 10)
    data['SVOL_Returns'] = np.random.normal(0.0002, 0.008, 10)
    data['TAIL_Returns'] = np.random.normal(0.0001, 0.012, 10)
    data['VIX'] = 20 + np.random.normal(0, 2, 10)
    data['VIX_MA20'] = data['VIX'].rolling(window=5, min_periods=1).mean()
    data['Drawdown'] = np.random.uniform(-0.05, 0, 10)
    
    return data


@pytest.fixture
def extended_market_data():
    """Extended market data for more comprehensive testing."""
    dates = pd.date_range('2022-01-01', periods=252, freq='D')
    np.random.seed(123)
    
    data = pd.DataFrame(index=dates)
    
    # Simulate realistic market data with some trends
    trend = np.linspace(0, 0.001, 252)  # Slight upward trend
    data['SPY_Returns'] = trend + np.random.normal(0, 0.015, 252)
    data['TQQQ_Returns'] = data['SPY_Returns'] * 2.5 + np.random.normal(0, 0.01, 252)
    data['SVOL_Returns'] = np.random.normal(0.0002, 0.008, 252)
    data['TAIL_Returns'] = np.random.normal(0.0001, 0.012, 252)
    
    # Realistic VIX pattern with some volatility clustering
    vix_base = 20 + 10 * np.sin(np.linspace(0, 4*np.pi, 252))
    vix_volatility = np.random.normal(0, 3, 252)
    data['VIX'] = np.maximum(vix_base + vix_volatility, 10)
    data['VIX_MA20'] = data['VIX'].rolling(window=20).mean()
    
    # Calculate drawdown
    data['Cumulative_Return'] = (1 + data['SPY_Returns']).cumprod()
    data['Peak'] = data['Cumulative_Return'].expanding().max()
    data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
    
    return data


@pytest.fixture
def crisis_market_data():
    """Market data simulating crisis conditions."""
    dates = pd.date_range('2008-01-01', periods=100, freq='D')
    np.random.seed(456)
    
    data = pd.DataFrame(index=dates)
    
    # Crisis conditions: negative returns with high volatility
    data['SPY_Returns'] = np.random.normal(-0.005, 0.03, 100)
    data['TQQQ_Returns'] = data['SPY_Returns'] * 2.5 + np.random.normal(0, 0.02, 100)
    data['SVOL_Returns'] = np.random.normal(0.001, 0.015, 100)  # Higher vol premium
    data['TAIL_Returns'] = np.random.normal(0.002, 0.02, 100)   # Positive tail returns
    
    # Very high VIX during crisis
    data['VIX'] = 40 + 15 * np.random.uniform(0, 1, 100)
    data['VIX_MA20'] = data['VIX'].rolling(window=20, min_periods=1).mean()
    
    # Severe drawdown
    data['Cumulative_Return'] = (1 + data['SPY_Returns']).cumprod()
    data['Peak'] = data['Cumulative_Return'].expanding().max()
    data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
    
    return data


@pytest.fixture
def low_volatility_data():
    """Market data simulating low volatility conditions."""
    dates = pd.date_range('2017-01-01', periods=100, freq='D')
    np.random.seed(789)
    
    data = pd.DataFrame(index=dates)
    
    # Low volatility conditions
    data['SPY_Returns'] = np.random.normal(0.0003, 0.008, 100)
    data['TQQQ_Returns'] = data['SPY_Returns'] * 2.5 + np.random.normal(0, 0.005, 100)
    data['SVOL_Returns'] = np.random.normal(0.0001, 0.004, 100)
    data['TAIL_Returns'] = np.random.normal(-0.0001, 0.006, 100)  # Cost of hedge
    
    # Low VIX
    data['VIX'] = 12 + 3 * np.random.uniform(0, 1, 100)
    data['VIX_MA20'] = data['VIX'].rolling(window=20, min_periods=1).mean()
    
    # Minimal drawdown
    data['Cumulative_Return'] = (1 + data['SPY_Returns']).cumprod()
    data['Peak'] = data['Cumulative_Return'].expanding().max()
    data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
    
    return data


@pytest.fixture
def empty_market_data():
    """Empty market data for edge case testing."""
    return pd.DataFrame()


@pytest.fixture
def incomplete_market_data():
    """Market data with missing required columns."""
    dates = pd.date_range('2023-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'SPY_Returns': [0.01, 0.02, -0.01, 0.005, -0.005],
        # Missing other required columns
    }, index=dates)


@pytest.fixture
def nan_market_data():
    """Market data with NaN values."""
    dates = pd.date_range('2023-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'TQQQ_Returns': [0.01, np.nan, 0.02, 0.015, np.nan],
        'SPY_Returns': [0.005, 0.008, np.nan, 0.003, 0.006],
        'SVOL_Returns': [0.001, 0.002, 0.0015, np.nan, 0.0018],
        'TAIL_Returns': [0.0005, np.nan, 0.0008, 0.0006, 0.0007],
        'VIX': [20, 22, np.nan, 25, 23],
        'VIX_MA20': [20, 21, 22, 23, 24],
        'Drawdown': [0, -0.02, np.nan, -0.01, -0.03]
    }, index=dates)


@pytest.fixture
def sample_weights():
    """Sample portfolio weights for testing."""
    return {
        'TQQQ': 0.70,
        'SVOL': 0.15,
        'TAIL': 0.10,
        'SGOV': 0.05
    }


@pytest.fixture
def drifted_weights():
    """Sample drifted portfolio weights for testing."""
    return {
        'TQQQ': 0.76,  # 6% drift
        'SVOL': 0.14,   # 1% drift
        'TAIL': 0.10,
        'SGOV': 0.00   # 5% drift
    }


@pytest.fixture
def invalid_config():
    """Invalid configuration for testing validation."""
    return {
        'barbell_allocation': {
            'tqqq_base_weight': 0.8,  # Invalid: sum > 1.0
            'short_vol_weight': 0.3,
            'tail_hedge_weight': 0.1,
            'cash_weight': 0.05
        },
        'drawdown_triggers': {
            'volatility_spike_threshold': 2.0,
            'max_drawdown_threshold': 0.15,
            'tqqq_scaling_factor': 0.5
        },
        'vol_sizing': {
            'vix_term_structure_threshold': 0.1,
            'svol_max_weight': 0.2,
            'tail_max_weight': 0.15
        },
        'rebalancing': {
            'frequency': 'monthly',
            'drift_bands': 5
        }
    }


@pytest.fixture(params=[
    'minimal_market_data',
    'extended_market_data', 
    'crisis_market_data',
    'low_volatility_data'
])
def all_market_data(request):
    """Parametrized fixture that provides all market data types."""
    return request.getfixturevalue(request.param)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "functional: marks tests as functional tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location."""
    for item in items:
        # Add unit marker to unit tests
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add functional marker to functional tests
        if "functional" in item.nodeid:
            item.add_marker(pytest.mark.functional)
        
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)