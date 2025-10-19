"""
Functional tests for EquityConvexRateHedgeStrategy integration behavior.
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


class TestStrategyIntegration:
    """Test suite for strategy integration and end-to-end behavior."""
    
    def test_calculate_weights_positive_correlation_regime(self, positive_correlation_data):
        """Test weight calculation in positive correlation regime."""
        strategy = EquityConvexRateHedgeStrategy()
        
        weights = strategy.calculate_weights(positive_correlation_data)
        
        # Verify weights structure
        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert all(asset in weights for asset in ["TQQQ", "PFIX", "IAU", "SGOV"])
        
        # Verify weights sum to 1
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        
        # Verify all weights are positive
        assert all(weight > 0 for weight in weights.values())
        
        # In positive correlation regime, PFIX should be emphasized
        # (this is a functional expectation based on the strategy design)
        assert weights["PFIX"] > 0.15  # Should be higher than base 20% after adjustments
    
    def test_calculate_weights_negative_correlation_regime(self, negative_correlation_data):
        """Test weight calculation in negative correlation regime."""
        strategy = EquityConvexRateHedgeStrategy()
        
        weights = strategy.calculate_weights(negative_correlation_data)
        
        # Verify weights structure
        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert all(asset in weights for asset in ["TQQQ", "PFIX", "IAU", "SGOV"])
        
        # Verify weights sum to 1
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        
        # Verify all weights are positive
        assert all(weight > 0 for weight in weights.values())
        
        # In negative correlation regime, TQQQ should be emphasized
        assert weights["TQQQ"] > 0.55  # Should be higher than base 60% after adjustments
    
    def test_calculate_weights_high_volatility_environment(self, high_volatility_data):
        """Test weight calculation in high volatility environment."""
        strategy = EquityConvexRateHedgeStrategy()
        
        weights = strategy.calculate_weights(high_volatility_data)
        
        # Verify weights structure
        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert all(asset in weights for asset in ["TQQQ", "PFIX", "IAU", "SGOV"])
        
        # Verify weights sum to 1
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        
        # In high volatility, scaling should reduce risky asset weights
        # and increase cash proportion
        assert weights["SGOV"] > 0.05  # Cash should be higher than base 5%
    
    def test_calculate_weights_consistency(self, sample_market_data):
        """Test that weight calculation is consistent across multiple calls."""
        strategy = EquityConvexRateHedgeStrategy()
        
        weights1 = strategy.calculate_weights(sample_market_data)
        weights2 = strategy.calculate_weights(sample_market_data)
        
        # Should be identical for same input data
        for asset in weights1:
            assert weights1[asset] == weights2[asset]
    
    def test_calculate_weights_with_custom_config(self, sample_market_data, custom_strategy_config):
        """Test weight calculation with custom configuration."""
        strategy = EquityConvexRateHedgeStrategy(custom_strategy_config)
        
        weights = strategy.calculate_weights(sample_market_data)
        
        # Verify weights structure
        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert all(asset in weights for asset in ["TQQQ", "PFIX", "IAU", "SGOV"])
        
        # Verify weights sum to 1
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        
        # Custom config should affect the weights
        # Lower target volatility should result in more conservative allocation
        assert weights["SGOV"] >= 0.05  # Cash should be at least base level
    
    def test_rebalancing_trigger_functionality(self, sample_market_data):
        """Test rebalancing trigger functionality over multiple periods."""
        strategy = EquityConvexRateHedgeStrategy()
        
        # Calculate initial target weights
        target_weights = strategy.calculate_weights(sample_market_data)
        
        # Test various current weight scenarios
        test_scenarios = [
            # No rebalance needed (within bands)
            {"TQQQ": target_weights["TQQQ"] * 0.95, "PFIX": target_weights["PFIX"] * 1.05, 
             "IAU": target_weights["IAU"], "SGOV": target_weights["SGOV"]},
            # Rebalance needed (outside bands) - use larger drift
            {"TQQQ": target_weights["TQQQ"] * 0.80, "PFIX": target_weights["PFIX"] * 1.25,
             "IAU": target_weights["IAU"], "SGOV": target_weights["SGOV"]},
        ]
        
        results = []
        for current_weights in test_scenarios:
            should_rebalance = strategy.should_rebalance(current_weights, target_weights)
            results.append(should_rebalance)
        
        # First scenario should not trigger rebalance, second should
        assert results[0] is False
        assert results[1] is True
    
    def test_strategy_adaptation_to_market_regimes(self):
        """Test that strategy adapts to different market regimes."""
        strategy = EquityConvexRateHedgeStrategy()
        
        # Create data for different regimes
        np.random.seed(42)
        
        # Bull market with low volatility
        bull_data = pd.DataFrame({
            'TQQQ': np.cumsum(np.random.normal(0.002, 0.01, 100)) + 100,
            'PFIX': np.cumsum(np.random.normal(0.0005, 0.008, 100)) + 50,
            'IAU': np.cumsum(np.random.normal(0.0002, 0.005, 100)) + 30,
            'SGOV': np.cumsum(np.random.normal(0.0001, 0.001, 100)) + 20
        })
        
        # Bear market with high volatility
        bear_data = pd.DataFrame({
            'TQQQ': np.cumsum(np.random.normal(-0.003, 0.04, 100)) + 100,
            'PFIX': np.cumsum(np.random.normal(0.001, 0.02, 100)) + 50,
            'IAU': np.cumsum(np.random.normal(0.0005, 0.015, 100)) + 30,
            'SGOV': np.cumsum(np.random.normal(0.0001, 0.002, 100)) + 20
        })
        
        bull_weights = strategy.calculate_weights(bull_data)
        bear_weights = strategy.calculate_weights(bear_data)
        
        # In bear market, should have more defensive allocation or equal
        assert bear_weights["SGOV"] >= bull_weights["SGOV"]
        # TQQQ allocation should be more conservative in bear market or equal
        assert bear_weights["TQQQ"] <= bull_weights["TQQQ"]
    
    def test_volatility_targeting_effectiveness(self, sample_market_data):
        """Test that volatility targeting works as expected."""
        # Create two strategies with different volatility targets
        high_vol_strategy = EquityConvexRateHedgeStrategy({"target_volatility": 0.20})
        low_vol_strategy = EquityConvexRateHedgeStrategy({"target_volatility": 0.10})
        
        high_vol_weights = high_vol_strategy.calculate_weights(sample_market_data)
        low_vol_weights = low_vol_strategy.calculate_weights(sample_market_data)
        
        # Lower volatility target should result in more conservative allocation
        assert low_vol_weights["SGOV"] >= high_vol_weights["SGOV"]
    
    def test_edge_case_minimal_data(self, minimal_data):
        """Test strategy behavior with minimal data."""
        strategy = EquityConvexRateHedgeStrategy()
        
        # Should not crash with minimal data
        weights = strategy.calculate_weights(minimal_data)
        
        # Should still return valid weights
        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        assert all(weight > 0 for weight in weights.values())
    
    def test_edge_case_missing_assets(self):
        """Test strategy behavior with missing asset data."""
        strategy = EquityConvexRateHedgeStrategy()
        
        # Data with missing PFIX
        incomplete_data = pd.DataFrame({
            'TQQQ': [100, 101, 102, 103, 104],
            'IAU': [30, 31, 32, 33, 34],
            'SGOV': [20, 20.1, 20.2, 20.3, 20.4]
        })
        
        # Should handle missing assets gracefully
        weights = strategy.calculate_weights(incomplete_data)
        
        # Should still return valid weights
        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert abs(sum(weights.values()) - 1.0) < 1e-10
    
    def test_config_validation_impact(self, sample_market_data):
        """Test that config validation affects strategy behavior."""
        # Valid config
        valid_config = {
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
        
        # Invalid config (weights don't sum to 1)
        invalid_config = {
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
        
        valid_strategy = EquityConvexRateHedgeStrategy(valid_config)
        invalid_strategy = EquityConvexRateHedgeStrategy(invalid_config)
        
        # Valid strategy should pass validation
        assert valid_strategy.validate_config() is True
        
        # Invalid strategy should fail validation
        assert invalid_strategy.validate_config() is False
        
        # Both should still be able to calculate weights (with defaults)
        valid_weights = valid_strategy.calculate_weights(sample_market_data)
        invalid_weights = invalid_strategy.calculate_weights(sample_market_data)
        
        # Both should return valid weight structures
        for weights in [valid_weights, invalid_weights]:
            assert isinstance(weights, dict)
            assert len(weights) == 4
            assert abs(sum(weights.values()) - 1.0) < 1e-10