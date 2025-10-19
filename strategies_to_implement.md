Yes. Use a TQQQ-centric core, then add uncorrelated sleeves with rules that bias expected return and control left-tail risk. Four ETF-only blueprints and the algorithm I’d use for each:

1. **Equity engine + crisis alpha**
   Assets: **TQQQ + DBMF/KMLM (managed futures) + Gold (IAU) + Cash (SGOV)**.
   Algorithm: **Leverage-aware ERC** with a **Black–Litterman tilt** that assigns a larger risk budget to TQQQ; **volatility targeting** at the portfolio level; **monthly** rebalance with 10-pt drift bands. Evidence: time-series momentum works across futures; managed-futures ETFs deliver trend exposure; gold’s equity correlation is near zero in calm times and turns negative in stress. Vol-managed overlays raise Sharpe. ([AQR Capital Management][1])

2. **Equity engine + convex rate hedge**
   Assets: **TQQQ + PFIX (payer-swaption rate hedge) + Gold + Cash**.
   Algorithm: **Regime-switch risk budget** for the bond/rate sleeve: when stock–bond correlation is >0, keep PFIX as the primary hedge; if correlation turns <0 and inflation risk subsides, allow some TMF or intermediate duration. Keep a **TQQQ overweight** via expected-return tilt; vol-target the whole book. Rationale: PFIX is convex to rising long rates and rate vol; gold diversifies especially when stocks and bonds move together. ([Simplify][2]) ([AQR Capital Management][3])

3. **Equity engine + inflation beta**
   Assets: **TQQQ + PDBC (broad commodities) + Gold + Cash**.
   Algorithm: **Two-signal tilt** on the diversifiers (**trend + carry**) layered on a **risk-parity base** between gold and commodities; keep a structural overweight to TQQQ but scale sleeve sizes with portfolio vol. Rationale: commodities improve diversification and help in high or rising inflation; PDBC is a liquid, no-K-1 commodity basket. ([AQR Capital Management][4])

4. **Equity engine + barbell of vol premia and tail**
   Assets: **TQQQ + SVOL (short-VIX with tail hedge) + TAIL (S&P put ladder) + Cash**.
   Algorithm: **Barbell allocator**: keep a high TQQQ weight, pair it with a small **income-oriented short-vol sleeve** (SVOL) and a **crisis convexity sleeve** (TAIL). Use **drawdown-triggered scaling** to cut TQQQ when realized vol spikes, replenishing cash. Note: SVOL harvests the VIX term-structure premium but needs a tail hedge; TAIL is designed to pay off in sharp equity selloffs. ([Simplify][5])

# Implementation notes

- **Targeting**: set a portfolio vol cap (e.g., 12–18% annualized). Volatility targeting is robust across factors and asset classes. ([Wiley Online Library][6])
- **Rebalance**: monthly with 10-pt drift bands; add a **correlation-regime guard** for bond/rate hedges. Positive stock–bond correlation argues for more gold/managed futures and less linear duration. ([AQR Capital Management][7])
- **Cash**: treat SGOV as the shock absorber, not return engine. ([ishares.com][8])

Pick one blueprint and I’ll translate it into precise weights, bands, and triggers aligned to your risk target.

[1]: https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum?utm_source=chatgpt.com "Time Series Momentum"
[2]: https://www.simplify.us/etfs/pfix-simplify-interest-rate-hedge-etf?utm_source=chatgpt.com "PFIX Simplify Interest Rate Hedge ETF"
[3]: https://www.aqr.com/Insights/Research/Journal-Article/A-Changing-Stock-Bond-Correlation?utm_source=chatgpt.com "A Changing Stock-Bond Correlation"
[4]: https://www.aqr.com/-/media/AQR/Documents/Whitepapers/Building-a-Better-Commodities-Portfolio.pdf?sc_lang=en&utm_source=chatgpt.com "Building a Better Commodities Portfolio"
[5]: https://www.simplify.us/etfs/svol-simplify-volatility-premium-etf?utm_source=chatgpt.com "SVOL Simplify Volatility Premium ETF"
[6]: https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513?utm_source=chatgpt.com "Volatility‐Managed Portfolios - MOREIRA - 2017"
[7]: https://www.aqr.com/-/media/AQR/Documents/Alternative-Thinking/A-Changing-Stock-Bond-Correlation_JPM.pdf?sc_lang=en&utm_source=chatgpt.com "A Changing Stock–Bond Correlation"
[8]: https://www.ishares.com/us/products/314116/ishares-0-3-month-treasury-bond-etf?utm_source=chatgpt.com "iShares 0-3 Month Treasury Bond ETF | SGOV"

Note: risk_parity in this repo is an old strategy, these above are newer strategies we want to implement

Implementation can include expanding python packages in this repo.
This code is very old and risk_parity.py should not be used as a template, quality of life features should be added.
All strategies should share a common interface so we can backtest them in the future easily
