"""
Equity Engine + Inflation Beta Strategy

Assets: TQQQ + PDBC (broad commodities) + Gold + Cash
Algorithm: Two-signal tilt on diversifiers with risk-parity base
"""

import numpy as np
import pandas as pd

from core.interfaces.strategy import Strategy


class EquityInflationBetaStrategy(Strategy):
    """
    TQQQ strategy with inflation protection via commodities.

    Uses two-signal tilt (trend + carry) on diversifiers with
    risk-parity base between gold and commodities.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize the strategy with configuration parameters.

        Args:
            config: Strategy-specific configuration dictionary
        """
        super().__init__(config)
        self.name = "equity_inflation_beta"
        self.assets = ["TQQQ", "PDBC", "IAU", "SGOV"]
        self.rebalance_frequency = self.config.get("rebalancing", {}).get(
            "frequency", "monthly"
        )
        self.drift_bands = self.config.get("rebalancing", {}).get("drift_bands", 10)

    def calculate_weights(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate target weights based on two-signal tilt and risk parity.

        Args:
            data: Market data with returns and signals

        Returns:
            Dictionary of target weights for each asset
        """
        # Get configuration parameters
        trend_weight = (
            self.config.get("signals", {}).get("trend", {}).get("weight", 0.6)
        )
        carry_weight = (
            self.config.get("signals", {}).get("carry", {}).get("weight", 0.4)
        )
        tqqq_base_weight = self.config.get("tqqq_overweight", {}).get(
            "base_weight", 0.6
        )
        scaling_factor = self.config.get("tqqq_overweight", {}).get(
            "scaling_factor", 1.2
        )

        # Calculate signals for diversifiers (PDBC and IAU)
        trend_signals = self.calculate_trend_signal(data)
        carry_signals = self.calculate_carry_signal(data)

        # Combine signals for diversifiers
        diversifier_signals = {}
        for asset in ["PDBC", "IAU"]:
            trend_sig = trend_signals.get(asset, 0)
            carry_sig = carry_signals.get(asset, 0)
            diversifier_signals[asset] = (
                trend_weight * trend_sig + carry_weight * carry_sig
            )

        # Apply risk parity between commodities and gold
        risk_parity_weights = self._calculate_risk_parity_weights(data, ["PDBC", "IAU"])

        # Calculate diversifier weights with signal tilt
        diversifier_weights = {}
        for asset in ["PDBC", "IAU"]:
            base_weight = risk_parity_weights[asset]
            signal_tilt = 0.5 * (
                1 + diversifier_signals[asset]
            )  # Scale signal to [0, 1]
            diversifier_weights[asset] = base_weight * signal_tilt

        # Normalize diversifier weights
        total_diversifier_weight = sum(diversifier_weights.values())
        if total_diversifier_weight > 0:
            for asset in diversifier_weights:
                diversifier_weights[asset] /= total_diversifier_weight

        # Calculate TQQQ weight with volatility scaling
        portfolio_vol = self._calculate_portfolio_volatility(data)
        vol_scale = (
            min(scaling_factor, max(0.5, 0.15 / portfolio_vol))
            if portfolio_vol > 0
            else 1.0
        )
        tqqq_weight = tqqq_base_weight * vol_scale

        # Normalize diversifier weights to fit within remaining allocation
        remaining_for_diversifiers = 1.0 - tqqq_weight
        if remaining_for_diversifiers > 0 and sum(diversifier_weights.values()) > 0:
            # Scale down diversifier weights to fit
            total_diversifier = sum(diversifier_weights.values())
            for asset in diversifier_weights:
                diversifier_weights[asset] = (
                    diversifier_weights[asset] / total_diversifier
                ) * remaining_for_diversifiers

        # Calculate cash weight
        total_risk_weight = tqqq_weight + sum(diversifier_weights.values())
        cash_weight = max(0, 1.0 - total_risk_weight)

        # Return final weights
        weights = {
            "TQQQ": tqqq_weight,
            "PDBC": diversifier_weights.get("PDBC", 0),
            "IAU": diversifier_weights.get("IAU", 0),
            "SGOV": cash_weight,
        }

        return self.postprocess_weights(weights)

    def calculate_trend_signal(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate trend signals for diversifiers.

        Args:
            data: Historical price data

        Returns:
            Dictionary of trend signals
        """
        lookback_periods = (
            self.config.get("signals", {})
            .get("trend", {})
            .get("lookback_periods", [20, 60, 120])
        )
        signals = {}

        for asset in ["PDBC", "IAU"]:
            if asset in data.columns:
                asset_signals = []
                for period in lookback_periods:
                    if len(data) >= period:
                        returns = data[asset].pct_change(period)
                        signal = (
                            np.sign(returns.iloc[-1])
                            if not pd.isna(returns.iloc[-1])
                            else 0
                        )
                        asset_signals.append(signal)

                # Average signals across timeframes
                signals[asset] = np.mean(asset_signals) if asset_signals else 0
            else:
                signals[asset] = 0

        return signals

    def calculate_carry_signal(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate carry signals for commodities.

        Args:
            data: Market data for carry calculation

        Returns:
            Dictionary of carry signals
        """
        signals = {}

        for asset in ["PDBC", "IAU"]:
            if asset in data.columns:
                # Simple carry signal using momentum and term structure
                # For commodities: positive carry if recent performance > long-term performance
                if len(data) >= 60:
                    short_term_return = data[asset].pct_change(20).iloc[-1]
                    long_term_return = data[asset].pct_change(60).iloc[-1]

                    # Positive carry if short-term > long-term
                    carry_signal = np.sign(short_term_return - long_term_return)
                    signals[asset] = carry_signal if not pd.isna(carry_signal) else 0
                else:
                    signals[asset] = 0
            else:
                signals[asset] = 0

        return signals

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
        for asset in self.assets:
            current_weight = current_weights.get(asset, 0)
            target_weight = target_weights.get(asset, 0)

            # Check if drift exceeds bands
            drift = abs(current_weight - target_weight)
            if drift > (self.drift_bands / 100.0):
                return True

        return False

    def validate_config(self) -> bool:
        """
        Validate strategy configuration.

        Returns:
            True if configuration is valid
        """
        required_keys = [
            "assets",
            "signals",
            "risk_parity",
            "tqqq_overweight",
            "volatility_targeting",
            "rebalancing",
        ]

        for key in required_keys:
            if key not in self.config:
                return False

        # Validate signal weights sum to 1
        trend_weight = self.config.get("signals", {}).get("trend", {}).get("weight", 0)
        carry_weight = self.config.get("signals", {}).get("carry", {}).get("weight", 0)

        if abs(trend_weight + carry_weight - 1.0) > 0.01:
            return False

        # Validate assets
        required_assets = ["TQQQ", "PDBC", "IAU", "SGOV"]
        config_assets = list(self.config.get("assets", {}).values())

        for asset in required_assets:
            if asset not in config_assets:
                return False

        return True

    def _calculate_risk_parity_weights(
        self, data: pd.DataFrame, assets: list[str]
    ) -> dict[str, float]:
        """
        Calculate risk parity weights between assets.

        Args:
            data: Market data
            assets: List of assets for risk parity calculation

        Returns:
            Dictionary of risk parity weights
        """
        lookback_period = self.config.get("risk_parity", {}).get("lookback_period", 60)
        weights = {}

        if len(data) < lookback_period:
            # Equal weights if insufficient data
            equal_weight = 1.0 / len(assets)
            return dict.fromkeys(assets, equal_weight)

        # Calculate volatilities
        volatilities = {}
        for asset in assets:
            if asset in data.columns:
                returns = data[asset].pct_change().dropna()
                if len(returns) >= lookback_period:
                    vol = returns.tail(lookback_period).std() * np.sqrt(
                        252
                    )  # Annualized
                    volatilities[asset] = (
                        vol if vol > 0 else 0.15
                    )  # Default vol if zero
                else:
                    volatilities[asset] = 0.15
            else:
                volatilities[asset] = 0.15

        # Risk parity weights: inversely proportional to volatility
        inv_vols = {asset: 1.0 / vol for asset, vol in volatilities.items()}
        total_inv_vol = sum(inv_vols.values())

        if total_inv_vol > 0:
            weights = {
                asset: inv_vol / total_inv_vol for asset, inv_vol in inv_vols.items()
            }
        else:
            # Equal weights fallback
            equal_weight = 1.0 / len(assets)
            weights = dict.fromkeys(assets, equal_weight)

        return weights

    def _calculate_portfolio_volatility(self, data: pd.DataFrame) -> float:
        """
        Calculate portfolio volatility for volatility targeting.

        Args:
            data: Market data

        Returns:
            Portfolio volatility estimate
        """
        lookback_period = self.config.get("volatility_targeting", {}).get(
            "lookback_period", 60
        )

        if len(data) < lookback_period:
            return 0.15  # Default volatility

        # Use TQQQ as proxy for portfolio volatility
        if "TQQQ" in data.columns:
            returns = data["TQQQ"].pct_change().dropna()
            if len(returns) >= lookback_period:
                vol = returns.tail(lookback_period).std() * np.sqrt(252)
                return vol if vol > 0 else 0.15

        return 0.15  # Default volatility
