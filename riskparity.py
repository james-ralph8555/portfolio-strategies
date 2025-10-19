"""
Risk parity portfolio optimization implementation.
"""

import datetime
import sys

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

TOLERANCE = 1e-10


def allocation_risk(weights, covariances):  # returns risk of weights distribution
    return np.sqrt(weights * covariances * weights.T)[0, 0]


def assets_risk_contribution_to_allocation_risk(
    weights, covariances
):  # returns contribution of each asset to risk of weight distribution
    portfolio_risk = allocation_risk(weights, covariances)
    return np.multiply(weights.T, covariances * weights.T) / portfolio_risk


def risk_budget_objective_error(
    weights, args
):  # returns error between desired contribution and calculated contribution of each asset
    covariances = args[0]
    assets_risk_budget = args[1]
    weights = np.matrix(weights)
    portfolio_risk = allocation_risk(weights, covariances)
    assets_risk_contribution = assets_risk_contribution_to_allocation_risk(
        weights, covariances
    )
    assets_risk_target = np.asmatrix(np.multiply(portfolio_risk, assets_risk_budget))
    return float(sum(np.square(assets_risk_contribution - assets_risk_target.T)))


def get_risk_parity_weights(covariances, assets_risk_budget, initial_weights):
    def flatten(t):
        return [item for sublist in t for item in sublist]

    constraints = (
        {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
        {"type": "ineq", "fun": lambda x: x},
    )
    return minimize(
        fun=risk_budget_objective_error,
        x0=initial_weights,
        args=[covariances, assets_risk_budget],
        method="SLSQP",
        constraints=constraints,
        tol=TOLERANCE,
        options={"disp": False},
    ).x


def get_weights_yahoo(
    yahoo_tickers=None,
    start_date=(datetime.date.today() - datetime.timedelta(90 + (1 / 2))).isoformat(),
    end_date=datetime.date.today(),
    assets_risk_budget=None,
):
    if assets_risk_budget is None:
        assets_risk_budget = [0.5, 0.5]
    if yahoo_tickers is None:
        yahoo_tickers = ["TQQQ", "TMF"]
    prices = pd.DataFrame(columns=yahoo_tickers)
    for i in range(len(yahoo_tickers)):
        data = yf.download(
            yahoo_tickers[i], start=start_date, end=end_date, interval="1d"
        )
        price = data.loc[:, "Close"]
        prices[yahoo_tickers[i]] = price
    covariances = 365.0 * prices.pct_change().iloc[1:, :].cov().values
    # assets_risk_budget = [1 / prices.shape[1]] * prices.shape[1]
    init_weights = [1 / prices.shape[1]] * prices.shape[1]
    weights = pd.Series(
        get_risk_parity_weights(covariances, assets_risk_budget, init_weights),
        index=prices.columns,
        name="weight",
    )
    return [weights, prices.iloc[-1, :]]


if __name__ == "__main__":
    args = sys.argv[1:]
    try:
        current = [float(arg) for arg in args]
    except (ValueError, TypeError) as err:
        raise Exception("Inputs must be floats") from err
    assert len(current) == 2
    pv = sum(current)
    sdata = get_weights_yahoo(
        yahoo_tickers=["QQQ", "TLT"], assets_risk_budget=[0.75, 0.25]
    )
    pdata = get_weights_yahoo(
        yahoo_tickers=["TQQQ", "TMF"], assets_risk_budget=[0.75, 0.25]
    )
    weights = sdata[0].values.tolist()
    prices = sdata[1].values.tolist()
    prices_l = pdata[1].values.tolist()
    print(f"TQQQ Price: ${prices_l[0]}, TMF Price: ${prices_l[1]}")
    print(
        f"TQQQ Allocation: {round(weights[0] * 100, 2)}%, TMF Allocation: {round(weights[1] * 100, 2)}%"
    )
    print(f"QQQ Price: ${prices[0]}, TLT Price: ${prices[1]}")
    print(f"TQQQ: ${pv * weights[0]} TMF: ${pv * weights[1]}")
    print(f"TQQQ: {(pv * weights[0]) / prices[0]} TMF: {(pv * weights[1]) / prices[1]}")
    print(
        f"TQQQ D: ${(pv * weights[0]) - current[0]} TMF D: {(pv * weights[1]) - current[1]}"
    )
# old backtesting code
# prices = get_data_csv(filenames=["UPROHIST.csv", "TMFHIST.csv"])
# print(backtest_csv(prices=prices, td=1, assets_risk_budget=[0.4, 0.6]))
# print(backtest_csv(prices=prices, td=1, assets_risk_budget=[0.5, 0.5]))
# print(backtest_csv(prices=prices, td=1, assets_risk_budget=[0.55, 0.45]))
# print(backtest_csv(prices=prices, td=1, assets_risk_budget=[0.6, 0.4]))

# # portfolio = backtest_csv(prices = prices, td = 7, assets_risk_budget = [0.4, 0.6])
# # print(portfolio[0])
# plt.figure(1, figsize=(4, 3), dpi=300, facecolor="w", edgecolor="k")
# # plt.plot(np.linspace(1986, 2019, len(portfolio[1])), portfolio[1], color='k', linewidth=0.25)
# # plt.yscale('log')
# portfolio = backtest_csv(prices=prices, td=7, assets_risk_budget=[0.5, 0.5])
# print(portfolio[0])
# # plt.figure(2, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
# plt.plot(
#     np.linspace(1986, 2019, len(portfolio[1])), portfolio[1], color="r", linewidth=0.33
# )
# plt.yscale("log")
# portfolio = backtest_csv(prices=prices, td=7, assets_risk_budget=[0.55, 0.45])
# print(portfolio[0])
# # plt.figure(3, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
# plt.plot(
#     np.linspace(1986, 2019, len(portfolio[1])), portfolio[1], color="b", linewidth=0.33
# )
# plt.yscale("log")
# portfolio = backtest_csv(prices=prices, td=7, assets_risk_budget=[0.6, 0.4])
# print(portfolio[0])
# # plt.figure(4, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
# plt.plot(
#     np.linspace(1986, 2019, len(portfolio[1])), portfolio[1], color="g", linewidth=0.33
# )
# plt.yscale("log")
# # portfolio = backtest_csv(prices = prices, td = 7, assets_risk_budget = [0.65, 0.35])
# # print(portfolio[0])
# # """
