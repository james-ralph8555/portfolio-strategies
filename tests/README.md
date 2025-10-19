# Test Suite for Equity Convex Rate Hedge Strategy

This directory contains comprehensive pytest-based tests for the equity convex rate hedge strategy implementation.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── fixtures/                   # Test fixtures and utilities
│   ├── __init__.py
│   └── data_fixtures.py       # Market data fixtures for testing
├── unit/                       # Unit tests for individual methods
│   └── test_strategy.py       # Strategy method unit tests
├── functional/                 # Functional tests for integration behavior
│   └── test_strategy_integration.py  # End-to-end strategy tests
└── README.md                  # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Strategy initialization**: Test default and custom configuration
- **Method validation**: Test individual strategy methods in isolation
- **Configuration validation**: Test config validation logic
- **Weight calculation**: Test regime-specific weight calculations
- **Rebalancing logic**: Test drift band and rebalancing triggers

### Functional Tests (`tests/functional/`)
- **End-to-end workflows**: Test complete strategy behavior
- **Market regime adaptation**: Test strategy response to different market conditions
- **Integration scenarios**: Test strategy with various data scenarios
- **Edge cases**: Test behavior with minimal or missing data

### Test Fixtures (`tests/fixtures/`)
- **Sample market data**: Realistic price series for testing
- **Correlation scenarios**: Positive/negative correlation data
- **Volatility scenarios**: High/low volatility environments
- **Configuration fixtures**: Standard and custom strategy configs

## Running Tests

### Run all tests
```bash
nix develop --command python -m pytest tests/ -v
```

### Run specific test categories
```bash
# Unit tests only
nix develop --command python -m pytest tests/unit/ -v

# Functional tests only
nix develop --command python -m pytest tests/functional/ -v
```

### Run with coverage
```bash
nix develop --command python -m pytest tests/ --cov=strategies --cov=core -v
```

### Run specific test
```bash
nix develop --command python -m pytest tests/unit/test_strategy.py::TestEquityConvexRateHedgeStrategy::test_strategy_initialization_default -v
```

## Test Configuration

The test suite uses the following configuration:

- **pytest.ini**: Main pytest configuration
- **pyproject.toml**: Project-level test configuration and dependencies
- **flake.nix**: Nix environment with test dependencies

## Test Data

All test data is generated programmatically using fixtures to ensure:

- **Reproducibility**: Fixed random seeds for consistent results
- **Isolation**: No external data dependencies
- **Variety**: Different market scenarios and edge cases
- **Performance**: Fast test execution without I/O bottlenecks

## Key Test Scenarios

### Market Regimes Tested
1. **Positive stock-bond correlation**: Emphasizes PFIX rate hedge
2. **Negative stock-bond correlation**: Reduces PFIX, increases TQQQ
3. **High volatility**: Triggers volatility scaling and defensive positioning
4. **Low volatility**: Allows more aggressive positioning

### Edge Cases Tested
1. **Minimal data**: Short time series with insufficient history
2. **Missing assets**: Incomplete asset data
3. **Invalid configurations**: Malformed strategy parameters
4. **Extreme correlations**: Boundary conditions for regime switching

### Integration Behaviors Tested
1. **Weight calculation consistency**: Same inputs produce same outputs
2. **Rebalancing triggers**: Drift band functionality
3. **Configuration updates**: Dynamic config changes
4. **Volatility targeting**: Scaling factor application

## Test Best Practices

1. **Isolation**: Each test is independent and doesn't rely on others
2. **Descriptive names**: Test names clearly indicate what is being tested
3. **Comprehensive coverage**: Both happy path and edge cases are covered
4. **Fixtures reuse**: Common test data is shared via fixtures
5. **Assertions**: Clear and specific assertions with meaningful messages

## Adding New Tests

When adding new tests:

1. **Unit tests** go in `tests/unit/test_strategy.py`
2. **Functional tests** go in `tests/functional/test_strategy_integration.py`
3. **New fixtures** go in `tests/fixtures/data_fixtures.py`
4. **Follow naming conventions**: `test_<method_name>` for unit tests
5. **Use appropriate markers**: `@pytest.mark.unit` or `@pytest.mark.functional`

## Coverage Goals

The test suite aims for:
- **100% method coverage** for all strategy methods
- **90%+ line coverage** for critical path logic
- **Edge case coverage** for all error conditions
- **Integration coverage** for end-to-end workflows