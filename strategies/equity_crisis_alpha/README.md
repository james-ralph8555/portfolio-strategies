# Equity Crisis Alpha Strategy

## Overview

TQQQ-centric strategy with managed futures and gold for crisis alpha protection. This strategy combines leveraged equity exposure with uncorrelated sleeves that bias expected returns while controlling left-tail risk through time-series momentum and crisis alpha allocation.

## Research Background

The strategy is based on extensive research showing that time-series momentum works across futures markets, with managed-futures ETFs delivering effective trend exposure. Gold's equity correlation is near zero in calm markets and turns negative during stress periods, providing valuable diversification. Volatility-managed overlays have been shown to increase Sharpe ratios across asset classes.

### Key Research Findings

- **Time-Series Momentum**: Demonstrated to provide positive returns across futures markets with low correlation to traditional assets (AQR Capital Management)
- **Crisis Alpha**: Managed futures strategies tend to perform well during market crises, providing protection when equities suffer
- **Gold Correlation Dynamics**: Gold exhibits near-zero correlation to equities in normal times and negative correlation during market stress
- **Volatility Management**: Portfolio-level volatility targeting improves risk-adjusted returns (Moreira & Muir, 2017)

## Assets

- **Core**: TQQQ (3x Nasdaq) - Primary return engine with leveraged equity exposure
- **Diversifiers**:
  - DBMF/KMLM (managed futures) - Time-series momentum exposure across asset classes
  - IAU (gold) - Crisis alpha and negative correlation during stress
- **Cash**: SGOV (treasury bills) - Shock absorber and volatility management tool

## Mathematical Framework

### Leverage-Aware Equal Risk Contribution (ERC)

The ERC allocation ensures each asset contributes equally to portfolio risk:

```
w_i = (1/σ_i) / Σ(1/σ_j)
```

Where:

- w_i = weight of asset i
- σ_i = volatility of asset i
- The sum is over all assets j

### Black-Litterman Integration

The Black-Litterman model incorporates views about TQQQ outperformance:

```
μ_BL = [(τΣ)^(-1) + P'Ω^(-1)P]^(-1) * [(τΣ)^(-1)π + P'Ω^(-1)Q]
```

Where:

- μ_BL = Black-Litterman expected returns
- τ = scaling parameter
- Σ = covariance matrix
- P = view matrix
- Ω = view uncertainty matrix
- π = equilibrium returns
- Q = view returns

### Volatility Targeting

Portfolio volatility is scaled to target 12-18% annualized:

```
λ = min(σ_target / σ_portfolio, λ_max)
w_scaled = λ * w_target
```

Where:

- λ = scaling factor
- σ_target = target volatility (12-18%)
- σ_portfolio = current portfolio volatility
- λ_max = maximum leverage constraint

## Algorithm

1. **Leverage-aware Equal Risk Contribution (ERC)**

   - Calculate risk contributions accounting for leverage in TQQQ
   - Ensure balanced risk allocation across assets

2. **Black-Litterman tilt** favoring TQQQ

   - Incorporate expected return views for TQQQ outperformance
   - Blend with equilibrium returns for robust allocation

3. **Portfolio-level volatility targeting** (12-18% annualized)

   - Scale entire portfolio to maintain target volatility
   - Use 60-day rolling volatility calculations

4. **Monthly rebalancing** with 10-point drift bands

   - Rebalance when any asset deviates >10% from target weight
   - Reduce transaction costs while maintaining risk profile

5. **Correlation regime guard** for bond/rate hedges
   - Monitor stock-bond correlation for regime changes
   - Adjust allocations based on correlation environment

## Implementation Status

- [ ] Leverage-aware ERC calculation
- [ ] Black-Litterman implementation
- [ ] Volatility targeting
- [ ] Drift band rebalancing logic
- [ ] Correlation regime detection

## Testing

- [ ] Unit tests for weight calculation
- [ ] Integration tests with market data
- [ ] Backtesting framework integration

## References

- [AQR Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum)
- [Volatility Managed Portfolios](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513)
- [AQR Crisis Alpha Research](https://www.aqr.com/Insights/Research)
- [Moreira & Muir (2017) - Volatility-Managed Portfolios](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513)
