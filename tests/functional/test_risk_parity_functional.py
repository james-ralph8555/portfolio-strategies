"""
Functional tests for Risk Parity Strategy
"""

import pytest
import pandas as pd
import numpy as np
from strategies.risk_parity.strategy import RiskParityStrategy


class TestRiskParityStrategyFunctional:
    """Functional tests for RiskParityStrategy class."""
    
    @pytest.fixture
    def strategy(self):
        """Create strategy instance with default config."""
        config = {
            "risk_parity": {
                "risk_budget": {"equity": 0.75, "bond": 0.25},
                "lookback_period": 60,
                "optimization": {
                    "tolerance": 1e-10,
                    "method": "SLSQP",
                    "min_weight": 0.01,
                    "max_weight": 0.99
                }
            },
            "risk_management": {
                "max_leverage": 3.0,
                "volatility_target": 0.15
            },
            "rebalancing": {
                "frequency": "monthly",
                "drift_bands": 5
            }
        }
        return RiskParityStrategy(config)
    
    @pytest.fixture
    def realistic_market_data(self):
        """Create realistic market data with known characteristics."""
        dates = pd.date_range('2022-01-01', periods=252, freq='D')  # 1 year of data
        
        # Simulate realistic returns with negative correlation
        np.random.seed(123)
        
        # TQQQ: Higher volatility, positive drift
        tqqq_daily_vol = 0.03  # 3% daily vol ~ 48% annual
        tqqq_daily_return = 0.001  # 0.1% daily return
        tqqq_returns = np.random.normal(tqqq_daily_return, tqqq_daily_vol, 252)
        
        # TMF: Lower volatility, slight positive drift, negatively correlated
        tmf_daily_vol = 0.015  # 1.5% daily vol ~ 24% annual
        tmf_daily_return = 0.0003  # 0.03% daily return
        tmf_returns = np.random.normal(tmf_daily_return, tmf_daily_vol, 252)
        
        # Add negative correlation
        correlation = -0.3
        tmf_returns = tmf_returns - correlation * tqqq_returns * (tmf_daily_vol / tqqq_daily_vol)
        
        # Convert to prices
        tqqq_prices = 100 * np.exp(np.cumsum(tqqq_returns))
        tmf_prices = 100 * np.exp(np.cumsum(tmf_returns))
        
        return pd.DataFrame({
            'TQQQ': tqqq_prices,
            'TMF': tmf_prices
        }, index=dates)
    
    def test_end_to_end_workflow(self, strategy, realistic_market_data):
        """Test complete workflow from data to weights."""
        # Calculate weights
        weights = strategy.calculate_weights(realistic_market_data)
        
        # Verify weights are valid
        assert isinstance(weights, dict)
        assert len(weights) == 2
        assert all(asset in weights for asset in ["TQQQ", "TMF"])
        assert all(0 <= weight <= 1 for weight in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 0.01
        
        # Test rebalancing logic
        current_weights = {"TQQQ": 0.6, "TMF": 0.4}
        should_rebalance = strategy.should_rebalance(current_weights, weights)
        assert isinstance(should_rebalance, bool)
        
        # Get portfolio metrics
        metrics = strategy.get_portfolio_metrics(realistic_market_data, weights)
        assert isinstance(metrics, dict)
        assert "volatility" in metrics
        assert "risk_parity_error" in metrics
    
    def test_risk_parity_properties(self, strategy, realistic_market_data):
        """Test that calculated weights achieve risk parity properties."""
        weights = strategy.calculate_weights(realistic_market_data)
        
        # Calculate risk contributions
        returns_data = realistic_market_data[list(weights.keys())].pct_change().dropna()
        cov_matrix = returns_data.cov() * 252
        weights_array = np.array(list(weights.values()))
        
        # Portfolio risk
        portfolio_risk = np.sqrt(np.dot(weights_array.T, np.dot(cov_matrix, weights_array)))
        
        # Risk contributions
        marginal_contrib = np.dot(cov_matrix, weights_array)
        risk_contributions = np.multiply(weights_array, marginal_contrib) / portfolio_risk
        
        # Check that risk contributions are close to target
        target_equity_risk = 0.75
        target_bond_risk = 0.25
        
        actual_equity_risk = risk_contributions[0]
        actual_bond_risk = risk_contributions[1]
        
        # Allow some tolerance due to optimization constraints
        assert abs(actual_equity_risk - target_equity_risk) < 0.1
        assert abs(actual_bond_risk - target_bond_risk) < 0.1
    
    def test_different_market_conditions(self, strategy):
        """Test strategy behavior under different market conditions."""
        # Bull market: equities up, bonds down
        bull_dates = pd.date_range('2023-01-01', periods=100, freq='D')
        tqqq_bull = np.linspace(100, 150, 100)  # 50% gain
        tmf_bull = np.linspace(100, 95, 100)   # 5% loss
        bull_data = pd.DataFrame({'TQQQ': tqqq_bull, 'TMF': tmf_bull}, index=bull_dates)
        
        bull_weights = strategy.calculate_weights(bull_data)
        
        # Bear market: equities down, bonds up
        bear_dates = pd.date_range('2023-01-01', periods=100, freq='D')
        tqqq_bear = np.linspace(100, 70, 100)   # 30% loss
        tmf_bear = np.linspace(100, 110, 100)   # 10% gain
        bear_data = pd.DataFrame({'TQQQ': tqqq_bear, 'TMF': tmf_bear}, index=bear_dates)
        
        bear_weights = strategy.calculate_weights(bear_data)
        
        # Weights should adapt to market conditions
        assert isinstance(bull_weights, dict)
        assert isinstance(bear_weights, dict)
        
        # In bull market, TQQQ should have higher weight (more risk contribution)
        # In bear market, weights may shift but still maintain risk parity targets
        assert all(0 <= w <= 1 for w in bull_weights.values())
        assert all(0 <= w <= 1 for w in bear_weights.values())
    
    def test_rebalancing_scenarios(self, strategy, realistic_market_data):
        """Test various rebalancing scenarios."""
        target_weights = strategy.calculate_weights(realistic_market_data)
        
        # Scenario 1: Small drift - no rebalance
        small_drift = {
            asset: weight + 0.02 if asset == "TQQQ" else weight - 0.02
            for asset, weight in target_weights.items()
        }
        assert strategy.should_rebalance(small_drift, target_weights) is False
        
        # Scenario 2: Large drift - rebalance
        large_drift = {
            asset: weight + 0.10 if asset == "TQQQ" else weight - 0.10
            for asset, weight in target_weights.items()
        }
        assert strategy.should_rebalance(large_drift, target_weights) is True
        
        # Scenario 3: Missing assets in current weights
        partial_weights = {"TQQQ": 0.8}
        assert strategy.should_rebalance(partial_weights, target_weights) is True
    
    def test_volatility_targeting(self, strategy, realistic_market_data):
        """Test volatility targeting functionality."""
        # Calculate weights without volatility targeting
        weights = strategy.calculate_weights(realistic_market_data)
        
        # Get portfolio volatility
        metrics = strategy.get_portfolio_metrics(realistic_market_data, weights)
        portfolio_vol = metrics["volatility"]
        
        # Volatility should be reasonable (not extremely high due to leverage)
        assert 0.05 <= portfolio_vol <= 0.5  # Between 5% and 50% annual vol
        
        # Test with very low volatility target
        strategy.volatility_target = 0.05  # 5% target
        constrained_weights = strategy.calculate_weights(realistic_market_data)
        constrained_metrics = strategy.get_portfolio_metrics(realistic_market_data, constrained_weights)
        
        # Constrained volatility should be closer to target
        constrained_vol = constrained_metrics["volatility"]
        assert constrained_vol <= portfolio_vol  # Should be lower
    
    def test_config_variations(self, realistic_market_data):
        """Test strategy with different configurations."""
        # Configuration 1: Equal risk budget
        equal_risk_config = {
            "risk_parity": {
                "risk_budget": {"equity": 0.5, "bond": 0.5},
                "lookback_period": 60
            },
            "risk_management": {"max_leverage": 3.0, "volatility_target": 0.15},
            "rebalancing": {"frequency": "monthly", "drift_bands": 5}
        }
        
        equal_strategy = RiskParityStrategy(equal_risk_config)
        equal_weights = equal_strategy.calculate_weights(realistic_market_data)
        
        # Configuration 2: Equity-heavy risk budget
        equity_heavy_config = {
            "risk_parity": {
                "risk_budget": {"equity": 0.9, "bond": 0.1},
                "lookback_period": 60
            },
            "risk_management": {"max_leverage": 3.0, "volatility_target": 0.15},
            "rebalancing": {"frequency": "monthly", "drift_bands": 5}
        }
        
        equity_heavy_strategy = RiskParityStrategy(equity_heavy_config)
        equity_heavy_weights = equity_heavy_strategy.calculate_weights(realistic_market_data)
        
        # Both should produce valid weights
        assert all(0 <= w <= 1 for w in equal_weights.values())
        assert all(0 <= w <= 1 for w in equity_heavy_weights.values())
        
        # Equity-heavy should allocate more capital to bonds (since bonds are less volatile)
        # but still achieve 90% risk contribution from equity
        assert equal_weights != equity_heavy_weights
    
    def test_error_handling(self, strategy):
        """Test error handling in various scenarios."""
        # Empty data
        empty_data = pd.DataFrame()
        
        # Should handle gracefully or raise appropriate error
        try:
            weights = strategy.calculate_weights(empty_data)
            # If no error, should return valid weights
            assert isinstance(weights, dict)
        except (ValueError, KeyError):
            # Expected error for insufficient data
            pass
        
        # Data with missing assets
        incomplete_data = pd.DataFrame({
            'TQQQ': [100, 101, 102]
        })
        
        with pytest.raises(ValueError):
            strategy.calculate_weights(incomplete_data)
        
        # Data with NaN values
        nan_data = pd.DataFrame({
            'TQQQ': [100, np.nan, 102],
            'TMF': [100, 101, np.nan]
        })
        
        # Should handle NaN values gracefully
        weights = strategy.calculate_weights(nan_data)
        assert isinstance(weights, dict)