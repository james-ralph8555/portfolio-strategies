# Equity Inflation Beta Strategy

## Overview

TQQQ strategy with inflation protection via commodities and gold. This strategy combines leveraged equity exposure with inflation-sensitive assets using a two-signal approach (trend + carry) layered on a risk-parity foundation, providing enhanced returns during inflationary environments while maintaining equity-like performance.

## Research Background

The strategy is based on extensive research showing that commodities improve diversification and deliver strong performance during high or rising inflation periods. AQR's research on building better commodities portfolios demonstrates that combining trend and carry signals enhances risk-adjusted returns. PDBC provides liquid, tax-efficient commodity exposure without K-1 tax forms.

### Key Research Findings

- **Commodities in Inflation**: Commodities historically perform well during high and rising inflation periods
- **Trend + Carry Signals**: Combining trend-following with carry analysis improves commodity returns (AQR Capital Management)
- **Risk Parity in Commodities**: Risk parity allocation between commodity sectors provides better diversification
- **Gold as Inflation Hedge**: Gold provides additional inflation protection and crisis alpha

## Assets

- **Core**: TQQQ (3x Nasdaq) - Primary return engine with leveraged equity exposure
- **Commodities**: PDBC (broad commodities, no K-1) - Inflation beta and diversification
- **Gold**: IAU - Additional inflation protection and crisis alpha
- **Cash**: SGOV - Shock absorber and volatility management tool

## Mathematical Framework

### Two-Signal Model

The commodity allocation uses combined trend and carry signals:

```
S_commodity = α * S_trend + (1-α) * S_carry
```

Where:

- S_trend = trend signal based on price momentum
- S_carry = carry signal based on term structure
- α = signal weighting parameter (typically 0.5-0.7)

#### Trend Signal Calculation

```
S_trend = sign(P_t / P_{t-lookback} - 1)
```

Using 12-month lookback for trend detection.

#### Carry Signal Calculation

```
S_carry = (F_{t+1} - P_t) / P_t
```

Where F\_{t+1} is the next-month futures price and P_t is the spot price.

### Risk Parity Allocation

Between gold and commodities using equal risk contribution:

```
w_i = (1/σ_i) / [(1/σ_gold) + (1/σ_commodities)]
```

Where σ_i is the volatility of each asset class.

### Portfolio Volatility Scaling

```
λ = min(σ_target / σ_portfolio, λ_max)
w_final = λ * w_base
```

With target volatility of 12-18% annualized.

## Algorithm

1. **Two-signal tilt** (trend + carry) on diversifiers

   - Calculate trend signals using 12-month price momentum
   - Calculate carry signals from futures term structure
   - Combine signals with optimal weighting

2. **Risk-parity base** between gold and commodities

   - Equal risk contribution allocation
   - Dynamic rebalancing based on volatility changes

3. **Structural TQQQ overweight** scaled by portfolio vol

   - Maintain higher TQQQ allocation for return enhancement
   - Scale overall portfolio to target volatility

4. **Monthly rebalancing** with drift bands
   - 10-point drift bands for trading efficiency
   - Signal updates on monthly basis

## Signal Implementation Details

### Trend Signal

- 12-month exponential moving average crossover
- Signal strength: -1 (strong downtrend) to +1 (strong uptrend)
- Applied to individual commodity sectors within PDBC

### Carry Signal

- Roll yield calculation for commodity futures
- Normalized across commodity sectors
- Positive carry indicates backwardation (bullish)

### Signal Combination

- Dynamic weighting based on signal confidence
- Risk-adjusted position sizing
- Sector rotation within commodity allocation

## Implementation Status

- [ ] Trend signal calculation
- [ ] Carry signal calculation
- [ ] Risk-parity implementation
- [ ] Volatility scaling
- [ ] Rebalancing logic
- [ ] Sector rotation within PDBC

## Configuration Parameters

- `target_volatility`: 12-18% annualized
- `trend_lookback`: 12 months
- `signal_weighting`: α parameter for trend/carry mix
- `drift_bands`: 10% rebalancing threshold
- `tqqq_overweight`: Structural overweight factor

## Expected Performance Characteristics

- **Inflation Sensitivity**: Positive exposure during high inflation periods
- **Return Profile**: TQQQ-driven with commodity enhancement
- **Diversification**: Low correlation to traditional 60/40 portfolios
- **Volatility**: Targeted 12-18% through systematic scaling

## Risk Management

- Maximum leverage constraints
- Signal validation and confidence weighting
- Drawdown controls for commodity positions
- Correlation monitoring between assets

## References

- [AQR Building a Better Commodities Portfolio](https://www.aqr.com/-/media/AQR/Documents/Whitepapers/Building-a-Better-Commodities-Portfolio.pdf)
- [PDBC ETF Information](https://www.invesco.com/us/financial-products/etfs/product-detail?ticker=PDBC)
- [Commodities as Inflation Hedge - AQR Research](https://www.aqr.com/Insights/Research)
- [Trend Following in Commodity Markets - Academic Research](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2860185)
