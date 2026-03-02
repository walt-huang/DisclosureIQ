#!/bin/bash
# Exit on error
set -e
pip install anthropic pdfplumber --quiet

echo "Starting backend..."
cd disclosure_iq/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

echo "Starting frontend..."
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5000
