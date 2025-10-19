"""
Risk Parity Strategy

Modern implementation of risk parity allocation between leveraged equity and bond ETFs.
Based on the legacy riskparity.py script with improvements for the modern framework.

Assets: TQQQ (3x NASDAQ-100) + TMF (3x Long-term Treasury)
Algorithm: Risk parity optimization with equal risk contributions
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from core.interfaces.strategy import Strategy


class RiskParityStrategy(Strategy):
    """
    Risk parity strategy using leveraged ETFs.

    Allocates between TQQQ and TMF based on risk contributions rather than
    capital allocations, ensuring each asset contributes equally to portfolio risk.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize the risk parity strategy.

        Args:
            config: Strategy-specific configuration dictionary
        """
        super().__init__(config)
        self.name = "risk_parity"
        self.assets = ["TQQQ", "TMF"]
        self.rebalance_frequency = self.config.get("rebalancing", {}).get(
            "frequency", "monthly"
        )
        self.drift_bands = self.config.get("rebalancing", {}).get("drift_bands", 5)

        # Risk parity parameters
        self.risk_budget = self.config.get("risk_parity", {}).get(
            "risk_budget", {"equity": 0.75, "bond": 0.25}
        )
        self.lookback_period = self.config.get("risk_parity", {}).get(
            "lookback_period", 90
        )
        self.tolerance = (
            self.config.get("risk_parity", {})
            .get("optimization", {})
            .get("tolerance", 1e-10)
        )

        # Risk management
        self.max_leverage = self.config.get("risk_management", {}).get(
            "max_leverage", 3.0
        )
        self.volatility_target = self.config.get("risk_management", {}).get(
            "volatility_target", 0.15
        )

    def calculate_weights(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate risk parity weights for TQQQ and TMF.

        Args:
            data: Market data with price history for assets

        Returns:
            Dictionary mapping asset symbols to target weights
        """
        # Ensure we have the required assets
        required_assets = ["TQQQ", "TMF"]
        for asset in required_assets:
            if asset not in data.columns:
                raise ValueError(f"Required asset {asset} not found in data")

        # Calculate returns using the lookback period
        returns_data = (
            data[required_assets]
            .iloc[-self.lookback_period :]
            .pct_change(fill_method=None)
            .dropna()
        )

        if len(returns_data) < 10:  # Need minimum data for robust covariance
            # Fall back to equal weights if insufficient data
            equal_weight = 1.0 / len(required_assets)
            return dict.fromkeys(required_assets, equal_weight)

        # Calculate annualized covariance matrix
        cov_matrix = returns_data.cov() * 252  # Annualize

        # Convert risk budget to array
        risk_budget_array = np.array(
            [self.risk_budget.get("equity", 0.75), self.risk_budget.get("bond", 0.25)]
        )

        # Initial equal weights
        initial_weights = np.array([1.0 / len(required_assets)] * len(required_assets))

        # Optimize for risk parity
        try:
            optimal_weights = self._get_risk_parity_weights(
                cov_matrix.values, risk_budget_array, initial_weights
            )
            weights_dict = dict(zip(required_assets, optimal_weights, strict=False))
        except Exception:
            # Fall back to equal weights if optimization fails
            equal_weight = 1.0 / len(required_assets)
            weights_dict = dict.fromkeys(required_assets, equal_weight)

        # Apply risk management constraints
        weights_dict = self._apply_risk_constraints(weights_dict, data)

        return weights_dict

    def _get_risk_parity_weights(
        self,
        covariances: np.ndarray,
        assets_risk_budget: np.ndarray,
        initial_weights: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate risk parity weights using optimization.

        Args:
            covariances: Covariance matrix of asset returns
            assets_risk_budget: Target risk contribution for each asset
            initial_weights: Starting weights for optimization

        Returns:
            Optimal risk parity weights
        """

        def allocation_risk(weights: np.ndarray) -> float:
            """Calculate portfolio risk."""
            return np.sqrt(np.dot(weights.T, np.dot(covariances, weights)))

        def assets_risk_contribution(weights: np.ndarray) -> np.ndarray:
            """Calculate risk contribution of each asset."""
            portfolio_risk = allocation_risk(weights)
            marginal_contrib = np.dot(covariances, weights)
            return np.multiply(weights, marginal_contrib) / portfolio_risk

        def risk_budget_objective(weights: np.ndarray) -> float:
            """Objective function for risk parity optimization."""
            portfolio_risk = allocation_risk(weights)
            assets_risk_contrib = assets_risk_contribution(weights)
            assets_risk_target = portfolio_risk * assets_risk_budget
            return float(np.sum(np.square(assets_risk_contrib - assets_risk_target)))

        # Constraints: weights sum to 1 and are non-negative
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "ineq", "fun": lambda x: x},  # weights >= 0
        ]

        # Bounds for individual weights
        min_weight = (
            self.config.get("risk_parity", {})
            .get("optimization", {})
            .get("min_weight", 0.01)
        )
        max_weight = (
            self.config.get("risk_parity", {})
            .get("optimization", {})
            .get("max_weight", 0.99)
        )
        bounds = [(min_weight, max_weight) for _ in range(len(initial_weights))]

        # Optimize
        result = minimize(
            fun=risk_budget_objective,
            x0=initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            tol=self.tolerance,
            options={"disp": False},
        )

        if result.success:
            return result.x
        else:
            # Return initial weights if optimization fails
            return initial_weights

    def _apply_risk_constraints(
        self, weights: dict[str, float], data: pd.DataFrame
    ) -> dict[str, float]:
        """
        Apply risk management constraints to weights.

        Args:
            weights: Raw calculated weights
            data: Market data for risk calculations

        Returns:
            Adjusted weights respecting risk constraints
        """
        # Calculate current portfolio volatility
        returns_data = (
            data[list(weights.keys())]
            .iloc[-self.lookback_period :]
            .pct_change()
            .dropna()
        )
        if len(returns_data) > 10:
            cov_matrix = returns_data.cov() * 252
            weights_array = np.array(list(weights.values()))
            portfolio_vol = np.sqrt(
                np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
            )

            # Scale down if volatility exceeds target
            if portfolio_vol > self.volatility_target:
                scale_factor = self.volatility_target / portfolio_vol
                weights = {k: v * scale_factor for k, v in weights.items()}

        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def should_rebalance(
        self, current_weights: dict[str, float], target_weights: dict[str, float]
    ) -> bool:
        """
        Determine if rebalancing is required based on drift bands.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target weights from strategy

        Returns:
            True if rebalancing should occur
        """
        # Check drift bands for each asset
        for asset in self.assets:
            current = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)

            if abs(current - target) > (self.drift_bands / 100):
                return True

        return False

    def validate_config(self) -> bool:
        """
        Validate strategy configuration.

        Returns:
            True if configuration is valid
        """
        # Check risk budget sums to 1
        risk_budget = self.config.get("risk_parity", {}).get("risk_budget", {})
        total_risk = risk_budget.get("equity", 0) + risk_budget.get("bond", 0)

        if abs(total_risk - 1.0) > 0.01:  # Allow small rounding error
            return False

        # Validate risk budget values are between 0 and 1
        for _key, value in risk_budget.items():
            if not (0 <= value <= 1):
                return False

        # Check required configuration sections
        required_sections = ["risk_parity", "risk_management", "rebalancing"]
        for section in required_sections:
            if section not in self.config:
                return False

        return True

    def get_portfolio_metrics(
        self, data: pd.DataFrame, weights: dict[str, float]
    ) -> dict[str, float]:
        """
        Calculate portfolio metrics.

        Args:
            data: Market data
            weights: Portfolio weights

        Returns:
            Dictionary with portfolio metrics
        """
        # Calculate returns using the lookback period
        returns_data = (
            data[list(weights.keys())]
            .iloc[-self.lookback_period :]
            .pct_change()
            .dropna()
        )

        if len(returns_data) < 10:
            return {"volatility": 0.0, "risk_parity_error": 1.0}

        # Calculate covariance matrix
        cov_matrix = returns_data.cov() * 252
        weights_array = np.array(list(weights.values()))

        # Portfolio volatility
        portfolio_vol = np.sqrt(
            np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        )

        # Risk contributions
        marginal_contrib = np.dot(cov_matrix, weights_array)
        risk_contributions = (
            np.multiply(weights_array, marginal_contrib) / portfolio_vol
        )

        return {
            "volatility": float(portfolio_vol),
            "risk_parity_error": self._calculate_risk_parity_error(risk_contributions),
        }

    def update_config(self, new_config: dict) -> None:
        """
        Update strategy configuration and instance attributes.

        Args:
            new_config: New configuration parameters
        """
        self.config.update(new_config)

        # Update instance attributes if they exist in new config
        if "risk_parity" in new_config:
            rp_config = new_config["risk_parity"]
            if "risk_budget" in rp_config:
                self.risk_budget.update(rp_config["risk_budget"])
            if "lookback_period" in rp_config:
                self.lookback_period = rp_config["lookback_period"]
            if "optimization" in rp_config:
                opt_config = rp_config["optimization"]
                if "tolerance" in opt_config:
                    self.tolerance = opt_config["tolerance"]

        if "risk_management" in new_config:
            rm_config = new_config["risk_management"]
            if "max_leverage" in rm_config:
                self.max_leverage = rm_config["max_leverage"]
            if "volatility_target" in rm_config:
                self.volatility_target = rm_config["volatility_target"]

        if "rebalancing" in new_config:
            reb_config = new_config["rebalancing"]
            if "frequency" in reb_config:
                self.rebalance_frequency = reb_config["frequency"]
            if "drift_bands" in reb_config:
                self.drift_bands = reb_config["drift_bands"]

        self.validate_config()

    def _calculate_risk_parity_error(self, risk_contributions: np.ndarray) -> float:
        """
        Calculate how far the current risk contributions deviate from perfect risk parity.

        Args:
            risk_contributions: Current risk contributions

        Returns:
            Error metric (lower is better)
        """
        if len(risk_contributions) < 2:
            return 0

        # Perfect risk parity would have equal contributions
        target_contribution = 1.0 / len(risk_contributions)
        errors = [abs(rc - target_contribution) for rc in risk_contributions]

        return float(np.mean(errors))
