#!/bin/bash

# Portfolio Management Web Application Startup Script

echo "🚀 Starting Portfolio Management Web Application..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"

# Check if we're in a Nix environment
if command -v nix &> /dev/null; then
    echo "📦 Using Nix environment..."
    nix develop --command bash -c "
        set -euo pipefail
        echo '🔧 Starting backend server...'
        (cd \"$BACKEND_DIR\" && python start.py) &
        BACKEND_PID=\$!

        echo '⏳ Waiting for backend to start...'
        sleep 3

        echo '🎨 Starting frontend development server...'
        (cd \"$FRONTEND_DIR\" && npm run dev) &
        FRONTEND_PID=\$!

        echo '✅ Application started!'
        echo '📊 Frontend: http://localhost:3000'
        echo '🔌 Backend API: http://localhost:8000'
        echo '📚 API Docs: http://localhost:8000/docs'
        echo ''
        echo 'Press Ctrl+C to stop both servers'

        # Wait for interrupt signal
        trap 'echo \"🛑 Stopping servers...\"; kill \$BACKEND_PID \$FRONTEND_PID 2>/dev/null || true; exit' INT
        wait
    "
else
    echo "⚠️  Nix not found. Please install dependencies manually."
    echo "Backend: pip install -e ."
    echo "Frontend: cd frontend && npm install"
    exit 1
fi
