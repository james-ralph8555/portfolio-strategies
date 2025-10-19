"""
Configuration Manager

Centralized configuration management for strategies and the portfolio system.
Supports YAML configuration files with validation and environment variable overrides.
"""

import os
from pathlib import Path
from typing import Any

import yaml


class ConfigManager:
    """
    Manages configuration loading, validation, and environment overrides.
    """

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "strategies"

        self.config_dir = Path(config_dir)
        self._configs: dict[str, dict] = {}

    def load_strategy_config(self, strategy_name: str) -> dict[str, Any]:
        """
        Load configuration for a specific strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Configuration dictionary
        """
        if strategy_name in self._configs:
            return self._configs[strategy_name]

        config_file = self.config_dir / strategy_name / "config.yaml"

        if not config_file.exists():
            return {}

        try:
            with open(config_file) as f:
                config = yaml.safe_load(f) or {}

            # Apply environment variable overrides
            config = self._apply_env_overrides(config, strategy_name)

            self._configs[strategy_name] = config
            return config

        except Exception as e:
            print(f"Error loading config for {strategy_name}: {e}")
            return {}

    def _apply_env_overrides(
        self, config: dict[str, Any], strategy_name: str
    ) -> dict[str, Any]:
        """
        Apply environment variable overrides to configuration.

        Args:
            config: Base configuration
            strategy_name: Strategy name for env variable prefix

        Returns:
            Configuration with env overrides applied
        """
        prefix = f"{strategy_name.upper()}_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()

                # Try to parse as YAML for proper type conversion
                try:
                    parsed_value = yaml.safe_load(value)
                except yaml.YAMLError:
                    parsed_value = value

                # Navigate nested keys (supports dot notation)
                self._set_nested_value(config, config_key, parsed_value)

        return config

    def _set_nested_value(self, config: dict, key: str, value: Any) -> None:
        """
        Set nested value in dictionary using dot notation.

        Args:
            config: Configuration dictionary
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def save_strategy_config(self, strategy_name: str, config: dict[str, Any]) -> bool:
        """
        Save configuration for a strategy.

        Args:
            strategy_name: Name of the strategy
            config: Configuration dictionary

        Returns:
            True if saved successfully
        """
        config_file = self.config_dir / strategy_name / "config.yaml"

        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

            self._configs[strategy_name] = config
            return True

        except Exception as e:
            print(f"Error saving config for {strategy_name}: {e}")
            return False

    def validate_config(self, strategy_name: str, config: dict[str, Any]) -> bool:
        """
        Validate strategy configuration.

        Args:
            strategy_name: Name of the strategy
            config: Configuration to validate

        Returns:
            True if configuration is valid
        """
        # Basic validation - can be extended per strategy
        required_fields = ["name", "description", "assets"]

        for field in required_fields:
            if field not in config:
                print(f"Missing required field '{field}' in {strategy_name} config")
                return False

        return True

    def get_all_configs(self) -> dict[str, dict[str, Any]]:
        """
        Load all strategy configurations.

        Returns:
            Dictionary mapping strategy names to their configurations
        """
        configs = {}

        if not self.config_dir.exists():
            return configs

        for strategy_dir in self.config_dir.iterdir():
            if strategy_dir.is_dir() and not strategy_dir.name.startswith("__"):
                config = self.load_strategy_config(strategy_dir.name)
                if config:
                    configs[strategy_dir.name] = config

        return configs


# Global configuration manager instance
config_manager = ConfigManager()
