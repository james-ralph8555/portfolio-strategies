"""
Unit tests for EquityInflationBetaStrategy.
"""

import pytest
import pandas as pd
import numpy as np
from strategies.equity_inflation_beta.strategy import EquityInflationBetaStrategy


class TestEquityInflationBetaStrategy:
    """Test suite for EquityInflationBetaStrategy class."""

    def test_initialization_with_config(self, sample_config):
        """Test strategy initialization with configuration."""
        strategy = EquityInflationBetaStrategy(sample_config)
        
        assert strategy.name == "equity_inflation_beta"
        assert strategy.assets == ["TQQQ", "PDBC", "IAU", "SGOV"]
        assert strategy.rebalance_frequency == "monthly"
        assert strategy.drift_bands == 10
        assert strategy.config == sample_config

    def test_initialization_without_config(self):
        """Test strategy initialization without configuration."""
        strategy = EquityInflationBetaStrategy()
        
        assert strategy.name == "equity_inflation_beta"
        assert strategy.assets == ["TQQQ", "PDBC", "IAU", "SGOV"]
        assert strategy.config == {}

    def test_initialization_with_partial_config(self):
        """Test strategy initialization with partial configuration."""
        partial_config = {
            'rebalancing': {'frequency': 'weekly', 'drift_bands': 5}
        }
        strategy = EquityInflationBetaStrategy(partial_config)
        
        assert strategy.rebalance_frequency == "weekly"
        assert strategy.drift_bands == 5

    def test_get_assets(self, strategy):
        """Test get_assets method."""
        assets = strategy.get_assets()
        assert assets == ["TQQQ", "PDBC", "IAU", "SGOV"]
        assert assets is not strategy.assets  # Should return a copy

    def test_get_name(self, strategy):
        """Test get_name method."""
        assert strategy.get_name() == "equity_inflation_beta"

    def test_get_config(self, strategy, sample_config):
        """Test get_config method."""
        config = strategy.get_config()
        assert config == sample_config
        assert config is not strategy.config  # Should return a copy

    def test_update_config(self, strategy):
        """Test update_config method."""
        new_config = {'rebalancing': {'frequency': 'daily'}}
        strategy.update_config(new_config)
        
        assert strategy.config['rebalancing']['frequency'] == 'daily'

    def test_validate_config_valid(self, sample_config):
        """Test configuration validation with valid config."""
        strategy = EquityInflationBetaStrategy(sample_config)
        assert strategy.validate_config() is True

    def test_validate_config_minimal(self, minimal_config):
        """Test configuration validation with minimal valid config."""
        strategy = EquityInflationBetaStrategy(minimal_config)
        assert strategy.validate_config() is True

    def test_validate_config_missing_keys(self, sample_config):
        """Test configuration validation with missing required keys."""
        incomplete_config = sample_config.copy()
        del incomplete_config['signals']
        
        strategy = EquityInflationBetaStrategy(incomplete_config)
        assert strategy.validate_config() is False

    def test_validate_config_invalid_signal_weights(self, sample_config):
        """Test configuration validation with invalid signal weights."""
        invalid_config = sample_config.copy()
        invalid_config['signals']['trend']['weight'] = 0.8
        invalid_config['signals']['carry']['weight'] = 0.4  # Sum = 1.2
        
        strategy = EquityInflationBetaStrategy(invalid_config)
        assert strategy.validate_config() is False

    def test_validate_config_missing_assets(self, sample_config):
        """Test configuration validation with missing required assets."""
        invalid_config = sample_config.copy()
        invalid_config['assets'] = {'core': 'TQQQ', 'commodities': 'PDBC'}  # Missing IAU, SGOV
        
        strategy = EquityInflationBetaStrategy(invalid_config)
        assert strategy.validate_config() is False

    def test_calculate_trend_signal(self, strategy, trending_data):
        """Test trend signal calculation."""
        signals = strategy.calculate_trend_signal(trending_data)
        
        assert isinstance(signals, dict)
        assert 'PDBC' in signals
        assert 'IAU' in signals
        assert all(isinstance(sig, (int, float)) for sig in signals.values())

    def test_calculate_trend_signal_insufficient_data(self, strategy):
        """Test trend signal calculation with insufficient data."""
        short_data = pd.DataFrame({
            'PDBC': [100, 101, 102],
            'IAU': [50, 51, 52]
        })
        
        signals = strategy.calculate_trend_signal(short_data)
        assert signals['PDBC'] == 0
        assert signals['IAU'] == 0

    def test_calculate_trend_signal_missing_columns(self, strategy, sample_price_data):
        """Test trend signal calculation with missing asset columns."""
        incomplete_data = sample_price_data.drop('PDBC', axis=1)
        
        signals = strategy.calculate_trend_signal(incomplete_data)
        assert signals['PDBC'] == 0
        assert 'IAU' in signals

    def test_calculate_carry_signal(self, strategy, sample_price_data):
        """Test carry signal calculation."""
        signals = strategy.calculate_carry_signal(sample_price_data)
        
        assert isinstance(signals, dict)
        assert 'PDBC' in signals
        assert 'IAU' in signals
        assert all(isinstance(sig, (int, float)) for sig in signals.values())
        assert all(sig in [-1, 0, 1] for sig in signals.values())

    def test_calculate_carry_signal_insufficient_data(self, strategy):
        """Test carry signal calculation with insufficient data."""
        short_data = pd.DataFrame({
            'PDBC': [100, 101, 102],
            'IAU': [50, 51, 52]
        })
        
        signals = strategy.calculate_carry_signal(short_data)
        assert signals['PDBC'] == 0
        assert signals['IAU'] == 0

    def test_calculate_carry_signal_missing_columns(self, strategy, sample_price_data):
        """Test carry signal calculation with missing asset columns."""
        incomplete_data = sample_price_data.drop('IAU', axis=1)
        
        signals = strategy.calculate_carry_signal(incomplete_data)
        assert signals['IAU'] == 0
        assert 'PDBC' in signals

    def test_calculate_risk_parity_weights(self, strategy, sample_price_data):
        """Test risk parity weight calculation."""
        weights = strategy._calculate_risk_parity_weights(sample_price_data, ['PDBC', 'IAU'])
        
        assert isinstance(weights, dict)
        assert 'PDBC' in weights
        assert 'IAU' in weights
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        assert all(weight > 0 for weight in weights.values())

    def test_calculate_risk_parity_weights_insufficient_data(self, strategy):
        """Test risk parity weights with insufficient data."""
        short_data = pd.DataFrame({'PDBC': [100, 101]})
        
        weights = strategy._calculate_risk_parity_weights(short_data, ['PDBC', 'IAU'])
        
        # Should return equal weights
        assert weights['PDBC'] == 0.5
        assert weights['IAU'] == 0.5

    def test_calculate_risk_parity_weights_missing_columns(self, strategy, sample_price_data):
        """Test risk parity weights with missing asset columns."""
        weights = strategy._calculate_risk_parity_weights(sample_price_data, ['PDBC', 'MISSING'])
        
        assert 'PDBC' in weights
        assert 'MISSING' in weights
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_calculate_portfolio_volatility(self, strategy, sample_price_data):
        """Test portfolio volatility calculation."""
        vol = strategy._calculate_portfolio_volatility(sample_price_data)
        
        assert isinstance(vol, (int, float))
        assert vol > 0
        assert vol < 1  # Should be reasonable

    def test_calculate_portfolio_volatility_insufficient_data(self, strategy):
        """Test portfolio volatility with insufficient data."""
        short_data = pd.DataFrame({'TQQQ': [100, 101]})
        
        vol = strategy._calculate_portfolio_volatility(short_data)
        assert vol == 0.15  # Default volatility

    def test_calculate_portfolio_volatility_missing_tqqq(self, strategy, sample_price_data):
        """Test portfolio volatility without TQQQ data."""
        no_tqqq_data = sample_price_data.drop('TQQQ', axis=1)
        
        vol = strategy._calculate_portfolio_volatility(no_tqqq_data)
        assert vol == 0.15  # Default volatility

    def test_should_rebalance_within_bands(self, strategy):
        """Test rebalancing logic when within drift bands."""
        current_weights = {'TQQQ': 0.6, 'PDBC': 0.2, 'IAU': 0.2, 'SGOV': 0.0}
        target_weights = {'TQQQ': 0.58, 'PDBC': 0.21, 'IAU': 0.19, 'SGOV': 0.02}
        
        assert strategy.should_rebalance(current_weights, target_weights) is False

    def test_should_rebalance_exceeds_bands(self, strategy):
        """Test rebalancing logic when drift exceeds bands."""
        current_weights = {'TQQQ': 0.6, 'PDBC': 0.2, 'IAU': 0.2, 'SGOV': 0.0}
        target_weights = {'TQQQ': 0.45, 'PDBC': 0.25, 'IAU': 0.25, 'SGOV': 0.05}
        
        assert strategy.should_rebalance(current_weights, target_weights) is True

    def test_should_rebalance_missing_assets(self, strategy):
        """Test rebalancing logic with missing assets in current weights."""
        current_weights = {'TQQQ': 0.6, 'PDBC': 0.2, 'IAU': 0.0, 'SGOV': 0.0}  # Zero weights for missing
        target_weights = {'TQQQ': 0.6, 'PDBC': 0.2, 'IAU': 0.15, 'SGOV': 0.15}  # Larger drift
        
        assert strategy.should_rebalance(current_weights, target_weights) is True

    def test_preprocess_data_default(self, strategy, sample_price_data):
        """Test default data preprocessing."""
        processed = strategy.preprocess_data(sample_price_data)
        
        assert processed.equals(sample_price_data)
        assert processed is not sample_price_data  # Should be a copy

    def test_postprocess_weights_default(self, strategy):
        """Test default weight postprocessing."""
        weights = {'TQQQ': 0.6, 'PDBC': 0.2, 'IAU': 0.2, 'SGOV': 0.0}
        processed = strategy.postprocess_weights(weights)
        
        assert processed == weights
        assert processed is not weights  # Should be a copy