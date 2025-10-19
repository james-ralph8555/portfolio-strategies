# Risk Parity Strategy

## Overview

The Risk Parity Strategy is a modern implementation of the legacy `riskparity.py` script, adapted for the new strategy framework. It allocates between leveraged equity and bond ETFs based on risk contributions rather than capital allocations.

## Strategy Logic

### Core Concept

Risk parity aims to equalize the risk contribution of each asset in the portfolio, rather than allocating equal capital. This means assets with lower volatility (like bonds) receive higher capital allocations, while higher volatility assets (like equities) receive lower allocations.

### Assets

- **TQQQ**: ProShares UltraPro QQQ (3x leveraged NASDAQ-100)
- **TMF**: Direxion Daily 20+ Year Treasury Bull 3X ETF (3x leveraged long-term Treasury)

### Risk Budget

- **Equity (TQQQ)**: 75% of portfolio risk contribution
- **Bonds (TMF)**: 25% of portfolio risk contribution

### Algorithm

1. Calculate covariance matrix of asset returns over lookback period
2. Optimize weights to achieve target risk contributions
3. Apply risk management constraints (volatility targeting, leverage limits)
4. Rebalance when weights drift beyond specified bands

## Key Improvements over Legacy

### 1. Framework Integration

- Implements the modern `Strategy` interface
- Compatible with backtesting and portfolio management systems
- Proper configuration management through YAML

### 2. Enhanced Risk Management

- Volatility targeting to control overall portfolio risk
- Maximum leverage constraints
- Drawdown monitoring and control
- Robust error handling and fallback mechanisms

### 3. Better Optimization

- Improved constraints handling
- Bounds checking for individual weights
- Fallback to equal weights if optimization fails
- More robust numerical methods

### 4. Monitoring & Metrics

- Portfolio volatility tracking
- Risk contribution analysis
- Risk parity error measurement
- Comprehensive performance metrics

## Configuration

### Risk Parity Parameters

```yaml
risk_parity:
  risk_budget:
    equity: 0.75 # 75% risk contribution from equity
    bond: 0.25 # 25% risk contribution from bonds
  lookback_period: 90 # Days for covariance calculation
  optimization:
    tolerance: 1e-10
    method: "SLSQP"
    min_weight: 0.01
    max_weight: 0.99
```

### Risk Management

```yaml
risk_management:
  max_leverage: 3.0
  volatility_target: 0.15 # 15% annualized volatility
  drawdown_control:
    enabled: true
    max_drawdown: 0.20
```

### Rebalancing

```yaml
rebalancing:
  frequency: "monthly"
  drift_bands: 5 # 5% drift triggers rebalance
```

## Usage

### Basic Implementation

```python
from strategies.risk_parity.strategy import RiskParityStrategy

# Load configuration
config = {
    "risk_parity": {
        "risk_budget": {"equity": 0.75, "bond": 0.25},
        "lookback_period": 90
    },
    "risk_management": {
        "volatility_target": 0.15,
        "max_leverage": 3.0
    }
}

# Initialize strategy
strategy = RiskParityStrategy(config)

# Calculate weights
weights = strategy.calculate_weights(market_data)
```

### Integration with Backtesting

The strategy integrates seamlessly with the existing backtesting framework:

```python
from core.config.manager import ConfigManager
from core.registry import StrategyRegistry

# Register strategy
StrategyRegistry.register("risk_parity", RiskParityStrategy)

# Load from config file
config_manager = ConfigManager()
strategy_config = config_manager.load_strategy_config("risk_parity")
strategy = RiskParityStrategy(strategy_config)
```

## Performance Characteristics

### Expected Behavior

- **Risk Profile**: Moderate to high (due to 3x leverage)
- **Return Profile**: Aims for equity-like returns with bond-like volatility
- **Market Sensitivity**: Benefits from equity bull markets, bond rally periods
- **Drawdown Protection**: Limited - risk parity doesn't provide crash protection

### Risk Factors

- **Leverage Risk**: 3x leverage amplifies both gains and losses
- **Correlation Risk**: Strategy assumes negative correlation between equities and bonds
- **Volatility Risk**: High volatility periods can lead to frequent rebalancing
- **Concentration Risk**: Only two assets, no diversification beyond asset classes

## Comparison with Legacy

| Feature         | Legacy Script        | Modern Implementation                 |
| --------------- | -------------------- | ------------------------------------- |
| Framework       | Standalone script    | Integrated strategy interface         |
| Configuration   | Hardcoded parameters | YAML configuration                    |
| Error Handling  | Basic                | Comprehensive with fallbacks          |
| Risk Management | None                 | Volatility targeting, leverage limits |
| Monitoring      | Print statements     | Structured metrics and logging        |
| Testing         | None                 | Unit and integration tests            |
| Documentation   | Minimal              | Comprehensive README                  |

## Testing

The strategy includes comprehensive tests:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Framework integration testing
- **Functional Tests**: End-to-end workflow testing

Run tests with:

```bash
python -m pytest tests/unit/test_risk_parity.py
python -m pytest tests/functional/test_risk_parity_functional.py
```

## Monitoring

Key metrics to monitor:

1. **Risk Parity Error**: How far current allocations deviate from perfect risk parity
2. **Portfolio Volatility**: Current vs target volatility
3. **Risk Contributions**: Actual risk contribution of each asset
4. **Rebalancing Frequency**: How often the strategy rebalances
5. **Leverage Utilization**: Current leverage vs maximum allowed

## Notes

- This strategy is suitable for investors seeking equity returns with lower volatility
- The 3x leverage significantly increases risk compared to unleveraged risk parity
- Regular monitoring is essential due to the high leverage
- Consider market regime when using this strategy (correlation breakdown can be problematic)
