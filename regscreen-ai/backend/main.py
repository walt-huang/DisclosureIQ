"""
Disclosure-IQ — FastAPI Backend
────────────────────────────────
Handles PDF upload, text extraction, chunking, and AI-powered compliance analysis.
Swap MOCK_MODE = True → False and add your OPENAI_API_KEY or ANTHROPIC_API_KEY to run live.
"""

import os
import json
import re
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ── Try to import PDF parser ──────────────────────────────────────────────────
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  pdfplumber not installed. Using text extraction fallback.")

app = FastAPI(title="Disclosure-IQ", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────────────────────────
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")  # "openai" or "anthropic"

CHUNK_SIZE = 3000      # characters per chunk
CHUNK_OVERLAP = 300    # overlap between chunks


# ─────────────────────────────────────────────────────────────────────────────
# TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    try:
        import pdfplumber
        import io
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {str(e)}")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks for LLM processing."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS  (document-type agnostic)
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENT_TYPES = {
    "offering_memorandum": {
        "display_name": "Offering Memorandum",
        "form": "Form 45-106F2",
        "regulatory_reference": "NI 45-106",
        "required_sections": [
            {"id": "business_description", "label": "Business Description", "red_flags": ["vague business description", "no operating history"]},
            {"id": "use_of_proceeds", "label": "Use of Proceeds", "red_flags": ["general working capital without breakdown", "vague milestones"]},
            {"id": "dilution", "label": "Dilution", "red_flags": ["no cap table provided", "missing post-offering share count"]},
            {"id": "material_agreements", "label": "Material Agreements", "red_flags": ["no material agreements listed"]},
            {"id": "risk_factors", "label": "Risk Factors", "red_flags": ["generic boilerplate risks", "no issuer-specific risk language"]},
            {"id": "purchaser_rights", "label": "Purchaser's Rights", "red_flags": ["missing 2-day rescission right", "no cancellation right mentioned"]},
            {"id": "financial_statements", "label": "Financial Statements", "red_flags": ["no financial statements included", "unaudited when audit required"]},
            {"id": "selling_agent_relationship", "label": "Selling Agent Relationship", "red_flags": ["no conflict of interest disclosure"]},
            {"id": "forward_looking_info", "label": "Forward-Looking Information", "red_flags": ["forward-looking statements without disclaimer"]},
        ],
    }
}


def build_completeness_prompt(doc_type: dict, text: str) -> str:
    sections = "\n".join([f"{i+1}. {s['label']}" for i, s in enumerate(doc_type["required_sections"])])
    return f"""You are a senior Canadian capital markets compliance reviewer specializing in {doc_type['regulatory_reference']}.

You are reviewing a {doc_type['display_name']} ({doc_type['form']}).

Required sections under {doc_type['regulatory_reference']}:
{sections}

For each section, return a JSON array with objects:
- section_id (snake_case)
- label (human readable)
- status: "present" | "incomplete" | "missing"
- confidence: float 0.0-1.0
- triggering_passage: verbatim excerpt or null
- notes: brief explanation

Be conservative. Vague language = "incomplete". Absent = "missing".

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON array. No other text."""


def build_red_flags_prompt(doc_type: dict, text: str) -> str:
    known_flags = []
    for s in doc_type["required_sections"]:
        known_flags.extend(s.get("red_flags", []))
    flags_list = "\n".join([f"{i+1}. {f}" for i, f in enumerate(known_flags)])
    
    return f"""You are a compliance reviewer for Canadian capital markets filings ({doc_type['regulatory_reference']}).

Known red flags for {doc_type['display_name']}:
{flags_list}

Universal red flags (all Canadian filings):
- Related party transactions not clearly disclosed
- Forward-looking statements without cautionary language
- Conflicts of interest not disclosed
- Missing statutory rights of rescission

For each flag found, return a JSON array with:
- flag_id: "FLAG_001", "FLAG_002", etc.
- flag_type: short snake_case label
- flag_category: "known_doctype" | "universal"
- severity: "high" | "medium" | "low"
- triggering_passage: exact text or null
- regulatory_basis: which rule is implicated
- suggested_action: one sentence for the human reviewer
- confidence: float 0.0-1.0

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON array. No other text."""


def build_risk_prompt(doc_type: dict, text: str) -> str:
    return f"""You are a Canadian capital markets analyst reviewing a {doc_type['display_name']} under {doc_type['regulatory_reference']}.

Extract all risk factor statements. For each, return a JSON array with:
- risk_id: "RISK_001", "RISK_002", etc.
- category: "issuer_specific" | "market" | "regulatory" | "forward_looking" | "operational" | "financial"
- summary: one sentence
- verbatim_passage: exact text (max 300 chars)
- is_boilerplate: true if generic/non-specific to this issuer
- severity: "high" | "medium" | "low"
- confidence: float 0.0-1.0

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON array. No other text."""


def build_summary_prompt(doc_type: dict, text: str) -> str:
    return f"""You are a senior Canadian capital markets analyst reviewing a {doc_type['display_name']} under {doc_type['regulatory_reference']}.

Provide an executive summary as a JSON object with:
- issuer_name: string or null
- offering_type: type of securities
- offering_size: dollar amount or null
- jurisdiction: province(s)
- business_summary: 2-3 sentences
- key_highlights: array of 3-5 strings (most important facts)
- overall_completeness: "complete" | "substantially_complete" | "materially_deficient"
- reviewer_priority: "high" | "medium" | "low"

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON object. No other text."""


# ─────────────────────────────────────────────────────────────────────────────
# AI CALLER
# ─────────────────────────────────────────────────────────────────────────────

def call_ai(prompt: str) -> Optional[str]:
    """Call the configured AI provider. Falls back to mock if no key set."""
    if MOCK_MODE or (not OPENAI_API_KEY and not ANTHROPIC_API_KEY):
        return None  # Signal to use mock
    
    if AI_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        return call_anthropic(prompt)
    elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
        return call_openai(prompt)
    return None


def call_anthropic(prompt: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except ImportError:
        print("⚠️ anthropic not installed. Falling back to mock.")
        return ""


def call_openai(prompt: str) -> str:
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


def parse_json_response(raw: str, fallback: list | dict) -> list | dict:
    """Safely parse JSON from LLM response."""
    if raw is None:
        return fallback
    try:
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        return json.loads(cleaned)
    except Exception:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA (used when MOCK_MODE=true or no API key)
# ─────────────────────────────────────────────────────────────────────────────

def get_mock_completeness():
    return [
        {"section_id": "business_description", "label": "Business Description", "status": "present", "confidence": 0.92, "triggering_passage": "The Company was incorporated under the Business Corporations Act (British Columbia) and is engaged in the exploration and development of mineral properties in Northern BC.", "notes": "Clear business description with incorporation details and operational focus."},
        {"section_id": "use_of_proceeds", "label": "Use of Proceeds", "status": "incomplete", "confidence": 0.78, "triggering_passage": "Net proceeds will be used for working capital and general corporate purposes.", "notes": "Vague — no specific percentage allocation or milestone breakdown provided."},
        {"section_id": "dilution", "label": "Dilution", "status": "present", "confidence": 0.88, "triggering_passage": "Post-offering, the Company will have 45,200,000 common shares issued and outstanding.", "notes": "Cap table present with pre and post-offering figures."},
        {"section_id": "material_agreements", "label": "Material Agreements", "status": "present", "confidence": 0.81, "triggering_passage": "The Company has entered into a property option agreement dated March 1, 2025 with Cariboo Resources Ltd.", "notes": "Material agreements identified and summarized."},
        {"section_id": "risk_factors", "label": "Risk Factors", "status": "incomplete", "confidence": 0.65, "triggering_passage": "Investing in the securities of the Company involves a high degree of risk.", "notes": "Risk factors present but several appear boilerplate and not issuer-specific."},
        {"section_id": "purchaser_rights", "label": "Purchaser's Rights", "status": "missing", "confidence": 0.95, "triggering_passage": None, "notes": "No 2-day rescission right disclosure found. Required under BC securities law."},
        {"section_id": "financial_statements", "label": "Financial Statements", "status": "present", "confidence": 0.90, "triggering_passage": "See Appendix A — Audited Financial Statements for the year ended December 31, 2024.", "notes": "Audited financials included and referenced correctly."},
        {"section_id": "selling_agent_relationship", "label": "Selling Agent Relationship", "status": "incomplete", "confidence": 0.72, "triggering_passage": "The Company may pay finder's fees in connection with this offering.", "notes": "Agent relationship vaguely disclosed — specific compensation not quantified."},
        {"section_id": "forward_looking_info", "label": "Forward-Looking Information", "status": "incomplete", "confidence": 0.83, "triggering_passage": "The Company expects to complete its Phase 1 drilling program by Q3 2025.", "notes": "Forward-looking statements present but cautionary language block is missing."},
    ]


def get_mock_red_flags():
    return [
        {"flag_id": "FLAG_001", "flag_type": "missing_rescission_right", "flag_category": "known_doctype", "severity": "high", "triggering_passage": None, "regulatory_basis": "NI 45-106 s.3.9 — BC purchasers have a 2-business-day right of rescission that must be disclosed", "suggested_action": "Add a Purchaser's Rights section explicitly stating the 2-business-day rescission period under BC securities law.", "confidence": 0.95},
        {"flag_id": "FLAG_002", "flag_type": "vague_use_of_proceeds", "flag_category": "known_doctype", "severity": "high", "triggering_passage": "Net proceeds will be used for working capital and general corporate purposes.", "regulatory_basis": "NI 45-106 Form 45-106F2, Item 4 — Use of Proceeds must be specific and include allocation percentages", "suggested_action": "Break down use of proceeds into specific line items with dollar amounts or percentage allocations for each use.", "confidence": 0.91},
        {"flag_id": "FLAG_003", "flag_type": "missing_fli_cautionary_language", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "The Company expects to complete its Phase 1 drilling program by Q3 2025 and anticipates first revenue by Q4 2025.", "regulatory_basis": "NI 51-102 s.4A.2 — Forward-looking information must be accompanied by cautionary language and material assumptions", "suggested_action": "Add a CAUTIONARY NOTE regarding forward-looking statements block before or adjacent to all FLI disclosures.", "confidence": 0.87},
        {"flag_id": "FLAG_004", "flag_type": "boilerplate_risk_factors", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "Investing in junior resource companies involves risks common to the resource sector.", "regulatory_basis": "NI 45-106 Form 45-106F2, Item 7 — Risk factors must be specific to the issuer", "suggested_action": "Replace generic risk language with risks specific to this issuer's stage of development, jurisdiction, and mineral property.", "confidence": 0.79},
        {"flag_id": "FLAG_005", "flag_type": "undisclosed_agent_compensation", "flag_category": "universal", "severity": "low", "triggering_passage": "The Company may pay finder's fees in connection with this offering.", "regulatory_basis": "NI 45-106 Form 45-106F2, Item 6 — Compensation paid to selling agents must be disclosed specifically", "suggested_action": "Specify the exact finder's fee structure (cash percentage, share compensation) or confirm no agent is engaged.", "confidence": 0.74},
    ]


def get_mock_risks():
    return [
        {"risk_id": "RISK_001", "category": "issuer_specific", "summary": "The Company has no producing assets and is entirely reliant on exploration success to generate value.", "verbatim_passage": "The Company is an exploration-stage company with no history of earnings or revenue from mineral production.", "is_boilerplate": False, "severity": "high", "confidence": 0.90},
        {"risk_id": "RISK_002", "category": "financial", "summary": "The Company will require additional financing within 12 months and there is no guarantee such financing will be available.", "verbatim_passage": "Management believes existing capital resources will be sufficient to fund operations for approximately 12 months; however, there can be no assurance that additional financing will be available.", "is_boilerplate": False, "severity": "high", "confidence": 0.88},
        {"risk_id": "RISK_003", "category": "regulatory", "summary": "Environmental regulations applicable to mineral exploration may impose significant costs or restrictions.", "verbatim_passage": "The operations of the Company are subject to environmental regulations promulgated by government authorities.", "is_boilerplate": True, "severity": "medium", "confidence": 0.75},
        {"risk_id": "RISK_004", "category": "market", "summary": "Commodity price volatility may adversely affect the economic viability of the Company's mineral properties.", "verbatim_passage": "The price of precious and base metals is subject to significant fluctuation and is affected by numerous factors beyond the Company's control.", "is_boilerplate": True, "severity": "medium", "confidence": 0.80},
        {"risk_id": "RISK_005", "category": "operational", "summary": "The Company's mineral property titles may be subject to challenge or defect which could impair the Company's interest.", "verbatim_passage": "Title to mineral properties is a complex matter and the Company's interest in its properties may be subject to prior unregistered agreements or transfers.", "is_boilerplate": False, "severity": "medium", "confidence": 0.82},
    ]


def get_mock_summary():
    return {
        "issuer_name": "Cariboo Minerals Corp.",
        "offering_type": "Common Shares",
        "offering_size": "$2,500,000",
        "jurisdiction": "BC",
        "business_summary": "Cariboo Minerals Corp. is a BC-incorporated mineral exploration company focused on gold and copper targets in the Cariboo Mining District. The company holds option rights on three contiguous claims totaling 4,200 hectares and has completed preliminary geophysical surveys.",
        "key_highlights": [
            "Offering size: $2.5M at $0.25/share via OM exemption",
            "Minimum subscription: $5,000 per investor",
            "Phase 1 drilling program planned Q3 2025",
            "Audited financials show $180K cash on hand as at Dec 31, 2024",
            "No revenue; exploration stage company"
        ],
        "overall_completeness": "substantially_complete",
        "reviewer_priority": "high"
    }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Disclosure-IQ API is running"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "mock_mode": MOCK_MODE,
        "ai_provider": AI_PROVIDER,
        "pdf_available": PDF_AVAILABLE,
    }


@app.post("/api/review")
async def review_document(
    file: UploadFile = File(...),
    doc_type_id: str = Form(...),
    jurisdiction: str = Form("BC"),
    reviewer_name: str = Form(""),
):
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=422, detail="Only PDF or text files are supported.")

    doc_type = DOCUMENT_TYPES.get(doc_type_id)
    if not doc_type:
        raise HTTPException(status_code=400, detail=f"Unknown document type: {doc_type_id}")

    file_bytes = await file.read()
    session_id = str(uuid.uuid4())

    # ── Extract text ──────────────────────────────────────────────────────────
    if file.content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="replace")

    # ── Mock mode ─────────────────────────────────────────────────────────────
    if MOCK_MODE or (not OPENAI_API_KEY and not ANTHROPIC_API_KEY):
        import asyncio
        await asyncio.sleep(0.5)  # Simulate processing
        return {
            "session_id": session_id,
            "doc_type_id": doc_type_id,
            "filename": file.filename,
            "jurisdiction": jurisdiction,
            "reviewed_at": datetime.utcnow().isoformat(),
            "completeness": get_mock_completeness(),
            "red_flags": get_mock_red_flags(),
            "risks": get_mock_risks(),
            "summary": get_mock_summary(),
            "mock": True,
        }

    # ── Live AI mode ──────────────────────────────────────────────────────────
    chunks = chunk_text(text)
    # Use first 2 chunks for analysis (covers most OMs)
    analysis_text = "\n\n---\n\n".join(chunks[:2])

    # Run all prompts
    completeness_raw = call_ai(build_completeness_prompt(doc_type, analysis_text))
    flags_raw = call_ai(build_red_flags_prompt(doc_type, analysis_text))
    risks_raw = call_ai(build_risk_prompt(doc_type, analysis_text))
    summary_raw = call_ai(build_summary_prompt(doc_type, analysis_text[:3000]))

    return {
        "session_id": session_id,
        "doc_type_id": doc_type_id,
        "filename": file.filename,
        "jurisdiction": jurisdiction,
        "reviewed_at": datetime.utcnow().isoformat(),
        "completeness": parse_json_response(completeness_raw, []),
        "red_flags": parse_json_response(flags_raw, []),
        "risks": parse_json_response(risks_raw, []),
        "summary": parse_json_response(summary_raw, {}),
        "mock": False,
    }
