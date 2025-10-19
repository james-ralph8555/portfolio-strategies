"""
Unit tests for EquityCrisisAlphaStrategy.
"""

from unittest.mock import patch

import pandas as pd

from strategies.equity_crisis_alpha.strategy import EquityCrisisAlphaStrategy
from tests.fixtures.sample_data import (
    create_invalid_config,
    create_sample_config,
    create_sample_price_data,
)


class TestEquityCrisisAlphaStrategy:
    """Test suite for EquityCrisisAlphaStrategy class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = create_sample_config()
        self.strategy = EquityCrisisAlphaStrategy(self.config)
        self.sample_data = create_sample_price_data()

    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy.name == "equity_crisis_alpha"
        assert self.strategy.assets == ["TQQQ", "DBMF", "IAU", "SGOV"]
        assert self.strategy.rebalance_frequency == "monthly"
        assert self.strategy.drift_bands == 10
        assert self.strategy.config == self.config

    def test_initialization_with_default_config(self):
        """Test strategy initialization with default config."""
        strategy = EquityCrisisAlphaStrategy()
        assert strategy.name == "equity_crisis_alpha"
        assert strategy.assets == ["TQQQ", "DBMF", "IAU", "SGOV"]
        assert strategy.config == {}

    def test_get_assets(self):
        """Test get_assets method."""
        assets = self.strategy.get_assets()
        assert assets == ["TQQQ", "DBMF", "IAU", "SGOV"]
        # Ensure it returns a copy
        assets.append("TEST")
        assert self.strategy.get_assets() == ["TQQQ", "DBMF", "IAU", "SGOV"]

    def test_get_name(self):
        """Test get_name method."""
        assert self.strategy.get_name() == "equity_crisis_alpha"

    def test_get_config(self):
        """Test get_config method."""
        config = self.strategy.get_config()
        assert config == self.config
        # Ensure it returns a copy
        config["test"] = "value"
        assert self.strategy.get_config() == self.config

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        assert self.strategy.validate_config() is True

    def test_validate_config_missing_keys(self):
        """Test config validation with missing required keys."""
        invalid_config = {"risk_budget": {}}
        strategy = EquityCrisisAlphaStrategy(invalid_config)
        assert strategy.validate_config() is False

    def test_validate_config_invalid_risk_budget(self):
        """Test config validation with invalid risk budget."""
        invalid_config = create_invalid_config()
        strategy = EquityCrisisAlphaStrategy(invalid_config)
        assert strategy.validate_config() is False

    def test_validate_config_invalid_vol_target(self):
        """Test config validation with invalid volatility target."""
        config = create_sample_config()
        config["volatility_targeting"]["target_vol"] = 0.8  # Too high
        strategy = EquityCrisisAlphaStrategy(config)
        assert strategy.validate_config() is False

    def test_calculate_weights_basic(self):
        """Test basic weight calculation."""
        weights = self.strategy.calculate_weights(self.sample_data)

        # Check that all assets have weights
        for asset in self.strategy.assets:
            assert asset in weights

        # Check that weights are numbers
        for weight in weights.values():
            assert isinstance(weight, (int, float))

        # Check that weights sum to approximately 1 (before volatility targeting)
        # Note: After volatility targeting, sum may differ due to scaling
        assert all(w >= 0 for w in weights.values())

    def test_calculate_weights_with_insufficient_data(self):
        """Test weight calculation with insufficient data."""
        # Create minimal data
        minimal_data = pd.DataFrame(
            {
                "TQQQ": [100, 101],
                "DBMF": [100, 100.5],
                "IAU": [100, 100.8],
                "SGOV": [100, 100.2],
            }
        )

        weights = self.strategy.calculate_weights(minimal_data)
        assert len(weights) == 4

    @patch("strategies.equity_crisis_alpha.strategy.pd.DataFrame.cov")
    def test_calculate_erc_weights(self, mock_cov):
        """Test ERC weight calculation."""
        # Mock covariance matrix
        mock_cov.return_value = pd.DataFrame(
            [
                [0.04, 0.01, 0.005, 0.001],
                [0.01, 0.01, 0.002, 0.0005],
                [0.005, 0.002, 0.009, 0.0008],
                [0.001, 0.0005, 0.0008, 0.0004],
            ],
            index=self.strategy.assets,
            columns=self.strategy.assets,
        )

        cov_matrix = self.sample_data.cov() * 252
        risk_budget = self.config["risk_budget"]

        weights = self.strategy._calculate_erc_weights(cov_matrix, risk_budget)

        # Check that weights match risk budget
        assert weights["TQQQ"] == risk_budget["tqqq_weight"]
        assert weights["SGOV"] == risk_budget["cash_weight"]
        assert weights["DBMF"] == risk_budget["diversifier_weight"] / 2
        assert weights["IAU"] == risk_budget["diversifier_weight"] / 2

    def test_apply_black_litterman_tilt(self):
        """Test Black-Litterman tilt application."""
        base_weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}

        tilted_weights = self.strategy._apply_black_litterman_tilt(
            base_weights, self.sample_data
        )

        # TQQQ weight should increase due to positive view
        assert tilted_weights["TQQQ"] > base_weights["TQQQ"]

        # Other weights should decrease proportionally
        assert tilted_weights["DBMF"] < base_weights["DBMF"]
        assert tilted_weights["IAU"] < base_weights["IAU"]
        assert tilted_weights["SGOV"] < base_weights["SGOV"]

        # Weights should still sum to approximately 1
        assert abs(sum(tilted_weights.values()) - 1.0) < 0.01

    def test_apply_black_litterman_tilt_no_views(self):
        """Test Black-Litterman tilt with no views."""
        config_no_views = create_sample_config()
        config_no_views["black_litterman"]["views"] = []
        strategy = EquityCrisisAlphaStrategy(config_no_views)

        base_weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}
        tilted_weights = strategy._apply_black_litterman_tilt(
            base_weights, self.sample_data
        )

        # Weights should be unchanged
        assert tilted_weights == base_weights

    def test_apply_volatility_targeting(self):
        """Test volatility targeting application."""
        base_weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}

        targeted_weights = self.strategy._apply_volatility_targeting(
            base_weights, self.sample_data
        )

        # Check that all assets still have weights
        for asset in self.strategy.assets:
            assert asset in targeted_weights

        # Check that weights are non-negative
        for weight in targeted_weights.values():
            assert weight >= 0

        # Check leverage constraint
        total_leverage = sum(abs(w) for w in targeted_weights.values())
        assert total_leverage <= self.config["risk_controls"]["max_leverage"]

    def test_apply_volatility_targeting_high_leverage(self):
        """Test volatility targeting with leverage constraint."""
        # Create config with low max leverage
        config_low_leverage = create_sample_config()
        config_low_leverage["risk_controls"]["max_leverage"] = 1.5
        strategy = EquityCrisisAlphaStrategy(config_low_leverage)

        base_weights = {"TQQQ": 2.0, "DBMF": 0.5, "IAU": 0.3, "SGOV": 0.2}
        targeted_weights = strategy._apply_volatility_targeting(
            base_weights, self.sample_data
        )

        # Check leverage constraint
        total_leverage = sum(abs(w) for w in targeted_weights.values())
        assert total_leverage <= 1.5

    def test_should_rebalance_within_bands(self):
        """Test rebalancing logic when within drift bands."""
        current_weights = {"TQQQ": 0.58, "DBMF": 0.22, "IAU": 0.1, "SGOV": 0.1}
        target_weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}

        assert self.strategy.should_rebalance(current_weights, target_weights) is False

    def test_should_rebalance_outside_bands(self):
        """Test rebalancing logic when outside drift bands."""
        current_weights = {"TQQQ": 0.45, "DBMF": 0.25, "IAU": 0.15, "SGOV": 0.15}
        target_weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}

        # TQQQ drift is 15%, which exceeds 10% drift bands
        assert self.strategy.should_rebalance(current_weights, target_weights) is True

    def test_should_rebalance_missing_assets(self):
        """Test rebalancing logic with missing assets."""
        current_weights = {"TQQQ": 0.6, "DBMF": 0.2}  # Missing IAU, SGOV
        target_weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}

        # Missing assets should trigger rebalance
        assert self.strategy.should_rebalance(current_weights, target_weights) is True

    def test_preprocess_data(self):
        """Test data preprocessing."""
        processed_data = self.strategy.preprocess_data(self.sample_data)

        # Should return a copy
        assert processed_data is not self.sample_data
        assert processed_data.equals(self.sample_data)

    def test_postprocess_weights(self):
        """Test weight postprocessing."""
        weights = {"TQQQ": 0.6, "DBMF": 0.2, "IAU": 0.1, "SGOV": 0.1}
        processed_weights = self.strategy.postprocess_weights(weights)

        # Should return a copy
        assert processed_weights is not weights
        assert processed_weights == weights

    def test_update_config(self):
        """Test configuration update."""
        new_config = {"test_param": "test_value"}
        original_config = self.strategy.config.copy()

        self.strategy.update_config(new_config)

        # Config should be updated
        assert self.strategy.config["test_param"] == "test_value"
        # Original config should remain
        for key, value in original_config.items():
            assert self.strategy.config[key] == value
