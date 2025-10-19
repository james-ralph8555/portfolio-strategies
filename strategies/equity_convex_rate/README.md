# Equity Convex Rate Hedge Strategy

## Overview
TQQQ strategy with convex rate hedge via PFIX and regime-switching logic.

## Assets
- **Core**: TQQQ (3x Nasdaq)
- **Rate Hedge**: PFIX (payer-swaption ETF)
- **Diversifier**: IAU (gold)
- **Cash**: SGOV (treasury bills)

## Algorithm
1. **Regime-switch risk budget** based on stock-bond correlation
2. **PFIX as primary hedge** when correlation > 0
3. **Allow TMF duration** when correlation < 0
4. **TQQQ overweight** via expected-return tilt
5. **Portfolio volatility targeting**

## Implementation Status
- [ ] Correlation regime detection
- [ ] Regime-switch allocation logic
- [ ] PFIX convexity modeling
- [ ] Volatility targeting
- [ ] Rebalancing logic

## References
- [Simplify PFIX ETF](https://www.simplify.us/etfs/pfix-simplify-interest-rate-hedge-etf)
- [AQR Stock-Bond Correlation](https://www.aqr.com/Insights/Research/Journal-Article/A-Changing-Stock-Bond-Correlation)