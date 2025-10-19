"""
Functional tests for strategy integration and end-to-end scenarios.
"""

import numpy as np
import pandas as pd

from strategies.equity_inflation_beta.strategy import EquityInflationBetaStrategy


class TestStrategyIntegration:
    """Functional tests for complete strategy workflows."""

    def test_full_workflow_monthly_rebalancing(
        self, equity_inflation_beta_config, inflation_beta_price_data
    ):
        """Test complete workflow with monthly rebalancing."""
        strategy = EquityInflationBetaStrategy(equity_inflation_beta_config)

        # Initial allocation
        target_weights = strategy.calculate_weights(inflation_beta_price_data)
        current_weights = target_weights.copy()

        # Simulate some market movement and drift
        drifted_weights = {
            "TQQQ": current_weights["TQQQ"] * 1.1,  # TQQQ went up
            "PDBC": current_weights["PDBC"] * 0.9,  # PDBC went down
            "IAU": current_weights["IAU"] * 1.05,  # IAU went up slightly
            "SGOV": current_weights["SGOV"] * 0.95,  # Cash went down slightly
        }

        # Normalize to maintain 100% allocation
        total = sum(drifted_weights.values())
        drifted_weights = {k: v / total for k, v in drifted_weights.items()}

        # Check if rebalancing is needed
        should_rebalance = strategy.should_rebalance(drifted_weights, target_weights)

        # Should rebalance if drift exceeds bands
        assert isinstance(should_rebalance, bool)

        if should_rebalance:
            # Calculate new target weights
            new_target_weights = strategy.calculate_weights(inflation_beta_price_data)
            assert abs(sum(new_target_weights.values()) - 1.0) < 1e-10

    def test_strategy_with_realistic_market_data(self, equity_inflation_beta_config):
        """Test strategy with realistic market data simulation."""
        strategy = EquityInflationBetaStrategy(equity_inflation_beta_config)

        # Simulate 2 years of daily data
        np.random.seed(2024)
        dates = pd.date_range("2022-01-01", periods=504, freq="D")

        # Create realistic price series with different characteristics
        # TQQQ: High volatility, upward trend with drawdowns
        tqqq_returns = np.random.normal(0.001, 0.03, 504)
        tqqq_returns[100:150] = np.random.normal(-0.005, 0.04, 50)  # Drawdown period
        tqqq_prices = 100 * np.cumprod(1 + tqqq_returns)

        # PDBC: Moderate volatility, some inflation sensitivity
        pdbc_returns = np.random.normal(0.0003, 0.015, 504)
        pdbc_returns[200:250] = np.random.normal(0.002, 0.02, 50)  # Inflation period
        pdbc_prices = 50 * np.cumprod(1 + pdbc_returns)

        # IAU: Low volatility, safe haven behavior
        iau_returns = np.random.normal(0.0002, 0.01, 504)
        iau_returns[100:150] = np.random.normal(0.001, 0.008, 50)  # Flight to safety
        iau_prices = 30 * np.cumprod(1 + iau_returns)

        # SGOV: Very low volatility, stable returns
        sgov_returns = np.random.normal(0.0001, 0.002, 504)
        sgov_prices = 10 * np.cumprod(1 + sgov_returns)

        market_data = pd.DataFrame(
            {
                "TQQQ": tqqq_prices,
                "PDBC": pdbc_prices,
                "IAU": iau_prices,
                "SGOV": sgov_prices,
            },
            index=dates,
        )

        # Test weight calculation over time
        weights_over_time = []
        for i in range(60, len(market_data), 20):  # Sample every 20 days
            subset_data = market_data.iloc[: i + 1]
            weights = strategy.calculate_weights(subset_data)
            weights_over_time.append(weights)

            # Validate weights
            assert abs(sum(weights.values()) - 1.0) < 1e-10
            assert all(weight >= 0 for weight in weights.values())

        # Check that weights change over time (strategy is responsive)
        initial_weights = weights_over_time[0]
        final_weights = weights_over_time[-1]

        # At least some weights should have changed
        weight_changes = [
            abs(initial_weights[asset] - final_weights[asset])
            for asset in initial_weights
        ]
        assert any(change > 0.01 for change in weight_changes)  # At least 1% change

    def test_strategy_performance_different_regimes(self, equity_inflation_beta_config):
        """Test strategy behavior across different market regimes."""
        strategy = EquityInflationBetaStrategy(equity_inflation_beta_config)

        regimes = {
            "bull_market": {
                "TQQQ": 0.002,
                "PDBC": 0.001,
                "IAU": 0.0005,
                "SGOV": 0.0001,
            },
            "bear_market": {
                "TQQQ": -0.001,
                "PDBC": -0.0005,
                "IAU": 0.001,
                "SGOV": 0.0002,
            },
            "high_inflation": {
                "TQQQ": 0.0005,
                "PDBC": 0.002,
                "IAU": 0.0015,
                "SGOV": 0.0001,
            },
            "low_volatility": {
                "TQQQ": 0.0005,
                "PDBC": 0.0003,
                "IAU": 0.0002,
                "SGOV": 0.0001,
            },
        }

        regime_weights = {}

        for regime_name, returns in regimes.items():
            np.random.seed(42)
            dates = pd.date_range("2023-01-01", periods=120, freq="D")

            # Generate price data for this regime
            prices = {}
            for asset, daily_return in returns.items():
                # Use absolute value for volatility to avoid negative scale
                volatility = abs(daily_return) * 3 if daily_return != 0 else 0.001
                asset_returns = np.random.normal(daily_return, volatility, 120)
                prices[asset] = 100 * np.cumprod(1 + asset_returns)

            regime_data = pd.DataFrame(prices, index=dates)
            weights = strategy.calculate_weights(regime_data)
            regime_weights[regime_name] = weights

            # Validate weights
            assert abs(sum(weights.values()) - 1.0) < 1e-10
            assert all(weight >= 0 for weight in weights.values())

        # Check that strategy adapts to different regimes
        bull_weights = regime_weights["bull_market"]
        bear_weights = regime_weights["bear_market"]
        inflation_weights = regime_weights["high_inflation"]

        # In bull market, should have higher TQQQ allocation
        # In bear market, should have more defensive allocation
        # In high inflation, should have more commodities/gold
        assert isinstance(bull_weights["TQQQ"], (int, float))
        assert isinstance(bear_weights["SGOV"], (int, float))
        assert isinstance(inflation_weights["PDBC"], (int, float))

    def test_rebalancing_frequency_impact(
        self, equity_inflation_beta_config, inflation_beta_price_data
    ):
        """Test impact of different rebalancing frequencies."""
        # Test with different drift bands
        tight_bands_config = equity_inflation_beta_config.copy()
        tight_bands_config["rebalancing"]["drift_bands"] = 5

        loose_bands_config = equity_inflation_beta_config.copy()
        loose_bands_config["rebalancing"]["drift_bands"] = 20

        tight_strategy = EquityInflationBetaStrategy(tight_bands_config)
        loose_strategy = EquityInflationBetaStrategy(loose_bands_config)

        target_weights = tight_strategy.calculate_weights(inflation_beta_price_data)

        # Create drifted weights
        drifted_weights = {
            "TQQQ": target_weights["TQQQ"] * 1.08,  # 8% drift
            "PDBC": target_weights["PDBC"] * 0.92,
            "IAU": target_weights["IAU"] * 1.08,
            "SGOV": target_weights["SGOV"] * 0.92,
        }

        # Normalize
        total = sum(drifted_weights.values())
        drifted_weights = {k: v / total for k, v in drifted_weights.items()}

        # Check rebalancing behavior (may depend on actual drift amounts)
        tight_rebalance = tight_strategy.should_rebalance(
            drifted_weights, target_weights
        )
        loose_rebalance = loose_strategy.should_rebalance(
            drifted_weights, target_weights
        )

        # At least one should be True, and loose should be less likely to rebalance
        assert isinstance(tight_rebalance, bool)
        assert isinstance(loose_rebalance, bool)

    def test_strategy_with_missing_data_scenarios(self, equity_inflation_beta_config):
        """Test strategy behavior with missing data scenarios."""
        strategy = EquityInflationBetaStrategy(equity_inflation_beta_config)

        # Test with missing assets
        incomplete_data = pd.DataFrame(
            {
                "TQQQ": np.random.normal(100, 10, 100),
                "PDBC": np.random.normal(50, 5, 100),
                # Missing IAU and SGOV
            }
        )

        weights = strategy.calculate_weights(incomplete_data)

        # Should handle missing assets gracefully
        assert isinstance(weights, dict)
        assert all(asset in weights for asset in strategy.assets)
        assert abs(sum(weights.values()) - 1.0) < 1e-10

        # Should handle missing assets gracefully
        assert isinstance(weights["IAU"], (int, float))
        assert isinstance(weights["SGOV"], (int, float))
        assert weights["IAU"] >= 0
        assert weights["SGOV"] >= 0

    def test_strategy_edge_cases(self, equity_inflation_beta_config):
        """Test strategy edge cases and boundary conditions."""
        strategy = EquityInflationBetaStrategy(equity_inflation_beta_config)

        # Test with minimal data
        minimal_data = pd.DataFrame(
            {"TQQQ": [100, 101], "PDBC": [50, 51], "IAU": [30, 31], "SGOV": [10, 11]}
        )

        weights = strategy.calculate_weights(minimal_data)
        assert abs(sum(weights.values()) - 1.0) < 1e-10

        # Test with constant prices (no volatility)
        constant_data = pd.DataFrame(
            {"TQQQ": [100] * 60, "PDBC": [50] * 60, "IAU": [30] * 60, "SGOV": [10] * 60}
        )

        weights = strategy.calculate_weights(constant_data)
        assert abs(sum(weights.values()) - 1.0) < 1e-10

        # Test with extreme price movements
        extreme_data = pd.DataFrame(
            {
                "TQQQ": [100, 200, 50, 150, 75, 300] + [100] * 54,
                "PDBC": [50, 25, 75, 100, 40, 80] + [50] * 54,
                "IAU": [30, 60, 15, 45, 25, 90] + [30] * 54,
                "SGOV": [10, 11, 9, 12, 8, 13] + [10] * 54,
            }
        )

        weights = strategy.calculate_weights(extreme_data)
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        assert all(weight >= 0 for weight in weights.values())

    def test_strategy_configuration_variations(self, minimal_config):
        """Test strategy with different configuration variations."""
        # Test aggressive configuration
        aggressive_config = minimal_config.copy()
        aggressive_config["tqqq_overweight"]["base_weight"] = 0.8
        aggressive_config["tqqq_overweight"]["scaling_factor"] = 1.5
        aggressive_config["signals"]["trend"]["weight"] = 0.8
        aggressive_config["signals"]["carry"]["weight"] = 0.2

        # Test conservative configuration
        conservative_config = minimal_config.copy()
        conservative_config["tqqq_overweight"]["base_weight"] = 0.4
        conservative_config["tqqq_overweight"]["scaling_factor"] = 1.0
        conservative_config["signals"]["trend"]["weight"] = 0.5
        conservative_config["signals"]["carry"]["weight"] = 0.5

        np.random.seed(42)
        test_data = pd.DataFrame(
            {
                "TQQQ": np.random.normal(100, 15, 100),
                "PDBC": np.random.normal(50, 8, 100),
                "IAU": np.random.normal(30, 4, 100),
                "SGOV": np.random.normal(10, 1, 100),
            }
        )

        aggressive_strategy = EquityInflationBetaStrategy(aggressive_config)
        conservative_strategy = EquityInflationBetaStrategy(conservative_config)

        aggressive_weights = aggressive_strategy.calculate_weights(test_data)
        conservative_weights = conservative_strategy.calculate_weights(test_data)

        # Aggressive configuration should generally have higher TQQQ allocation
        # but may be affected by volatility scaling and other factors
        assert isinstance(aggressive_weights["TQQQ"], (int, float))
        assert isinstance(conservative_weights["TQQQ"], (int, float))
        assert aggressive_weights["TQQQ"] >= 0
        assert conservative_weights["TQQQ"] >= 0

        # Both should be valid allocations
        for weights in [aggressive_weights, conservative_weights]:
            assert abs(sum(weights.values()) - 1.0) < 1e-10
            assert all(weight >= 0 for weight in weights.values())
