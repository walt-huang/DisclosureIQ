#!/bin/bash
# Exit on error
set -e

echo "Starting backend..."
cd regscreen-ai/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

echo "Starting frontend..."
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5000
