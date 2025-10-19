# Equity Convex Rate Hedge Strategy

## Overview

The Equity Convex Rate Hedge strategy combines a TQQQ-centric equity engine with a convex rate hedge using PFIX and gold diversification. This approach uses regime-switch risk budgeting based on stock-bond correlation to optimize the allocation between rate protection and other diversifiers.

## Assets

- **TQQQ** (60% base): ProShares UltraPro QQQ - 3x leveraged NASDAQ-100 equity engine
- **PFIX** (20% base): Simplify Interest Rate Hedge ETF - convex to rising long rates and rate volatility
- **IAU** (15% base): iShares Gold Trust - diversification, especially when stocks and bonds move together
- **SGOV** (5% base): iShares 0-3 Month Treasury Bond ETF - cash shock absorber

## Algorithm

### Regime-Switch Risk Budget

The strategy uses a regime-switch approach for the bond/rate sleeve:

1. **Positive Stock-Bond Correlation Regime** (correlation > 0):
   - Increase PFIX weight (primary hedge)
   - Reduce gold allocation slightly
   - Maintain TQQQ overweight

2. **Negative Stock-Bond Correlation Regime** (correlation ≤ 0):
   - Reduce PFIX weight
   - Allow some duration exposure
   - Slightly increase TQQQ allocation
   - Increase cash allocation

### Volatility Targeting

- Portfolio-level volatility targeting at 15% annualized
- 60-day lookback for volatility calculations
- Scaling factor capped at 2x maximum leverage
- Cash (SGOV) excluded from volatility scaling as shock absorber

### Rebalancing

- Monthly rebalancing with 10-point drift bands
- Correlation regime guard for bond/rate hedges
- 252-day lookback for stock-bond correlation calculations

## Rationale

1. **PFIX Convexity**: PFIX provides convex exposure to rising long rates and rate volatility, offering protection when traditional bonds may underperform.

2. **Gold Diversification**: Gold's equity correlation is near zero in calm times and turns negative in stress, providing valuable diversification especially when stocks and bonds move together.

3. **Regime Awareness**: The strategy adapts to changing stock-bond correlation regimes, optimizing the mix between rate protection and other diversifiers.

4. **Volatility Management**: Portfolio-level volatility targeting helps manage risk across different market conditions while maintaining expected returns.

## Configuration Parameters

Key configurable parameters in `config.yaml`:

- `target_volatility`: 15% annualized volatility target
- `correlation_threshold`: 0.0 for regime switching
- `volatility_lookback`: 60 days
- `correlation_lookback`: 252 days
- Base weights for each asset class

## Risk Management

- Maximum leverage capped at 2x
- Minimum cash allocation of 5%
- Drift band monitoring for rebalancing triggers
- Correlation regime switching to adapt to market conditions

## Expected Performance Characteristics

- **Return Profile**: TQQQ-driven returns with rate hedge protection
- **Volatility**: Targeted 15% annualized through volatility scaling
- **Drawdown Protection**: PFIX convexity and gold diversification in stress scenarios
- **Inflation Sensitivity**: Positive exposure to rising rate environments

## Implementation Notes

This strategy is designed to provide equity-like returns with enhanced protection against rising interest rates and market stress scenarios. The regime-switch approach allows the strategy to adapt to changing market conditions while maintaining a consistent risk profile through volatility targeting.