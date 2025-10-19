"""
Market Data Module

Provides common market data fetching and caching functionality for all strategies.
Uses yfinance for data fetching and DuckDB for efficient storage and retrieval.
"""

from .cache import DataCache
from .fetcher import MarketDataFetcher
from .manager import MarketDataManager

__all__ = ["MarketDataFetcher", "DataCache", "MarketDataManager"]
