"""
Unit tests for Market Data module
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from core.market_data.cache import DataCache
from core.market_data.fetcher import MarketDataFetcher
from core.market_data.manager import MarketDataManager


class TestDataCache:
    """Test cases for DataCache class."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.temp_dir, "test_cache.duckdb")
        self.cache = DataCache(self.cache_path, cache_duration_days=1)

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.cache.close()
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)
        os.rmdir(self.temp_dir)

    def test_cache_initialization(self) -> None:
        """Test cache initialization creates tables."""
        # Check that tables exist
        tables = self.cache.conn.execute("SHOW TABLES").fetchall()
        table_names = [row[0] for row in tables]

        assert "price_data" in table_names
        assert "metadata" in table_names

    def test_store_and_retrieve_price_data(self) -> None:
        """Test storing and retrieving price data."""
        # Create test data
        dates = pd.date_range("2023-01-01", "2023-01-05")
        symbols = ["AAPL", "MSFT"]
        data = pd.DataFrame(
            {
                "AAPL": [100.0, 101.0, 102.0, 103.0, 104.0],
                "MSFT": [200.0, 201.0, 202.0, 203.0, 204.0],
            },
            index=dates,
        )

        # Store data
        self.cache.store_price_data(data, symbols)

        # Retrieve data
        retrieved = self.cache.get_price_data(symbols, "2023-01-01", "2023-01-05")

        assert not retrieved.empty
        assert len(retrieved.columns) == 2
        assert "AAPL" in retrieved.columns
        assert "MSFT" in retrieved.columns

    def test_cache_expiration(self):
        """Test cache expiration logic."""
        # This would require mocking datetime.now()
        # For now, just test the basic structure
        assert self.cache.cache_duration.days == 1


class TestMarketDataFetcher:
    """Test cases for MarketDataFetcher class."""

    def setup_method(self):
        """Setup test environment."""
        self.fetcher = MarketDataFetcher(max_retries=2, retry_delay=0.1)

    @patch("yfinance.Tickers")
    def test_fetch_price_data_success(self, mock_tickers):
        """Test successful price data fetching."""
        # Mock yfinance response
        mock_data = Mock()
        mock_data.empty = False
        mock_data.__getitem__ = Mock(return_value=Mock())
        mock_data.__contains__ = Mock(return_value=True)

        mock_tickers_instance = Mock()
        mock_tickers_instance.history.return_value = mock_data
        mock_tickers.return_value = mock_tickers_instance

        # Test fetch
        self.fetcher.fetch_price_data(["AAPL"], "2023-01-01", "2023-01-05")

        # Verify calls were made (may be called multiple times due to retry logic)
        assert mock_tickers.call_count >= 1
        mock_tickers.assert_called_with(["AAPL"])
        assert mock_tickers_instance.history.call_count >= 1

    @patch("yfinance.Ticker")
    def test_fetch_metadata_success(self, mock_ticker):
        """Test successful metadata fetching."""
        # Mock yfinance response
        mock_info = {
            "longName": "Apple Inc.",
            "sector": "Technology",
            "marketCap": 3000000000000,
        }

        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance

        # Test fetch
        result = self.fetcher.fetch_metadata(["AAPL"])

        assert "AAPL" in result
        assert result["AAPL"]["name"] == "Apple Inc."
        assert result["AAPL"]["sector"] == "Technology"


class TestMarketDataManager:
    """Test cases for MarketDataManager class."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.temp_dir, "test_manager_cache.duckdb")
        self.manager = MarketDataManager(cache_path=self.cache_path)

    def teardown_method(self):
        """Cleanup test environment."""
        self.manager.close()
        if os.path.exists(self.cache_path):
            os.remove(self.cache_path)
        os.rmdir(self.temp_dir)

    def test_manager_initialization(self):
        """Test manager initialization."""
        assert self.manager.cache is not None
        assert self.manager.fetcher is not None

    @patch.object(MarketDataFetcher, "validate_symbols")
    def test_get_price_data_with_invalid_symbols(self, mock_validate):
        """Test handling of invalid symbols."""
        mock_validate.return_value = (["AAPL"], ["INVALID"])

        self.manager.get_price_data(["AAPL", "INVALID"], "2023-01-01", "2023-01-05")

        # Should only return data for valid symbols
        mock_validate.assert_called_once_with(["AAPL", "INVALID"])

    def test_get_returns_data(self):
        """Test returns data calculation."""
        # Create mock price data
        dates = pd.date_range("2023-01-01", "2023-01-03")
        price_data = pd.DataFrame(
            {"AAPL": [100.0, 101.0, 102.0], "MSFT": [200.0, 201.0, 202.0]}, index=dates
        )

        # Mock the get_price_data method
        self.manager.get_price_data = Mock(return_value=price_data)

        # Test simple returns
        returns = self.manager.get_returns_data(
            ["AAPL", "MSFT"], "2023-01-01", "2023-01-03"
        )

        assert not returns.empty
        assert len(returns.columns) == 2
        # Check that returns are calculated correctly
        assert (
            abs(returns["AAPL"].iloc[1] - 0.00990099) < 1e-6
        )  # (101-100)/100 = 0.00990099

    def test_cache_info(self):
        """Test cache info retrieval."""
        info = self.manager.get_cache_info()
        assert isinstance(info, dict)
        assert "unique_symbols" in info
        assert "total_records" in info


@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data."""
    dates = pd.date_range("2023-01-01", "2023-01-10")
    return pd.DataFrame(
        {
            "SPY": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
            ],
            "QQQ": [
                200.0,
                202.0,
                204.0,
                206.0,
                208.0,
                210.0,
                212.0,
                214.0,
                216.0,
                218.0,
            ],
        },
        index=dates,
    )


@pytest.fixture
def sample_metadata():
    """Fixture providing sample metadata."""
    return {
        "SPY": {
            "name": "SPDR S&P 500 ETF Trust",
            "sector": "ETF",
            "market_cap": 400000000000,
        },
        "QQQ": {
            "name": "Invesco QQQ Trust",
            "sector": "ETF",
            "market_cap": 200000000000,
        },
    }


class TestMarketDataIntegration:
    """Integration tests for market data components."""

    def test_full_workflow(self, sample_price_data, sample_metadata):
        """Test complete workflow from fetch to cache to retrieve."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = os.path.join(temp_dir, "integration_test.duckdb")

            # Initialize manager
            manager = MarketDataManager(cache_path=cache_path)

            try:
                # Mock the fetcher to return our sample data
                manager.fetcher.fetch_price_data = Mock(return_value=sample_price_data)
                manager.fetcher.fetch_metadata = Mock(return_value=sample_metadata)
                manager.fetcher.validate_symbols = Mock(
                    return_value=(["SPY", "QQQ"], [])
                )

                # Get price data (should fetch and cache)
                data = manager.get_price_data(
                    ["SPY", "QQQ"], "2023-01-01", "2023-01-10"
                )
                assert not data.empty
                assert len(data.columns) == 2

                # Get metadata
                metadata = manager.get_metadata(["SPY", "QQQ"])
                assert len(metadata) == 2
                assert metadata["SPY"]["name"] == "SPDR S&P 500 ETF Trust"

                # Get data again (should use cache)
                manager.fetcher.fetch_price_data.reset_mock()
                cached_data = manager.get_price_data(
                    ["SPY", "QQQ"], "2023-01-01", "2023-01-10"
                )
                assert not cached_data.empty

                # Fetcher should not be called again due to cache
                manager.fetcher.fetch_price_data.assert_not_called()

            finally:
                manager.close()
