// ─────────────────────────────────────────────────────────────────────────────
// DOCUMENT TYPE REGISTRY
// Adding a new document type = adding an entry here. No other code changes needed.
// ─────────────────────────────────────────────────────────────────────────────

export const DOCUMENT_REGISTRY = {
  offering_memorandum: {
    id: "offering_memorandum",
    display_name: "Offering Memorandum",
    form: "Form 45-106F2",
    regulatory_reference: "NI 45-106",
    status: "live",
    jurisdictions: ["BC", "AB", "ON", "National"],
    category: "Offering Documents",
    description: "Exempt market capital raises under the OM exemption",
    required_sections: [
      {
        id: "business_description",
        label: "Business Description",
        description: "Nature of business, history, and key milestones",
        red_flags: ["vague business description", "no operating history disclosed"],
      },
      {
        id: "use_of_proceeds",
        label: "Use of Proceeds",
        description: "Specific breakdown of how funds will be allocated",
        red_flags: ["general working capital without breakdown", "vague milestones", "no percentage allocation"],
      },
      {
        id: "dilution",
        label: "Dilution",
        description: "Current vs. post-offering capitalization table",
        red_flags: ["no cap table provided", "missing post-offering share count"],
      },
      {
        id: "material_agreements",
        label: "Material Agreements",
        description: "Contracts the business depends on",
        red_flags: ["no material agreements listed", "related party agreements not identified"],
      },
      {
        id: "risk_factors",
        label: "Risk Factors",
        description: "Issuer-specific risks — not boilerplate",
        red_flags: ["generic boilerplate risks", "no issuer-specific risk language", "missing regulatory risk"],
      },
      {
        id: "purchaser_rights",
        label: "Purchaser's Rights",
        description: "2-day rescission right must be explicitly stated (BC)",
        red_flags: ["missing 2-day rescission right", "no cancellation right mentioned", "rescission period incorrect"],
      },
      {
        id: "financial_statements",
        label: "Financial Statements",
        description: "Audited financials where required by raise size",
        red_flags: ["no financial statements included", "unaudited when audit required", "financials not dated within required period"],
      },
      {
        id: "selling_agent_relationship",
        label: "Selling Agent Relationship",
        description: "Conflicts of interest and compensation disclosure",
        red_flags: ["no conflict of interest disclosure", "agent compensation not disclosed"],
      },
      {
        id: "forward_looking_info",
        label: "Forward-Looking Information",
        description: "If FLI is present, cautionary language must accompany it",
        red_flags: ["forward-looking statements without disclaimer", "no material assumptions disclosed", "missing CAUTIONARY NOTE header"],
      },
    ],
  },

  short_form_prospectus: {
    id: "short_form_prospectus",
    display_name: "Short Form Prospectus",
    form: "NI 44-101",
    regulatory_reference: "NI 44-101",
    status: "coming_soon",
    category: "Offering Documents",
    description: "Accelerated prospectus for reporting issuers",
  },

  long_form_prospectus: {
    id: "long_form_prospectus",
    display_name: "Long Form Prospectus",
    form: "NI 41-101",
    regulatory_reference: "NI 41-101",
    status: "coming_soon",
    category: "Offering Documents",
    description: "Full prospectus for non-reporting issuers or IPOs",
  },

  mda: {
    id: "mda",
    display_name: "MD&A",
    form: "NI 51-102",
    regulatory_reference: "NI 51-102",
    status: "coming_soon",
    category: "Continuous Disclosure",
    description: "Annual and interim management discussion & analysis",
  },

  aif: {
    id: "aif",
    display_name: "Annual Information Form",
    form: "NI 51-102 Form 52-110F1",
    regulatory_reference: "NI 51-102",
    status: "coming_soon",
    category: "Continuous Disclosure",
    description: "Annual disclosure of issuer information",
  },

  cse_listing_statement: {
    id: "cse_listing_statement",
    display_name: "CSE Listing Statement",
    form: "Form 2A",
    regulatory_reference: "CSE Policy 2",
    status: "coming_soon",
    category: "Exchange Filings",
    description: "Canadian Securities Exchange initial listing disclosure",
  },

  tsxv_filing_statement: {
    id: "tsxv_filing_statement",
    display_name: "TSX-V Filing Statement",
    form: "Form 3B1",
    regulatory_reference: "TSX-V Policy 2.4",
    status: "coming_soon",
    category: "Exchange Filings",
    description: "TSX Venture Exchange capital pool company filings",
  },
};

// Grouped by category for sidebar rendering
export const REGISTRY_BY_CATEGORY = Object.values(DOCUMENT_REGISTRY).reduce((acc, doc) => {
  if (!acc[doc.category]) acc[doc.category] = [];
  acc[doc.category].push(doc);
  return acc;
}, {});
