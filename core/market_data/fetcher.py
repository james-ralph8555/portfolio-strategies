"""
Market Data Fetcher Module

Handles fetching market data from external sources using yfinance API.
Provides retry logic, rate limiting, and data validation.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf


class MarketDataFetcher:
    """
    Fetches market data from yfinance with retry logic and validation.

    Provides robust data fetching with automatic retries, rate limiting,
    and data quality checks to ensure reliable market data.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_delay: float = 0.5,
    ):
        """
        Initialize the market data fetcher.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            rate_limit_delay: Delay between requests to avoid rate limiting
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)

    def fetch_price_data(
        self, symbols: list[str], start_date: str, end_date: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch price data for given symbols and date range.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval (1d, 1w, 1mo, etc.)

        Returns:
            DataFrame with price data indexed by date, columns are symbols
        """
        if not symbols:
            return pd.DataFrame()

        # Apply rate limiting
        self._apply_rate_limit()

        for attempt in range(self.max_retries):
            try:
                data = self._fetch_with_validation(
                    symbols, start_date, end_date, interval
                )
                if not data.empty:
                    return data

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff

        self.logger.error(
            f"Failed to fetch data for {symbols} after {self.max_retries} attempts"
        )
        return pd.DataFrame()

    def _fetch_with_validation(
        self, symbols: list[str], start_date: str, end_date: str, interval: str
    ) -> pd.DataFrame:
        """
        Fetch data with validation and quality checks.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval

        Returns:
            Validated DataFrame with price data
        """
        # Download data using yfinance
        tickers = yf.Tickers(symbols)
        data = tickers.history(
            start=start_date, end=end_date, interval=interval, period=None
        )

        if data is None or data.empty:
            return pd.DataFrame()

        # Extract adjusted close prices
        if "Adj Close" in data.columns:
            price_data = data["Adj Close"]
        elif "Close" in data.columns:
            price_data = data["Close"]
        else:
            raise ValueError("No price data found in yfinance response")

        # Validate data quality
        price_data = self._validate_data(price_data, symbols)

        return price_data

    def _validate_data(
        self, data: pd.DataFrame | pd.Series, symbols: list[str]
    ) -> pd.DataFrame:
        """
        Validate and clean the fetched data.

        Args:
            data: Raw price data
            symbols: Expected symbols

        Returns:
            Cleaned and validated data
        """
        if data is None or data.empty:
            return pd.DataFrame()

        # Convert Series to DataFrame if needed
        if isinstance(data, pd.Series):
            data = data.to_frame()

        # Check for missing data
        missing_data = data.isnull().sum()
        if missing_data.any():
            self.logger.warning(
                f"Missing data detected: {missing_data[missing_data > 0].to_dict()}"
            )

        # Forward fill missing values (limited)
        data = data.ffill(limit=5)

        # Remove symbols with excessive missing data
        max_missing_ratio = 0.1  # Allow up to 10% missing data
        for symbol in symbols:
            if symbol in data.columns:
                missing_ratio = data[symbol].isnull().sum() / len(data)
                if missing_ratio > max_missing_ratio:
                    self.logger.warning(
                        f"Dropping {symbol} due to excessive missing data: {missing_ratio:.2%}"
                    )
                    data = data.drop(columns=[symbol])

        # Remove any remaining rows with all NaN values
        data = data.dropna(how="all")

        # Sort by date
        data = data.sort_index()

        return data

    def fetch_metadata(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """
        Fetch metadata for given symbols.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dictionary mapping symbols to their metadata
        """
        metadata = {}

        for symbol in symbols:
            try:
                # Apply rate limiting
                self._apply_rate_limit()

                ticker = yf.Ticker(symbol)
                info = ticker.info

                # Extract relevant metadata
                symbol_metadata = {
                    "name": info.get("longName", info.get("shortName", "")),
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "market_cap": info.get("marketCap", 0),
                    "currency": info.get("currency", "USD"),
                    "exchange": info.get("exchange", ""),
                    "country": info.get("country", ""),
                    "timezone": info.get("timeZoneFullName", ""),
                }

                metadata[symbol] = symbol_metadata

            except Exception as e:
                self.logger.warning(f"Failed to fetch metadata for {symbol}: {e}")
                metadata[symbol] = {}

        return metadata

    def fetch_latest_prices(self, symbols: list[str]) -> dict[str, float]:
        """
        Fetch latest prices for given symbols.

        Args:
            symbols: List of ticker symbols

        Returns:
            Dictionary mapping symbols to their latest prices
        """
        if not symbols:
            return {}

        # Apply rate limiting
        self._apply_rate_limit()

        try:
            # Get today's date and yesterday for comparison
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

            data = self.fetch_price_data(symbols, start_date, end_date, interval="1d")

            if data.empty:
                return {}

            # Get the last available price for each symbol
            latest_prices = {}
            for symbol in symbols:
                if symbol in data.columns:
                    latest_price = data[symbol].dropna().iloc[-1]
                    latest_prices[symbol] = float(latest_price)

            return latest_prices

        except Exception as e:
            self.logger.error(f"Failed to fetch latest prices: {e}")
            return {}

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = int(time.time())

    def validate_symbols(self, symbols: list[str]) -> tuple[list[str], list[str]]:
        """
        Validate which symbols exist and can be fetched.

        Args:
            symbols: List of ticker symbols to validate

        Returns:
            Tuple of (valid_symbols, invalid_symbols)
        """
        valid_symbols = []
        invalid_symbols = []

        for symbol in symbols:
            try:
                # Apply rate limiting
                self._apply_rate_limit()

                ticker = yf.Ticker(symbol)
                # Try to get some basic info to validate the symbol
                info = ticker.info

                # Check if we got valid data
                if info and "regularMarketPrice" in info:
                    valid_symbols.append(symbol)
                else:
                    invalid_symbols.append(symbol)

            except Exception as e:
                self.logger.warning(f"Invalid symbol {symbol}: {e}")
                invalid_symbols.append(symbol)

        return valid_symbols, invalid_symbols

    def get_trading_days(self, start_date: str, end_date: str) -> pd.DatetimeIndex:
        """
        Get trading days between two dates.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DatetimeIndex of trading days
        """
        try:
            # Use a major index like SPY to get trading calendar
            spy_data = self.fetch_price_data(["SPY"], start_date, end_date)
            if not spy_data.empty:
                return pd.DatetimeIndex(spy_data.index)
        except Exception as e:
            self.logger.warning(f"Failed to get trading days from SPY: {e}")

        # Fallback to business days
        return pd.DatetimeIndex(pd.bdate_range(start=start_date, end=end_date))
