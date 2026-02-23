#!/bin/bash
echo "Installing Python dependencies..."
pip install fastapi uvicorn python-multipart pdfplumber openai --quiet

echo "Installing Node dependencies..."
cd frontend && npm install --silent && cd ..

echo "Starting backend..."
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
cd ..

echo "Starting frontend..."
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
