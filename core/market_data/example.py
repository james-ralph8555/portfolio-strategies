"""
Example usage of the Market Data Manager

This example demonstrates how to use the market data manager
to fetch and cache market data for use in strategies.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from core.market_data import MarketDataManager

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Example usage of MarketDataManager."""

    # Initialize the market data manager
    with MarketDataManager() as data_manager:
        # Example symbols
        symbols = ["SPY", "QQQ", "VTI", "AGG", "GLD"]

        # Date range for data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        print(f"Fetching price data for {symbols} from {start_date} to {end_date}")

        # Get price data
        price_data = data_manager.get_price_data(symbols, start_date, end_date)

        if not price_data.empty:
            print(f"Successfully retrieved data for {len(price_data.columns)} symbols")
            print(f"Date range: {price_data.index.min()} to {price_data.index.max()}")
            print(f"Data shape: {price_data.shape}")
            print("\nSample data:")
            print(price_data.tail())
        else:
            print("No data retrieved")

        # Get latest prices
        print("\nFetching latest prices...")
        latest_prices = data_manager.get_latest_prices(symbols)
        print("Latest prices:")
        for symbol, price in latest_prices.items():
            print(f"  {symbol}: ${price:.2f}")

        # Get metadata
        print("\nFetching metadata...")
        metadata = data_manager.get_metadata(symbols)
        for symbol, meta in metadata.items():
            if meta:
                print(
                    f"  {symbol}: {meta.get('name', 'N/A')} - {meta.get('sector', 'N/A')}"
                )

        # Get returns data
        print("\nCalculating returns...")
        returns = data_manager.get_returns_data(
            symbols, start_date, end_date, return_type="simple"
        )
        if not returns.empty:
            print(f"Returns data shape: {returns.shape}")
            print("Sample daily returns:")
            print(returns.tail())

        # Validate data coverage
        print("\nValidating data coverage...")
        coverage = data_manager.validate_data_coverage(symbols, start_date, end_date)
        for symbol, is_valid in coverage.items():
            status = "✓" if is_valid else "✗"
            print(f"  {symbol}: {status}")

        # Get cache info
        print("\nCache information:")
        cache_info = data_manager.get_cache_info()
        for key, value in cache_info.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
