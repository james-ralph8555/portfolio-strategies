# Testing Structure Guide

This document outlines the standardized testing structure for all strategies in the portfolio project.

## Overview

Each strategy has its own dedicated testing folder with consistent structure and pytest implementation.

## Directory Structure

```
strategies/
├── equity_convex_rate/
│   ├── strategy.py
│   ├── config.yaml
│   ├── README.md
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_unit.py
│       └── test_functional.py
├── equity_convex_rate_hedge/
│   ├── strategy.py
│   ├── config.yaml
│   ├── README.md
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_unit.py
│       └── test_functional.py
├── equity_crisis_alpha/
│   ├── strategy.py
│   ├── config.yaml
│   ├── README.md
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_unit.py
│       └── test_functional.py
├── equity_inflation_beta/
│   ├── strategy.py
│   ├── config.yaml
│   ├── README.md
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_unit.py
│       └── test_functional.py
└── equity_vol_barbell/
    ├── strategy.py
    ├── config.yaml
    ├── README.md
    └── tests/
        ├── __init__.py
        ├── conftest.py
        ├── test_unit.py
        └── test_functional.py
```

## Test File Types

### 1. `conftest.py`
Contains strategy-specific fixtures and configuration:
- Strategy configuration fixtures
- Sample data fixtures
- Strategy instance fixtures
- Minimal configuration fixtures

### 2. `test_unit.py`
Contains unit tests for individual methods and components:
- Strategy initialization tests
- Configuration validation tests
- Individual method tests
- Error handling tests
- Data preprocessing/postprocessing tests

### 3. `test_functional.py`
Contains end-to-end workflow and integration tests:
- Complete workflow tests
- Market scenario tests (normal, stress, crisis)
- Rebalancing workflow tests
- Configuration update tests
- Performance consistency tests

## Standardized Test Patterns

### Unit Test Structure
```python
class TestStrategyName:
    def test_initialization_with_config(self, config_fixture):
        # Test strategy initialization with configuration
        
    def test_initialization_without_config(self):
        # Test strategy initialization without configuration
        
    def test_get_assets(self, strategy_fixture):
        # Test get_assets method
        
    def test_get_name(self, strategy_fixture):
        # Test get_name method
        
    def test_validate_config_valid(self, strategy_fixture):
        # Test config validation with valid config
        
    def test_calculate_weights_basic(self, strategy_fixture, data_fixture):
        # Test basic weight calculation
        
    def test_should_rebalance_within_bands(self, strategy_fixture):
        # Test rebalancing logic when within drift bands
```

### Functional Test Structure
```python
class TestStrategyNameFunctional:
    def test_full_workflow_normal_market(self, strategy_fixture, data_fixture):
        # Test complete workflow in normal market conditions
        
    def test_workflow_with_market_stress(self, strategy_fixture):
        # Test workflow during market stress conditions
        
    def test_rebalancing_workflow(self, strategy_fixture):
        # Test complete rebalancing workflow
        
    def test_config_updates_workflow(self, strategy_fixture):
        # Test workflow when configuration is updated
        
    def test_error_handling_workflow(self, strategy_fixture):
        # Test workflow with various error conditions
```

## Pytest Configuration

The main `pytest.ini` file includes:
- Test paths for both central tests and strategy-specific tests
- Standard markers for test categorization
- Consistent output formatting
- Warning filters

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Strategy Tests
```bash
pytest strategies/equity_vol_barbell/tests/
```

### Run Only Unit Tests
```bash
pytest -m unit
```

### Run Only Functional Tests
```bash
pytest -m functional
```

### Run Tests with Verbose Output
```bash
pytest -v
```

## Best Practices

1. **Consistent Naming**: Use descriptive test method names following the pattern `test_<functionality>_<scenario>`

2. **Fixture Usage**: Leverage fixtures in `conftest.py` for common test data and strategy instances

3. **Test Coverage**: Ensure both positive and negative test cases are covered

4. **Isolation**: Unit tests should test individual methods in isolation

5. **Integration**: Functional tests should test complete workflows

6. **Data Consistency**: Use consistent seed values for random data generation to ensure reproducible tests

7. **Error Handling**: Test error conditions and edge cases

8. **Performance**: Include performance consistency tests where applicable

## Adding New Strategies

When adding a new strategy:

1. Create the strategy folder with standard structure
2. Create the `tests/` subfolder
3. Copy the template files from existing strategies
4. Update the strategy-specific fixtures in `conftest.py`
5. Implement unit tests in `test_unit.py`
6. Implement functional tests in `test_functional.py`
7. Update the main `pytest.ini` if needed

## Migration Notes

The existing centralized tests in `tests/` are being migrated to strategy-specific folders. During the transition period, both structures may coexist. Eventually, all strategy tests should be moved to their respective strategy folders for better organization and maintainability.