# Market Data Module

This module provides a unified interface for fetching and caching market data using yfinance and DuckDB. It's designed to be used by all trading strategies in the portfolio system.

## Features

- **Data Fetching**: Robust market data fetching from yfinance with retry logic and rate limiting
- **Caching**: Efficient DuckDB-based caching with automatic expiration
- **Data Validation**: Built-in data quality checks and validation
- **Unified Interface**: Single entry point for all market data needs
- **Metadata Support**: Fetch and cache symbol metadata
- **Returns Calculation**: Built-in returns calculation (simple and log returns)

## Architecture

The module consists of three main components:

1. **MarketDataFetcher**: Handles fetching data from external sources
2. **DataCache**: Manages DuckDB-based caching with expiration
3. **MarketDataManager**: Coordinates fetching and caching, provides unified interface

## Usage

### Basic Usage

```python
from core.market_data import MarketDataManager

# Initialize the manager
with MarketDataManager() as data_manager:
    # Fetch price data
    symbols = ["SPY", "QQQ", "VTI"]
    price_data = data_manager.get_price_data(
        symbols=symbols,
        start_date="2023-01-01",
        end_date="2023-12-31"
    )

    # Get latest prices
    latest_prices = data_manager.get_latest_prices(symbols)

    # Calculate returns
    returns = data_manager.get_returns_data(
        symbols=symbols,
        start_date="2023-01-01",
        end_date="2023-12-31",
        return_type="simple"
    )
```

### Advanced Usage

```python
# Custom cache configuration
data_manager = MarketDataManager(
    cache_path="/path/to/cache.duckdb",
    cache_duration_days=7,  # Cache for 7 days
    max_retries=5,
    rate_limit_delay=1.0
)

# Force refresh from API
fresh_data = data_manager.get_price_data(
    symbols=["AAPL"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    force_refresh=True
)

# Validate data coverage
coverage = data_manager.validate_data_coverage(
    symbols=["SPY", "QQQ"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    min_coverage_ratio=0.95
)

# Get metadata
metadata = data_manager.get_metadata(["SPY", "QQQ"])
```

## Configuration

The module can be configured via the `config.yaml` file:

```yaml
cache:
  cache_path: null # Use default location
  cache_duration_days: 1

fetcher:
  max_retries: 3
  retry_delay: 1.0
  rate_limit_delay: 0.5

validation:
  min_coverage_ratio: 0.9
  max_missing_ratio: 0.1
  max_forward_fill_days: 5
```

## Data Sources

### Primary Source: yfinance

The module uses yfinance as the primary data source, providing access to:

- Stock prices (OHLCV)
- Adjusted close prices
- Corporate actions
- Symbol metadata

### Supported Data Types

- **Price Data**: Daily, weekly, monthly intervals
- **Metadata**: Company information, sector, market cap
- **Trading Calendar**: Trading days and holidays
- **Returns**: Simple and log returns

## Caching Strategy

### Cache Location

By default, cache is stored in `~/.portfolio_cache/market_data.duckdb`

### Cache Duration

- Default: 1 day
- Configurable via `cache_duration_days`
- Automatic cleanup of expired data

### Cache Structure

```sql
-- Price data table
CREATE TABLE price_data (
    symbol VARCHAR,
    date DATE,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    adjusted_close FLOAT,
    created_at TIMESTAMP,
    PRIMARY KEY (symbol, date)
);

-- Metadata table
CREATE TABLE metadata (
    symbol VARCHAR PRIMARY KEY,
    name VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    market_cap BIGINT,
    currency VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Error Handling

The module includes comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff
- **Rate Limiting**: Built-in delays to avoid API limits
- **Data Validation**: Quality checks and missing data handling
- **Fallback**: Returns stale cached data if fresh fetch fails
- **Logging**: Detailed logging for debugging

## Performance Considerations

### Optimization Features

- **Connection Pooling**: Reuses database connections
- **Batch Operations**: Efficient bulk inserts and queries
- **Indexing**: Optimized database indexes for fast queries
- **Memory Management**: Efficient data handling for large datasets

### Best Practices

1. **Use Context Managers**: Always use `with` statement for proper cleanup
2. **Batch Requests**: Fetch multiple symbols in single requests
3. **Appropriate Cache Duration**: Balance freshness with performance
4. **Handle Missing Data**: Check data coverage before analysis

## Integration with Strategies

### Strategy Integration Example

```python
from core.interfaces.strategy import Strategy
from core.market_data import MarketDataManager

class MyStrategy(Strategy):
    def __init__(self, config=None):
        super().__init__(config)
        self.data_manager = MarketDataManager()

    def calculate_weights(self, data):
        # Strategy logic here
        return weights

    def get_market_data(self, start_date, end_date):
        return self.data_manager.get_price_data(
            symbols=self.assets,
            start_date=start_date,
            end_date=end_date
        )
```

## Testing

The module includes comprehensive tests:

```bash
# Run all market data tests
pytest tests/unit/test_market_data.py

# Run with coverage
pytest tests/unit/test_market_data.py --cov=core.market_data
```

## Troubleshooting

### Common Issues

1. **Cache Corruption**: Clear cache with `data_manager.clear_cache()`
2. **API Limits**: Increase `rate_limit_delay` in configuration
3. **Missing Data**: Check symbol validity with `validate_symbols()`
4. **Performance**: Use appropriate cache duration and batch requests

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('core.market_data').setLevel(logging.DEBUG)
```

## Dependencies

- `pandas>=1.5.0` - Data manipulation
- `numpy>=1.21.0` - Numerical operations
- `yfinance>=0.2.0` - Market data source
- `duckdb>=0.9.0` - Caching database
