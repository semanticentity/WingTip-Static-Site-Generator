#!/bin/bash

# Function to check if port is in use
port_in_use() {
  lsof -i:"$1" >/dev/null 2>&1
  return $?
}

# First try to kill any Python processes serving on port 8000
echo "Checking for processes on port 8000..."
PORT_PIDS=$(lsof -ti:8000)
if [ ! -z "$PORT_PIDS" ]; then
  echo "Found processes: $PORT_PIDS"
  kill -9 $PORT_PIDS
  
  # Wait for port to be released (max 5 seconds)
  echo "Waiting for port 8000 to be released..."
  for i in {1..5}; do
    if ! port_in_use 8000; then
      echo "Port 8000 is now free"
      break
    fi
    sleep 1
  done
fi

# Then try to kill any Python processes running serve.py
echo "Checking for serve.py processes..."
SERVE_PIDS=$(pgrep -f "python.*serve\.py")
if [ ! -z "$SERVE_PIDS" ]; then
  echo "Found processes: $SERVE_PIDS"
  kill -9 $SERVE_PIDS
  sleep 1  # Give a moment for processes to die
fi

# Clean up PID file if it exists
PID_FILE="devServer.pid"
if [ -f "$PID_FILE" ]; then
  rm "$PID_FILE"
  echo "Removed stale PID file"
fi

# Final verification
if port_in_use 8000; then
  echo "Warning: Port 8000 is still in use!"
else
  echo "Port 8000 is free and ready"
fi
