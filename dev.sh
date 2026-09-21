#!/bin/bash

set -e

echo "🚀 Starting PvtSearchEng development environment..."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Backend already running on port 8000${NC}"
else
    echo -e "${GREEN}[1/2]${NC} Starting FastAPI backend..."
    cd backend
    source .venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    cd ..
fi

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${YELLOW}Frontend already running on port 5173${NC}"
else
    echo -e "${GREEN}[2/2]${NC} Starting React frontend..."
    cd frontend
    npm run dev &
    cd ..
fi

echo ""
echo -e "${GREEN}✅ PvtSearchEng is running!${NC}"
echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

wait