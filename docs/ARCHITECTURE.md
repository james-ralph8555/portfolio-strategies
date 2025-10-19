# Architecture Documentation

## Overview

The portfolio strategies framework is designed to support independent development of multiple trading strategies without merge conflicts. The architecture emphasizes modularity, extensibility, and clear separation of concerns.

## Core Components

### 1. Strategy Interface (`core/interfaces/strategy.py`)

The `Strategy` abstract base class defines the contract that all strategies must implement:

```python
class Strategy(ABC):
    @abstractmethod
    def calculate_weights(self, data: pd.DataFrame) -> Dict[str, float]
    
    @abstractmethod
    def should_rebalance(self, current_weights, target_weights) -> bool
    
    @abstractmethod
    def validate_config(self) -> bool
```

**Key Benefits:**
- Ensures consistent API across all strategies
- Enables polymorphic usage in backtesting framework
- Provides clear implementation guidelines

### 2. Strategy Registry (`core/registry.py`)

The registry system provides automatic discovery and management of strategies:

```python
registry = StrategyRegistry()
registry.discover_strategies()  # Auto-discover all strategies
strategy = registry.create_strategy("equity_crisis_alpha", config)
```

**Features:**
- Convention-based discovery (directory → class mapping)
- Dynamic loading without import conflicts
- Centralized strategy metadata management

### 3. Configuration Management (`core/config/manager.py`)

Centralized configuration system with validation and environment overrides:

```python
config_manager = ConfigManager()
config = config_manager.load_strategy_config("equity_crisis_alpha")
```

**Capabilities:**
- YAML-based configuration files
- Environment variable overrides
- Nested configuration support
- Automatic validation

## Strategy Structure

Each strategy follows a standardized directory structure:

```
strategies/strategy_name/
├── strategy.py          # Main strategy implementation
├── config.yaml          # Strategy configuration
├── README.md           # Strategy documentation
└── tests/              # Strategy-specific tests
```

### Naming Conventions

- **Directory**: `snake_case` (e.g., `equity_crisis_alpha`)
- **Class**: `PascalCase` + `Strategy` (e.g., `EquityCrisisAlphaStrategy`)
- **Config**: `snake_case` keys
- **Assets**: `UPPER_CASE` symbols

## Data Flow

```
Market Data → Strategy.calculate_weights() → Target Weights
                ↓
Current Weights → Strategy.should_rebalance() → Rebalance Decision
                ↓
Configuration → Strategy.validate_config() → Validation Result
```

## Extensibility

### Adding New Strategies

1. Create directory under `strategies/`
2. Implement strategy class inheriting from `Strategy`
3. Add configuration file
4. Strategy is automatically discovered

### Extending Core Components

- **Interface**: Add methods to `Strategy` base class
- **Registry**: Add custom discovery logic
- **Config**: Add validation rules and loaders

## Isolation Benefits

### 1. No Merge Conflicts

- Each strategy in separate directory
- Independent configuration files
- Isolated test suites

### 2. Independent Development

- Contributors can work on different strategies simultaneously
- No shared code modification required
- Clear ownership boundaries

### 3. Flexible Deployment

- Strategies can be enabled/disabled independently
- Different configurations per environment
- Easy A/B testing of strategy variants

## Performance Considerations

### Lazy Loading

- Strategies loaded only when needed
- Configuration cached after first load
- Minimal memory footprint for unused strategies

### Caching

- Strategy instances cached in registry
- Configuration validation cached
- Market data preprocessing cached per strategy

## Security

### Configuration Validation

- All configuration parameters validated
- Type checking and range validation
- Safe defaults for missing parameters

### Sandboxing

- Strategies run in isolated namespace
- No access to other strategy internals
- Controlled external dependencies

## Testing Architecture

### Unit Tests

- Strategy logic testing
- Configuration validation
- Edge case handling

### Integration Tests

- Registry discovery
- Configuration loading
- Strategy instantiation

### Backtesting Tests

- Historical performance validation
- Risk metric calculations
- Rebalancing logic verification

## Future Enhancements

### 1. Strategy Composition

- Combine multiple strategies
- Dynamic allocation between strategies
- Risk budgeting across strategies

### 2. Real-time Integration

- Live market data feeds
- Real-time rebalancing
- Performance monitoring

### 3. Advanced Analytics

- Strategy comparison tools
- Performance attribution
- Risk analytics dashboard