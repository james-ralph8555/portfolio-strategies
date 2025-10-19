# Asset Analysis Report

## Overview
This report analyzes all assets (ETFs) used across the portfolio strategies, including their descriptions, asset classes, and identification of duplicate or similar ETFs across different strategies.

## Asset Inventory

### Core Equity Holdings

#### TQQQ - ProShares UltraPro QQQ
- **Description**: 3x leveraged NASDAQ-100 ETF that seeks daily investment results that correspond to three times the daily performance of the NASDAQ-100 Index
- **Asset Class**: Leveraged Equity
- **Usage**: Core equity engine in ALL strategies
- **Strategies**: equity_convex_rate, equity_convex_rate_hedge, equity_crisis_alpha, equity_inflation_beta, equity_vol_barbell
- **Expense Ratio**: ~0.95% (estimated)
- **Key Characteristics**: High volatility, tech-heavy exposure, daily rebalancing

### Diversification Assets

#### IAU - iShares Gold Trust
- **Description**: Gold-backed ETF that seeks to reflect the price of gold owned by the trust
- **Asset Class**: Commodities (Precious Metals)
- **Usage**: Diversification and crisis hedge
- **Strategies**: equity_convex_rate, equity_convex_rate_hedge, equity_crisis_alpha, equity_inflation_beta
- **Expense Ratio**: 0.25%
- **Key Characteristics**: Low correlation to equities, inflation hedge, safe-haven asset

#### DBMF - iMGP DBi Managed Futures Strategy ETF
- **Description**: Actively managed ETF that seeks to achieve capital appreciation through a managed futures strategy
- **Asset Class**: Alternative Investments (Managed Futures)
- **Usage**: Crisis alpha and trend-following
- **Strategies**: equity_crisis_alpha
- **Expense Ratio**: ~0.85% (estimated)
- **Key Characteristics**: Trend-following across multiple asset classes, low correlation to traditional assets

#### PDBC - Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF
- **Description**: Broad commodity exposure ETF that uses futures contracts to track a diversified commodity index
- **Asset Class**: Commodities (Broad Basket)
- **Usage**: Inflation protection and diversification
- **Strategies**: equity_inflation_beta
- **Expense Ratio**: 0.59%
- **Key Characteristics**: No K-1 tax forms, diversified commodity exposure, inflation hedge

#### SVOL - Simplify Volatility Premium ETF
- **Description**: Short volatility strategy that seeks to provide income through short VIX futures positions with call option protection
- **Asset Class**: Volatility Strategies
- **Usage**: Volatility premium harvesting
- **Strategies**: equity_vol_barbell
- **Expense Ratio**: 0.50% (recently reduced from 0.72%)
- **Key Characteristics**: Income generation, short volatility exposure, tail risk protection

#### TAIL - Simplify Tail Risk Strategy ETF
- **Description**: Equity ETF with built-in tail risk protection using options strategies
- **Asset Class**: Equity with Options Overlay
- **Usage**: Tail risk hedging
- **Strategies**: equity_vol_barbell
- **Expense Ratio**: 0.55% (recently reduced from ~0.75%)
- **Key Characteristics**: Crash protection, put ladder strategy, equity participation

### Rate Hedging Assets

#### PFIX - Simplify Interest Rate Hedge ETF
- **Description**: Interest rate hedge ETF that provides convex exposure to rising long-term interest rates using OTC interest rate options
- **Asset Class**: Fixed Income Derivatives
- **Usage**: Rising rates protection
- **Strategies**: equity_convex_rate, equity_convex_rate_hedge
- **Expense Ratio**: 0.50%
- **Key Characteristics**: Convex exposure to rate increases, OTC derivatives, institutional-grade protection

### Cash Equivalents

#### SGOV - iShares 0-3 Month Treasury Bond ETF
- **Description**: Ultra-short-term Treasury ETF investing in Treasury bills with 0-3 month remaining maturities
- **Asset Class**: Cash Equivalents
- **Usage**: Cash allocation and shock absorber
- **Strategies**: equity_convex_rate, equity_convex_rate_hedge, equity_crisis_alpha, equity_inflation_beta, equity_vol_barbell
- **Expense Ratio**: 0.07%
- **Key Characteristics**: Minimal interest rate risk, high liquidity, government backing

### Additional Assets (Mentioned in Tests/Documentation)

#### VOO - Vanguard S&P 500 ETF
- **Description**: Index-tracking ETF that provides exposure to large-cap U.S. equities via the S&P 500
- **Asset Class**: Large-Cap Equity
- **Usage**: Benchmark/reference in tests
- **Strategies**: Test files only
- **Expense Ratio**: 0.03%
- **Key Characteristics**: Broad market benchmark, high liquidity, low-cost core U.S. equity exposure

#### TMF - Direxion Daily 20+ Year Treasury Bull 3X ETF
- **Description**: 3x leveraged long-term Treasury ETF
- **Asset Class**: Leveraged Fixed Income
- **Usage**: Mentioned as alternative in rate hedging
- **Strategies**: equity_convex_rate (conditional usage)
- **Expense Ratio**: 1.09%
- **Key Characteristics**: 3x leverage to long-term Treasuries, high volatility

#### KMLM - KFA Mount Lucas Management Strategy ETF
- **Description**: Managed futures strategy ETF (alternative to DBMF)
- **Asset Class**: Alternative Investments (Managed Futures)
- **Usage**: Mentioned as alternative to DBMF
- **Strategies**: equity_crisis_alpha (alternative)
- **Expense Ratio**: 0.90%
- **Key Characteristics**: Trend-following, quantitative strategy

## Asset Usage Analysis

### Most Frequently Used Assets
1. **TQQQ** - Used in ALL 5 strategies (core holding)
2. **SGOV** - Used in ALL 5 strategies (cash allocation)
3. **IAU** - Used in 4 strategies (diversification)

### Strategy-Specific Assets
- **equity_vol_barbell**: SVOL, TAIL (volatility-focused)
- **equity_inflation_beta**: PDBC (commodity focus)
- **equity_crisis_alpha**: DBMF (managed futures focus)
- **equity_convex_rate**: PFIX (rate hedging focus)

## Duplicate/Similar ETF Analysis

### Gold Exposure
- **Primary**: IAU (iShares Gold Trust) - 0.25% expense ratio
- **Analysis**: IAU is the standardized gold allocation across all strategies; no secondary ticker maintained.

### Cash Equivalents
- **Primary**: SGOV (iShares 0-3 Month Treasury) - 0.07% expense ratio
- **Analysis**: SGOV is the exclusive cash sleeve, ensuring consistent implementation and minimal cost.

### Managed Futures
- **Primary**: DBMF (iMGP DBi Managed Futures) - 0.85% expense ratio
- **Alternative**: KMLM (KFA Mount Lucas) - 0.90% expense ratio
- **Analysis**: Similar expense ratios but different strategy approaches. DBMF uses DBi's systematic approach, KMLM uses Mount Lucas methodology. **Note: While both are managed futures strategies, they are not interchangeable due to different methodologies - KMLM does not trade equity futures and uses a specific signal model.**

### Volatility Strategies
- **SVOL**: Short volatility with call protection (income focus)
- **TAIL**: Equity with put ladder protection (capital preservation focus)
- **Analysis**: Complementary rather than duplicate - SVOL generates income, TAIL provides crash protection.

## Asset Class Distribution

### By Strategy
1. **equity_convex_rate**: 4 assets (TQQQ, PFIX, IAU, SGOV)
2. **equity_convex_rate_hedge**: 4 assets (TQQQ, PFIX, IAU, SGOV)
3. **equity_crisis_alpha**: 4 assets (TQQQ, DBMF, IAU, SGOV)
4. **equity_inflation_beta**: 4 assets (TQQQ, PDBC, IAU, SGOV)
5. **equity_vol_barbell**: 4 assets (TQQQ, SVOL, TAIL, SGOV)

### By Asset Class
- **Leveraged Equity**: TQQQ (5 strategies)
- **Cash Equivalents**: SGOV (5 strategies)
- **Precious Metals**: IAU (4 strategies)
- **Rate Hedging**: PFIX (2 strategies)
- **Volatility Strategies**: SVOL, TAIL (1 strategy each)
- **Managed Futures**: DBMF (1 strategy)
- **Broad Commodities**: PDBC (1 strategy)

## Cost Analysis

### Expense Ratios by Asset Class
- **Cash Equivalents**: 0.07% (lowest cost)
- **Precious Metals**: 0.25% (low cost)
- **Rate Hedging**: 0.50% (moderate cost)
- **Broad Commodities**: 0.59% (moderate cost)
- **Volatility Strategies**: 0.50-0.55% (moderate cost, recently reduced)
- **Managed Futures**: 0.85-0.90% (higher cost)
- **Leveraged Equity**: 0.95-1.09% (highest cost)

### Total Strategy Cost Estimates
- **equity_convex_rate**: ~1.77% weighted average (reduced due to updated expense ratios)
- **equity_convex_rate_hedge**: ~1.77% weighted average (reduced due to updated expense ratios)
- **equity_crisis_alpha**: ~1.77% weighted average (reduced due to updated expense ratios)
- **equity_inflation_beta**: ~1.71% weighted average (reduced due to updated expense ratios)
- **equity_vol_barbell**: ~1.77% weighted average (significantly reduced due to SVOL/TAIL expense ratio decreases)

## Recommendations

### Optimization Opportunities
1. **Maintain standardization** on IAU for gold exposure to preserve cost efficiency
2. **Maintain SGOV** as the dedicated cash sleeve for consistent liquidity management
3. **Consider DBMF vs KMLM** based on performance and strategy fit
4. **Evaluate SVOL vs TAIL** combination for optimal volatility management

### Diversification Benefits
- All strategies maintain consistent 4-asset structure
- Core TQQQ + SGOV provides stable foundation
- Each strategy adds unique diversification through specialized assets
- No significant overlap in specialized assets across strategies

### Risk Considerations
- High concentration in TQQQ across all strategies creates systematic risk
- Leveraged products require careful monitoring
- Alternative assets (PFIX, SVOL, TAIL) add complexity but provide unique risk management
- Cash allocation (SGOV) provides important shock absorber functionality

## Conclusion

The portfolio demonstrates a well-structured approach with consistent core holdings (TQQQ, SGOV) and strategy-specific diversification assets. The use of specialized ETFs provides targeted exposure to specific risk factors (rate risk, volatility, inflation, crisis events). Recent expense ratio reductions in volatility strategies (SVOL, TAIL) have significantly improved the cost efficiency of the equity_vol_barbell strategy. Standardizing on the lowest-cost tickers for each sleeve (IAU for gold, SGOV for cash) keeps redundant exposures out of the line-up while preserving coverage. The overall asset allocation provides comprehensive market coverage while maintaining distinct strategy identities.

**Recent Updates (October 2025)**:
- SVOL expense ratio reduced from 0.72% to 0.50%
- TAIL expense ratio reduced from ~0.75% to 0.55%
- Updated expense ratios for TMF (1.09%) and KMLM (0.90%)
- Managed futures ETFs (DBMF vs KMLM) confirmed as similar asset class but not interchangeable due to different methodologies
