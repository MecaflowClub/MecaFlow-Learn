#!/bin/bash

# Set default port if not provided
PORT="${PORT:-8000}"

# Start uvicorn with the resolved port
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 1 --timeout-keep-alive 75