#!/bin/bash

cd `dirname $0`/..

PORT=$1  
if [ -z "$PORT" ]; then
  PORT=8000                 # Default: 8000
fi

echo "Starting frontend connecting to backend port $PORT"
streamlit run fe/main.py -- --be_port $PORT