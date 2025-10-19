# Portfolio Management Web Application

A modern TypeScript SolidJS frontend with FastAPI backend for managing portfolio strategies, running backtests, and analyzing results from DuckDB databases.

## Features

- **Strategy Management**: View and configure trading strategies
- **Backtesting**: Run backtests for individual strategies or all strategies at once
- **Market Data**: Fetch and cache market data with DuckDB
- **Results Visualization**: View detailed backtest results and performance metrics
- **Real-time Updates**: WebSocket support for real-time backtest progress

## Architecture

### Backend (FastAPI + Python)

- FastAPI REST API with Pydantic models
- DuckDB integration for market data and results storage
- Unified backtesting system
- WebSocket support for real-time updates

### Frontend (SolidJS + TypeScript)

- Modern reactive UI with SolidJS
- TypeScript for type safety
- Tailwind CSS for styling
- Responsive design

## Setup Instructions

### Prerequisites

- Python 3.13+
- Node.js 18+
- Nix (recommended for development)

### Backend Setup

1. **Install Dependencies**:

   ```bash
   # Using Nix (recommended)
   nix develop

   # Or install manually
   pip install -e .
   ```

2. **Start the Backend Server**:

   ```bash
   cd backend
   python start.py
   ```

   The backend will be available at `http://localhost:8000`

3. **API Documentation**:
   Visit `http://localhost:8000/docs` for interactive API documentation

### Frontend Setup

1. **Install Dependencies**:

   ```bash
   cd frontend
   npm install
   ```

2. **Start the Development Server**:

   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## Usage

### 1. Market Data Management

- Navigate to the **Market Data** page
- Enter symbols (e.g., AAPL, GOOGL, MSFT)
- Select date range and fetch data
- Data is cached in DuckDB for performance

### 2. Strategy Configuration

- Visit the **Strategies** page to view available strategies
- Each strategy shows its assets and configuration
- Strategies are automatically loaded from the `strategies/` directory

### 3. Running Backtests

- Go to the **Backtest** page
- Select a strategy and configure parameters:
  - Start/End dates
  - Initial capital
- Run individual backtests or all strategies
- View results in real-time

### 4. Analyzing Results

- The **Results** page shows all backtest results
- Click "View" to see detailed strategy performance
- Includes portfolio values, trades, and performance metrics

### 5. Dashboard Overview

- The **Dashboard** provides a summary of:
  - Total strategies and results
  - Best performing strategy
  - Average returns
  - Cache statistics

## API Endpoints

### Strategies

- `GET /strategies` - List all strategies
- `GET /strategies/{name}` - Get strategy details

### Backtesting

- `POST /backtest` - Run single strategy backtest
- `POST /backtest/run-all` - Run all strategies
- `GET /backtest/results` - Get all results
- `GET /backtest/results/{strategy}` - Get strategy results

### Market Data

- `POST /market/data` - Fetch market data
- `GET /market/cache/info` - Get cache information
- `DELETE /market/cache` - Clear cache

### WebSocket

- `WS /ws` - Real-time updates

## DuckDB Integration

The application uses two DuckDB databases:

1. **Market Data Cache** (`~/.portfolio_cache/market_data.duckdb`)

   - Price data with automatic expiration
   - Metadata for symbols
   - Optimized for fast queries

2. **Backtest Results** (`backtest_results/backtest_results.duckdb`)
   - Backtest summary metrics
   - Portfolio value history
   - Trade execution records

## Development

### Backend Development

- Use `nix develop` for the development environment
- Backend code is in `backend/main.py`
- Pydantic models define API schemas
- FastAPI auto-generates documentation

### Frontend Development

- SolidJS components in `frontend/src/`
- TypeScript for type safety
- Tailwind CSS for styling
- Vite for fast development

### Adding New Strategies

1. Create strategy in `strategies/{name}/strategy.py`
2. Add `config.yaml` with strategy configuration
3. Implement required methods: `get_assets()`, `calculate_weights()`, etc.
4. Strategy will be automatically available in the UI

## Production Deployment

### Backend

```bash
# Production server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
# Build for production
cd frontend
npm run build

# Serve with nginx or similar
npm run preview
```

## Troubleshooting

### Common Issues

1. **Backend won't start**: Ensure all dependencies are installed and Python 3.13+ is used
2. **Frontend can't connect to backend**: Check that backend is running on port 8000
3. **No strategies showing**: Verify strategy files exist in the `strategies/` directory
4. **Market data errors**: Check internet connection and symbol validity

### Logs

- Backend logs show in console
- Frontend logs in browser dev tools
- DuckDB logs in database files

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Update API documentation
4. Test with sample data
5. Update this README if needed
