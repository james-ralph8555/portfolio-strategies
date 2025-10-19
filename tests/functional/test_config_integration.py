"""
Integration tests for configuration loading and validation.
"""

import os
import tempfile

import yaml

from strategies.equity_crisis_alpha.strategy import EquityCrisisAlphaStrategy


class TestConfigIntegration:
    """Test suite for configuration integration."""

    def test_load_config_from_yaml_file(self):
        """Test loading configuration from YAML file."""
        config_path = "strategies/equity_crisis_alpha/config.yaml"

        # Check if config file exists
        assert os.path.exists(config_path)

        # Load config from file
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Create strategy with loaded config
        strategy = EquityCrisisAlphaStrategy(config)

        # Validate that strategy was created successfully
        assert strategy.name == "equity_crisis_alpha"
        assert strategy.validate_config() is True

    def test_config_file_structure(self):
        """Test that config file has required structure."""
        config_path = "strategies/equity_crisis_alpha/config.yaml"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check required top-level keys
        required_keys = [
            "name",
            "description",
            "assets",
            "risk_budget",
            "volatility_targeting",
            "rebalancing",
            "risk_controls",
        ]

        for key in required_keys:
            assert key in config, f"Missing required key: {key}"

        # Check assets structure
        assert "core" in config["assets"]
        assert "diversifiers" in config["assets"]
        assert "cash" in config["assets"]

        # Check risk budget structure
        risk_budget = config["risk_budget"]
        assert "tqqq_weight" in risk_budget
        assert "diversifier_weight" in risk_budget
        assert "cash_weight" in risk_budget

        # Check that risk budget sums to approximately 1
        total_budget = sum(risk_budget.values())
        assert abs(total_budget - 1.0) < 0.01, (
            f"Risk budget sums to {total_budget}, should be 1.0"
        )

    def test_invalid_config_handling(self):
        """Test handling of invalid configuration."""
        # Create invalid config
        invalid_config = {
            "name": "test",
            "risk_budget": {
                "tqqq_weight": 0.8,
                "diversifier_weight": 0.4,  # Sum > 1.0
                "cash_weight": 0.1,
            },
            # Missing other required sections
        }

        strategy = EquityCrisisAlphaStrategy(invalid_config)

        # Should fail validation
        assert strategy.validate_config() is False

    def test_config_update_and_validation(self):
        """Test configuration updates and re-validation."""
        # Start with valid config
        config_path = "strategies/equity_crisis_alpha/config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        strategy = EquityCrisisAlphaStrategy(config)
        assert strategy.validate_config() is True

        # Update with invalid parameter
        strategy.update_config(
            {
                "volatility_targeting": {
                    "target_vol": 0.8  # Too high
                }
            }
        )

        # Should fail validation after update
        assert strategy.validate_config() is False

        # Update with valid parameter
        strategy.update_config(
            {
                "volatility_targeting": {
                    "target_vol": 0.15  # Valid
                }
            }
        )

        # Should pass validation again
        assert strategy.validate_config() is True

    def test_config_with_temp_file(self):
        """Test configuration loading from temporary file."""
        # Create temporary config file
        config_data = {
            "name": "test_strategy",
            "description": "Test strategy",
            "assets": {"core": "TQQQ", "diversifiers": ["DBMF", "IAU"], "cash": "SGOV"},
            "risk_budget": {
                "tqqq_weight": 0.6,
                "diversifier_weight": 0.3,
                "cash_weight": 0.1,
            },
            "volatility_targeting": {"target_vol": 0.15, "lookback_period": 60},
            "rebalancing": {"frequency": "monthly", "drift_bands": 10},
            "risk_controls": {
                "max_leverage": 3.0,
                "max_single_asset_weight": 0.8,
                "correlation_regime_guard": True,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            # Load config from temp file
            with open(temp_path) as f:
                loaded_config = yaml.safe_load(f)

            # Create strategy
            strategy = EquityCrisisAlphaStrategy(loaded_config)

            # Validate
            assert strategy.validate_config() is True
            assert strategy.name == "test_strategy"

        finally:
            # Clean up
            os.unlink(temp_path)

    def test_config_parameter_types(self):
        """Test that config parameters have correct types."""
        config_path = "strategies/equity_crisis_alpha/config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check parameter types
        assert isinstance(config["name"], str)
        assert isinstance(config["description"], str)
        assert isinstance(config["assets"]["core"], str)
        assert isinstance(config["assets"]["diversifiers"], list)
        assert isinstance(config["assets"]["cash"], str)

        assert isinstance(config["risk_budget"]["tqqq_weight"], (int, float))
        assert isinstance(config["risk_budget"]["diversifier_weight"], (int, float))
        assert isinstance(config["risk_budget"]["cash_weight"], (int, float))

        assert isinstance(config["volatility_targeting"]["target_vol"], (int, float))
        assert isinstance(config["volatility_targeting"]["lookback_period"], int)

        assert isinstance(config["rebalancing"]["frequency"], str)
        assert isinstance(config["rebalancing"]["drift_bands"], (int, float))

        assert isinstance(config["risk_controls"]["max_leverage"], (int, float))
        assert isinstance(
            config["risk_controls"]["max_single_asset_weight"], (int, float)
        )
        assert isinstance(config["risk_controls"]["correlation_regime_guard"], bool)

    def test_config_default_values(self):
        """Test that strategy uses appropriate default values."""
        # Create strategy with minimal config
        minimal_config = {
            "risk_budget": {
                "tqqq_weight": 0.6,
                "diversifier_weight": 0.3,
                "cash_weight": 0.1,
            },
            "volatility_targeting": {"target_vol": 0.15, "lookback_period": 60},
            "rebalancing": {"frequency": "monthly", "drift_bands": 10},
        }

        strategy = EquityCrisisAlphaStrategy(minimal_config)

        # Should use default values for missing parameters
        assert strategy.drift_bands == 10  # From class default
        assert strategy.rebalance_frequency == "monthly"  # From class default

        # Should use config values for specified parameters
        assert strategy.config["risk_budget"]["tqqq_weight"] == 0.6
        assert strategy.config["volatility_targeting"]["target_vol"] == 0.15
