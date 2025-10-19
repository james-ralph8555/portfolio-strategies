# Contributing to Portfolio Strategies

This repository provides a structured framework for implementing trading strategies. The design allows multiple contributors to work on different strategies independently without merge conflicts.

## Repository Structure

```
portfolio/
├── strategies/                    # Strategy implementations
│   ├── equity_crisis_alpha/      # Strategy 1: TQQQ + managed futures
│   ├── equity_convex_rate/       # Strategy 2: TQQQ + rate hedge
│   ├── equity_inflation_beta/    # Strategy 3: TQQQ + commodities
│   └── equity_vol_barbell/       # Strategy 4: TQQQ + vol sleeves
├── core/                         # Shared components
│   ├── interfaces/               # Base classes and interfaces
│   ├── registry.py               # Strategy discovery system
│   └── config/                   # Configuration management
├── tests/                        # Test suite
└── docs/                         # Documentation
```

## Adding a New Strategy

### 1. Create Strategy Directory

```bash
mkdir strategies/your_strategy_name
```

### 2. Implement Strategy Class

Create `strategies/your_strategy_name/strategy.py`:

```python
from typing import Dict, Optional
import pandas as pd
from core.interfaces.strategy import Strategy

class YourStrategyNameStrategy(Strategy):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.name = "your_strategy_name"
        self.assets = ["TQQQ", "OTHER_ASSETS"]

    def calculate_weights(self, data: pd.DataFrame) -> Dict[str, float]:
        # Implement your strategy logic here
        return {}

    def should_rebalance(self, current_weights, target_weights) -> bool:
        # Implement rebalancing logic
        return False

    def validate_config(self) -> bool:
        # Validate configuration
        return True
```

### 3. Add Configuration

Create `strategies/your_strategy_name/config.yaml`:

```yaml
name: your_strategy_name
description: "Brief description of your strategy"

assets:
  core: "TQQQ"
  # Add other assets

# Strategy-specific parameters
parameters:
  # Add your parameters here
```

### 4. Add Documentation

Create `strategies/your_strategy_name/README.md` with:

- Strategy overview
- Asset allocation
- Algorithm description
- Implementation status
- References

## Development Guidelines

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints for all functions
- Include docstrings for all public methods
- Write unit tests for all functionality

### Testing

- Place tests in `tests/` directory
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies

### Configuration

- Use YAML configuration files
- Support environment variable overrides
- Validate all configuration parameters
- Provide sensible defaults

### Naming Conventions

- Strategy directories: `snake_case`
- Strategy classes: `PascalCase` ending with `Strategy`
- Configuration keys: `snake_case`
- Asset symbols: `UPPER_CASE`

## Workflow

1. **Fork** the repository
2. **Create** a feature branch for your strategy
3. **Implement** your strategy following the structure above
4. **Test** thoroughly
5. **Submit** a pull request

## Strategy Registry

Strategies are automatically discovered by the registry system. Your strategy will be available once:

- The strategy directory exists
- `strategy.py` contains a class named `{StrategyName}Strategy`
- The class implements the `Strategy` interface

## Common Interface

All strategies must implement these methods:

- `calculate_weights(data)`: Calculate target asset weights
- `should_rebalance(current, target)`: Determine if rebalancing needed
- `validate_config()`: Validate strategy configuration

## Configuration Management

The configuration system supports:

- YAML configuration files
- Environment variable overrides (prefix with `STRATEGY_NAME_`)
- Nested configuration with dot notation
- Automatic validation

## Questions?

- Check existing strategy implementations for examples
- Review the core interfaces for required methods
- Look at configuration files for parameter patterns
