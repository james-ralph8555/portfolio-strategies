# Portfolio Strategies Framework

A structured framework for implementing and backtesting quantitative trading strategies focused on TQQQ-centric portfolios with various risk management approaches.

## Overview

This repository provides a modular architecture for implementing trading strategies that allows multiple contributors to work independently without merge conflicts. The framework includes:

- **Common Strategy Interface**: Standardized base class for all strategies
- **Strategy Registry**: Automatic discovery and management of strategies
- **Configuration Management**: Centralized config system with validation
- **Modular Structure**: Isolated strategy implementations

## Available Strategies

### 1. Equity Crisis Alpha

- **Assets**: TQQQ + DBMF/KMLM (managed futures) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Leverage-aware ERC with Black-Litterman tilt
- **Focus**: Crisis protection through managed futures

### 2. Equity Convex Rate Hedge

- **Assets**: TQQQ + PFIX (rate hedge) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Regime-switch risk budget
- **Focus**: Protection against rising interest rates

### 3. Equity Inflation Beta

- **Assets**: TQQQ + PDBC (commodities) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Two-signal tilt (trend + carry)
- **Focus**: Inflation protection through commodities

### 4. Equity Volatility Barbell

- **Assets**: TQQQ + SVOL (short vol) + TAIL (tail hedge) + SGOV (Cash)
- **Algorithm**: Barbell allocator with drawdown triggers
- **Focus**: Volatility premium harvesting with tail protection

### 5. Equity Convex Rate Hedge

- **Assets**: TQQQ + PFIX (rate hedge) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Regime-switch risk budget based on stock-bond correlation
- **Focus**: Enhanced protection against rising interest rates with convex rate protection

### 6. Risk Parity

- **Assets**: TQQQ + TMF (3x leveraged Treasury)
- **Algorithm**: Risk contribution equalization (75% equity, 25% bond risk)
- **Focus**: Equity-like returns with bond-like volatility through risk parity allocation

## Repository Structure

```
portfolio/
├── strategies/                    # Strategy implementations
│   ├── equity_crisis_alpha/      # Crisis alpha strategy
│   ├── equity_convex_rate/       # Convex rate hedge
│   ├── equity_convex_rate_hedge/ # Enhanced convex rate hedge
│   ├── equity_inflation_beta/    # Inflation beta strategy
│   ├── equity_vol_barbell/       # Volatility barbell
│   └── risk_parity/              # Risk parity strategy
├── core/                         # Shared framework components
│   ├── interfaces/               # Base classes and interfaces
│   ├── registry.py               # Strategy discovery system
│   └── config/                   # Configuration management
├── tests/                        # Test suite
└── docs/                         # Documentation
```

## Quick Start

### Prerequisites

```bash
# Enter the Nix shell
nix develop
```

### Using a Strategy

```python
from core.registry import registry

# Discover all available strategies
registry.discover_strategies()
print(registry.list_strategies())

# Create a strategy instance
strategy = registry.create_strategy("equity_crisis_alpha", config)

# Calculate weights
weights = strategy.calculate_weights(market_data)
```

### Adding a New Strategy

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on implementing new strategies.

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_strategy.py
```

## Configuration

Strategies use YAML configuration files with support for:

- Environment variable overrides
- Nested configuration
- Automatic validation

Example environment override:

```bash
export EQUITY_CRISIS_ALPHA_VOLATILITY_TARGET=0.12
```

## References

- [AQR Capital Management Research](https://www.aqr.com/Insights/Research)
- [Simplify ETFs](https://www.simplify.us/etfs)
- [Volatility Managed Portfolios](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513)
