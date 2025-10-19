"""
Pytest configuration and fixtures for strategy testing.
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any
from strategies.equity_inflation_beta.strategy import EquityInflationBetaStrategy


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for equity inflation beta strategy."""
    return {
        'assets': {
            'core': 'TQQQ',
            'commodities': 'PDBC', 
            'gold': 'IAU',
            'cash': 'SGOV'
        },
        'signals': {
            'trend': {
                'weight': 0.6,
                'lookback_periods': [20, 60, 120]
            },
            'carry': {
                'weight': 0.4
            }
        },
        'risk_parity': {
            'commodities_gold_ratio': 0.5,
            'lookback_period': 60
        },
        'tqqq_overweight': {
            'base_weight': 0.6,
            'scaling_factor': 1.2
        },
        'volatility_targeting': {
            'target_vol': 0.15,
            'lookback_period': 60
        },
        'rebalancing': {
            'frequency': 'monthly',
            'drift_bands': 10
        }
    }


@pytest.fixture
def sample_price_data() -> pd.DataFrame:
    """Sample price data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=200, freq='D')
    
    # Create realistic price series with some trends
    tqqq_prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 200))
    pdbc_prices = np.cumprod(1 + np.random.normal(0.0005, 0.015, 200))
    iau_prices = np.cumprod(1 + np.random.normal(0.0003, 0.01, 200))
    sgov_prices = np.cumprod(1 + np.random.normal(0.0001, 0.002, 200))
    
    return pd.DataFrame({
        'TQQQ': tqqq_prices,
        'PDBC': pdbc_prices,
        'IAU': iau_prices,
        'SGOV': sgov_prices
    }, index=dates)


@pytest.fixture
def trending_data() -> pd.DataFrame:
    """Price data with clear trends for signal testing."""
    np.random.seed(123)
    dates = pd.date_range('2020-01-01', periods=150, freq='D')
    
    # Create trending data
    tqqq_trend = np.linspace(100, 150, 150) + np.random.normal(0, 2, 150)
    pdbc_trend = np.linspace(50, 60, 150) + np.random.normal(0, 1, 150)
    iau_trend = np.linspace(30, 35, 150) + np.random.normal(0, 0.5, 150)
    sgov_trend = np.linspace(10, 11, 150) + np.random.normal(0, 0.1, 150)
    
    return pd.DataFrame({
        'TQQQ': tqqq_trend,
        'PDBC': pdbc_trend,
        'IAU': iau_trend,
        'SGOV': sgov_trend
    }, index=dates)


@pytest.fixture
def strategy(sample_config):
    """Strategy instance with sample configuration."""
    return EquityInflationBetaStrategy(sample_config)


@pytest.fixture
def minimal_config() -> Dict[str, Any]:
    """Minimal valid configuration."""
    return {
        'assets': {'core': 'TQQQ', 'commodities': 'PDBC', 'gold': 'IAU', 'cash': 'SGOV'},
        'signals': {'trend': {'weight': 0.6}, 'carry': {'weight': 0.4}},
        'risk_parity': {'lookback_period': 60},
        'tqqq_overweight': {'base_weight': 0.6, 'scaling_factor': 1.2},
        'volatility_targeting': {'lookback_period': 60},
        'rebalancing': {'frequency': 'monthly', 'drift_bands': 10}
    }