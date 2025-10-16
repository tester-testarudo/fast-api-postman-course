#!/bin/bash

uvicorn main:app --host 127.0.0.1 --port 8000 & 

UVICORN_PID=$!

echo "Esperando que el servidor arranque..."
sleep 5

newman run tests/collection.json \
  --environment tests/env.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export reports/newman-report.html

kill $UVICORN_PID