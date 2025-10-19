# Test Suite for Equity Volatility Barbell Strategy

This directory contains comprehensive tests for the equity volatility barbell strategy implementation.

## Test Structure

### Test Files

- **`test_equity_vol_barbell_unit.py`** - Unit tests for individual methods and components
- **`test_equity_vol_barbell_functional.py`** - Functional tests for end-to-end workflows
- **`test_integration.py`** - Integration tests with external systems and dependencies
- **`conftest.py`** - Shared fixtures and pytest configuration

### Test Categories

#### Unit Tests
- Test individual methods in isolation
- Validate configuration handling
- Test edge cases and error conditions
- Verify mathematical calculations

#### Functional Tests
- Test complete strategy workflows
- Simulate different market conditions (bull, bear, volatile)
- Validate rebalancing logic
- Test market regime transitions

#### Integration Tests
- Test integration with portfolio management systems
- Validate data pipeline compatibility
- Test risk management integration
- Simulate backtesting framework integration

## Running Tests

### Prerequisites
Ensure you're in the Nix development environment:
```bash
nix develop
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest -m unit

# Run only functional tests
pytest -m functional

# Run only integration tests
pytest -m integration
```

### Run Specific Test Files
```bash
# Run unit tests only
pytest tests/test_equity_vol_barbell_unit.py

# Run functional tests only
pytest tests/test_equity_vol_barbell_functional.py

# Run integration tests only
pytest tests/test_integration.py
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage
```bash
pytest --cov=strategies/equity_vol_barbell --cov-report=html
```

## Test Fixtures

The test suite includes comprehensive fixtures for different market scenarios:

- **`minimal_market_data`** - Basic market data with required columns
- **`extended_market_data`** - Full year of realistic market data
- **`crisis_market_data`** - Market data simulating crisis conditions
- **`low_volatility_data`** - Market data with low volatility conditions
- **`empty_market_data`** - Empty data for edge case testing
- **`incomplete_market_data`** - Data with missing columns
- **`nan_market_data`** - Data with NaN values

## Test Data

All test data is generated programmatically using deterministic random seeds to ensure:
- Reproducible test results
- No dependency on external data sources
- Fast test execution
- Comprehensive coverage of market scenarios

## Configuration

Test configuration is managed through:
- **`pytest.ini`** - Pytest configuration and markers
- **`conftest.py`** - Shared fixtures and test utilities
- **`flake.nix`** - Development environment with pytest dependency

## Test Coverage

The test suite covers:

### Strategy Methods
- `calculate_weights()` - Core weight allocation logic
- `calculate_drawdown_trigger()` - Drawdown detection
- `size_vol_sleeves()` - Volatility sleeve sizing
- `should_rebalance()` - Rebalancing logic
- `validate_config()` - Configuration validation

### Market Conditions
- Bull markets (low volatility, positive returns)
- Bear markets (high volatility, negative returns)
- Volatile sideways markets
- Crisis conditions (severe drawdowns)
- Low volatility environments

### Edge Cases
- Missing or incomplete data
- NaN values in market data
- Invalid configurations
- Extreme market conditions
- Empty datasets

### Integration Points
- Portfolio management systems
- Risk management frameworks
- Data pipelines
- Backtesting engines
- Monitoring systems

## Best Practices

1. **Deterministic Tests** - All tests use fixed random seeds for reproducibility
2. **Isolation** - Each test is independent and doesn't rely on other tests
3. **Comprehensive Coverage** - Tests cover happy paths, edge cases, and error conditions
4. **Clear Assertions** - Tests have clear, specific assertions with meaningful messages
5. **Proper Fixtures** - Shared setup code is properly factored into fixtures
6. **Mock External Dependencies** - External systems are mocked to ensure test isolation

## Adding New Tests

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Add proper markers (unit, functional, integration)
4. Include both positive and negative test cases
5. Test edge cases and error conditions
6. Ensure tests are deterministic and fast

## Troubleshooting

### Common Issues

1. **Import Errors** - Ensure you're in the Nix development environment
2. **Random Test Failures** - Check that random seeds are set in test data
3. **Slow Tests** - Use minimal data sizes for unit tests
4. **Fixture Conflicts** - Ensure fixtures don't have unintended side effects

### Debugging Failed Tests

```bash
# Run with detailed output
pytest -v -s --tb=long

# Run specific failing test
pytest tests/test_file.py::test_function

# Run with debugger
pytest --pdb
```