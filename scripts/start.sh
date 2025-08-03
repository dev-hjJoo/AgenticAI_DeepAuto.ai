#!/bin/bash

cd `dirname $0`/..

PORT=8080

./scripts/run_be.sh $PORT & UVICORN_PID=$!
./scripts/run_fe.sh $PORT

kill $UVICORN_PID