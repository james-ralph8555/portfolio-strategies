"""
Equity Engine + Convex Rate Hedge Strategy

Assets: TQQQ + PFIX (payer-swaption rate hedge) + Gold (IAU) + Cash (SGOV)
Algorithm: Regime-switch risk budget for the bond/rate sleeve with volatility targeting
"""

import numpy as np
import pandas as pd

from core.interfaces.strategy import Strategy


class EquityConvexRateHedgeStrategy(Strategy):
    """
    TQQQ strategy with convex rate hedge using PFIX and gold diversification.

    Uses regime-switch risk budget for bond/rate sleeve based on stock-bond correlation,
    with TQQQ overweight via expected-return tilt and portfolio-level volatility targeting.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize the strategy with configuration parameters.

        Args:
            config: Strategy-specific configuration dictionary
        """
        super().__init__(config)
        self.name = "equity_convex_rate_hedge"
        self.assets = ["TQQQ", "PFIX", "IAU", "SGOV"]
        self.rebalance_frequency = "monthly"
        self.drift_bands = 10

        # Default configuration
        self.default_config = {
            "target_volatility": 0.15,  # 15% annualized volatility target
            "tqqq_base_weight": 0.60,  # Base TQQQ allocation
            "pfix_base_weight": 0.20,  # Base PFIX allocation
            "gold_base_weight": 0.15,  # Base gold allocation
            "cash_base_weight": 0.05,  # Base cash allocation
            "correlation_threshold": 0.0,  # Stock-bond correlation regime threshold
            "volatility_lookback": 60,  # Days for volatility calculation
            "correlation_lookback": 252,  # Days for correlation calculation
            "drift_bands": 10,  # Drift bands for rebalancing
        }

        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}

    def calculate_weights(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate target weights based on regime-switch risk budget.

        Args:
            data: Market data with returns, volatility, and correlation metrics

        Returns:
            Dictionary of target weights for each asset
        """
        # Calculate stock-bond correlation regime
        stock_bond_corr = self._calculate_stock_bond_correlation(data)

        # Calculate portfolio volatility scaling
        vol_scale = self._calculate_volatility_scaling(data)

        # Determine regime-based weights
        if stock_bond_corr > self.config["correlation_threshold"]:
            # Positive correlation regime: emphasize PFIX as primary hedge
            weights = self._positive_correlation_weights()
        else:
            # Negative correlation regime: allow some duration exposure
            weights = self._negative_correlation_weights()

        # Apply volatility targeting
        weights = self._apply_volatility_targeting(weights, vol_scale)

        # Normalize to ensure weights sum to 1
        weights = self._normalize_weights(weights)

        return weights

    def _calculate_stock_bond_correlation(self, data: pd.DataFrame) -> float:
        """
        Calculate rolling correlation between stocks and bonds.

        Args:
            data: Market data with price returns

        Returns:
            Rolling correlation value
        """
        lookback = self.config["correlation_lookback"]

        # Use TQQQ as proxy for stocks, PFIX for rates
        if "TQQQ" in data.columns and "PFIX" in data.columns:
            stock_returns = data["TQQQ"].pct_change().dropna()
            bond_returns = data["PFIX"].pct_change().dropna()

            if len(stock_returns) >= lookback and len(bond_returns) >= lookback:
                correlation = stock_returns.tail(lookback).corr(
                    bond_returns.tail(lookback)
                )
                return correlation if not np.isnan(correlation) else 0.0

        return 0.0

    def _calculate_volatility_scaling(self, data: pd.DataFrame) -> float:
        """
        Calculate volatility scaling factor for targeting.

        Args:
            data: Market data with returns

        Returns:
            Volatility scaling factor
        """
        lookback = self.config["volatility_lookback"]
        target_vol = self.config["target_volatility"]

        # Calculate realized volatility of TQQQ
        if "TQQQ" in data.columns:
            returns = data["TQQQ"].pct_change().dropna()
            if len(returns) >= lookback:
                realized_vol = returns.tail(lookback).std() * np.sqrt(252)
                if realized_vol > 0:
                    return min(target_vol / realized_vol, 2.0)  # Cap scaling at 2x

        return 1.0

    def _positive_correlation_weights(self) -> dict[str, float]:
        """
        Calculate weights for positive stock-bond correlation regime.

        Returns:
            Dictionary of regime-specific weights
        """
        return {
            "TQQQ": self.config["tqqq_base_weight"],
            "PFIX": self.config["pfix_base_weight"] * 1.2,  # Increase PFIX weight
            "IAU": self.config["gold_base_weight"] * 0.8,  # Reduce gold slightly
            "SGOV": self.config["cash_base_weight"],
        }

    def _negative_correlation_weights(self) -> dict[str, float]:
        """
        Calculate weights for negative stock-bond correlation regime.

        Returns:
            Dictionary of regime-specific weights
        """
        return {
            "TQQQ": self.config["tqqq_base_weight"] * 1.1,  # Slightly increase TQQQ
            "PFIX": self.config["pfix_base_weight"] * 0.8,  # Reduce PFIX
            "IAU": self.config["gold_base_weight"],  # Keep gold allocation
            "SGOV": self.config["cash_base_weight"] * 1.2,  # Increase cash slightly
        }

    def _apply_volatility_targeting(
        self, weights: dict[str, float], vol_scale: float
    ) -> dict[str, float]:
        """
        Apply volatility targeting to weights.

        Args:
            weights: Base weights
            vol_scale: Volatility scaling factor

        Returns:
            Volatility-adjusted weights
        """
        # Scale risky assets (TQQQ, PFIX, IAU) but keep cash as shock absorber
        adjusted_weights = {}
        for asset, weight in weights.items():
            if asset == "SGOV":
                adjusted_weights[asset] = weight
            else:
                adjusted_weights[asset] = weight * vol_scale

        return adjusted_weights

    def _normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        """
        Normalize weights to sum to 1.

        Args:
            weights: Raw weights

        Returns:
            Normalized weights
        """
        total = sum(weights.values())
        if total > 0:
            return {asset: weight / total for asset, weight in weights.items()}
        return weights

    def should_rebalance(
        self, current_weights: dict[str, float], target_weights: dict[str, float]
    ) -> bool:
        """
        Check if rebalancing is needed based on drift bands.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target weights from strategy

        Returns:
            True if rebalancing is needed
        """
        drift_threshold = self.config["drift_bands"] / 100.0

        for asset in self.assets:
            current = current_weights.get(asset, 0.0)
            target = target_weights.get(asset, 0.0)
            drift = abs(current - target)

            if drift > drift_threshold:
                return True

        return False

    def validate_config(self) -> bool:
        """
        Validate strategy configuration.

        Returns:
            True if configuration is valid
        """
        required_keys = [
            "target_volatility",
            "tqqq_base_weight",
            "pfix_base_weight",
            "gold_base_weight",
            "cash_base_weight",
            "correlation_threshold",
            "volatility_lookback",
            "correlation_lookback",
            "drift_bands",
        ]

        for key in required_keys:
            if key not in self.config:
                return False

        # Check that weights sum to approximately 1
        total_weight = (
            self.config["tqqq_base_weight"]
            + self.config["pfix_base_weight"]
            + self.config["gold_base_weight"]
            + self.config["cash_base_weight"]
        )

        if abs(total_weight - 1.0) > 0.01:
            return False

        # Check reasonable parameter ranges
        if not (0.05 <= self.config["target_volatility"] <= 0.30):
            return False

        if not (20 <= self.config["volatility_lookback"] <= 252):
            return False

        if not (60 <= self.config["correlation_lookback"] <= 504):
            return False

        return True
