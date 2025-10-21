"""
FastAPI Backend for Portfolio Management System

Provides REST API endpoints for managing market data, running backtests,
and viewing results from DuckDB databases.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.market_data.manager import MarketDataManager
from unified_backtest import UnifiedBacktester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
market_data_manager: MarketDataManager | None = None
backtester: UnifiedBacktester | None = None


def _sanitize_for_json(obj: Any) -> Any:
    """Sanitize object for JSON serialization by handling inf/NaN values."""
    import math

    import numpy as np

    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if math.isinf(obj) or math.isnan(obj):
            return 0.0 if math.isnan(obj) else 999999999.0  # Large finite value for inf
        return float(obj)
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return 0.0 if math.isnan(obj) else 999999999.0  # Large finite value for inf
        return obj
    elif isinstance(obj, np.ndarray):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    else:
        return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global market_data_manager, backtester
    try:
        market_data_manager = MarketDataManager()
        backtester = UnifiedBacktester()
        logger.info("Backend services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize backend services: {e}")
        yield
    finally:
        # Shutdown
        if market_data_manager:
            market_data_manager.close()
        if backtester:
            backtester.close()
        logger.info("Backend services shut down")


# Initialize FastAPI app
app = FastAPI(
    title="Portfolio Management API",
    description="API for managing portfolio strategies, market data, and backtesting",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # SolidJS dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# Pydantic models
class BacktestRequest(BaseModel):
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float = 100000.0


class BacktestResponse(BaseModel):
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    metrics: dict[str, float]
    status: str
    message: str | None = None


class StrategyInfo(BaseModel):
    name: str
    description: str | None = None
    assets: list[str]
    config: dict[str, Any]


class MarketDataRequest(BaseModel):
    symbols: list[str]
    start_date: str
    end_date: str
    force_refresh: bool = False


class MarketDataResponse(BaseModel):
    symbols: list[str]
    data: dict[str, list[dict[str, Any]]]
    metadata: dict[str, Any]


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Strategy endpoints
@app.get("/strategies", response_model=list[StrategyInfo])
async def get_strategies():
    """Get list of available strategies."""
    if not backtester:
        raise HTTPException(status_code=500, detail="Backtester not initialized")

    strategies = []
    for name, strategy in backtester.strategies.items():
        try:
            if strategy is None:
                # Skip strategies that failed to load
                continue

            assets = strategy.get_assets()
            config = getattr(strategy, "config", {})
            description = config.get("description", f"{name} strategy")

            strategies.append(
                StrategyInfo(
                    name=name, description=description, assets=assets, config=config
                )
            )
        except Exception as e:
            logger.error(f"Error getting strategy info for {name}: {e}")
            continue

    return strategies


@app.get("/strategies/{strategy_name}", response_model=StrategyInfo)
async def get_strategy(strategy_name: str):
    """Get detailed information about a specific strategy."""
    if not backtester or strategy_name not in backtester.strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")

    strategy = backtester.strategies[strategy_name]
    try:
        assets = strategy.get_assets()
        config = getattr(strategy, "config", {})
        description = config.get("description", f"{strategy_name} strategy")

        return StrategyInfo(
            name=strategy_name, description=description, assets=assets, config=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting strategy info: {e}"
        ) from e


# Backtest endpoints
@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run a backtest for a specific strategy."""
    if not backtester:
        raise HTTPException(status_code=500, detail="Backtester not initialized")

    try:
        results = backtester.run_backtest(
            request.strategy_name,
            request.start_date,
            request.end_date,
            request.initial_capital,
        )

        # Sanitize metrics to ensure JSON compatibility
        sanitized_metrics = {}
        for key, value in results["metrics"].items():
            if isinstance(value, float):
                if value == float("inf") or value == float("-inf"):
                    sanitized_metrics[key] = 999.0
                elif value != value:  # Check for NaN
                    sanitized_metrics[key] = 0.0
                else:
                    sanitized_metrics[key] = value
            else:
                sanitized_metrics[key] = value

        return BacktestResponse(
            strategy_name=results["strategy_name"],
            start_date=results["start_date"],
            end_date=results["end_date"],
            initial_capital=results["initial_capital"],
            final_value=results["final_value"],
            metrics=sanitized_metrics,
            status="completed",
        )
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {e}") from e


@app.get("/backtest/results")
async def get_backtest_results():
    """Get all backtest results."""
    if not backtester:
        raise HTTPException(status_code=500, detail="Backtester not initialized")

    try:
        summary = backtester.get_results_summary()
        # Sanitize float values in the summary
        summary_dict = summary.to_dict(orient="records")
        for record in summary_dict:
            for key, value in record.items():
                if isinstance(value, float):
                    if value == float("inf") or value == float("-inf"):
                        record[key] = 999.0
                    elif value != value:  # Check for NaN
                        record[key] = 0.0
        return summary_dict
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting results: {e}"
        ) from e


@app.get("/backtest/results/{strategy_name}")
async def get_strategy_results(strategy_name: str):
    """Get backtest results for a specific strategy."""
    if not backtester:
        raise HTTPException(status_code=500, detail="Backtester not initialized")

    try:
        # Get portfolio values for the strategy
        portfolio_data = backtester.results_conn.execute(
            """
            SELECT date, portfolio_value, cash, weights
            FROM portfolio_values
            WHERE strategy_name = ?
            ORDER BY date
            """,
            [strategy_name],
        ).fetchdf()

        # Get trades for the strategy
        trades_data = backtester.results_conn.execute(
            """
            SELECT trade_date, symbol, action, quantity, price, value
            FROM trades
            WHERE strategy_name = ?
            ORDER BY trade_date
            """,
            [strategy_name],
        ).fetchdf()

        # Sanitize float values in the dataframes
        portfolio_dict = portfolio_data.to_dict(orient="records")
        trades_dict = trades_data.to_dict(orient="records")

        for record in portfolio_dict:
            for key, value in record.items():
                if isinstance(value, float):
                    if value == float("inf") or value == float("-inf"):
                        record[key] = 999.0
                    elif value != value:  # Check for NaN
                        record[key] = 0.0

        for record in trades_dict:
            for key, value in record.items():
                if isinstance(value, float):
                    if value == float("inf") or value == float("-inf"):
                        record[key] = 999.0
                    elif value != value:  # Check for NaN
                        record[key] = 0.0

        return {
            "portfolio_values": portfolio_dict,
            "trades": trades_dict,
        }
    except Exception as e:
        logger.error(f"Error getting strategy results: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting strategy results: {e}"
        ) from e


@app.get("/backtest/traces/{strategy_name}")
async def get_strategy_traces(
    strategy_name: str, start_date: str | None = None, end_date: str | None = None
):
    """Get trace logs for a specific strategy."""
    if not backtester:
        raise HTTPException(status_code=500, detail="Backtester not initialized")

    try:
        # Build query with optional date filters
        query = """
            SELECT trace_timestamp, level, category, message, data
            FROM backtest_traces
            WHERE strategy_name = ?
        """
        params = [strategy_name]

        if start_date:
            query += " AND start_date = ?"
            params.append(start_date)
        if end_date:
            query += " AND end_date = ?"
            params.append(end_date)

        query += " ORDER BY trace_timestamp ASC"

        traces_data = backtester.results_conn.execute(query, params).fetchdf()

        # Convert to dict format
        traces_dict = traces_data.to_dict(orient="records")

        # Parse JSON data for each trace and sanitize
        for trace in traces_dict:
            # Convert timestamp to string for JSON compatibility
            if "trace_timestamp" in trace and trace["trace_timestamp"]:
                trace["trace_timestamp"] = str(trace["trace_timestamp"])

            if trace.get("data"):
                try:
                    import json

                    trace["data"] = json.loads(trace["data"])
                    # Sanitize the data to handle inf/NaN values
                    trace["data"] = _sanitize_for_json(trace["data"])
                except Exception:
                    trace["data"] = {}
            else:
                trace["data"] = {}

        return {"traces": traces_dict}
    except Exception as e:
        logger.error(f"Error getting strategy traces: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting strategy traces: {e}"
        ) from e


# Market data endpoints
@app.post("/market/data", response_model=MarketDataResponse)
async def get_market_data(request: MarketDataRequest):
    """Get market data for specified symbols and date range."""
    if not market_data_manager:
        raise HTTPException(
            status_code=500, detail="Market data manager not initialized"
        )

    try:
        price_data = market_data_manager.get_price_data(
            request.symbols, request.start_date, request.end_date, request.force_refresh
        )

        if price_data.empty:
            return MarketDataResponse(symbols=request.symbols, data={}, metadata={})

        # Convert DataFrame to dict format
        data_dict = {}
        for symbol in request.symbols:
            if symbol in price_data.columns:
                symbol_data = price_data[symbol].dropna()
                data_dict[symbol] = [
                    {"date": date.isoformat(), "price": float(price)}
                    for date, price in symbol_data.items()
                ]

        # Get metadata
        metadata = market_data_manager.get_metadata(request.symbols)

        return MarketDataResponse(
            symbols=request.symbols, data=data_dict, metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting market data: {e}"
        ) from e


@app.get("/market/cache/info")
async def get_cache_info():
    """Get information about market data cache."""
    if not market_data_manager:
        raise HTTPException(
            status_code=500, detail="Market data manager not initialized"
        )

    try:
        cache_info = market_data_manager.get_cache_info()
        return cache_info
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting cache info: {e}"
        ) from e


@app.delete("/market/cache")
async def clear_cache(symbols: str | None = None):
    """Clear market data cache."""
    if not market_data_manager:
        raise HTTPException(
            status_code=500, detail="Market data manager not initialized"
        )

    try:
        if symbols:
            symbol_list = symbols.split(",")
            market_data_manager.clear_cache(symbol_list)
        else:
            market_data_manager.clear_cache()

        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {e}") from e


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle WebSocket messages here
            await manager.send_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Run all strategies endpoint
@app.post("/backtest/run-all")
async def run_all_strategies(
    start_date: str, end_date: str, initial_capital: float = 100000.0
):
    """Run backtests for all strategies."""
    if not backtester:
        raise HTTPException(status_code=500, detail="Backtester not initialized")

    try:
        results = backtester.run_all_strategies(start_date, end_date, initial_capital)

        # Broadcast completion via WebSocket
        await manager.broadcast(
            f"All strategies backtest completed for {start_date} to {end_date}"
        )

        return results
    except Exception as e:
        logger.error(f"Error running all strategies: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error running all strategies: {e}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
