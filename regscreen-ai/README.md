# 🍁 Disclosure-IQ — Canadian Capital Markets Compliance Platform

AI-assisted compliance review platform for Canadian capital markets filings.
Built for the exempt market (NI 45-106), extensible to all CSA document types.

---

## Quick Start on Replit

### 1. Import to Replit
- Go to replit.com → + Create Repl
- Choose "Import from GitHub" (or upload this folder as a zip)
- Select Node.js as the template

### 2. Add Your API Key (Secrets)
In Replit, click the Secrets tab (padlock icon in left sidebar):

  Key: OPENAI_API_KEY
  Value: your key from platform.openai.com

### 3. Install + Run
In Replit Shell: npm install
Then click the green Run button (or: npm start)

Demo Mode: If no API key is set, the app loads realistic sample data automatically.

---

## Project Structure

regscreen/
├── server.js                    # Express server + all API routes
├── package.json
├── .replit                      # Replit run config
├── public/
│   └── index.html               # Full frontend (no build step)
└── src/
    ├── config/
    │   └── documentRegistry.js  # ADD NEW DOCUMENT TYPES HERE
    ├── prompts/
    │   └── promptBuilder.js     # Document-agnostic LLM prompts
    └── utils/
        ├── pdfParser.js         # PDF extraction + chunking
        └── llmAnalyzer.js       # OpenAI calls + result merging

---

## Adding a New Document Type

1. Open src/config/documentRegistry.js
2. Copy the offering_memorandum block as a template
3. Change status to "live"
4. Fill in required_sections

That's it. Prompts, UI, and review workflow adapt automatically.

---

## API Endpoints

GET  /api/registry           — All document types (sidebar)
POST /api/analyze            — Upload PDF, run 3-pass analysis
GET  /api/session/:id        — Fetch full review session
PATCH /api/session/:id/flag  — Reviewer confirm/dismiss flag
POST /api/session/:id/signoff — Sign off review
GET  /api/audit              — Full audit log

---

## Resume Talking Points

- Configuration-driven architecture: document types as JSON schemas
- Human-in-the-loop review: AI flags, human confirms with audit trail
- Domain-specific prompting: built around actual CSA/BCSC requirements
- Confidence scoring: per-finding AI confidence surfaced to reviewer
- Audit-first design: every action timestamped and logged
- Multi-pass LLM analysis: 3 structured passes for higher precision
