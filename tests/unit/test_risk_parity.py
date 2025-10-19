"""
Unit tests for Risk Parity Strategy
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from strategies.risk_parity.strategy import RiskParityStrategy


class TestRiskParityStrategy:
    """Test cases for RiskParityStrategy class."""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "risk_parity": {
                "risk_budget": {"equity": 0.75, "bond": 0.25},
                "lookback_period": 90,
                "optimization": {
                    "tolerance": 1e-10,
                    "method": "SLSQP",
                    "min_weight": 0.01,
                    "max_weight": 0.99,
                },
            },
            "risk_management": {
                "max_leverage": 3.0,
                "volatility_target": 0.15,
                "drawdown_control": {"enabled": True, "max_drawdown": 0.20},
            },
            "rebalancing": {"frequency": "monthly", "drift_bands": 5},
        }

    @pytest.fixture
    def strategy(self, sample_config):
        """Create strategy instance for testing."""
        return RiskParityStrategy(sample_config)

    @pytest.fixture
    def sample_data(self):
        """Sample market data for testing."""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        np.random.seed(42)  # For reproducible results

        # Create correlated price series for TQQQ and TMF
        tqqq_returns = np.random.normal(0.001, 0.02, 100)  # Higher volatility
        tmf_returns = np.random.normal(0.0005, 0.01, 100)  # Lower volatility

        # Add some negative correlation
        tmf_returns -= 0.3 * tqqq_returns

        tqqq_prices = 100 * np.exp(np.cumsum(tqqq_returns))
        tmf_prices = 100 * np.exp(np.cumsum(tmf_returns))

        return pd.DataFrame({"TQQQ": tqqq_prices, "TMF": tmf_prices}, index=dates)

    def test_initialization(self, strategy, sample_config):
        """Test strategy initialization."""
        assert strategy.name == "risk_parity"
        assert strategy.assets == ["TQQQ", "TMF"]
        assert strategy.rebalance_frequency == "monthly"
        assert strategy.drift_bands == 5
        assert strategy.risk_budget == {"equity": 0.75, "bond": 0.25}
        assert strategy.lookback_period == 90

    def test_validate_config_valid(self, strategy):
        """Test configuration validation with valid config."""
        assert strategy.validate_config() is True

    def test_validate_config_invalid_risk_budget(self, strategy):
        """Test configuration validation with invalid risk budget."""
        strategy.config["risk_parity"]["risk_budget"] = {
            "equity": 0.8,
            "bond": 0.3,
        }  # Sum > 1
        assert strategy.validate_config() is False

    def test_validate_config_missing_section(self, strategy):
        """Test configuration validation with missing section."""
        del strategy.config["risk_management"]
        assert strategy.validate_config() is False

    def test_calculate_weights_sufficient_data(self, strategy, sample_data):
        """Test weight calculation with sufficient data."""
        weights = strategy.calculate_weights(sample_data)

        assert isinstance(weights, dict)
        assert "TQQQ" in weights
        assert "TMF" in weights
        assert len(weights) == 2

        # Weights should sum to 1 (approximately)
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01

        # All weights should be positive
        for weight in weights.values():
            assert weight >= 0

    def test_calculate_weights_insufficient_data(self, strategy):
        """Test weight calculation with insufficient data."""
        # Create minimal data
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        minimal_data = pd.DataFrame(
            {"TQQQ": [100, 101, 102, 103, 104], "TMF": [100, 101, 102, 103, 104]},
            index=dates,
        )

        weights = strategy.calculate_weights(minimal_data)

        # Should fall back to equal weights
        assert weights == {"TQQQ": 0.5, "TMF": 0.5}

    def test_calculate_weights_missing_asset(self, strategy, sample_data):
        """Test weight calculation with missing asset."""
        incomplete_data = sample_data.drop("TMF", axis=1)

        with pytest.raises(ValueError, match="Required asset TMF not found"):
            strategy.calculate_weights(incomplete_data)

    def test_should_rebalance_within_bands(self, strategy):
        """Test rebalancing logic when within drift bands."""
        current_weights = {"TQQQ": 0.7, "TMF": 0.3}
        target_weights = {"TQQQ": 0.72, "TMF": 0.28}  # 2% drift

        assert strategy.should_rebalance(current_weights, target_weights) is False

    def test_should_rebalance_outside_bands(self, strategy):
        """Test rebalancing logic when outside drift bands."""
        current_weights = {"TQQQ": 0.7, "TMF": 0.3}
        target_weights = {"TQQQ": 0.8, "TMF": 0.2}  # 10% drift

        assert strategy.should_rebalance(current_weights, target_weights) is True

    def test_get_risk_parity_weights_optimization(self, strategy):
        """Test risk parity weight optimization."""
        # Create simple covariance matrix
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.01]])  # TQQQ more volatile
        risk_budget = np.array([0.75, 0.25])
        initial_weights = np.array([0.5, 0.5])

        weights = strategy._get_risk_parity_weights(
            cov_matrix, risk_budget, initial_weights
        )

        assert len(weights) == 2
        assert all(w >= 0 for w in weights)
        assert abs(sum(weights) - 1.0) < 0.01

    def test_apply_risk_constraints(self, strategy, sample_data):
        """Test risk constraint application."""
        weights = {"TQQQ": 0.8, "TMF": 0.2}

        constrained_weights = strategy._apply_risk_constraints(weights, sample_data)

        assert isinstance(constrained_weights, dict)
        assert len(constrained_weights) == 2
        assert abs(sum(constrained_weights.values()) - 1.0) < 0.01

    def test_get_portfolio_metrics(self, strategy, sample_data):
        """Test portfolio metrics calculation."""
        weights = {"TQQQ": 0.7, "TMF": 0.3}

        metrics = strategy.get_portfolio_metrics(sample_data, weights)

        assert isinstance(metrics, dict)
        assert "volatility" in metrics
        assert "risk_parity_error" in metrics
        assert isinstance(metrics["volatility"], float)
        assert isinstance(metrics["risk_parity_error"], float)
        assert metrics["volatility"] >= 0
        assert metrics["risk_parity_error"] >= 0

    def test_calculate_risk_parity_error(self, strategy):
        """Test risk parity error calculation."""
        # Perfect risk parity
        perfect_contributions = np.array([0.5, 0.5])
        assert strategy._calculate_risk_parity_error(perfect_contributions) == 0

        # Imperfect risk parity
        imperfect_contributions = np.array([0.7, 0.3])
        error = strategy._calculate_risk_parity_error(imperfect_contributions)
        assert error > 0

    def test_get_assets(self, strategy):
        """Test getting asset list."""
        assets = strategy.get_assets()
        assert assets == ["TQQQ", "TMF"]

    def test_get_name(self, strategy):
        """Test getting strategy name."""
        assert strategy.get_name() == "risk_parity"

    def test_get_config(self, strategy, sample_config):
        """Test getting configuration."""
        config = strategy.get_config()
        assert config == sample_config

    def test_update_config(self, strategy):
        """Test updating configuration."""
        new_config = {"risk_parity": {"lookback_period": 120}}
        strategy.update_config(new_config)

        assert strategy.lookback_period == 120

    @patch("strategies.risk_parity.strategy.minimize")
    def test_optimization_fallback(self, mock_minimize, strategy, sample_data):
        """Test fallback when optimization fails."""
        # Mock optimization failure
        mock_minimize.return_value = Mock(success=False)

        weights = strategy.calculate_weights(sample_data)

        # Should fall back to equal weights
        assert weights == {"TQQQ": 0.5, "TMF": 0.5}
