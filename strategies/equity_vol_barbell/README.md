# Equity Volatility Barbell Strategy

## Overview

TQQQ strategy with volatility premium harvesting and tail protection. This barbell approach combines high equity exposure with a short-volatility income sleeve and a crisis convexity sleeve, creating asymmetric payoff profiles that harvest volatility premiums while protecting against tail events.

## Research Background

The strategy is based on research showing that the VIX term structure contains a persistent premium that can be harvested through short-volatility positions, but this exposure requires tail protection. The barbell approach maximizes returns during normal markets while providing convex protection during crises. SVOL harvests the VIX term-structure premium while TAIL provides crisis convexity through S&P put ladders.

### Key Research Findings

- **VIX Term Structure Premium**: The VIX futures term structure typically exhibits contango, creating a harvestable premium
- **Volatility Risk Premium**: Investors demand premium for bearing volatility risk, creating systematic returns for short-vol strategies
- **Tail Risk Hedging**: Put ladder structures provide cost-effective tail protection during market crises
- **Barbell Allocation**: Combining high-return assets with tail hedges creates superior risk-adjusted profiles

## Assets

- **Core**: TQQQ (3x Nasdaq) - Primary return engine with leveraged equity exposure
- **Short Vol**: SVOL (short-VIX premium) - Harvests VIX term structure premium
- **Tail Hedge**: TAIL (S&P put ladder) - Crisis convexity and tail protection
- **Cash**: SGOV - Shock absorber and funding source for hedges

## Mathematical Framework

### Barbell Allocation Structure

```
w_TQQQ = w_base + w_return_enhancement
w_SVOL = w_income_sleeve * f(VIX_level, term_structure)
w_TAIL = w_tail_sleeve * g(VIX_stress, correlation)
w_SGOV = 1 - w_TQQQ - w_SVOL - w_TAIL
```

### VIX-Responsive SVOL Sizing

```
SVOL_scale = max(0, 1 - (VIX_current - VIX_median) / (VIX_90th - VIX_median))
w_SVOL = w_SVOL_base * SVOL_scale * contango_factor
```

Where contango_factor accounts for VIX futures term structure.

### Drawdown-Triggered TQQQ Scaling

```
if drawdown > threshold_drawdown OR VIX > threshold_VIX:
    w_TQQQ = w_TQQQ_base * reduction_factor
else:
    w_TQQQ = w_TQQQ_base
```

### Stress-Responsive TAIL Sizing

```
TAIL_scale = min(1, (VIX_current - VIX_75th) / (VIX_90th - VIX_75th))
w_TAIL = w_TAIL_base + w_TAIL_enhancement * TAIL_scale
```

## Algorithm

1. **Barbell allocator** with high TQQQ weight

   - Base allocation with structural TQQQ overweight
   - Dynamic sizing based on market conditions

2. **Short-vol income sleeve** (SVOL) for premium harvesting

   - VIX-responsive position sizing
   - Term structure analysis for optimal entry/exit

3. **Crisis convexity sleeve** (TAIL) for tail protection

   - Stress-responsive sizing based on VIX levels
   - Put ladder structure for cost-effective protection

4. **Drawdown-triggered scaling** to reduce TQQQ in volatility spikes

   - 50% reduction when drawdown > 15% or VIX > 2x normal
   - Systematic risk management during stress periods

5. **Monthly rebalancing** with daily drawdown monitoring
   - 10-point drift bands for trading efficiency
   - Daily monitoring for drawdown triggers

## Implementation Status

- [x] Barbell allocation logic
- [x] Drawdown trigger calculation
- [x] VIX term structure analysis
- [x] Sleeve sizing methodology
- [x] Rebalancing logic

## Key Features

- **Dynamic TQQQ Scaling**: Automatically reduces TQQQ exposure by 50% when drawdown exceeds 15% or volatility spikes 2x normal levels
- **VIX-Responsive SVOL Sizing**: Reduces short-vol exposure when VIX is elevated (unfavorable contango)
- **Stress-Responsive TAIL Sizing**: Increases tail hedge when VIX is in upper quartile of historical range
- **Drift Band Rebalancing**: Rebalances when any asset deviates more than 10% from target weight
- **Configuration Validation**: Ensures all weights sum to 100% and are within valid ranges

## VIX Term Structure Analysis

### Contango Detection

```
contango_ratio = VIX_futures_3M / VIX_spot
contango_factor = max(0, min(1, (contango_ratio - 1) / contango_threshold))
```

### Volatility Regime Classification

- **Low Vol**: VIX < 25th percentile
- **Normal Vol**: 25th ≤ VIX ≤ 75th percentile
- **High Vol**: VIX > 75th percentile

## Risk Management Framework

### Drawdown Controls

- Maximum portfolio drawdown: 20%
- TQQQ reduction trigger: 15% drawdown
- Recovery mechanism: gradual TQQQ restoration

### Volatility Spikes

- VIX spike threshold: 2x 60-day average
- SVOL reduction: proportional to VIX elevation
- TAIL enhancement: proportional to stress level

### Correlation Monitoring

- Stock-volatility correlation monitoring
- Hedge effectiveness validation
- Regime-based allocation adjustments

## Expected Performance Characteristics

- **Return Profile**: TQQQ-driven with volatility premium enhancement
- **Asymmetric Payoffs**: Positive skew during normal markets, protection during crises
- **Volatility**: Targeted 12-18% through dynamic allocation
- **Tail Protection**: Convex payoffs during market crashes

## Configuration Parameters

- `base_tqqq_weight`: Core equity allocation
- `svol_base_weight`: Short-volatility sleeve size
- `tail_base_weight`: Tail hedge sleeve size
- `drawdown_threshold`: 15% for TQQQ reduction
- `vix_spike_threshold`: 2x normal volatility
- `drift_bands`: 10% rebalancing threshold

## References

- [Simplify SVOL ETF - Volatility Premium](https://www.simplify.us/etfs/svol-simplify-volatility-premium-etf)
- [Simplify TAIL ETF - Tail Protection](https://www.simplify.us/etfs/tail-simplify-hedged-equity-etf)
- [Volatility Risk Premium Research](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1698125)
- [Barbell Portfolio Theory](https://www.aqr.com/Insights/Research)
- [VIX Term Structure Analysis](https://www.cboe.com/volatility/)
