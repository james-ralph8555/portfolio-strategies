# Portfolio Strategies Framework

A modern web application for implementing and backtesting quantitative trading strategies focused on TQQQ-centric portfolios with various risk management approaches.

# TODO INSERT public/homescreen.webp here

## Quick Start

### Prerequisites

```bash
# Enter the Nix shell (recommended)
nix develop
```

### Launch the Web Application

The easiest way to get started is using the provided startup script:

```bash
# Start both backend and frontend servers
./start-web.sh
```

This will:

- Start the FastAPI backend server on `http://localhost:8000`
- Start the frontend development server on `http://localhost:3000`
- Open the web interface in your browser

### Manual Startup

If you prefer to start the servers manually:

```bash
# Terminal 1: Start backend
cd backend
python start.py

# Terminal 2: Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Using the Application

1. **Open your browser** to `http://localhost:3000`
2. **Fetch market data** using the Market Data panel
3. **Run backtests** for individual strategies or all at once
4. **View results** with interactive charts and performance metrics
5. **Analyze performance** using the time series viewer

## Available Strategies

### 1. Equity Crisis Alpha

- **Assets**: TQQQ + DBMF/KMLM (managed futures) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Leverage-aware ERC with Black-Litterman tilt
- **Focus**: Crisis protection through managed futures

### 2. Equity Convex Rate Hedge

- **Assets**: TQQQ + PFIX (rate hedge) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Regime-switch risk budget
- **Focus**: Protection against rising interest rates

### 3. Equity Inflation Beta

- **Assets**: TQQQ + PDBC (commodities) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Two-signal tilt (trend + carry)
- **Focus**: Inflation protection through commodities

### 4. Equity Volatility Barbell

- **Assets**: TQQQ + SVOL (short vol) + TAIL (tail hedge) + SGOV (Cash)
- **Algorithm**: Barbell allocator with drawdown triggers
- **Focus**: Volatility premium harvesting with tail protection

### 5. Equity Convex Rate Hedge

- **Assets**: TQQQ + PFIX (rate hedge) + IAU (Gold) + SGOV (Cash)
- **Algorithm**: Regime-switch risk budget based on stock-bond correlation
- **Focus**: Enhanced protection against rising interest rates with convex rate protection

### 6. Risk Parity

- **Assets**: TQQQ + TMF (3x leveraged Treasury)
- **Algorithm**: Risk contribution equalization (75% equity, 25% bond risk)
- **Focus**: Equity-like returns with bond-like volatility through risk parity allocation

### Adding a New Strategy

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on implementing new strategies.

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_strategy.py
```

### Web Application Development

For development on the web application:

```bash
# Start backend in development mode
cd backend
python start.py

# Start frontend with hot reload
cd frontend
npm run dev
```

For detailed web application documentation, see [README_WEB.md](README_WEB.md)

The backend API documentation is available at `http://localhost:8000/docs`

## Configuration

Strategies use YAML configuration files with support for:

- Environment variable overrides
- Nested configuration
- Automatic validation

Example environment override:

```bash
export EQUITY_CRISIS_ALPHA_VOLATILITY_TARGET=0.12
```
