"""
Equity Engine + Barbell of Vol Premia and Tail Strategy

Assets: TQQQ + SVOL (short-VIX) + TAIL (S&P put ladder) + Cash
Algorithm: Barbell allocator with drawdown-triggered scaling
"""

import pandas as pd

from core.interfaces.strategy import Strategy


class EquityVolBarbellStrategy(Strategy):
    """
    TQQQ strategy with volatility premium harvesting and tail protection.

    Uses barbell approach with high TQQQ weight, short-vol income sleeve,
    and crisis convexity sleeve with drawdown-triggered scaling.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize the strategy with configuration parameters.

        Args:
            config: Strategy-specific configuration dictionary
        """
        super().__init__(config)
        self.name = "equity_vol_barbell"
        self.assets = ["TQQQ", "SVOL", "TAIL", "SGOV"]
        self.rebalance_frequency = self.config.get("rebalancing", {}).get(
            "frequency", "monthly"
        )
        self.drift_bands = self.config.get("rebalancing", {}).get("drift_bands", 10)

    def calculate_weights(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Calculate target weights based on barbell allocation.

        Args:
            data: Market data with volatility and drawdown metrics

        Returns:
            Dictionary of target weights for each asset
        """
        # Get base allocation from config
        barbell_config = self.config.get("barbell_allocation", {})
        tqqq_base = barbell_config.get("tqqq_base_weight", 0.7)
        short_vol = barbell_config.get("short_vol_weight", 0.15)
        tail_hedge = barbell_config.get("tail_hedge_weight", 0.1)
        barbell_config.get("cash_weight", 0.05)

        # Calculate drawdown-triggered TQQQ scaling
        tqqq_scaling = self.calculate_drawdown_trigger(data)
        tqqq_weight = tqqq_base * tqqq_scaling

        # Size volatility sleeves
        vol_sleeves = self.size_vol_sleeves(data)
        svol_weight = min(
            vol_sleeves.get("SVOL", short_vol) or short_vol,
            self.config.get("vol_sizing", {}).get("svol_max_weight", 0.2),
        )
        tail_weight = min(
            vol_sleeves.get("TAIL", tail_hedge) or tail_hedge,
            self.config.get("vol_sizing", {}).get("tail_max_weight", 0.15),
        )

        # Calculate remaining weight for cash
        total_allocated = tqqq_weight + svol_weight + tail_weight
        cash_weight = max(0.0, 1.0 - total_allocated)

        return {
            "TQQQ": tqqq_weight,
            "SVOL": svol_weight,
            "TAIL": tail_weight,
            "SGOV": cash_weight,
        }

    def calculate_drawdown_trigger(self, data: pd.DataFrame) -> float:
        """
        Calculate drawdown-based scaling factor for TQQQ.

        Args:
            data: Market data with price history

        Returns:
            Scaling factor for TQQQ allocation
        """
        drawdown_config = self.config.get("drawdown_triggers", {})
        vol_spike_threshold = drawdown_config.get("volatility_spike_threshold", 2.0)
        max_drawdown_threshold = drawdown_config.get("max_drawdown_threshold", 0.15)
        scaling_factor = drawdown_config.get("tqqq_scaling_factor", 0.5)

        # Calculate current drawdown (assuming data has cumulative returns)
        if "TQQQ" in data.columns:
            tqqq_prices = data["TQQQ"]
            peak = tqqq_prices.expanding().max()
            drawdown = (tqqq_prices - peak) / peak
            current_drawdown = drawdown.iloc[-1] if len(drawdown) > 0 else 0
        else:
            current_drawdown = 0

        # Calculate volatility spike (using returns volatility)
        if "TQQQ" in data.columns:
            returns = data["TQQQ"].pct_change().dropna()
            current_vol = (
                returns.rolling(20).std().iloc[-1]
                if len(returns) > 20
                else returns.std()
            )
            historical_vol = returns.std()
            vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1
        else:
            vol_ratio = 1

        # Apply scaling if triggers are hit
        if (
            current_drawdown < -max_drawdown_threshold
            or vol_ratio > vol_spike_threshold
        ):
            return scaling_factor

        return 1.0

    def size_vol_sleeves(self, data: pd.DataFrame) -> dict[str, float]:
        """
        Size the volatility premium and tail protection sleeves.

        Args:
            data: Market data with VIX term structure

        Returns:
            Dictionary of sleeve weights
        """
        vol_config = self.config.get("vol_sizing", {})
        vix_threshold = vol_config.get("vix_term_structure_threshold", 0.1)

        # Default base weights
        svol_base = self.config.get("barbell_allocation", {}).get(
            "short_vol_weight", 0.15
        )
        tail_base = self.config.get("barbell_allocation", {}).get(
            "tail_hedge_weight", 0.1
        )

        # Adjust SVOL based on VIX term structure (if VIX data available)
        if "VIX" in data.columns:
            vix_current = data["VIX"].iloc[-1]
            vix_ma = (
                data["VIX"].rolling(50).mean().iloc[-1]
                if len(data) > 50
                else data["VIX"].mean()
            )
            vix_ratio = vix_current / vix_ma if vix_ma > 0 else 1

            # Reduce SVOL when VIX is elevated (contango less favorable)
            if vix_ratio > (1 + vix_threshold):
                svol_weight = svol_base * 0.5
            else:
                svol_weight = svol_base
        else:
            svol_weight = svol_base

        # Adjust TAIL based on market stress (higher weight in stress)
        if "VIX" in data.columns:
            vix_percentile = (
                data["VIX"].rolling(252).rank(pct=True).iloc[-1]
                if len(data) > 252
                else 0.5
            )
            # Increase tail hedge when VIX is in upper quartile
            if vix_percentile > 0.75:
                tail_weight = tail_base * 1.5
            else:
                tail_weight = tail_base
        else:
            tail_weight = tail_base

        return {"SVOL": svol_weight, "TAIL": tail_weight}

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
        # Check required configuration sections
        required_sections = [
            "barbell_allocation",
            "drawdown_triggers",
            "vol_sizing",
            "rebalancing",
        ]
        for section in required_sections:
            if section not in self.config:
                return False

        # Validate barbell allocation sums to 1
        barbell = self.config.get("barbell_allocation", {})
        total = (
            barbell.get("tqqq_base_weight", 0)
            + barbell.get("short_vol_weight", 0)
            + barbell.get("tail_hedge_weight", 0)
            + barbell.get("cash_weight", 0)
        )

        if abs(total - 1.0) > 0.01:  # Allow small rounding error
            return False

        # Validate weights are between 0 and 1
        for _key, value in barbell.items():
            if not (0 <= value <= 1):
                return False

        return True
