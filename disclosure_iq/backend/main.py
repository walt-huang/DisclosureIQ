"""
DisclosureIQ — FastAPI Backend
────────────────────────────────
Canadian Capital Markets Compliance Review Platform
Supports: Offering Memorandum (NI 45-106), MD&A (NI 51-102), AIF (NI 51-102)
"""

import os
import json
import re
import uuid
from datetime import datetime

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

app = FastAPI(title="DisclosureIQ", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────────────────────────
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 300

# ── Root health check ─────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "app": "DisclosureIQ", "version": "2.0.0"}

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "mock_mode": MOCK_MODE,
        "ai_provider": AI_PROVIDER,
        "pdf_available": PDF_AVAILABLE,
        "anthropic_configured": bool(ANTHROPIC_API_KEY),
    }

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT TYPE REGISTRY (backend mirror of frontend registry)
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENT_TYPES = {
    "offering_memorandum": {
        "display_name": "Offering Memorandum",
        "form": "Form 45-106F2",
        "regulatory_reference": "NI 45-106",
        "required_sections": [
            {"id": "business_description", "label": "Business Description", "red_flags": ["vague business description", "no operating history"]},
            {"id": "use_of_proceeds", "label": "Use of Proceeds", "red_flags": ["general working capital without breakdown", "vague milestones"]},
            {"id": "dilution", "label": "Dilution", "red_flags": ["no cap table provided"]},
            {"id": "material_agreements", "label": "Material Agreements", "red_flags": ["no material agreements listed"]},
            {"id": "risk_factors", "label": "Risk Factors", "red_flags": ["generic boilerplate risks"]},
            {"id": "purchaser_rights", "label": "Purchaser's Rights", "red_flags": ["missing 2-day rescission right"]},
            {"id": "financial_statements", "label": "Financial Statements", "red_flags": ["no financial statements included", "unaudited when audit required"]},
            {"id": "selling_agent_relationship", "label": "Selling Agent Relationship", "red_flags": ["no conflict of interest disclosure"]},
            {"id": "forward_looking_info", "label": "Forward-Looking Information", "red_flags": ["forward-looking statements without disclaimer"]},
        ],
    },

    "mda": {
        "display_name": "MD&A",
        "form": "NI 51-102 Form 51-102F1",
        "regulatory_reference": "NI 51-102",
        "required_sections": [
            {"id": "overall_performance", "label": "Overall Performance", "red_flags": ["no comparison to prior period", "missing revenue discussion"]},
            {"id": "selected_financial_info", "label": "Selected Annual Information", "red_flags": ["less than 3 years of data", "missing key financial metrics"]},
            {"id": "results_of_operations", "label": "Results of Operations", "red_flags": ["no period comparison", "unexplained material variances"]},
            {"id": "liquidity_capital", "label": "Liquidity & Capital Resources", "red_flags": ["no liquidity discussion", "going concern not addressed", "no cash flow discussion"]},
            {"id": "capital_resources", "label": "Capital Resources", "red_flags": ["no capex discussion", "missing commitments disclosure"]},
            {"id": "off_balance_sheet", "label": "Off-Balance Sheet Arrangements", "red_flags": ["no off-balance sheet discussion"]},
            {"id": "transactions_related_parties", "label": "Transactions with Related Parties", "red_flags": ["no related party disclosure", "missing transaction terms"]},
            {"id": "critical_accounting_estimates", "label": "Critical Accounting Estimates", "red_flags": ["no accounting estimates discussion", "vague estimates disclosure"]},
            {"id": "forward_looking_statements", "label": "Forward-Looking Statements", "red_flags": ["forward-looking statements without disclaimer", "missing material assumptions"]},
            {"id": "risks_uncertainties", "label": "Risks & Uncertainties", "red_flags": ["generic boilerplate risks only", "no issuer-specific risks"]},
            {"id": "internal_controls", "label": "Internal Controls Over Financial Reporting", "red_flags": ["no ICFR discussion", "missing CEO/CFO certification reference"]},
        ],
    },

    "aif": {
        "display_name": "Annual Information Form",
        "form": "NI 51-102 Form 51-102F2",
        "regulatory_reference": "NI 51-102",
        "required_sections": [
            {"id": "corporate_structure", "label": "Corporate Structure", "red_flags": ["no corporate structure chart", "missing subsidiary disclosure"]},
            {"id": "general_development", "label": "General Development of Business", "red_flags": ["less than 3 years of history", "missing material events"]},
            {"id": "description_of_business", "label": "Description of Business", "red_flags": ["vague business description", "no competitive landscape"]},
            {"id": "risk_factors", "label": "Risk Factors", "red_flags": ["generic boilerplate risks", "no issuer-specific risks"]},
            {"id": "dividends", "label": "Dividends", "red_flags": ["no dividend policy disclosed"]},
            {"id": "capital_structure", "label": "Capital Structure", "red_flags": ["incomplete capital structure", "missing rights and restrictions"]},
            {"id": "market_for_securities", "label": "Market for Securities", "red_flags": ["missing price/volume table", "incomplete trading data"]},
            {"id": "directors_officers", "label": "Directors & Officers", "red_flags": ["missing 5-year occupation history", "no cease trade order disclosure"]},
            {"id": "audit_committee", "label": "Audit Committee", "red_flags": ["missing audit committee charter", "independence not confirmed"]},
            {"id": "legal_proceedings", "label": "Legal Proceedings & Regulatory Actions", "red_flags": ["no legal proceedings disclosure"]},
            {"id": "interests_of_experts", "label": "Interests of Experts", "red_flags": ["no expert interests disclosed", "missing auditor independence statement"]},
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# TEXT EXTRACTION & CHUNKING
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not PDF_AVAILABLE:
        return "[PDF extraction unavailable — pdfplumber not installed]"
    import io
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {str(e)}")


def chunk_text(text: str) -> list:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP
        if start >= len(text):
            break
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

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
- triggering_passage: verbatim excerpt (max 200 chars) or null
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
- CEO/CFO certifications missing or incomplete (NI 52-109)
- Material changes not disclosed on timely basis

For each flag found, return a JSON array with:
- flag_id: "FLAG_001", "FLAG_002", etc.
- flag_type: short snake_case label
- flag_category: "known_doctype" | "universal"
- severity: "high" | "medium" | "low"
- triggering_passage: exact text (max 200 chars) or null
- regulatory_basis: which rule is implicated
- suggested_action: one sentence for the human reviewer
- confidence: float 0.0-1.0

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON array. No other text."""


def build_risk_prompt(doc_type: dict, text: str) -> str:
    return f"""You are a Canadian capital markets analyst reviewing a {doc_type['display_name']} under {doc_type['regulatory_reference']}.

Extract all risk factor statements. For each, return a JSON array with:
- risk_id: "RISK_001", etc.
- category: "issuer_specific" | "market" | "regulatory" | "forward_looking" | "operational" | "financial"
- summary: one sentence
- verbatim_passage: exact text (max 300 chars)
- is_boilerplate: true if generic/non-specific
- severity: "high" | "medium" | "low"
- confidence: float 0.0-1.0

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON array. No other text."""


def build_summary_prompt(doc_type: dict, text: str) -> str:
    specific = {
        "mda": "Focus on: fiscal period, key financial metrics, going concern language, and overall management tone.",
        "aif": "Focus on: issuer's primary business, exchange listing, fiscal year end, and notable director/legal disclosures.",
        "offering_memorandum": "Focus on: offering size, security type, minimum subscription, and stage of business.",
    }
    doc_specific = specific.get(doc_type.get("id", ""), "Focus on key facts most relevant to a compliance reviewer.")

    return f"""You are a senior Canadian capital markets analyst reviewing a {doc_type['display_name']} under {doc_type['regulatory_reference']}.

{doc_specific}

Return a JSON object with:
- issuer_name: string or null
- fiscal_period: period covered (e.g. "Year ended December 31, 2024")
- offering_type: type of filing
- jurisdiction: province(s)
- business_summary: 2-3 sentences
- key_highlights: array of 4-6 strings
- overall_completeness: "complete" | "substantially_complete" | "materially_deficient"
- reviewer_priority: "high" | "medium" | "low"
- going_concern: true | false

DOCUMENT TEXT:
{text}

Return ONLY a valid JSON object. No other text."""


# ─────────────────────────────────────────────────────────────────────────────
# AI CALLER
# ─────────────────────────────────────────────────────────────────────────────

def call_ai(prompt: str):
    if MOCK_MODE or not ANTHROPIC_API_KEY:
        return None
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
    except Exception as e:
        print(f"Anthropic error: {e}")
        return None


def call_openai(prompt: str) -> str:
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None


def parse_json_response(raw, fallback):
    if raw is None:
        return fallback
    try:
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        return json.loads(cleaned)
    except Exception:
        return fallback


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────────────────────────────────────

MOCK_DATA = {
    "offering_memorandum": {
        "summary": {
            "issuer_name": "Cariboo Minerals Corp.",
            "fiscal_period": "Offering dated March 1, 2025",
            "offering_type": "Common Shares",
            "jurisdiction": "BC",
            "business_summary": "Cariboo Minerals Corp. is a BC-incorporated mineral exploration company focused on gold and copper targets in the Cariboo Mining District. The company holds option rights on three contiguous claims totaling 4,200 hectares.",
            "key_highlights": [
                "Offering size: $2.5M at $0.25/share via OM exemption",
                "Minimum subscription: $5,000 per investor",
                "Phase 1 drilling program planned Q3 2025",
                "Audited financials show $180K cash on hand as at Dec 31, 2024",
                "No revenue; exploration stage company"
            ],
            "overall_completeness": "substantially_complete",
            "reviewer_priority": "high",
            "going_concern": False,
        },
        "completeness": [
            {"section_id": "business_description", "label": "Business Description", "status": "present", "confidence": 0.92, "triggering_passage": "The Company was incorporated under the Business Corporations Act (British Columbia) and is engaged in the exploration and development of mineral properties in Northern BC.", "notes": "Clear business description with incorporation details and operational focus."},
            {"section_id": "use_of_proceeds", "label": "Use of Proceeds", "status": "incomplete", "confidence": 0.78, "triggering_passage": "Net proceeds will be used for working capital and general corporate purposes.", "notes": "Vague — no specific percentage allocation or milestone breakdown provided."},
            {"section_id": "dilution", "label": "Dilution", "status": "present", "confidence": 0.88, "triggering_passage": "Post-offering, the Company will have 45,200,000 common shares issued and outstanding.", "notes": "Cap table present with pre and post-offering figures."},
            {"section_id": "material_agreements", "label": "Material Agreements", "status": "present", "confidence": 0.81, "triggering_passage": "The Company has entered into a property option agreement dated March 1, 2025 with Cariboo Resources Ltd.", "notes": "Material agreements identified and summarized."},
            {"section_id": "risk_factors", "label": "Risk Factors", "status": "incomplete", "confidence": 0.65, "triggering_passage": "Investing in the securities of the Company involves a high degree of risk.", "notes": "Risk factors present but several appear boilerplate and not issuer-specific."},
            {"section_id": "purchaser_rights", "label": "Purchaser's Rights", "status": "missing", "confidence": 0.95, "triggering_passage": None, "notes": "No 2-day rescission right disclosure found. Required under BC securities law."},
            {"section_id": "financial_statements", "label": "Financial Statements", "status": "present", "confidence": 0.90, "triggering_passage": "See Appendix A — Audited Financial Statements for the year ended December 31, 2024.", "notes": "Audited financials included and referenced correctly."},
            {"section_id": "selling_agent_relationship", "label": "Selling Agent Relationship", "status": "incomplete", "confidence": 0.72, "triggering_passage": "The Company may pay finder's fees in connection with this offering.", "notes": "Agent relationship vaguely disclosed — specific compensation not quantified."},
            {"section_id": "forward_looking_info", "label": "Forward-Looking Information", "status": "incomplete", "confidence": 0.83, "triggering_passage": "The Company expects to complete its Phase 1 drilling program by Q3 2025.", "notes": "Forward-looking statements present but cautionary language block is missing."},
        ],
        "red_flags": [
            {"flag_id": "FLAG_001", "flag_type": "missing_rescission_right", "flag_category": "known_doctype", "severity": "high", "triggering_passage": None, "regulatory_basis": "NI 45-106 s.3.9 — BC purchasers have a 2-business-day right of rescission", "suggested_action": "Add a Purchaser's Rights section explicitly stating the 2-business-day rescission period under BC securities law.", "confidence": 0.95},
            {"flag_id": "FLAG_002", "flag_type": "vague_use_of_proceeds", "flag_category": "known_doctype", "severity": "high", "triggering_passage": "Net proceeds will be used for working capital and general corporate purposes.", "regulatory_basis": "NI 45-106 Form 45-106F2, Item 4 — Use of Proceeds must be specific with allocation percentages", "suggested_action": "Break down use of proceeds into specific line items with dollar amounts or percentage allocations.", "confidence": 0.91},
            {"flag_id": "FLAG_003", "flag_type": "missing_fli_cautionary_language", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "The Company expects to complete its Phase 1 drilling program by Q3 2025.", "regulatory_basis": "NI 51-102 s.4A.2 — Forward-looking information must be accompanied by cautionary language", "suggested_action": "Add a CAUTIONARY NOTE regarding forward-looking statements adjacent to all FLI disclosures.", "confidence": 0.87},
            {"flag_id": "FLAG_004", "flag_type": "boilerplate_risk_factors", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "Investing in junior resource companies involves risks common to the resource sector.", "regulatory_basis": "NI 45-106 Form 45-106F2, Item 7 — Risk factors must be specific to the issuer", "suggested_action": "Replace generic risk language with risks specific to this issuer's stage of development and mineral property.", "confidence": 0.79},
            {"flag_id": "FLAG_005", "flag_type": "undisclosed_agent_compensation", "flag_category": "universal", "severity": "low", "triggering_passage": "The Company may pay finder's fees in connection with this offering.", "regulatory_basis": "NI 45-106 Form 45-106F2, Item 6 — Agent compensation must be disclosed specifically", "suggested_action": "Specify the exact finder's fee structure or confirm no agent is engaged.", "confidence": 0.74},
        ],
        "risks": [
            {"risk_id": "RISK_001", "category": "issuer_specific", "summary": "The Company has no producing assets and is entirely reliant on exploration success.", "verbatim_passage": "The Company is an exploration-stage company with no history of earnings or revenue from mineral production.", "is_boilerplate": False, "severity": "high", "confidence": 0.90},
            {"risk_id": "RISK_002", "category": "financial", "summary": "The Company will require additional financing within 12 months with no guarantee of availability.", "verbatim_passage": "Management believes existing capital resources will be sufficient for approximately 12 months; however, there can be no assurance that additional financing will be available.", "is_boilerplate": False, "severity": "high", "confidence": 0.88},
            {"risk_id": "RISK_003", "category": "regulatory", "summary": "Environmental regulations may impose significant costs or restrictions on operations.", "verbatim_passage": "The operations of the Company are subject to environmental regulations promulgated by government authorities.", "is_boilerplate": True, "severity": "medium", "confidence": 0.75},
        ],
    },

    "mda": {
        "summary": {
            "issuer_name": "Pacific Northern Resources Ltd.",
            "fiscal_period": "Year ended December 31, 2024",
            "offering_type": "Annual MD&A",
            "jurisdiction": "BC",
            "business_summary": "Pacific Northern Resources Ltd. is a BC-based junior mining company with gold exploration properties in the Golden Triangle. The company is pre-revenue and relies on equity financings to fund exploration activities.",
            "key_highlights": [
                "Net loss of $2.1M for fiscal year 2024 (2023: $1.8M)",
                "Cash and equivalents: $340K as at December 31, 2024",
                "Working capital deficit of $180K — going concern risk noted",
                "Exploration expenditures of $1.4M capitalized during the year",
                "$3M private placement completed in Q1 2025 subsequent to year end",
                "CEO/CFO certifications filed under NI 52-109"
            ],
            "overall_completeness": "substantially_complete",
            "reviewer_priority": "high",
            "going_concern": True,
        },
        "completeness": [
            {"section_id": "overall_performance", "label": "Overall Performance", "status": "present", "confidence": 0.88, "triggering_passage": "For the year ended December 31, 2024, the Company incurred a net loss of $2,143,217 compared to a net loss of $1,821,445 for the year ended December 31, 2023.", "notes": "Year-over-year comparison provided with explanation of variance drivers."},
            {"section_id": "selected_financial_info", "label": "Selected Annual Information", "status": "present", "confidence": 0.85, "triggering_passage": "The following table sets forth selected financial information for each of the three most recently completed financial years.", "notes": "3-year summary table present with required financial metrics."},
            {"section_id": "results_of_operations", "label": "Results of Operations", "status": "present", "confidence": 0.87, "triggering_passage": "General and administrative expenses increased by $245,000 due to increased professional fees and investor relations costs.", "notes": "Material variances explained with reasonable detail."},
            {"section_id": "liquidity_capital", "label": "Liquidity & Capital Resources", "status": "incomplete", "confidence": 0.82, "triggering_passage": "As at December 31, 2024, the Company had cash of $340,217 and a working capital deficit of $180,443.", "notes": "Going concern language present but 12-month cash runway analysis is insufficiently detailed."},
            {"section_id": "capital_resources", "label": "Capital Resources", "status": "present", "confidence": 0.78, "triggering_passage": "The Company has no material commitments for capital expenditures beyond its planned exploration program.", "notes": "Capital resources discussion present though brief."},
            {"section_id": "off_balance_sheet", "label": "Off-Balance Sheet Arrangements", "status": "present", "confidence": 0.90, "triggering_passage": "The Company has no off-balance sheet arrangements.", "notes": "Clearly stated — no off-balance sheet arrangements."},
            {"section_id": "transactions_related_parties", "label": "Transactions with Related Parties", "status": "incomplete", "confidence": 0.71, "triggering_passage": "During the year, the Company paid management fees of $180,000 to a company controlled by the CEO.", "notes": "Related party transactions disclosed but terms and balances not fully detailed per IAS 24."},
            {"section_id": "critical_accounting_estimates", "label": "Critical Accounting Estimates", "status": "present", "confidence": 0.80, "triggering_passage": "The most significant estimates relate to the carrying value of exploration and evaluation assets and the fair value of stock-based compensation.", "notes": "Key estimates identified and discussed."},
            {"section_id": "forward_looking_statements", "label": "Forward-Looking Statements", "status": "incomplete", "confidence": 0.75, "triggering_passage": "The Company expects to commence drilling on its flagship property in Q2 2025.", "notes": "Forward-looking statements present but cautionary language block not prominently placed."},
            {"section_id": "risks_uncertainties", "label": "Risks & Uncertainties", "status": "present", "confidence": 0.83, "triggering_passage": "The Company faces risks related to financing, commodity prices, permitting, and exploration success.", "notes": "Risk discussion present — some items appear boilerplate."},
            {"section_id": "internal_controls", "label": "Internal Controls Over Financial Reporting", "status": "present", "confidence": 0.86, "triggering_passage": "The CEO and CFO have evaluated the effectiveness of the Company's disclosure controls and procedures as required under NI 52-109.", "notes": "ICFR discussion present with NI 52-109 reference."},
        ],
        "red_flags": [
            {"flag_id": "FLAG_001", "flag_type": "going_concern_insufficient_disclosure", "flag_category": "known_doctype", "severity": "high", "triggering_passage": "As at December 31, 2024, the Company had cash of $340,217 and a working capital deficit of $180,443.", "regulatory_basis": "NI 51-102 Form 51-102F1, Item 1.6 — Going concern requires detailed disclosure of plans to address the condition", "suggested_action": "Expand liquidity discussion to include specific plans to address going concern, including timing and probability of planned financing.", "confidence": 0.91},
            {"flag_id": "FLAG_002", "flag_type": "related_party_incomplete_disclosure", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "During the year, the Company paid management fees of $180,000 to a company controlled by the CEO.", "regulatory_basis": "IAS 24 / NI 51-102 — Related party transactions require disclosure of terms, outstanding balances, and nature of relationship", "suggested_action": "Add disclosure of outstanding balances, payment terms, and confirmation that transactions were at arm's length or explanation if not.", "confidence": 0.85},
            {"flag_id": "FLAG_003", "flag_type": "fli_cautionary_language_placement", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "The Company expects to commence drilling on its flagship property in Q2 2025.", "regulatory_basis": "NI 51-102 s.4A — Cautionary language must be proximate to forward-looking statements", "suggested_action": "Move or repeat the cautionary note immediately before or after the forward-looking statements rather than only at the document header.", "confidence": 0.80},
            {"flag_id": "FLAG_004", "flag_type": "liquidity_runway_insufficient", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "Management believes existing cash resources will be sufficient to meet obligations as they come due.", "regulatory_basis": "NI 51-102 Form 51-102F1, Item 1.6 — 12-month liquidity analysis required when going concern exists", "suggested_action": "Provide a month-by-month or quarterly cash flow projection for the next 12 months to support the going concern disclosure.", "confidence": 0.77},
        ],
        "risks": [
            {"risk_id": "RISK_001", "category": "financial", "summary": "Going concern doubt exists due to working capital deficit and reliance on future financings.", "verbatim_passage": "The Company's ability to continue as a going concern is dependent upon its ability to raise additional capital.", "is_boilerplate": False, "severity": "high", "confidence": 0.93},
            {"risk_id": "RISK_002", "category": "issuer_specific", "summary": "Exploration properties may not contain economic mineral deposits.", "verbatim_passage": "There is no assurance that the Company's exploration activities will result in any discoveries of commercial quantities of minerals.", "is_boilerplate": False, "severity": "high", "confidence": 0.88},
            {"risk_id": "RISK_003", "category": "market", "summary": "Gold price volatility could materially affect the economic viability of exploration properties.", "verbatim_passage": "The price of gold is subject to significant fluctuation and is affected by numerous factors beyond the Company's control.", "is_boilerplate": True, "severity": "medium", "confidence": 0.78},
            {"risk_id": "RISK_004", "category": "regulatory", "summary": "Permitting delays could impact planned exploration timeline.", "verbatim_passage": "The Company's exploration activities require permits from various government agencies which may not be obtained on a timely basis.", "is_boilerplate": False, "severity": "medium", "confidence": 0.82},
        ],
    },

    "aif": {
        "summary": {
            "issuer_name": "Westcoast Ventures Inc.",
            "fiscal_period": "Year ended December 31, 2024",
            "offering_type": "Annual Information Form",
            "jurisdiction": "BC",
            "business_summary": "Westcoast Ventures Inc. is a BC-incorporated reporting issuer listed on the CSE focused on technology-enabled financial services for the Canadian exempt market. The company operates a digital platform connecting exempt market dealers with accredited investors.",
            "key_highlights": [
                "Listed on the Canadian Securities Exchange (CSE: WCV)",
                "Fiscal year ended December 31, 2024",
                "Three wholly-owned subsidiaries — BC, Alberta, Ontario",
                "Board of 4 directors — 2 independent, 2 management",
                "No legal proceedings or regulatory actions outstanding",
                "Audit committee meets NI 52-110 composition requirements"
            ],
            "overall_completeness": "substantially_complete",
            "reviewer_priority": "medium",
            "going_concern": False,
        },
        "completeness": [
            {"section_id": "corporate_structure", "label": "Corporate Structure", "status": "present", "confidence": 0.89, "triggering_passage": "The Company was incorporated under the Business Corporations Act (British Columbia) on January 15, 2019. The Company has three wholly-owned subsidiaries.", "notes": "Corporate structure with subsidiary disclosure present. Intercorporate chart included."},
            {"section_id": "general_development", "label": "General Development of Business", "status": "present", "confidence": 0.84, "triggering_passage": "The following is a summary of the general development of the business of the Company over the three most recently completed financial years.", "notes": "3-year narrative present with key milestones identified."},
            {"section_id": "description_of_business", "label": "Description of Business", "status": "present", "confidence": 0.86, "triggering_passage": "The Company operates a technology platform that facilitates exempt market securities transactions between registered dealers and accredited investors.", "notes": "Business description is reasonably detailed with competitive context."},
            {"section_id": "risk_factors", "label": "Risk Factors", "status": "incomplete", "confidence": 0.74, "triggering_passage": "The Company is subject to risks common to early-stage technology companies operating in regulated industries.", "notes": "Risk factors present but several appear boilerplate — regulatory and competitive risks need more specificity."},
            {"section_id": "dividends", "label": "Dividends", "status": "present", "confidence": 0.95, "triggering_passage": "The Company has not paid any dividends and does not anticipate paying dividends in the foreseeable future.", "notes": "Dividend policy clearly stated."},
            {"section_id": "capital_structure", "label": "Capital Structure", "status": "present", "confidence": 0.88, "triggering_passage": "The authorized capital of the Company consists of an unlimited number of common shares without par value.", "notes": "Capital structure described with voting rights and transfer restrictions noted."},
            {"section_id": "market_for_securities", "label": "Market for Securities", "status": "incomplete", "confidence": 0.79, "triggering_passage": "The common shares of the Company are listed on the Canadian Securities Exchange under the symbol WCV.", "notes": "Exchange listing confirmed but quarterly high/low trading price and volume table is incomplete — only 2 quarters provided."},
            {"section_id": "directors_officers", "label": "Directors & Officers", "status": "incomplete", "confidence": 0.76, "triggering_passage": "The following table sets forth the name, municipality of residence and principal occupation of each director and officer.", "notes": "Director profiles present but 5-year occupation history is incomplete for two directors. Cease trade order disclosure absent."},
            {"section_id": "audit_committee", "label": "Audit Committee", "status": "present", "confidence": 0.87, "triggering_passage": "The Audit Committee is composed of three members, two of whom are independent and financially literate within the meaning of NI 52-110.", "notes": "Audit committee composition, independence, and financial literacy addressed. Charter attached."},
            {"section_id": "legal_proceedings", "label": "Legal Proceedings & Regulatory Actions", "status": "present", "confidence": 0.92, "triggering_passage": "The Company is not a party to any legal proceedings and is not aware of any contemplated legal proceedings.", "notes": "Clear statement — no outstanding legal proceedings or regulatory actions."},
            {"section_id": "interests_of_experts", "label": "Interests of Experts", "status": "incomplete", "confidence": 0.71, "triggering_passage": "The auditors of the Company are Davidson & Company LLP, Chartered Professional Accountants.", "notes": "Auditor identified but independence statement and beneficial ownership confirmation not included."},
        ],
        "red_flags": [
            {"flag_id": "FLAG_001", "flag_type": "incomplete_trading_price_table", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "The common shares of the Company are listed on the CSE under the symbol WCV.", "regulatory_basis": "NI 51-102 Form 51-102F2, Item 7 — Full year quarterly high/low price and volume data required", "suggested_action": "Complete the trading price and volume table with all four quarters of fiscal 2024 and the most recent quarter.", "confidence": 0.87},
            {"flag_id": "FLAG_002", "flag_type": "incomplete_director_5year_history", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": "John Smith, Director since 2022, previously served as CFO of various technology companies.", "regulatory_basis": "NI 51-102 Form 51-102F2, Item 10.1 — Principal occupation for each of the 5 preceding years required for all directors", "suggested_action": "Complete the 5-year occupation history for all directors including specific company names, positions, and dates.", "confidence": 0.84},
            {"flag_id": "FLAG_003", "flag_type": "missing_cease_trade_order_disclosure", "flag_category": "known_doctype", "severity": "medium", "triggering_passage": None, "regulatory_basis": "NI 51-102 Form 51-102F2, Item 10.2 — Cease trade order disclosure required for all directors and officers", "suggested_action": "Add disclosure confirming no director or officer has been subject to a cease trade order, bankruptcy, or penalty in the past 10 years.", "confidence": 0.90},
            {"flag_id": "FLAG_004", "flag_type": "missing_auditor_independence_statement", "flag_category": "known_doctype", "severity": "low", "triggering_passage": "The auditors of the Company are Davidson & Company LLP.", "regulatory_basis": "NI 51-102 Form 51-102F2, Item 15 — Auditor's interests and independence must be confirmed", "suggested_action": "Add a statement confirming the auditor holds no securities of the Company and is independent within the meaning of applicable securities legislation.", "confidence": 0.78},
        ],
        "risks": [
            {"risk_id": "RISK_001", "category": "regulatory", "summary": "Changes to exempt market regulations could materially affect the Company's business model.", "verbatim_passage": "The Company operates in a highly regulated environment and changes to securities legislation governing the exempt market could adversely affect our platform.", "is_boilerplate": False, "severity": "high", "confidence": 0.89},
            {"risk_id": "RISK_002", "category": "operational", "summary": "Technology platform reliability and cybersecurity risks could disrupt operations.", "verbatim_passage": "The Company's business is dependent on the reliable operation of its technology platform and any significant disruption could harm our reputation.", "is_boilerplate": False, "severity": "high", "confidence": 0.85},
            {"risk_id": "RISK_003", "category": "market", "summary": "General economic conditions could reduce exempt market investment activity.", "verbatim_passage": "Economic downturns or periods of market volatility may reduce investor appetite for exempt market securities.", "is_boilerplate": True, "severity": "medium", "confidence": 0.72},
        ],
    },
}


def get_mock_data(doc_type_id: str, key: str):
    return MOCK_DATA.get(doc_type_id, MOCK_DATA["offering_memorandum"]).get(key, [])


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

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

    doc_type["id"] = doc_type_id
    file_bytes = await file.read()
    session_id = str(uuid.uuid4())

    # Extract text
    if file.content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="replace")

    # Mock mode
    if MOCK_MODE or not ANTHROPIC_API_KEY:
        import asyncio
        await asyncio.sleep(0.5)
        return {
            "session_id": session_id,
            "doc_type_id": doc_type_id,
            "filename": file.filename,
            "jurisdiction": jurisdiction,
            "reviewed_at": datetime.utcnow().isoformat(),
            "completeness": get_mock_data(doc_type_id, "completeness"),
            "red_flags": get_mock_data(doc_type_id, "red_flags"),
            "risks": get_mock_data(doc_type_id, "risks"),
            "summary": get_mock_data(doc_type_id, "summary"),
            "mock": True,
        }

    # Live AI mode
    chunks = chunk_text(text)
    analysis_text = "\n\n---\n\n".join(chunks[:2])

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
