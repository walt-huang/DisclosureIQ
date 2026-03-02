// ─────────────────────────────────────────────────────────────────────────────
// PROMPT TEMPLATES
// All prompts are document-type agnostic.
// They receive the document schema at runtime and produce structured JSON.
// ─────────────────────────────────────────────────────────────────────────────

export function buildCompletenessPrompt(docType, textChunk) {
  const sections = docType.required_sections
    .map((s, i) => `${i + 1}. ${s.label}: ${s.description}`)
    .join("\n");

  return `You are a senior Canadian capital markets compliance reviewer with expertise in ${docType.regulatory_reference}.

You are reviewing a ${docType.display_name} (${docType.form}) filing.

The following sections are REQUIRED under ${docType.regulatory_reference}:
${sections}

Review the provided text and for each required section return a JSON array with objects containing:
- "section_id": the section identifier (use snake_case of the label)
- "label": human-readable section name
- "status": one of "present" | "incomplete" | "missing"
- "confidence": float 0.0-1.0
- "triggering_passage": the verbatim text excerpt that satisfies the section, or null if missing
- "notes": brief explanation of why status was assigned

Be conservative: if a section exists but lacks the specificity required by regulation, mark it "incomplete" not "present".
If a section is entirely absent, mark it "missing".

DOCUMENT TEXT:
${textChunk}

Respond ONLY with a valid JSON array. No preamble, no explanation outside the JSON.`;
}

export function buildRiskExtractionPrompt(docType, textChunk) {
  return `You are a Canadian capital markets compliance reviewer specializing in ${docType.regulatory_reference}.

You are reviewing a ${docType.display_name} filing.

Extract ALL risk factor statements from the following text. For each risk, return a JSON array with objects containing:
- "risk_id": sequential identifier like "RISK_001"
- "category": one of "issuer_specific" | "market" | "regulatory" | "forward_looking" | "operational" | "financial"
- "summary": one clear sentence summarizing the risk
- "verbatim_passage": the exact text from the document
- "is_boilerplate": true if the risk appears generic and not tailored to this issuer, false otherwise
- "severity": one of "high" | "medium" | "low"
- "confidence": float 0.0-1.0

Flag is_boilerplate = true when risk language could apply to any company (e.g. "general economic conditions may affect the business").
Flag is_boilerplate = false when the risk is specific to this issuer, industry, or offering.

DOCUMENT TEXT:
${textChunk}

Respond ONLY with a valid JSON array. No preamble, no explanation outside the JSON.`;
}

export function buildRedFlagPrompt(docType, textChunk) {
  const knownFlags = docType.required_sections
    .flatMap((s) => s.red_flags || [])
    .map((f, i) => `${i + 1}. ${f}`)
    .join("\n");

  return `You are a compliance reviewer for Canadian capital markets filings with expertise in ${docType.regulatory_reference}.

Review this ${docType.display_name} for compliance red flags.

KNOWN RED FLAGS FOR THIS DOCUMENT TYPE (${docType.regulatory_reference}):
${knownFlags}

UNIVERSAL RED FLAGS (apply to all Canadian securities filings):
- Related party transactions not clearly disclosed or identified
- Forward-looking statements without cautionary language or material assumptions
- Conflicts of interest between issuer and selling agents not disclosed
- Ambiguous or missing references to financial statements
- Missing or incorrect statutory rights of rescission or withdrawal
- Auditor independence concerns
- Undisclosed material changes since last filing date

For each red flag found, return a JSON array with objects containing:
- "flag_id": sequential identifier like "FLAG_001"
- "flag_type": short label (e.g. "vague_use_of_proceeds", "missing_rescission_right")
- "flag_category": one of "known_doctype" | "universal"
- "severity": one of "high" | "medium" | "low"
- "triggering_passage": the exact text that triggered the flag, or null
- "regulatory_basis": which rule, form item, or policy is implicated
- "suggested_action": one sentence of guidance for the human reviewer
- "confidence": float 0.0-1.0

DOCUMENT TEXT:
${textChunk}

Respond ONLY with a valid JSON array. No preamble, no explanation outside the JSON.`;
}

export function buildSummaryPrompt(docType, textChunk) {
  return `You are a senior Canadian capital markets analyst reviewing a ${docType.display_name} under ${docType.regulatory_reference}.

Provide a structured executive summary of this filing. Return a JSON object with:
- "issuer_name": name of the issuing company (or null if not found)
- "offering_type": type of securities being offered
- "offering_size": dollar amount of the offering (or null)
- "jurisdiction": province(s) where the offering is being made
- "business_summary": 2-3 sentence plain-language description of the issuer's business
- "key_highlights": array of 3-5 strings — the most important facts a reviewer should know immediately
- "overall_completeness": one of "complete" | "substantially_complete" | "materially_deficient"
- "reviewer_priority": "high" | "medium" | "low" — urgency for human review

DOCUMENT TEXT:
${textChunk}

Respond ONLY with a valid JSON object. No preamble, no explanation outside the JSON.`;
}
