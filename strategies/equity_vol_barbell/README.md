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
- [ ] Barbell allocation logic
- [ ] Drawdown trigger calculation
- [ ] VIX term structure analysis
- [ ] Sleeve sizing methodology
- [ ] Rebalancing logic

## References
- [Simplify SVOL ETF](https://www.simplify.us/etfs/svol-simplify-volatility-premium-etf)
- [Simplify TAIL ETF](https://www.simplify.us/etfs/tail-simplify-hedged-equity-etf)