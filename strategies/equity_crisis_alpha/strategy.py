"""
Equity Engine + Crisis Alpha Strategy

Assets: TQQQ + DBMF/KMLM (managed futures) + Gold (IAU) + Cash (SGOV)
Algorithm: Leverage-aware ERC with Black-Litterman tilt, volatility targeting, monthly rebalance
"""

import numpy as np
import pandas as pd

from core.interfaces.strategy import Strategy


class EquityCrisisAlphaStrategy(Strategy):
    """
    TQQQ-centric strategy with managed futures and gold for crisis alpha.

    Uses leverage-aware Equal Risk Contribution with Black-Litterman tilt
    that assigns larger risk budget to TQQQ, with portfolio-level volatility targeting.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize the strategy with configuration parameters.

        Args:
            config: Strategy-specific configuration dictionary
        """
        super().__init__(config)
        self.name = self.config.get("name", "equity_crisis_alpha")
        self.assets = ["TQQQ", "DBMF", "IAU", "SGOV"]  # Default assets
        self.rebalance_frequency = self.config.get("rebalancing", {}).get(
            "frequency", "monthly"
        )
        self.drift_bands = self.config.get("rebalancing", {}).get(
            "drift_bands", 10
        )  # 10-point drift bands

    def calculate_weights(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate target weights based on leverage-aware ERC with Black-Litterman tilt.

        Args:
            data: Market data with returns for all assets

        Returns:
            Dictionary of target weights for each asset
        """
        # Extract returns data
        returns = data.pct_change().dropna()

        # Calculate covariance matrix
        cov_matrix = returns.cov() * 252  # Annualized

        # Get risk budget from config
        risk_budget = self.config.get(
            "risk_budget",
            {"tqqq_weight": 0.6, "diversifier_weight": 0.3, "cash_weight": 0.1},
        )

        # Calculate ERC weights based on risk budget
        erc_weights = self._calculate_erc_weights(cov_matrix, risk_budget)

        # Apply Black-Litterman tilt
        bl_weights = self._apply_black_litterman_tilt(erc_weights, returns)

        # Apply volatility targeting
        final_weights = self._apply_volatility_targeting(bl_weights, returns)

        return final_weights

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
        # Check if any assets are missing from current weights
        for asset in self.assets:
            if asset not in current_weights:
                return True

        for asset in self.assets:
            current_weight = current_weights.get(asset, 0)
            target_weight = target_weights.get(asset, 0)
            drift = abs(current_weight - target_weight)

            if drift > self.drift_bands / 100:  # Convert percentage points to decimal
                return True

        return False

    def validate_config(self) -> bool:
        """
        Validate strategy configuration.

        Returns:
            True if configuration is valid
        """
        required_keys = ["risk_budget", "volatility_targeting", "rebalancing"]

        for key in required_keys:
            if key not in self.config:
                return False

        # Validate risk budget sums to 1
        risk_budget = self.config["risk_budget"]
        total_budget = sum(risk_budget.values())
        if abs(total_budget - 1.0) > 0.01:  # Allow small rounding error
            return False

        # Validate volatility target is reasonable
        vol_target = self.config["volatility_targeting"].get("target_vol", 0.15)
        if not 0.05 <= vol_target <= 0.5:  # Between 5% and 50%
            return False

        return True

    def _calculate_erc_weights(
        self, cov_matrix: pd.DataFrame, risk_budget: dict
    ) -> dict[str, float]:
        """
        Calculate Equal Risk Contribution weights based on risk budget.

        Args:
            cov_matrix: Covariance matrix of asset returns
            risk_budget: Risk budget allocation

        Returns:
            Dictionary of ERC weights
        """
        n_assets = len(self.assets)
        weights = np.ones(n_assets) / n_assets  # Start with equal weights

        # Simple ERC implementation - risk budget proportional to weights
        # In practice, this would use numerical optimization
        for i, asset in enumerate(self.assets):
            if asset == "TQQQ":
                weights[i] = risk_budget["tqqq_weight"]
            elif asset in ["DBMF", "IAU"]:
                weights[i] = (
                    risk_budget["diversifier_weight"] / 2
                )  # Split between diversifiers
            elif asset == "SGOV":
                weights[i] = risk_budget["cash_weight"]

        return dict(zip(self.assets, weights, strict=False))

    def _apply_black_litterman_tilt(
        self, weights: dict[str, float], returns: pd.DataFrame
    ) -> dict[str, float]:
        """
        Apply Black-Litterman tilt favoring TQQQ.

        Args:
            weights: Base weights from ERC
            returns: Historical returns data

        Returns:
            Dictionary of tilted weights
        """
        bl_config = self.config.get("black_litterman", {})
        views = bl_config.get("views", [])

        tilted_weights = weights.copy()

        for view in views:
            if "TQQQ" in view.get("assets", []):
                confidence = view.get("confidence", 0.5)
                expected_return = view.get("expected_return", 0.1)

                # Tilt direction depends on expected return
                if expected_return > 0:
                    # Bullish view: increase TQQQ weight
                    tilt_amount = confidence * 0.1  # Max 10% tilt
                    tilted_weights["TQQQ"] += tilt_amount
                else:
                    # Bearish view: decrease TQQQ weight
                    tilt_amount = confidence * 0.1  # Max 10% tilt
                    tilted_weights["TQQQ"] -= tilt_amount

                # Adjust other weights proportionally to maintain sum = 1
                total_tilt = tilted_weights["TQQQ"] - weights["TQQQ"]
                if total_tilt != 0:
                    other_assets = [
                        asset for asset in tilted_weights if asset != "TQQQ"
                    ]
                    other_total = sum(weights[asset] for asset in other_assets)

                    for asset in other_assets:
                        if other_total > 0:
                            weight_ratio = weights[asset] / other_total
                            tilted_weights[asset] = weights[asset] - (
                                total_tilt * weight_ratio
                            )

        return tilted_weights

    def _apply_volatility_targeting(
        self, weights: dict[str, float], returns: pd.DataFrame
    ) -> dict[str, float]:
        """
        Apply volatility targeting at portfolio level.

        Args:
            weights: Input weights
            returns: Historical returns data

        Returns:
            Dictionary of volatility-targeted weights
        """
        vol_config = self.config.get("volatility_targeting", {})
        target_vol = vol_config.get("target_vol", 0.15)
        lookback = vol_config.get("lookback_period", 60)

        # Calculate portfolio volatility
        recent_returns = returns.tail(lookback)
        cov_matrix = recent_returns.cov() * 252  # Annualized

        # Convert weights dict to array
        weight_array = np.array([weights.get(asset, 0) for asset in self.assets])

        # Calculate portfolio volatility
        portfolio_vol = np.sqrt(
            np.dot(
                weight_array.T,
                np.dot(cov_matrix.loc[self.assets, self.assets], weight_array),
            )
        )

        # Scale weights to target volatility
        if portfolio_vol > 0:
            scaling_factor = target_vol / portfolio_vol
            scaled_weights = weight_array * scaling_factor
        else:
            scaled_weights = weight_array

        # Apply leverage constraints
        max_leverage = self.config.get("risk_controls", {}).get("max_leverage", 3.0)
        total_leverage = np.sum(np.abs(scaled_weights))

        if total_leverage > max_leverage:
            scaled_weights = scaled_weights * (max_leverage / total_leverage)

        return dict(zip(self.assets, scaled_weights, strict=False))
