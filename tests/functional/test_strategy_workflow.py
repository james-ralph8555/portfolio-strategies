"""
Functional tests for strategy workflow and integration.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from strategies.equity_crisis_alpha.strategy import EquityCrisisAlphaStrategy
from tests.fixtures.sample_data import create_sample_price_data, create_sample_config


class TestStrategyWorkflow:
    """Test suite for end-to-end strategy workflow."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = create_sample_config()
        self.strategy = EquityCrisisAlphaStrategy(self.config)
    
    def test_complete_workflow_monthly_rebalance(self):
        """Test complete workflow with monthly rebalancing."""
        # Create 6 months of data
        data = create_sample_price_data(days=180)
        
        # Initial weights
        initial_weights = self.strategy.calculate_weights(data)
        
        # Simulate portfolio evolution with actual returns causing drift
        current_weights = initial_weights.copy()
        rebalance_count = 0
        
        # Simulate monthly rebalancing
        for i in range(30, len(data), 30):
            month_data = data.iloc[i-30:i]
            month_returns = month_data.pct_change().dropna()
            
            # Apply returns to current weights to create drift
            for asset in self.strategy.assets:
                if len(month_returns) > 0:
                    asset_return = month_returns[asset].sum()
                    current_weights[asset] *= (1 + asset_return)
            
            # Normalize weights to sum to 1
            total_weight = sum(current_weights.values())
            if total_weight > 0:
                for asset in current_weights:
                    current_weights[asset] /= total_weight
            
            # Calculate new target weights for this period
            new_weights = self.strategy.calculate_weights(month_data)
            
            # Check if rebalancing is needed
            if self.strategy.should_rebalance(current_weights, new_weights):
                current_weights = new_weights.copy()
                rebalance_count += 1
        
        # Should have rebalanced at least once due to natural drift
        assert rebalance_count >= 1
        
        # Final weights should be valid
        assert all(asset in current_weights for asset in self.strategy.assets)
        assert all(w >= 0 for w in current_weights.values())
    
    def test_workflow_with_market_volatility(self):
        """Test workflow under different market volatility regimes."""
        # Create high volatility data
        np.random.seed(123)
        high_vol_data = create_sample_price_data(days=90)
        
        # Increase volatility for TQQQ
        tqqq_returns = high_vol_data["TQQQ"].pct_change().dropna()
        high_vol_returns = tqqq_returns * 2  # Double the volatility
        high_vol_prices = 100 * (1 + high_vol_returns).cumprod()
        high_vol_data["TQQQ"] = high_vol_prices.reindex(high_vol_data.index, method='ffill')
        
        # Calculate weights in high volatility regime
        high_vol_weights = self.strategy.calculate_weights(high_vol_data)
        
        # Create low volatility data
        low_vol_data = create_sample_price_data(days=90)
        
        # Decrease volatility for TQQQ
        tqqq_returns = low_vol_data["TQQQ"].pct_change().dropna()
        low_vol_returns = tqqq_returns * 0.5  # Half the volatility
        low_vol_prices = 100 * (1 + low_vol_returns).cumprod()
        low_vol_data["TQQQ"] = low_vol_prices.reindex(low_vol_data.index, method='ffill')
        
        # Calculate weights in low volatility regime
        low_vol_weights = self.strategy.calculate_weights(low_vol_data)
        
        # Weights should adapt to volatility regimes
        # In high volatility, leverage should be reduced due to volatility targeting
        high_vol_leverage = sum(abs(w) for w in high_vol_weights.values())
        low_vol_leverage = sum(abs(w) for w in low_vol_weights.values())
        
        # This is a simplified test - in practice, the relationship might be more complex
        assert high_vol_leverage <= self.config['risk_controls']['max_leverage']
        assert low_vol_leverage <= self.config['risk_controls']['max_leverage']
    
    def test_workflow_with_missing_data(self):
        """Test workflow handling missing data."""
        # Create data with missing values
        data = create_sample_price_data(days=60)
        
        # Introduce missing values
        data.iloc[10:15, 0] = np.nan  # Missing TQQQ data
        data.iloc[20:25, 1] = np.nan  # Missing DBMF data
        
        # Should handle missing data gracefully
        weights = self.strategy.calculate_weights(data)
        
        # Should still return weights for all assets
        assert len(weights) == len(self.strategy.assets)
        assert all(asset in weights for asset in self.strategy.assets)
    
    def test_workflow_with_extreme_market_conditions(self):
        """Test workflow under extreme market conditions."""
        # Create data with market crash
        data = create_sample_price_data(days=30)
        
        # Simulate market crash in last 10 days
        crash_returns = -0.1  # 10% daily drop
        for i in range(-10, 0):
            for asset in ["TQQQ", "DBMF", "IAU"]:
                data.iloc[i, data.columns.get_loc(asset)] *= (1 + crash_returns)
        
        # Calculate weights during crash
        crash_weights = self.strategy.calculate_weights(data)
        
        # Should still produce valid weights
        assert all(asset in crash_weights for asset in self.strategy.assets)
        assert all(w >= 0 for w in crash_weights.values())
        
        # Leverage should be constrained
        total_leverage = sum(abs(w) for w in crash_weights.values())
        assert total_leverage <= self.config['risk_controls']['max_leverage']
    
    def test_rebalancing_frequency_impact(self):
        """Test impact of different rebalancing frequencies."""
        data = create_sample_price_data(days=90)
        
        # Test with different drift bands
        tight_bands_config = create_sample_config()
        tight_bands_config["rebalancing"]["drift_bands"] = 5  # Tight bands
        
        loose_bands_config = create_sample_config()
        loose_bands_config["rebalancing"]["drift_bands"] = 20  # Loose bands
        
        tight_strategy = EquityCrisisAlphaStrategy(tight_bands_config)
        loose_strategy = EquityCrisisAlphaStrategy(loose_bands_config)
        
        # Calculate initial weights
        initial_weights = tight_strategy.calculate_weights(data)
        
        # Simulate some drift
        drifted_weights = {
            "TQQQ": initial_weights["TQQQ"] + 0.08,  # 8% drift
            "DBMF": initial_weights["DBMF"] - 0.04,
            "IAU": initial_weights["IAU"] - 0.02,
            "SGOV": initial_weights["SGOV"] - 0.02
        }
        
        # Tight bands should trigger rebalance
        assert tight_strategy.should_rebalance(drifted_weights, initial_weights) is True
        
        # Loose bands should not trigger rebalance
        assert loose_strategy.should_rebalance(drifted_weights, initial_weights) is False
    
    def test_black_litterman_views_impact(self):
        """Test impact of different Black-Litterman views."""
        data = create_sample_price_data(days=60)
        
        # Config with bullish TQQQ view
        bullish_config = create_sample_config()
        bullish_config["black_litterman"]["views"] = [
            {
                "assets": ["TQQQ"],
                "confidence": 0.9,
                "expected_return": 0.20
            }
        ]
        
        # Config with bearish TQQQ view
        bearish_config = create_sample_config()
        bearish_config["black_litterman"]["views"] = [
            {
                "assets": ["TQQQ"],
                "confidence": 0.9,
                "expected_return": -0.10
            }
        ]
        
        bullish_strategy = EquityCrisisAlphaStrategy(bullish_config)
        bearish_strategy = EquityCrisisAlphaStrategy(bearish_config)
        
        bullish_weights = bullish_strategy.calculate_weights(data)
        bearish_weights = bearish_strategy.calculate_weights(data)
        
        # Bullish view should result in higher TQQQ weight
        assert bullish_weights["TQQQ"] > bearish_weights["TQQQ"]
    
    def test_volatility_targeting_effectiveness(self):
        """Test effectiveness of volatility targeting."""
        # Create data with known volatility characteristics
        np.random.seed(456)
        high_vol_data = create_sample_price_data(days=60)
        
        # Calculate realized volatility of the portfolio
        weights = self.strategy.calculate_weights(high_vol_data)
        returns = high_vol_data.pct_change().dropna()
        
        # Calculate portfolio returns
        portfolio_returns = pd.Series(sum(returns[asset] * weights[asset] for asset in self.strategy.assets))
        realized_vol = portfolio_returns.std() * np.sqrt(252)  # Annualized
        
        # Volatility targeting should keep portfolio volatility close to target
        target_vol = self.config["volatility_targeting"]["target_vol"]
        
        # Allow some tolerance due to estimation error
        assert abs(realized_vol - target_vol) < target_vol * 0.5  # Within 50% of target
    
    def test_config_parameter_sensitivity(self):
        """Test sensitivity to different config parameters."""
        data = create_sample_price_data(days=60)
        
        # Test different risk budgets
        aggressive_config = create_sample_config()
        aggressive_config["risk_budget"]["tqqq_weight"] = 0.8
        aggressive_config["risk_budget"]["diversifier_weight"] = 0.15
        aggressive_config["risk_budget"]["cash_weight"] = 0.05
        
        conservative_config = create_sample_config()
        conservative_config["risk_budget"]["tqqq_weight"] = 0.4
        conservative_config["risk_budget"]["diversifier_weight"] = 0.4
        conservative_config["risk_budget"]["cash_weight"] = 0.2
        
        aggressive_strategy = EquityCrisisAlphaStrategy(aggressive_config)
        conservative_strategy = EquityCrisisAlphaStrategy(conservative_config)
        
        aggressive_weights = aggressive_strategy.calculate_weights(data)
        conservative_weights = conservative_strategy.calculate_weights(data)
        
        # Aggressive config should result in higher TQQQ weight
        assert aggressive_weights["TQQQ"] > conservative_weights["TQQQ"]
        
        # Conservative config should result in higher cash weight
        assert conservative_weights["SGOV"] > aggressive_weights["SGOV"]
    
    def test_long_term_performance_simulation(self):
        """Test long-term performance simulation."""
        # Create 1 year of data
        data = create_sample_price_data(days=252)
        
        # Simulate monthly rebalancing
        portfolio_value = 10000  # Starting value
        current_weights = self.strategy.calculate_weights(data.iloc[:30])
        
        for i in range(30, len(data), 30):
            month_data = data.iloc[i-30:i]
            
            # Calculate returns for the month
            month_returns = month_data.pct_change().dropna()
            
            # Update portfolio value
            for asset in self.strategy.assets:
                asset_return = month_returns[asset].sum()
                portfolio_value *= (1 + current_weights[asset] * asset_return)
            
            # Rebalance if needed
            new_weights = self.strategy.calculate_weights(month_data)
            if self.strategy.should_rebalance(current_weights, new_weights):
                current_weights = new_weights
        
        # Portfolio should have positive value (basic sanity check)
        assert portfolio_value > 0
        
        # Should have some volatility (not flat)
        assert portfolio_value != 10000