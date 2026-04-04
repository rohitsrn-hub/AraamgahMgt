#!/bin/bash

# E-ARMS Production Build & Deploy Script
# Builds optimized production version and starts services

echo "🏗️  Building E-ARMS for Production..."
echo "======================================"

# Get local IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
else
    LOCAL_IP="localhost"
fi

echo "Local IP detected: $LOCAL_IP"

# Configure frontend environment
cd frontend
if [ ! -f .env.local ]; then
    echo "Creating .env.local..."
    echo "REACT_APP_BACKEND_URL=http://$LOCAL_IP:8001" > .env.local
fi

# Build frontend
echo ""
echo "Building frontend (this may take a few minutes)..."
yarn build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend build complete!"

# Start backend
echo ""
echo "Starting backend..."
cd ../backend
python server.py &
BACKEND_PID=$!
sleep 3

# Serve frontend build
echo ""
echo "Serving frontend production build..."
cd ../frontend
npx serve -s build -l 3000 &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "🎉 Production deployment started!"
echo "======================================"
echo ""
echo "Access URLs:"
echo "  • Local:    http://localhost:3000"
echo "  • Network:  http://$LOCAL_IP:3000"
echo ""
echo "Backend API: http://$LOCAL_IP:8001"
echo ""
echo "Press Ctrl+C to stop all services"

trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
