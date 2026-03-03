# DisclosureIQ

**AI-powered compliance review platform for Canadian capital markets filings**

DisclosureIQ helps issuers, legal counsel, and IR teams review public disclosure documents against Canadian securities regulations — including NI 45-106, CSA, and BCSC requirements — using AI to flag potential issues before filing.

🔗 **Live App:** [disclosure-iq--walthuang.replit.app](https://disclosure-iq--walthuang.replit.app/)

---

## What It Does

DisclosureIQ accepts uploaded disclosure documents and runs AI-assisted compliance checks against applicable Canadian securities rules. It is designed to support early-stage review workflows, not replace legal counsel.

**Supported document types:**
- **MD&A** — Management's Discussion and Analysis
- **AIF** — Annual Information Form
- **NI 45-106** — Prospectus Exemption filings (CSA / BCSC)

**Key features:**
- Upload and parse disclosure documents (PDF, DOCX)
- AI-generated compliance review with flagged issues and recommendations
- Sign-off summary for review tracking
- Health check endpoint to confirm API availability
- Clean review dashboard with sidebar navigation

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, CSS |
| Backend | Python, FastAPI |
| AI | Anthropic Claude API |
| Hosting | Replit |
| Version Control | GitHub |

---

## Project Structure
```
DisclosureIQ/
├── disclosure_iq/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── ReviewDashboard.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── SignOffSummary.jsx
│   │   │   │   └── UploadScreen.jsx
│   │   │   ├── config/
│   │   │   │   ├── documentRegistry.js
│   │   │   │   └── prompts.jsx
│   │   │   ├── App.jsx
│   │   │   └── main.jsx
│   │   └── index.html
│   └── backend/
│       └── main.py
├── main.py
└── README.md
```

---

## Getting Started (Local Development)

### Prerequisites
- Node.js 18+
- Python 3.11+
- An Anthropic API key

### 1. Clone the repo
```bash
git clone https://github.com/walt-huang/DisclosureIQ.git
cd DisclosureIQ
```

### 2. Set up the backend
```bash
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```
ANTHROPIC_API_KEY=your_api_key_here
```

Start the backend:
```bash
uvicorn backend.main:app --reload
```

### 3. Set up the frontend
```bash
cd disclosure_iq/frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## API Health Check
```
GET /health
```

Returns `200 OK` if the backend is running correctly.

---

## Regulatory Scope

DisclosureIQ is currently scoped to the following Canadian securities frameworks:

- **NI 45-106** — Prospectus Exemptions (CSA)
- **CSA** — Canadian Securities Administrators guidance
- **BCSC** — British Columbia Securities Commission requirements

Support for additional instruments (e.g., NI 51-102 continuous disclosure) is planned.

---

## Disclaimer

DisclosureIQ is an AI-assisted review tool intended to support — not replace — qualified legal and compliance professionals. Output should always be reviewed by counsel familiar with applicable securities laws before reliance or filing.

---

## Author

**Walt Huang** — [github.com/walt-huang](https://github.com/walt-huang)

---

## License

Private repository. All rights reserved.
```

---

After pasting and saving in Replit, run this in the Shell:
```
git add README.md && git commit -m "Add README" && git push origin main