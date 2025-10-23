"""
Data Cache Module

Provides DuckDB-based caching for market data to improve performance
and reduce API calls to external data sources.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


class DataCache:
    """
    DuckDB-based cache for market data with automatic expiration.

    Provides efficient storage and retrieval of market data with
    configurable cache duration and automatic cleanup.
    """

    def __init__(self, cache_path: str | None = None, cache_duration_days: int = 1):
        """
        Initialize the data cache.

        Args:
            cache_path: Path to DuckDB database file
            cache_duration_days: Number of days to cache data before refresh
        """
        if cache_path is None:
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            cache_path = str(cache_dir / "market_data.duckdb")

        self.cache_path = cache_path
        self.cache_duration = timedelta(days=cache_duration_days)
        self.conn = duckdb.connect(self.cache_path)
        self._initialize_cache()

    def _ensure_connection(self) -> None:
        """Ensure database connection is available."""
        if self.conn is None:
            self.conn = duckdb.connect(self.cache_path)

    def _initialize_cache(self) -> None:
        """Initialize the cache database and create tables if needed."""
        self._ensure_connection()

        # Create sequences for autoincrementing primary keys
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS symbols_id_seq START 1")
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS price_data_id_seq START 1")

        # Create symbols table for proper foreign key relationships
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id BIGINT PRIMARY KEY DEFAULT nextval('symbols_id_seq'),
                symbol VARCHAR UNIQUE NOT NULL,
                name VARCHAR,
                sector VARCHAR,
                industry VARCHAR,
                market_cap BIGINT,
                currency VARCHAR,
                exchange VARCHAR,
                country VARCHAR,
                timezone VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create tables for different data types
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                id BIGINT PRIMARY KEY DEFAULT nextval('price_data_id_seq'),
                symbol_id BIGINT NOT NULL,
                date DATE NOT NULL,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume BIGINT,
                adjusted_close FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol_id) REFERENCES symbols(id),
                UNIQUE(symbol_id, date)
            )
        """)

        # Create indexes for better performance
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_symbol_date ON price_data(symbol_id, date)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_created_at ON price_data(created_at)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_symbols_symbol ON symbols(symbol)"
        )

    def get_price_data(
        self, symbols: list[str], start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Retrieve price data from cache.

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with price data, empty if not found or expired
        """
        self._ensure_connection()

        if not self._is_cache_valid(symbols, start_date, end_date):
            return pd.DataFrame()

        placeholders = ",".join(["?" for _ in symbols])
        query = f"""
            SELECT s.symbol, p.date, p.open, p.high, p.low, p.close, p.volume, p.adjusted_close
            FROM price_data p
            JOIN symbols s ON p.symbol_id = s.id
            WHERE s.symbol IN ({placeholders})
            AND p.date BETWEEN ? AND ?
            ORDER BY s.symbol, p.date
        """

        try:
            result = self.conn.execute(
                query, symbols + [start_date, end_date]
            ).fetchdf()

            if not result.empty:
                # Pivot to have symbols as columns
                pivot_data = result.pivot(
                    index="date", columns="symbol", values="adjusted_close"
                )
                return pivot_data.sort_index()

        except Exception as e:
            print(f"Error retrieving cached data: {e}")

        return pd.DataFrame()

    def store_price_data(self, data: pd.DataFrame, symbols: list[str]) -> None:
        """
        Store price data in cache.

        Args:
            data: DataFrame with price data (indexed by date, columns are symbols)
            symbols: List of ticker symbols
        """
        self._ensure_connection()

        if data.empty:
            return

        # Ensure all symbols exist in symbols table
        for symbol in symbols:
            self.conn.execute(
                "INSERT OR IGNORE INTO symbols (symbol) VALUES (?)", [symbol]
            )

        # Convert to long format for storage
        long_data = []
        for symbol in symbols:
            if symbol in data.columns:
                symbol_data = data[symbol].dropna()
                for date, price in symbol_data.items():
                    long_data.append(
                        {
                            "symbol": symbol,
                            "date": date,
                            "open": price,  # Placeholder values
                            "high": price,
                            "low": price,
                            "close": price,  # Using adjusted_close as close for simplicity
                            "volume": 0,
                            "adjusted_close": price,
                            "created_at": datetime.now(),
                        }
                    )

        if long_data:
            df_to_store = pd.DataFrame(long_data)

            # Remove existing data for these symbols and date range
            min_date = df_to_store["date"].min()
            max_date = df_to_store["date"].max()
            placeholders = ",".join(["?" for _ in symbols])

            self.conn.execute(
                f"""
                DELETE FROM price_data
                USING symbols s
                WHERE price_data.symbol_id = s.id
                AND s.symbol IN ({placeholders})
                AND price_data.date BETWEEN ? AND ?
            """,
                symbols + [min_date, max_date],
            )

            # Insert new data using subquery to get symbol_id
            self.conn.execute(
                f"""
                INSERT INTO price_data (symbol_id, date, open, high, low, close, volume, adjusted_close, created_at)
                SELECT s.id, t.date, t.open, t.high, t.low, t.close, t.volume, t.adjusted_close, t.created_at
                FROM df_to_store t
                JOIN symbols s ON t.symbol = s.symbol
                WHERE s.symbol IN ({placeholders})
            """,
                symbols,
            )

    def get_metadata(self, symbol: str) -> dict[str, Any]:
        """
        Retrieve metadata for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with metadata, empty if not found
        """
        self._ensure_connection()

        try:
            result = self.conn.execute(
                "SELECT * FROM symbols WHERE symbol = ?", [symbol]
            ).fetchdf()

            if not result.empty:
                return result.iloc[0].to_dict()
        except Exception as e:
            print(f"Error retrieving metadata: {e}")

        return {}

    def store_metadata(self, symbol: str, metadata: dict[str, Any]) -> None:
        """
        Store metadata for a symbol.

        Args:
            symbol: Ticker symbol
            metadata: Dictionary with metadata
        """
        self._ensure_connection()

        # Filter metadata to only include valid columns
        filtered_metadata = {
            "symbol": symbol,
            "name": metadata.get("name", ""),
            "sector": metadata.get("sector", ""),
            "industry": metadata.get("industry", ""),
            "market_cap": metadata.get("market_cap", 0),
            "currency": metadata.get("currency", "USD"),
            "exchange": metadata.get("exchange", ""),
            "country": metadata.get("country", ""),
            "timezone": metadata.get("timezone", ""),
        }

        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO symbols (symbol, name, sector, industry, market_cap, currency, exchange, country, timezone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    filtered_metadata["symbol"],
                    filtered_metadata["name"],
                    filtered_metadata["sector"],
                    filtered_metadata["industry"],
                    filtered_metadata["market_cap"],
                    filtered_metadata["currency"],
                    filtered_metadata["exchange"],
                    filtered_metadata["country"],
                    filtered_metadata["timezone"],
                ],
            )
        except Exception as e:
            print(f"Error storing metadata: {e}")

    def _is_cache_valid(
        self, symbols: list[str], start_date: str, end_date: str
    ) -> bool:
        """
        Check if cached data is still valid (not expired).

        Args:
            symbols: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            True if cache is valid, False otherwise
        """
        self._ensure_connection()

        try:
            placeholders = ",".join(["?" for _ in symbols])
            result = self.conn.execute(
                f"""
                SELECT MAX(p.created_at) as max_created_at
                FROM price_data p
                JOIN symbols s ON p.symbol_id = s.id
                WHERE s.symbol IN ({placeholders})
                AND p.date BETWEEN ? AND ?
            """,
                symbols + [start_date, end_date],
            ).fetchone()

            if result and result[0]:
                max_created = pd.to_datetime(result[0])
                return datetime.now() - max_created < self.cache_duration

        except Exception as e:
            print(f"Error checking cache validity: {e}")

        return False

    def clear_cache(self, symbols: list[str] | None = None) -> None:
        """
        Clear cached data.

        Args:
            symbols: List of symbols to clear, if None clears all
        """
        self._ensure_connection()

        try:
            if symbols:
                placeholders = ",".join(["?" for _ in symbols])
                self.conn.execute(
                    f"""
                    DELETE FROM price_data
                    USING symbols s
                    WHERE price_data.symbol_id = s.id
                    AND s.symbol IN ({placeholders})
                """,
                    symbols,
                )
                self.conn.execute(
                    f"DELETE FROM symbols WHERE symbol IN ({placeholders})", symbols
                )
            else:
                self.conn.execute("DELETE FROM price_data")
                self.conn.execute("DELETE FROM symbols")
        except Exception as e:
            print(f"Error clearing cache: {e}")

    def cleanup_expired_data(self) -> None:
        """Remove expired data from cache."""
        self._ensure_connection()

        try:
            cutoff_date = datetime.now() - self.cache_duration
            self.conn.execute(
                "DELETE FROM price_data WHERE created_at < ?", [cutoff_date]
            )
        except Exception as e:
            print(f"Error cleaning up expired data: {e}")

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
