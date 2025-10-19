"""
Functional tests for the EquityVolBarbellStrategy class.

This module tests the end-to-end workflow and integration scenarios
to ensure the strategy works correctly in realistic conditions.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from strategies.equity_vol_barbell.strategy import EquityVolBarbellStrategy


class TestEquityVolBarbellFunctional:
    """Functional tests for EquityVolBarbellStrategy class."""

    @pytest.fixture
    def realistic_config(self):
        """Realistic configuration for functional testing."""
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
    def strategy(self, realistic_config):
        """Create strategy instance with realistic config."""
        return EquityVolBarbellStrategy(realistic_config)

    @pytest.fixture
    def bull_market_data(self):
        """Simulate bull market data with low volatility."""
        dates = pd.date_range('2023-01-01', periods=252, freq='D')  # 1 year of data
        np.random.seed(123)  # For reproducible results
        
        data = pd.DataFrame(index=dates)
        
        # Bull market: positive returns with low volatility
        data['TQQQ_Returns'] = np.random.normal(0.002, 0.02, 252)  # Positive drift
        data['VOO_Returns'] = np.random.normal(0.0008, 0.01, 252)  # Positive drift
        data['SVOL_Returns'] = np.random.normal(0.0001, 0.005, 252)  # Low vol returns
        data['TAIL_Returns'] = np.random.normal(-0.0002, 0.008, 252)  # Negative drift (cost of hedge)
        
        # Low VIX environment
        data['VIX'] = 15 + 3 * np.sin(np.linspace(0, 8*np.pi, 252)) + np.random.normal(0, 1, 252)
        data['VIX_MA20'] = data['VIX'].rolling(window=20).mean()
        
        # Calculate drawdown
        data['Cumulative_Return'] = (1 + data['VOO_Returns']).cumprod()
        data['Peak'] = data['Cumulative_Return'].expanding().max()
        data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
        
        return data

    @pytest.fixture
    def bear_market_data(self):
        """Simulate bear market data with high volatility."""
        dates = pd.date_range('2022-01-01', periods=252, freq='D')  # 1 year of data
        np.random.seed(456)  # For reproducible results
        
        data = pd.DataFrame(index=dates)
        
        # Bear market: negative returns with high volatility
        data['TQQQ_Returns'] = np.random.normal(-0.003, 0.04, 252)  # Negative drift, high vol
        data['VOO_Returns'] = np.random.normal(-0.001, 0.02, 252)  # Negative drift
        data['SVOL_Returns'] = np.random.normal(0.0003, 0.01, 252)  # Volatility premium
        data['TAIL_Returns'] = np.random.normal(0.001, 0.015, 252)  # Positive tail returns
        
        # High VIX environment with spikes
        base_vix = 30 + 10 * np.sin(np.linspace(0, 4*np.pi, 252))
        vix_spikes = np.random.choice([0, 15], size=252, p=[0.9, 0.1])  # Occasional spikes
        data['VIX'] = np.maximum(base_vix + vix_spikes, 10)
        data['VIX_MA20'] = data['VIX'].rolling(window=20).mean()
        
        # Calculate drawdown
        data['Cumulative_Return'] = (1 + data['VOO_Returns']).cumprod()
        data['Peak'] = data['Cumulative_Return'].expanding().max()
        data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
        
        return data

    @pytest.fixture
    def volatile_sideways_data(self):
        """Simulate volatile sideways market data."""
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        np.random.seed(789)  # For reproducible results
        
        data = pd.DataFrame(index=dates)
        
        # Sideways market with volatility
        data['TQQQ_Returns'] = np.random.normal(0.0, 0.035, 252)  # No drift, high vol
        data['VOO_Returns'] = np.random.normal(0.0, 0.018, 252)  # No drift
        data['SVOL_Returns'] = np.random.normal(0.0002, 0.008, 252)  # Volatility premium
        data['TAIL_Returns'] = np.random.normal(0.0001, 0.012, 252)  # Small positive
        
        # Fluctuating VIX
        data['VIX'] = 20 + 15 * np.sin(np.linspace(0, 6*np.pi, 252)) + np.random.normal(0, 3, 252)
        data['VIX_MA20'] = data['VIX'].rolling(window=20).mean()
        
        # Calculate drawdown
        data['Cumulative_Return'] = (1 + data['VOO_Returns']).cumprod()
        data['Peak'] = data['Cumulative_Return'].expanding().max()
        data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
        
        return data

    def test_bull_market_workflow(self, strategy, bull_market_data):
        """Test complete strategy workflow in bull market conditions."""
        # Calculate weights for bull market
        weights = strategy.calculate_weights(bull_market_data)
        
        # Verify weights are valid
        assert set(weights.keys()) == set(strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 0.01
        assert all(w > 0 for w in weights.values())
        
        # In bull market, should have normal TQQQ allocation
        expected_tqqq = strategy.config['barbell_allocation']['tqqq_base_weight']
        assert abs(weights['TQQQ'] - expected_tqqq) < 0.01
        
        # Should not trigger drawdown protection
        drawdown_trigger = strategy.calculate_drawdown_trigger(bull_market_data)
        assert drawdown_trigger == 1.0  # No scaling
        
        # Should size vol sleeves normally (low VIX)
        vol_sleeves = strategy.size_vol_sleeves(bull_market_data)
        svol_weight = vol_sleeves['SVOL']
        tail_weight = vol_sleeves['TAIL']
        expected_svol = strategy.config['barbell_allocation']['short_vol_weight']
        expected_tail = strategy.config['barbell_allocation']['tail_hedge_weight']
        assert abs(svol_weight - expected_svol) < 0.02
        assert abs(tail_weight - expected_tail) < 0.02

    def test_bear_market_workflow(self, strategy, bear_market_data):
        """Test complete strategy workflow in bear market conditions."""
        # Should trigger drawdown protection due to high drawdown
        # Add TQQQ price data with drawdown to trigger the logic
        bear_market_data_with_prices = bear_market_data.copy()
        # Create TQQQ price series with significant drawdown
        prices = [100, 95, 90, 85, 80] * 50  # Repeated drawdown pattern
        bear_market_data_with_prices = bear_market_data_with_prices.iloc[:len(prices)].copy()
        bear_market_data_with_prices['TQQQ'] = prices
        
        # Calculate weights for bear market with drawdown data
        weights = strategy.calculate_weights(bear_market_data_with_prices)
        
        # Verify weights are valid
        assert set(weights.keys()) == set(strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 0.01
        assert all(w > 0 for w in weights.values())
        
        drawdown_trigger = strategy.calculate_drawdown_trigger(bear_market_data_with_prices)
        assert drawdown_trigger == 0.5  # Scaling factor applied
        
        # TQQQ should be reduced by 50%
        expected_tqqq = strategy.config['barbell_allocation']['tqqq_base_weight'] * 0.5
        assert abs(weights['TQQQ'] - expected_tqqq) < 0.01
        
        # Should size vol sleeves for high VIX
        vol_sleeves = strategy.size_vol_sleeves(bear_market_data)
        svol_weight = vol_sleeves['SVOL']
        tail_weight = vol_sleeves['TAIL']
        expected_svol = strategy.config['barbell_allocation']['short_vol_weight']
        expected_tail = strategy.config['barbell_allocation']['tail_hedge_weight']
        assert svol_weight <= expected_svol  # Reduced SVOL
        assert tail_weight >= expected_tail   # Increased TAIL

    def test_volatile_market_workflow(self, strategy, volatile_sideways_data):
        """Test strategy workflow in volatile sideways market."""
        # Calculate weights for volatile market
        weights = strategy.calculate_weights(volatile_sideways_data)
        
        # Verify weights are valid
        assert set(weights.keys()) == set(strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 0.01
        assert all(w > 0 for w in weights.values())
        
        # Check volatility sleeve sizing varies with VIX
        high_vix_data = volatile_sideways_data.copy()
        high_vix_data['VIX'] = 40
        high_vix_data['VIX_MA20'] = 35
        
        low_vix_data = volatile_sideways_data.copy()
        low_vix_data['VIX'] = 15
        low_vix_data['VIX_MA20'] = 15
        
        high_vol_sleeves = strategy.size_vol_sleeves(high_vix_data)
        low_vol_sleeves = strategy.size_vol_sleeves(low_vix_data)
        
        high_svol = high_vol_sleeves['SVOL']
        high_tail = high_vol_sleeves['TAIL']
        low_svol = low_vol_sleeves['SVOL']
        low_tail = low_vol_sleeves['TAIL']
        
        # High VIX should reduce SVOL and increase TAIL
        assert high_svol <= low_svol
        assert high_tail >= low_tail

    def test_rebalancing_workflow(self, strategy):
        """Test complete rebalancing workflow."""
        # Initial target weights
        target_weights = {
            'TQQQ': 0.70,
            'SVOL': 0.15,
            'TAIL': 0.10,
            'SGOV': 0.05
        }
        
        # Test no rebalancing needed
        current_weights = target_weights.copy()
        assert strategy.should_rebalance(current_weights, target_weights) is False
        
        # Test rebalancing needed due to drift
        drifted_weights = {
            'TQQQ': 0.76,  # 6% drift
            'SVOL': 0.14,   # 1% drift
            'TAIL': 0.10,
            'SGOV': 0.00   # 5% drift
        }
        assert strategy.should_rebalance(drifted_weights, target_weights) is True
        
        # Test rebalancing needed due to missing assets
        incomplete_weights = {
            'TQQQ': 0.70,
            'SVOL': 0.15
            # Missing TAIL, SGOV
        }
        assert strategy.should_rebalance(incomplete_weights, target_weights) is True

    def test_market_regime_changes(self, strategy):
        """Test strategy behavior across market regime changes."""
        # Create synthetic data representing different regimes
        dates = pd.date_range('2022-01-01', periods=360, freq='D')
        
        # Regime 1: Bull market (days 0-120)
        regime1_returns = np.random.normal(0.001, 0.015, 120)
        
        # Regime 2: Crisis/correction (days 120-240)
        regime2_returns = np.random.normal(-0.002, 0.025, 120)
        
        # Regime 3: Recovery (days 240-360)
        regime3_returns = np.random.normal(0.0008, 0.018, 120)
        
        # Combine regimes
        all_returns = np.concatenate([regime1_returns, regime2_returns, regime3_returns])
        
        data = pd.DataFrame(index=dates)
        data['VOO_Returns'] = all_returns
        data['TQQQ_Returns'] = all_returns * 2.5  # Leveraged version
        data['SVOL_Returns'] = np.random.normal(0.0002, 0.008, 360)
        data['TAIL_Returns'] = np.random.normal(0.0001, 0.012, 360)
        
        # VIX that responds to market conditions
        vix_values = []
        for i, ret in enumerate(all_returns):
            if i < 120:  # Bull market
                vix = 15 + np.random.normal(0, 2)
            elif i < 240:  # Crisis
                vix = 35 + np.random.normal(0, 5)
            else:  # Recovery
                vix = 22 + np.random.normal(0, 3)
            vix_values.append(max(vix, 10))
        
        data['VIX'] = vix_values
        data['VIX_MA20'] = data['VIX'].rolling(window=20).mean()
        
        # Calculate drawdown
        data['Cumulative_Return'] = (1 + data['VOO_Returns']).cumprod()
        data['Peak'] = data['Cumulative_Return'].expanding().max()
        data['Drawdown'] = (data['Cumulative_Return'] - data['Peak']) / data['Peak']
        
        # Test strategy behavior in each regime
        bull_data = data.iloc[:120]
        crisis_data = data.iloc[120:240]
        recovery_data = data.iloc[240:]
        
        # Bull market: normal allocation
        bull_weights = strategy.calculate_weights(bull_data)
        expected_tqqq = strategy.config['barbell_allocation']['tqqq_base_weight']
        assert abs(bull_weights['TQQQ'] - expected_tqqq) < 0.01
        
        # Crisis: reduced TQQQ, adjusted vol sleeves
        crisis_weights = strategy.calculate_weights(crisis_data)
        assert crisis_weights['TQQQ'] <= bull_weights['TQQQ']
        
        # Recovery: gradual normalization
        recovery_weights = strategy.calculate_weights(recovery_data)
        assert recovery_weights['TQQQ'] >= crisis_weights['TQQQ']

    def test_config_updates_workflow(self, strategy):
        """Test workflow when configuration is updated."""
        # Original config
        original_weights = strategy.calculate_weights(pd.DataFrame())
        
        # Update configuration
        new_config = {
            'barbell_allocation': {
                'tqqq_base_weight': 0.6,
                'short_vol_weight': 0.2,
                'tail_hedge_weight': 0.15,
                'cash_weight': 0.05
            }
        }
        
        strategy.update_config(new_config)
        
        # New weights should reflect updated config
        updated_weights = strategy.calculate_weights(pd.DataFrame())
        assert abs(updated_weights['TQQQ'] - 0.6) < 0.01
        assert abs(updated_weights['SVOL'] - 0.2) < 0.01
        assert abs(updated_weights['TAIL'] - 0.15) < 0.01
        assert abs(updated_weights['SGOV'] - 0.05) < 0.01

    def test_error_handling_workflow(self, strategy):
        """Test workflow with various error conditions."""
        # Test with completely empty data
        empty_data = pd.DataFrame()
        weights = strategy.calculate_weights(empty_data)
        assert set(weights.keys()) == set(strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 0.01
        
        # Test with data missing required columns
        incomplete_data = pd.DataFrame({
            'VOO_Returns': [0.01, 0.02, -0.01]
            # Missing other required columns
        })
        weights = strategy.calculate_weights(incomplete_data)
        assert set(weights.keys()) == set(strategy.assets)
        
        # Test with NaN values
        nan_data = pd.DataFrame({
            'TQQQ_Returns': [np.nan, 0.01, 0.02],
            'VOO_Returns': [0.01, np.nan, -0.01],
            'SVOL_Returns': [0.001, 0.002, np.nan],
            'TAIL_Returns': [0.0005, np.nan, 0.001],
            'VIX': [20, 25, 30],
            'VIX_MA20': [20, 22, 25],
            'Drawdown': [0, -0.05, -0.1]
        })
        weights = strategy.calculate_weights(nan_data)
        assert set(weights.keys()) == set(strategy.assets)
        assert all(not np.isnan(w) for w in weights.values())

    def test_performance_consistency(self, strategy, bull_market_data):
        """Test that strategy performance is consistent across multiple runs."""
        # Calculate weights multiple times with same data
        weights1 = strategy.calculate_weights(bull_market_data)
        weights2 = strategy.calculate_weights(bull_market_data)
        weights3 = strategy.calculate_weights(bull_market_data)
        
        # Results should be identical
        for asset in strategy.assets:
            assert abs(weights1[asset] - weights2[asset]) < 1e-10
            assert abs(weights2[asset] - weights3[asset]) < 1e-10

    def test_integration_with_base_interface(self, strategy):
        """Test integration with base Strategy interface."""
        # Test all required methods are implemented and work
        assert hasattr(strategy, 'calculate_weights')
        assert hasattr(strategy, 'should_rebalance')
        assert hasattr(strategy, 'validate_config')
        
        # Test they return expected types
        weights = strategy.calculate_weights(pd.DataFrame())
        assert isinstance(weights, dict)
        
        rebalance = strategy.should_rebalance({}, {})
        assert isinstance(rebalance, bool)
        
        valid = strategy.validate_config()
        assert isinstance(valid, bool)
        
        # Test inherited methods work
        assert isinstance(strategy.get_assets(), list)
        assert isinstance(strategy.get_name(), str)
        assert isinstance(strategy.get_config(), dict)