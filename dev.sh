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

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker daemon is not running. Please start Docker first.${NC}"
    exit 1
fi

if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo -e "${YELLOW}SearXNG already running on port 8080${NC}"
else
    echo -e "${GREEN}[1/3]${NC} Starting SearXNG containers..."
    cd searxng-instance
    docker compose up -d
    cd ..
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Backend already running on port 8000${NC}"
else
    echo -e "${GREEN}[2/3]${NC} Starting FastAPI backend..."
    cd backend
    source .venv/bin/activate
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    cd ..
fi

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${YELLOW}Frontend already running on port 5173${NC}"
else
    echo -e "${GREEN}[3/3]${NC} Starting React frontend..."
    cd frontend
    npm run dev &
    cd ..
fi

echo ""
echo -e "${GREEN}✅ PvtSearchEng is running!${NC}"
echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  SearXNG:  http://localhost:8080"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop local dev servers"

wait