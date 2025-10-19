# Equity Convex Rate Strategy

## Overview

TQQQ strategy with convex rate hedge via PFIX and regime-switching logic. This strategy combines leveraged equity exposure with convex rate protection that adapts based on stock-bond correlation regimes, providing enhanced protection against rising interest rates while maintaining equity-like returns.

## Research Background

This strategy is grounded in research demonstrating that the relationship between stocks and bonds is not static, with correlation regimes significantly impacting optimal portfolio construction. During periods of positive stock-bond correlation, traditional diversification breaks down and convex rate hedges become particularly valuable. PFIX provides asymmetric protection against rising rates through its payer swaption structure.

### Key Research Findings

- **Dynamic Stock-Bond Correlation**: The correlation between equities and bonds shifts over time, affecting optimal hedge allocation (AQR Capital Management)
- **Convex Rate Protection**: Payer swaption ETFs offer convex exposure to rising rates that traditional linear instruments cannot match
- **Regime-Dependent Allocation**: Optimal allocation between rate hedges and other diversifiers depends on correlation regime
- **Expected Return Tilts**: Systematic expected return tilts can enhance portfolio performance while managing risk

## Assets

- **Core**: TQQQ (3x Nasdaq) - Primary return engine with leveraged equity exposure
- **Rate Hedge**: PFIX (payer-swaption ETF) - Convex protection against rising rates
- **Diversifier**: IAU (gold) - Additional diversification, especially in stress scenarios
- **Cash**: SGOV (treasury bills) - Shock absorber and volatility management tool

## Mathematical Framework

### Regime-Switch Allocation Model

Based on stock-bond correlation ρ_SB:

```
If ρ_SB > 0 (Positive Correlation Regime):
  w_PFIX = w_base_PFIX + Δw_positive
  w_IAU = w_base_IAU - Δw_positive/2
  w_TQQQ = w_base_TQQQ + Δw_positive/4
  w_SGOV = w_base_SGOV + Δw_positive/4

If ρ_SB ≤ 0 (Negative Correlation Regime):
  w_PFIX = w_base_PFIX - Δw_negative
  w_TMF = w_duration_allowed (if available)
  w_TQQQ = w_base_TQQQ + Δw_negative/2
  w_SGOV = w_base_SGOV + Δw_negative/2
```

### Expected Return Tilt Implementation

Black-Litterman framework for TQQQ overweight:

```
μ_BL = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) * [(τΣ)^(-1)π + P'Ω^(-1)Q]
```

Where Q represents the view on TQQQ outperformance.

### Volatility Targeting

```
σ_portfolio = √(w'Σw)
λ = min(σ_target / σ_portfolio, λ_max)
w_final = λ * w_regime_adjusted
```

Target volatility: 12-18% annualized, maximum leverage: 2x.

### PFIX Convexity Modeling

PFIX payoff approximation:

```
Payoff_PFIX ≈ max(0, Rate_change - Strike) * Notional
```

Providing convex exposure to rate increases with limited downside.

## Algorithm

1. **Regime-switch risk budget** based on stock-bond correlation

   - Calculate 252-day rolling correlation between stocks and bonds
   - Classify regime based on correlation threshold (typically 0)
   - Adjust allocations according to regime-specific rules

2. **PFIX as primary hedge** when correlation > 0

   - Increase PFIX allocation during positive correlation regimes
   - Reduce traditional duration exposure
   - Maintain convex protection against rate spikes

3. **Allow TMF duration** when correlation < 0

   - Reduce PFIX allocation during negative correlation
   - Introduce traditional duration exposure (TMF if available)
   - Benefit from traditional flight-to-safety behavior

4. **TQQQ overweight** via expected-return tilt

   - Apply Black-Litterman framework with TQQQ outperformance view
   - Maintain structural equity overweight for return enhancement
   - Scale exposure based on volatility targeting

5. **Portfolio volatility targeting**
   - Scale entire portfolio to target 12-18% annualized volatility
   - Use 60-day rolling volatility calculations
   - Apply maximum leverage constraints

## Implementation Status

- [ ] Correlation regime detection
- [ ] Regime-switch allocation logic
- [ ] PFIX convexity modeling
- [ ] Volatility targeting
- [ ] Black-Litterman expected return tilt
- [ ] Rebalancing logic with drift bands

## Configuration Parameters

- `target_volatility`: 12-18% annualized
- `correlation_threshold`: 0.0 for regime switching
- `correlation_lookback`: 252 days
- `volatility_lookback`: 60 days
- `max_leverage`: 2.0
- `base_weights`: Initial allocation weights
- `regime_adjustments`: Δw parameters for regime switching

## Risk Management

- Maximum leverage constraint of 2x
- Minimum cash allocation of 5%
- Regime-based allocation adjustments
- Volatility scaling for risk control
- Convex payoff structures for asymmetric protection

## Expected Performance Characteristics

- **Return Profile**: TQQQ-driven returns with rate hedge protection
- **Rate Sensitivity**: Positive exposure to rising rate environments
- **Regime Adaptation**: Dynamic allocation based on stock-bond correlation
- **Volatility**: Targeted 12-18% through systematic scaling
- **Asymmetric Protection**: Convex payoffs during rate spikes

## Implementation Notes

This strategy differs from the hedge version by focusing more on expected return enhancement through systematic TQQQ overweight while maintaining convex rate protection. The regime-switch approach allows the strategy to adapt to changing market conditions, optimizing the mix between rate protection and traditional diversification based on the stock-bond correlation environment.

## References

- [Simplify PFIX ETF - Convex Rate Hedge](https://www.simplify.us/etfs/pfix-simplify-interest-rate-hedge-etf)
- [AQR Stock-Bond Correlation Research](https://www.aqr.com/Insights/Research/Journal-Article/A-Changing-Stock-Bond-Correlation)
- [AQR Changing Correlation Regimes](https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/A-Changing-Stock-Bond-Correlation_JPM.pdf)
- [Black-Litterman Portfolio Theory](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=171835)
- [Convex Payoff Structures in Rate Hedges](https://www.simplify.us/etfs/pfix-simplify-interest-rate-hedge-etf)
