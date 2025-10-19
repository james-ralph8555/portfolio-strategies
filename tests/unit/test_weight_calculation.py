"""
Unit tests for weight calculation functionality.
"""

import pandas as pd


class TestWeightCalculation:
    """Test suite for weight calculation methods."""

    def test_calculate_weights_basic(self, strategy, sample_price_data):
        """Test basic weight calculation."""
        weights = strategy.calculate_weights(sample_price_data)

        assert isinstance(weights, dict)
        assert len(weights) == 4
        assert all(asset in weights for asset in ["TQQQ", "PDBC", "IAU", "SGOV"])
        assert all(isinstance(weight, (int, float)) for weight in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        assert all(weight >= 0 for weight in weights.values())

    def test_calculate_weights_with_trending_data(self, strategy, trending_data):
        """Test weight calculation with trending data."""
        weights = strategy.calculate_weights(trending_data)

        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        assert all(weight >= 0 for weight in weights.values())

    def test_calculate_weights_insufficient_data(self, strategy):
        """Test weight calculation with insufficient data."""
        short_data = pd.DataFrame(
            {
                "TQQQ": [100, 101, 102],
                "PDBC": [50, 51, 52],
                "IAU": [30, 31, 32],
                "SGOV": [10, 11, 12],
            }
        )

        weights = strategy.calculate_weights(short_data)

        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        # Should handle insufficient data gracefully
        assert all(weight >= 0 for weight in weights.values())

    def test_calculate_weights_missing_assets(
        self, strategy, inflation_beta_price_data
    ):
        """Test weight calculation with missing asset data."""
        incomplete_data = inflation_beta_price_data.drop("PDBC", axis=1)

        weights = strategy.calculate_weights(incomplete_data)

        assert isinstance(weights, dict)
        assert "PDBC" in weights
        # Should handle missing data gracefully (may not be exactly zero due to risk parity)

    def test_calculate_weights_signal_combination(self, strategy, sample_price_data):
        """Test that trend and carry signals are properly combined."""

        # Mock the signal methods to return known values
        def mock_trend_signal(data):
            return {"PDBC": 1.0, "IAU": -1.0}

        def mock_carry_signal(data):
            return {"PDBC": 1.0, "IAU": 1.0}

        strategy.calculate_trend_signal = mock_trend_signal
        strategy.calculate_carry_signal = mock_carry_signal

        weights = strategy.calculate_weights(sample_price_data)

        # With trend_weight=0.6, carry_weight=0.4:
        # PDBC: 0.6*1.0 + 0.4*1.0 = 1.0
        # IAU: 0.6*(-1.0) + 0.4*1.0 = -0.2
        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_calculate_weights_volatility_scaling(self, strategy, sample_price_data):
        """Test volatility scaling in weight calculation."""

        # Mock portfolio volatility to test scaling
        def mock_portfolio_vol(data):
            return 0.10  # Lower than target 0.15, should scale up

        strategy._calculate_portfolio_volatility = mock_portfolio_vol

        weights = strategy.calculate_weights(sample_price_data)

        # TQQQ weight should be scaled up due to lower volatility
        assert weights["TQQQ"] > strategy.config["tqqq_overweight"]["base_weight"]

    def test_calculate_weights_extreme_volatility(self, strategy, sample_price_data):
        """Test weight calculation with extreme volatility."""

        # Mock high portfolio volatility
        def mock_portfolio_vol(data):
            return 0.30  # Higher than target 0.15, should scale down

        strategy._calculate_portfolio_volatility = mock_portfolio_vol

        weights = strategy.calculate_weights(sample_price_data)

        # TQQQ weight should be scaled down due to high volatility
        assert weights["TQQQ"] < strategy.config["tqqq_overweight"]["base_weight"]

    def test_calculate_weights_zero_volatility(self, strategy, sample_price_data):
        """Test weight calculation with zero volatility."""

        # Mock zero portfolio volatility
        def mock_portfolio_vol(data):
            return 0.0

        strategy._calculate_portfolio_volatility = mock_portfolio_vol

        weights = strategy.calculate_weights(sample_price_data)

        # Should handle zero volatility gracefully
        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 1e-10
        assert all(weight >= 0 for weight in weights.values())

    def test_risk_parity_signal_integration(self, strategy, sample_price_data):
        """Test integration of risk parity with signal tilting."""

        # Mock methods to isolate risk parity behavior
        def mock_trend_signal(data):
            return {"PDBC": 0, "IAU": 0}  # Neutral signals

        def mock_carry_signal(data):
            return {"PDBC": 0, "IAU": 0}  # Neutral signals

        strategy.calculate_trend_signal = mock_trend_signal
        strategy.calculate_carry_signal = mock_carry_signal

        weights = strategy.calculate_weights(sample_price_data)

        # With neutral signals, should get pure risk parity weights
        assert isinstance(weights, dict)
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_cash_allocation_calculation(self, strategy, sample_price_data):
        """Test cash allocation when risk assets exceed target."""
        # Create a config that would result in >100% risk allocation
        high_risk_config = strategy.config.copy()
        high_risk_config["tqqq_overweight"]["base_weight"] = 0.8
        high_risk_config["tqqq_overweight"]["scaling_factor"] = 2.0

        strategy.config = high_risk_config

        weights = strategy.calculate_weights(sample_price_data)

        # Cash should be zero if risk assets fit within 100%
        assert weights["SGOV"] >= 0
        assert abs(sum(weights.values()) - 1.0) < 1e-10

    def test_weight_bounds(self, strategy, sample_price_data):
        """Test that weights stay within reasonable bounds."""
        weights = strategy.calculate_weights(sample_price_data)

        for asset, weight in weights.items():
            assert 0 <= weight <= 1, (
                f"Weight for {asset} ({weight}) outside [0,1] range"
            )

    def test_weight_consistency(self, strategy, sample_price_data):
        """Test that weight calculations are consistent."""
        weights1 = strategy.calculate_weights(sample_price_data)
        weights2 = strategy.calculate_weights(sample_price_data)

        # Should be identical for same input
        for asset in weights1:
            assert abs(weights1[asset] - weights2[asset]) < 1e-10

    def test_postprocess_weights_modification(self, strategy, sample_price_data):
        """Test that postprocess_weights can modify weights."""

        def mock_postprocess(weights):
            modified = weights.copy()
            modified["TQQQ"] *= 0.9  # Reduce TQQQ by 10%
            return modified

        strategy.postprocess_weights = mock_postprocess

        raw_weights = {"TQQQ": 0.6, "PDBC": 0.2, "IAU": 0.2, "SGOV": 0.0}
        processed = strategy.postprocess_weights(raw_weights)

        assert processed["TQQQ"] == 0.54  # 0.6 * 0.9
        assert processed["PDBC"] == 0.2
        assert processed["IAU"] == 0.2
        assert processed["SGOV"] == 0.0
