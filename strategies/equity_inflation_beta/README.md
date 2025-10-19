# Equity Inflation Beta Strategy

## Overview
TQQQ strategy with inflation protection via commodities and gold.

## Assets
- **Core**: TQQQ (3x Nasdaq)
- **Commodities**: PDBC (broad commodities, no K-1)
- **Gold**: IAU
- **Cash**: SGOV

## Algorithm
1. **Two-signal tilt** (trend + carry) on diversifiers
2. **Risk-parity base** between gold and commodities
3. **Structural TQQQ overweight** scaled by portfolio vol
4. **Monthly rebalancing** with drift bands

## Implementation Status
- [ ] Trend signal calculation
- [ ] Carry signal calculation
- [ ] Risk-parity implementation
- [ ] Volatility scaling
- [ ] Rebalancing logic

## References
- [AQR Commodities Portfolio](https://www.aqr.com/-/media/AQR/Documents/Whitepapers/Building-a-Better-Commodities-Portfolio.pdf)
- [PDBC ETF Info](https://www.invesco.com/us/financial-products/etfs/product-detail?ticker=PDBC)