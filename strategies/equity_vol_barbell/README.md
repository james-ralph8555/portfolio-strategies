# Equity Volatility Barbell Strategy

## Overview
TQQQ strategy with volatility premium harvesting and tail protection.

## Assets
- **Core**: TQQQ (3x Nasdaq)
- **Short Vol**: SVOL (short-VIX premium)
- **Tail Hedge**: TAIL (S&P put ladder)
- **Cash**: SGOV

## Algorithm
1. **Barbell allocator** with high TQQQ weight
2. **Short-vol income sleeve** (SVOL) for premium harvesting
3. **Crisis convexity sleeve** (TAIL) for tail protection
4. **Drawdown-triggered scaling** to reduce TQQQ in volatility spikes
5. **Monthly rebalancing** with daily drawdown monitoring

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

## References
- [Simplify SVOL ETF](https://www.simplify.us/etfs/svol-simplify-volatility-premium-etf)
- [Simplify TAIL ETF](https://www.simplify.us/etfs/tail-simplify-hedged-equity-etf)