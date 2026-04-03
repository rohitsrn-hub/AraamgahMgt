#!/bin/bash

# E-ARMS Local Startup Script
# This script starts all required services for E-ARMS

echo "🏠 Starting E-ARMS Locally..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if MongoDB is running
echo -e "${YELLOW}1. Checking MongoDB...${NC}"
if pgrep -x "mongod" > /dev/null; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo "Starting MongoDB..."
    # Try to start MongoDB
    if command -v brew &> /dev/null; then
        # Mac
        brew services start mongodb-community
    elif command -v systemctl &> /dev/null; then
        # Linux
        sudo systemctl start mongod
    else
        echo "Please start MongoDB manually"
        exit 1
    fi
fi

# Get local IP address
echo -e "\n${YELLOW}2. Detecting local IP address...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    LOCAL_IP="localhost"
fi

echo -e "${GREEN}✓ Your local IP: $LOCAL_IP${NC}"
echo "   Access from other devices: http://$LOCAL_IP:3000"

# Start backend in background
echo -e "\n${YELLOW}3. Starting Backend...${NC}"
cd backend
python server.py &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo "   Waiting for backend to be ready..."
sleep 3

# Start frontend
echo -e "\n${YELLOW}4. Starting Frontend...${NC}"
cd ../frontend

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "Creating .env.local with your IP..."
    echo "REACT_APP_BACKEND_URL=http://$LOCAL_IP:8001" > .env.local
fi

# Start frontend in development mode
yarn start &
FRONTEND_PID=$!

echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}🎉 E-ARMS is starting!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Access URLs:"
echo "  • Local:    http://localhost:3000"
echo "  • Network:  http://$LOCAL_IP:3000"
echo ""
echo "Backend API: http://$LOCAL_IP:8001"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to stop all processes
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait
wait
