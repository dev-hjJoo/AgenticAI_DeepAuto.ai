#!/bin/bash

cd `dirname $0`/..

PORT=$1  
if [ -z "$PORT" ]; then
  PORT=8000                 # Default: 8000
fi

echo "Starting backend at port $PORT"
uvicorn be.main:app --reload --port $PORT