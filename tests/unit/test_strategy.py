"""
Unit tests for EquityConvexRateHedgeStrategy.
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from strategies.equity_convex_rate_hedge.strategy import EquityConvexRateHedgeStrategy
from tests.fixtures.data_fixtures import *


class TestEquityConvexRateHedgeStrategy:
    """Test suite for EquityConvexRateHedgeStrategy class."""
    
    def test_strategy_initialization_default(self):
        """Test strategy initialization with default config."""
        strategy = EquityConvexRateHedgeStrategy()
        
        assert strategy.name == "equity_convex_rate_hedge"
        assert strategy.assets == ["TQQQ", "PFIX", "IAU", "SGOV"]
        assert strategy.rebalance_frequency == "monthly"
        assert strategy.drift_bands == 10
        assert strategy.validate_config() is True
    
    def test_strategy_initialization_custom_config(self, custom_strategy_config):
        """Test strategy initialization with custom config."""
        strategy = EquityConvexRateHedgeStrategy(custom_strategy_config)
        
        assert strategy.config["target_volatility"] == 0.12
        assert strategy.config["tqqq_base_weight"] == 0.55
        assert strategy.config["drift_bands"] == 5
        assert strategy.validate_config() is True
    
    def test_strategy_initialization_invalid_config(self):
        """Test strategy initialization with invalid config."""
        invalid_config = {
            "target_volatility": 0.50,  # Too high
            "tqqq_base_weight": 0.80,   # Weights won't sum to 1
            "pfix_base_weight": 0.30,
            "gold_base_weight": 0.15,
            "cash_base_weight": 0.05,
        }
        
        strategy = EquityConvexRateHedgeStrategy(invalid_config)
        assert strategy.validate_config() is False
    
    def test_calculate_stock_bond_correlation(self, sample_market_data):
        """Test stock-bond correlation calculation."""
        strategy = EquityConvexRateHedgeStrategy()
        
        correlation = strategy._calculate_stock_bond_correlation(sample_market_data)
        
        assert isinstance(correlation, float)
        assert -1.0 <= correlation <= 1.0
    
    def test_calculate_stock_bond_correlation_insufficient_data(self, minimal_data):
        """Test correlation calculation with insufficient data."""
        strategy = EquityConvexRateHedgeStrategy()
        strategy.config["correlation_lookback"] = 300  # More than available data
        
        correlation = strategy._calculate_stock_bond_correlation(minimal_data)
        
        assert correlation == 0.0
    
    def test_calculate_volatility_scaling(self, sample_market_data):
        """Test volatility scaling calculation."""
        strategy = EquityConvexRateHedgeStrategy()
        
        vol_scale = strategy._calculate_volatility_scaling(sample_market_data)
        
        assert isinstance(vol_scale, float)
        assert vol_scale > 0
        assert vol_scale <= 2.0  # Should be capped at 2x
    
    def test_calculate_volatility_scaling_insufficient_data(self, minimal_data):
        """Test volatility scaling with insufficient data."""
        strategy = EquityConvexRateHedgeStrategy()
        strategy.config["volatility_lookback"] = 100  # More than available data
        
        vol_scale = strategy._calculate_volatility_scaling(minimal_data)
        
        assert vol_scale == 1.0  # Should default to 1.0
    
    def test_positive_correlation_weights(self):
        """Test weight calculation for positive correlation regime."""
        strategy = EquityConvexRateHedgeStrategy()
        
        weights = strategy._positive_correlation_weights()
        
        assert isinstance(weights, dict)
        assert "TQQQ" in weights
        assert "PFIX" in weights
        assert "IAU" in weights
        assert "SGOV" in weights
        
        # PFIX should be increased in positive correlation regime
        assert weights["PFIX"] > strategy.config["pfix_base_weight"]
        # Gold should be reduced
        assert weights["IAU"] < strategy.config["gold_base_weight"]
    
    def test_negative_correlation_weights(self):
        """Test weight calculation for negative correlation regime."""
        strategy = EquityConvexRateHedgeStrategy()
        
        weights = strategy._negative_correlation_weights()
        
        assert isinstance(weights, dict)
        assert "TQQQ" in weights
        assert "PFIX" in weights
        assert "IAU" in weights
        assert "SGOV" in weights
        
        # TQQQ should be increased in negative correlation regime
        assert weights["TQQQ"] > strategy.config["tqqq_base_weight"]
        # PFIX should be reduced
        assert weights["PFIX"] < strategy.config["pfix_base_weight"]
        # Cash should be increased
        assert weights["SGOV"] > strategy.config["cash_base_weight"]
    
    def test_apply_volatility_targeting(self):
        """Test volatility targeting application."""
        strategy = EquityConvexRateHedgeStrategy()
        
        base_weights = {
            "TQQQ": 0.6,
            "PFIX": 0.2,
            "IAU": 0.15,
            "SGOV": 0.05
        }
        
        vol_scale = 0.8
        adjusted_weights = strategy._apply_volatility_targeting(base_weights, vol_scale)
        
        # Risky assets should be scaled
        assert adjusted_weights["TQQQ"] == 0.6 * 0.8
        assert adjusted_weights["PFIX"] == 0.2 * 0.8
        assert adjusted_weights["IAU"] == 0.15 * 0.8
        # Cash should not be scaled
        assert adjusted_weights["SGOV"] == 0.05
    
    def test_normalize_weights(self):
        """Test weight normalization."""
        strategy = EquityConvexRateHedgeStrategy()
        
        unnormalized_weights = {
            "TQQQ": 0.7,
            "PFIX": 0.25,
            "IAU": 0.2,
            "SGOV": 0.05
        }
        
        normalized = strategy._normalize_weights(unnormalized_weights)
        
        # Should sum to 1
        assert abs(sum(normalized.values()) - 1.0) < 1e-10
        
        # Proportions should be preserved
        total = sum(unnormalized_weights.values())
        for asset in unnormalized_weights:
            expected = unnormalized_weights[asset] / total
            assert abs(normalized[asset] - expected) < 1e-10
    
    def test_normalize_weights_zero_total(self):
        """Test weight normalization with zero total."""
        strategy = EquityConvexRateHedgeStrategy()
        
        zero_weights = {"TQQQ": 0.0, "PFIX": 0.0, "IAU": 0.0, "SGOV": 0.0}
        
        normalized = strategy._normalize_weights(zero_weights)
        
        # Should return original weights when total is zero
        assert normalized == zero_weights
    
    def test_should_rebalance_within_bands(self):
        """Test rebalancing logic when within drift bands."""
        strategy = EquityConvexRateHedgeStrategy()
        strategy.config["drift_bands"] = 10
        
        current_weights = {"TQQQ": 0.58, "PFIX": 0.22, "IAU": 0.15, "SGOV": 0.05}
        target_weights = {"TQQQ": 0.60, "PFIX": 0.20, "IAU": 0.15, "SGOV": 0.05}
        
        should_rebalance = strategy.should_rebalance(current_weights, target_weights)
        
        assert should_rebalance is False  # All within 10% bands
    
    def test_should_rebalance_outside_bands(self):
        """Test rebalancing logic when outside drift bands."""
        strategy = EquityConvexRateHedgeStrategy()
        strategy.config["drift_bands"] = 5
        
        current_weights = {"TQQQ": 0.50, "PFIX": 0.30, "IAU": 0.15, "SGOV": 0.05}
        target_weights = {"TQQQ": 0.60, "PFIX": 0.20, "IAU": 0.15, "SGOV": 0.05}
        
        should_rebalance = strategy.should_rebalance(current_weights, target_weights)
        
        assert should_rebalance is True  # TQQQ and PFIX outside 5% bands
    
    def test_should_rebalance_missing_assets(self):
        """Test rebalancing logic with missing assets."""
        strategy = EquityConvexRateHedgeStrategy()
        
        current_weights = {"TQQQ": 0.60, "PFIX": 0.20}  # Missing IAU, SGOV
        target_weights = {"TQQQ": 0.60, "PFIX": 0.20, "IAU": 0.15, "SGOV": 0.05}
        
        should_rebalance = strategy.should_rebalance(current_weights, target_weights)
        
        assert should_rebalance is True  # Missing assets should trigger rebalance
    
    def test_validate_config_complete(self, strategy_config):
        """Test configuration validation with complete valid config."""
        strategy = EquityConvexRateHedgeStrategy(strategy_config)
        
        assert strategy.validate_config() is True
    
    def test_validate_config_incomplete_config_merges_with_defaults(self):
        """Test that incomplete config merges with defaults and validates."""
        incomplete_config = {
            "target_volatility": 0.15,
            "tqqq_base_weight": 0.60
            # Missing other required keys - should merge with defaults
        }
        
        strategy = EquityConvexRateHedgeStrategy(incomplete_config)
        
        # Should still validate True because defaults are merged
        assert strategy.validate_config() is True
        # But the custom values should be preserved
        assert strategy.config["target_volatility"] == 0.15
        assert strategy.config["tqqq_base_weight"] == 0.60
    
    def test_validate_config_invalid_weights(self):
        """Test configuration validation with invalid weights."""
        invalid_weights_config = {
            "target_volatility": 0.15,
            "tqqq_base_weight": 0.80,
            "pfix_base_weight": 0.30,
            "gold_base_weight": 0.15,
            "cash_base_weight": 0.05,
            "correlation_threshold": 0.0,
            "volatility_lookback": 60,
            "correlation_lookback": 252,
            "drift_bands": 10
        }
        
        strategy = EquityConvexRateHedgeStrategy(invalid_weights_config)
        
        assert strategy.validate_config() is False  # Weights sum to 1.3
    
    def test_validate_config_invalid_volatility(self):
        """Test configuration validation with invalid volatility target."""
        invalid_vol_config = {
            "target_volatility": 0.50,  # Too high
            "tqqq_base_weight": 0.60,
            "pfix_base_weight": 0.20,
            "gold_base_weight": 0.15,
            "cash_base_weight": 0.05,
            "correlation_threshold": 0.0,
            "volatility_lookback": 60,
            "correlation_lookback": 252,
            "drift_bands": 10
        }
        
        strategy = EquityConvexRateHedgeStrategy(invalid_vol_config)
        
        assert strategy.validate_config() is False
    
    def test_get_assets(self):
        """Test get_assets method."""
        strategy = EquityConvexRateHedgeStrategy()
        
        assets = strategy.get_assets()
        
        assert assets == ["TQQQ", "PFIX", "IAU", "SGOV"]
        # Should return a copy, not reference to internal list
        assert assets is not strategy.assets
    
    def test_get_name(self):
        """Test get_name method."""
        strategy = EquityConvexRateHedgeStrategy()
        
        assert strategy.get_name() == "equity_convex_rate_hedge"
    
    def test_get_config(self):
        """Test get_config method."""
        custom_config = {"test_param": "test_value"}
        strategy = EquityConvexRateHedgeStrategy(custom_config)
        
        config = strategy.get_config()
        
        assert "test_param" in config
        assert config["test_param"] == "test_value"
        # Should return a copy, not reference to internal dict
        assert config is not strategy.config
    
    def test_update_config(self, strategy_config):
        """Test update_config method."""
        strategy = EquityConvexRateHedgeStrategy(strategy_config)
        
        new_config = {"target_volatility": 0.18}
        strategy.update_config(new_config)
        
        assert strategy.config["target_volatility"] == 0.18
        # Original config should still be there
        assert strategy.config["tqqq_base_weight"] == 0.60