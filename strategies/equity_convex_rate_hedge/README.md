# Equity Convex Rate Hedge Strategy

## Overview

The Equity Convex Rate Hedge strategy combines a TQQQ-centric equity engine with a convex rate hedge using PFIX and gold diversification. This approach uses regime-switch risk budgeting based on stock-bond correlation to optimize the allocation between rate protection and other diversifiers, providing enhanced protection against rising interest rates while maintaining equity-like returns.

## Research Background

This strategy is grounded in research showing that the stock-bond correlation regime is a critical factor in portfolio construction. When stocks and bonds move together (positive correlation), traditional diversification fails, and alternative hedges like rate protection become more valuable. PFIX provides convex exposure to rising rates that linear instruments cannot match.

### Key Research Findings

- **Stock-Bond Correlation Regimes**: The correlation between stocks and bonds shifts over time, affecting optimal hedge allocation (AQR Capital Management)
- **Convex Rate Protection**: Payer swaption ETFs like PFIX offer convex exposure to rising rates and rate volatility
- **Gold in Stress Scenarios**: Gold provides diversification especially when stocks and bonds move together
- **Regime-Switch Allocation**: Dynamic allocation based on correlation regimes improves risk-adjusted returns

## Assets

- **TQQQ** (60% base): ProShares UltraPro QQQ - 3x leveraged NASDAQ-100 equity engine
- **PFIX** (20% base): Simplify Interest Rate Hedge ETF - convex to rising long rates and rate volatility
- **IAU** (15% base): iShares Gold Trust - diversification, especially when stocks and bonds move together
- **SGOV** (5% base): iShares 0-3 Month Treasury Bond ETF - cash shock absorber

## Mathematical Framework

### Regime-Switch Risk Budget

The allocation adapts based on stock-bond correlation ρ_SB:

```
If ρ_SB > 0 (Positive Correlation Regime):
  w_PFIX = w_base_PFIX + Δw_positive
  w_IAU = w_base_IAU - Δw_positive/2
  w_TQQQ = w_base_TQQQ

If ρ_SB ≤ 0 (Negative Correlation Regime):
  w_PFIX = w_base_PFIX - Δw_negative
  w_TMQF = w_duration_allowed (if applicable)
  w_TQQQ = w_base_TQQQ + Δw_negative/2
  w_SGOV = w_base_SGOV + Δw_negative/2
```

Where Δw represents the regime-specific allocation adjustments.

### Volatility Targeting

Portfolio volatility scaling:

```
σ_portfolio = √(w'Σw)
λ = min(σ_target / σ_portfolio, λ_max)
w_scaled = λ * w_regime
```

Where:

- Σ = covariance matrix
- λ = scaling factor (capped at λ_max = 2.0)
- σ_target = 15% annualized

### Correlation Regime Detection

Rolling correlation calculation:

```
ρ_SB(t) = Corr(r_stock(t-252:t), r_bond(t-252:t))
```

Using 252-day rolling window for regime determination.

## Algorithm

### Regime-Switch Risk Budget

The strategy uses a regime-switch approach for the bond/rate sleeve:

1. **Positive Stock-Bond Correlation Regime** (correlation > 0):

   - Increase PFIX weight (primary hedge)
   - Reduce gold allocation slightly
   - Maintain TQQQ overweight

2. **Negative Stock-Bond Correlation Regime** (correlation ≤ 0):
   - Reduce PFIX weight
   - Allow some duration exposure (TMF if available)
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

1. **PFIX Convexity**: PFIX provides convex exposure to rising long rates and rate volatility, offering protection when traditional bonds may underperform. The payer swaption structure provides asymmetric payoff profiles.

2. **Gold Diversification**: Gold's equity correlation is near zero in calm times and turns negative in stress, providing valuable diversification especially when stocks and bonds move together.

3. **Regime Awareness**: The strategy adapts to changing stock-bond correlation regimes, optimizing the mix between rate protection and other diversifiers based on market conditions.

4. **Volatility Management**: Portfolio-level volatility targeting helps manage risk across different market conditions while maintaining expected returns through systematic scaling.

## Configuration Parameters

Key configurable parameters in `config.yaml`:

- `target_volatility`: 15% annualized volatility target
- `correlation_threshold`: 0.0 for regime switching
- `volatility_lookback`: 60 days
- `correlation_lookback`: 252 days
- Base weights for each asset class
- `max_leverage`: 2.0 maximum scaling factor

## Risk Management

- Maximum leverage capped at 2x
- Minimum cash allocation of 5%
- Drift band monitoring for rebalancing triggers
- Correlation regime switching to adapt to market conditions
- Convex payoff structures to protect against rate shocks

## Expected Performance Characteristics

- **Return Profile**: TQQQ-driven returns with rate hedge protection
- **Volatility**: Targeted 15% annualized through volatility scaling
- **Drawdown Protection**: PFIX convexity and gold diversification in stress scenarios
- **Inflation Sensitivity**: Positive exposure to rising rate environments
- **Regime Adaptation**: Dynamic allocation based on stock-bond correlation

## Implementation Notes

This strategy is designed to provide equity-like returns with enhanced protection against rising interest rates and market stress scenarios. The regime-switch approach allows the strategy to adapt to changing market conditions while maintaining a consistent risk profile through volatility targeting. The convex nature of PFIX provides asymmetric protection against rate spikes that traditional linear hedges cannot match.

## References

- [Simplify PFIX ETF](https://www.simplify.us/etfs/pfix-simplify-interest-rate-hedge-etf)
- [AQR Stock-Bond Correlation Research](https://www.aqr.com/Insights/Research/Journal-Article/A-Changing-Stock-Bond-Correlation)
- [AQR Changing Stock-Bond Correlation](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/A-Changing-Stock-Bond-Correlation_JPM.pdf)
- [Rate Hedge Convexity Research](https://www.simplify.us/etfs/pfix-simplify-interest-rate-hedge-etf)
