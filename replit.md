# RegScreen AI

## Overview

RegScreen AI is a Canadian capital markets compliance review platform that uses AI to analyze regulatory filings (primarily offering memorandums under NI 45-106). Users upload PDF documents, and the system extracts text, chunks it, and runs AI-powered compliance analysis to check for completeness, risk factors, and red flags.

The project has a split architecture: a Python/FastAPI backend for PDF processing and AI analysis, and a React/Vite frontend for the user interface. It supports a mock/demo mode for running without API keys and can connect to OpenAI or Anthropic for live AI analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend (regscreen-ai/frontend/)
- **Framework**: React 18 with Vite 4 as the build tool
- **Styling**: Custom CSS design system with a dark editorial/financial aesthetic (no CSS framework like Tailwind)
- **Fonts**: DM Serif Display, DM Mono, Literata (loaded from Google Fonts)
- **Icons**: lucide-react
- **Dev server**: Runs on port 5000, proxies `/api` requests to the backend at `http://localhost:8000`
- **No build step needed for dev** — Vite handles HMR and module resolution
- **Document Registry**: A client-side config (`src/config/documentRegistry.js`) defines all supported document types, their required sections, and red flags. Adding a new document type means adding an entry here — no other code changes needed.
- **Prompt Templates**: Client-side prompt builders (`src/config/prompts.js`) generate structured prompts for the AI, parameterized by document type. These produce requests for JSON-only responses.

### Backend (regscreen-ai/backend/)
- **Framework**: Python FastAPI
- **Port**: 8000 (inferred from Vite proxy config)
- **PDF Parsing**: Uses `pdfplumber` with a graceful fallback if not installed
- **Text Chunking**: 3000-character chunks with 300-character overlap for feeding into LLMs
- **AI Providers**: Supports both OpenAI and Anthropic, selected via `AI_PROVIDER` env var
- **Mock Mode**: Enabled by default (`MOCK_MODE=true`). When no API key is set, returns realistic sample data so the app is demo-able without credentials.
- **CORS**: Wide open (allow all origins) — suitable for development, should be locked down for production.

### Environment Variables
| Variable | Purpose | Default |
|---|---|---|
| `MOCK_MODE` | Use mock data instead of real AI | `"true"` |
| `OPENAI_API_KEY` | OpenAI API key | `""` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `""` |
| `AI_PROVIDER` | Which AI to use: `"openai"` or `"anthropic"` | `"anthropic"` |

### Root-Level Files
There's a root `package.json` and `main.py` that appear to be workspace scaffolding from the Replit template. The actual application code lives inside `regscreen-ai/`. When setting up, focus on the `regscreen-ai/frontend/` and `regscreen-ai/backend/` directories.

### Running the Application
1. **Backend**: `cd regscreen-ai/backend && pip install fastapi uvicorn pdfplumber && uvicorn main:app --host 0.0.0.0 --port 8000`
2. **Frontend**: `cd regscreen-ai/frontend && npm install && npm run dev`
3. The frontend on port 5000 proxies API calls to the backend on port 8000.

### Design Patterns
- **Registry-driven architecture**: Document types are defined declaratively in a registry config. The prompts, UI, and analysis logic are all generic and parameterized by this registry. This makes the system extensible without code changes.
- **Chunk-and-merge**: Large PDFs are split into overlapping chunks, each analyzed independently, then results are merged. This handles LLM context window limits.
- **Structured JSON responses**: All AI prompts request JSON-only output with defined schemas, making parsing reliable.

## External Dependencies

### AI/LLM Services
- **OpenAI API** — GPT models for compliance analysis (optional, selected via env var)
- **Anthropic API** — Claude models for compliance analysis (default provider)
- Neither is required when running in mock mode

### Python Packages
- `fastapi` — Web framework
- `uvicorn` — ASGI server
- `pdfplumber` — PDF text extraction (optional, has fallback)

### Node/Frontend Packages
- `react` / `react-dom` 18 — UI framework
- `vite` 4 — Dev server and bundler
- `@vitejs/plugin-react` — React support for Vite
- `lucide-react` — Icon library

### External Services
- Google Fonts CDN — Font loading (DM Serif Display, DM Mono, Literata)