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
  echo "Attempting graceful shutdown of processes on port 8000: $PORT_PIDS..."
  kill $PORT_PIDS
  sleep 1 # Wait a moment for processes to shut down
  # Check if processes are still alive
  ALIVE_PIDS=$(lsof -ti:8000) # Re-check PIDs on port
  if [ ! -z "$ALIVE_PIDS" ]; then
    echo "Processes still alive on port 8000: $ALIVE_PIDS. Forcing shutdown..."
    kill -9 $ALIVE_PIDS
  else
    echo "Processes on port 8000 shut down gracefully."
  fi
  
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
  echo "Attempting graceful shutdown of serve.py processes: $SERVE_PIDS..."
  kill $SERVE_PIDS
  sleep 1 # Wait a moment
  # Re-check if serve.py processes are still running
  STILL_SERVE_PIDS=$(pgrep -f "python.*serve\.py")
  if [ ! -z "$STILL_SERVE_PIDS" ]; then
    echo "Some serve.py processes still alive: $STILL_SERVE_PIDS. Forcing shutdown..."
    kill -9 $STILL_SERVE_PIDS # Force kill any remaining ones
  else
    echo "serve.py processes shut down gracefully."
  fi
  sleep 1  # Give a moment for processes to die
fi

# Final verification
if port_in_use 8000; then
  echo "Warning: Port 8000 is still in use!"
else
  echo "Port 8000 is free and ready"
fi
