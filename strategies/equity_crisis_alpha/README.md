# Equity Crisis Alpha Strategy

## Overview
TQQQ-centric strategy with managed futures and gold for crisis alpha protection.

## Assets
- **Core**: TQQQ (3x Nasdaq)
- **Diversifiers**: DBMF/KMLM (managed futures), IAU/GLD (gold)
- **Cash**: SGOV/BIL (treasury bills)

## Algorithm
1. **Leverage-aware Equal Risk Contribution (ERC)**
2. **Black-Litterman tilt** favoring TQQQ
3. **Portfolio-level volatility targeting** (12-18% annualized)
4. **Monthly rebalancing** with 10-point drift bands
5. **Correlation regime guard** for bond/rate hedges

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