"""
Market Data Manager Module

Coordinates market data fetching and caching to provide a unified interface
for all strategies to access market data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from .cache import DataCache
from .fetcher import MarketDataFetcher


class MarketDataManager:
    """
    Unified market data manager that coordinates fetching and caching.

    Provides a single interface for strategies to access market data,
    automatically handling caching, fetching, and data validation.
    """

    def __init__(
        self,
        cache_path: str | None = None,
        cache_duration_days: int = 1,
        max_retries: int = 3,
        rate_limit_delay: float = 0.5,
    ):
        """
        Initialize the market data manager.

        Args:
            cache_path: Path to cache database
            cache_duration_days: Number of days to cache data
            max_retries: Maximum retry attempts for fetching
            rate_limit_delay: Delay between requests in seconds
        """
        self.cache = DataCache(cache_path, cache_duration_days)
        self.fetcher = MarketDataFetcher(max_retries, rate_limit_delay=rate_limit_delay)
        self.logger = logging.getLogger(__name__)

    def get_price_data(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        force_refresh: bool = False,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get price data for symbols, using cache when available.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            force_refresh: Force refresh from API even if cached data exists
            interval: Data interval (1d, 1w, 1mo, etc.)

        Returns:
            DataFrame with price data indexed by date, columns are symbols
        """
        if not symbols:
            return pd.DataFrame()

        # Validate symbols first
        valid_symbols, invalid_symbols = self.fetcher.validate_symbols(symbols)
        if invalid_symbols:
            self.logger.warning(f"Invalid symbols will be excluded: {invalid_symbols}")

        if not valid_symbols:
            self.logger.error("No valid symbols provided")
            return pd.DataFrame()

        # Try to get from cache first (unless force refresh)
        if not force_refresh:
            cached_data = self.cache.get_price_data(valid_symbols, start_date, end_date)
            if not cached_data.empty:
                self.logger.info(
                    f"Retrieved cached data for {len(cached_data.columns)} symbols"
                )
                return cached_data

        # Fetch from API
        self.logger.info(f"Fetching fresh data for {valid_symbols}")
        fresh_data = self.fetcher.fetch_price_data(
            valid_symbols, start_date, end_date, interval
        )

        if not fresh_data.empty:
            # Store in cache
            self.cache.store_price_data(fresh_data, valid_symbols)
            self.logger.info(f"Cached fresh data for {len(fresh_data.columns)} symbols")
            return fresh_data
        else:
            # If fresh fetch fails, try to return stale cached data
            stale_data = self.cache.get_price_data(valid_symbols, start_date, end_date)
            if not stale_data.empty:
                self.logger.warning("Using stale cached data due to fetch failure")
                return stale_data

        return pd.DataFrame()

    def get_latest_prices(
        self, symbols: list[str], force_refresh: bool = False
    ) -> dict[str, float]:
        """
        Get latest prices for symbols.

        Args:
            symbols: List of ticker symbols
            force_refresh: Force refresh from API

        Returns:
            Dictionary mapping symbols to latest prices
        """
        if not symbols:
            return {}

        # Validate symbols
        valid_symbols, invalid_symbols = self.fetcher.validate_symbols(symbols)
        if invalid_symbols:
            self.logger.warning(f"Invalid symbols will be excluded: {invalid_symbols}")

        if not valid_symbols:
            return {}

        # For latest prices, always try fresh data first
        if force_refresh:
            return self.fetcher.fetch_latest_prices(valid_symbols)

        # Try to get recent cached data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        cached_data = self.cache.get_price_data(valid_symbols, start_date, end_date)
        if not cached_data.empty:
            latest_prices = {}
            for symbol in valid_symbols:
                if symbol in cached_data.columns:
                    latest_price = cached_data[symbol].dropna().iloc[-1]
                    latest_prices[symbol] = float(latest_price)
            return latest_prices

        # Fallback to fresh fetch
        return self.fetcher.fetch_latest_prices(valid_symbols)

    def get_metadata(
        self, symbols: list[str], force_refresh: bool = False
    ) -> dict[str, dict[str, Any]]:
        """
        Get metadata for symbols.

        Args:
            symbols: List of ticker symbols
            force_refresh: Force refresh from API

        Returns:
            Dictionary mapping symbols to metadata
        """
        if not symbols:
            return {}

        metadata = {}

        for symbol in symbols:
            if not force_refresh:
                # Try cache first
                cached_meta = self.cache.get_metadata(symbol)
                if cached_meta:
                    metadata[symbol] = cached_meta
                    continue

            # Fetch fresh metadata
            fresh_meta = self.fetcher.fetch_metadata([symbol])
            if symbol in fresh_meta:
                metadata[symbol] = fresh_meta[symbol]
                self.cache.store_metadata(symbol, fresh_meta[symbol])

        return metadata

    def get_returns_data(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        return_type: str = "simple",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Get returns data for symbols.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            return_type: Type of returns ('simple' or 'log')
            force_refresh: Force refresh from API

        Returns:
            DataFrame with returns data
        """
        price_data = self.get_price_data(symbols, start_date, end_date, force_refresh)

        if price_data.empty:
            return pd.DataFrame()

        if return_type == "simple":
            returns = price_data.pct_change().dropna()
        elif return_type == "log":
            returns = np.log(price_data / price_data.shift(1)).dropna()
        else:
            raise ValueError(f"Invalid return_type: {return_type}")

        return returns

    def get_trading_days(self, start_date: str, end_date: str) -> pd.DatetimeIndex:
        """
        Get trading days between two dates.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DatetimeIndex of trading days
        """
        return self.fetcher.get_trading_days(start_date, end_date)

    def validate_data_coverage(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        min_coverage_ratio: float = 0.9,
    ) -> dict[str, bool]:
        """
        Validate data coverage for symbols over a date range.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            min_coverage_ratio: Minimum required data coverage ratio

        Returns:
            Dictionary mapping symbols to coverage validation result
        """
        data = self.get_price_data(symbols, start_date, end_date)

        if data.empty:
            return dict.fromkeys(symbols, False)

        # Get expected trading days
        trading_days = self.get_trading_days(start_date, end_date)
        expected_days = len(trading_days)

        coverage_results = {}
        for symbol in symbols:
            if symbol in data.columns:
                actual_days = data[symbol].dropna().count()
                coverage_ratio = actual_days / expected_days if expected_days > 0 else 0
                coverage_results[symbol] = coverage_ratio >= min_coverage_ratio
            else:
                coverage_results[symbol] = False

        return coverage_results

    def clear_cache(self, symbols: list[str] | None = None) -> None:
        """
        Clear cached data.

        Args:
            symbols: List of symbols to clear, if None clears all
        """
        self.cache.clear_cache(symbols)
        self.logger.info(f"Cleared cache for symbols: {symbols if symbols else 'all'}")

    def cleanup_expired_data(self) -> None:
        """Remove expired data from cache."""
        self.cache.cleanup_expired_data()
        self.logger.info("Cleaned up expired cache data")

    def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about cache status.

        Returns:
            Dictionary with cache information
        """
        try:
            self.cache._ensure_connection()
            # Get basic cache statistics
            result = self.cache.conn.execute("""
                SELECT
                    COUNT(DISTINCT s.symbol) as unique_symbols,
                    COUNT(*) as total_records,
                    MIN(p.date) as earliest_date,
                    MAX(p.date) as latest_date
                FROM price_data p
                JOIN symbols s ON p.symbol_id = s.id
            """).fetchone()

            if result:
                return {
                    "unique_symbols": result[0],
                    "total_records": result[1],
                    "earliest_date": result[2],
                    "latest_date": result[3],
                    "cache_duration_days": self.cache.cache_duration.days,
                }
        except Exception as e:
            self.logger.error(f"Error getting cache info: {e}")

        return {}

    def close(self) -> None:
        """Close connections and cleanup resources."""
        self.cache.close()

    def __enter__(self) -> "MarketDataManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
