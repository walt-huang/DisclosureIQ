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

  mda: {
    id: "mda",
    display_name: "MD&A",
    form: "NI 51-102 Form 51-102F1",
    regulatory_reference: "NI 51-102",
    status: "live",
    jurisdictions: ["BC", "AB", "ON", "National"],
    category: "Continuous Disclosure",
    description: "Annual and interim management discussion & analysis",
    required_sections: [
      {
        id: "overall_performance",
        label: "Overall Performance",
        description: "Discussion of results of operations for the period",
        red_flags: ["no comparison to prior period", "missing revenue discussion", "vague performance narrative"],
      },
      {
        id: "selected_financial_info",
        label: "Selected Annual Information",
        description: "3-year summary of key financial data for annual MD&A",
        red_flags: ["less than 3 years of data", "missing key financial metrics", "no per share data"],
      },
      {
        id: "results_of_operations",
        label: "Results of Operations",
        description: "Period-over-period comparison with explanations for material changes",
        red_flags: ["no period comparison", "unexplained material variances", "missing segment discussion"],
      },
      {
        id: "liquidity_capital",
        label: "Liquidity & Capital Resources",
        description: "Cash position, working capital, financing sources, going concern if applicable",
        red_flags: ["no liquidity discussion", "missing working capital analysis", "going concern not addressed", "no cash flow discussion"],
      },
      {
        id: "capital_resources",
        label: "Capital Resources",
        description: "Material commitments for capital expenditures",
        red_flags: ["no capex discussion", "missing commitments disclosure"],
      },
      {
        id: "off_balance_sheet",
        label: "Off-Balance Sheet Arrangements",
        description: "Any off-balance sheet financing, guarantees, or contingencies",
        red_flags: ["no off-balance sheet discussion", "missing guarantee disclosure"],
      },
      {
        id: "transactions_related_parties",
        label: "Transactions with Related Parties",
        description: "All material related party transactions with terms and balances",
        red_flags: ["no related party disclosure", "missing transaction terms", "no IAS 24 reference"],
      },
      {
        id: "critical_accounting_estimates",
        label: "Critical Accounting Estimates",
        description: "Key judgments and estimates that materially affect financial statements",
        red_flags: ["no accounting estimates discussion", "missing key judgments", "vague estimates disclosure"],
      },
      {
        id: "forward_looking_statements",
        label: "Forward-Looking Statements",
        description: "Cautionary language and material assumptions for any FLS",
        red_flags: ["forward-looking statements without disclaimer", "missing material assumptions", "no CAUTIONARY NOTE"],
      },
      {
        id: "risks_uncertainties",
        label: "Risks & Uncertainties",
        description: "Material risks specific to the issuer and industry",
        red_flags: ["generic boilerplate risks only", "no issuer-specific risks", "missing industry risks"],
      },
      {
        id: "internal_controls",
        label: "Internal Controls Over Financial Reporting",
        description: "CEO/CFO certification of disclosure controls (NI 52-109)",
        red_flags: ["no ICFR discussion", "missing CEO/CFO certification reference", "material weakness not disclosed"],
      },
    ],
  },

  aif: {
    id: "aif",
    display_name: "Annual Information Form",
    form: "NI 51-102 Form 51-102F2",
    regulatory_reference: "NI 51-102",
    status: "live",
    jurisdictions: ["BC", "AB", "ON", "National"],
    category: "Continuous Disclosure",
    description: "Annual disclosure of issuer information for reporting issuers",
    required_sections: [
      {
        id: "corporate_structure",
        label: "Corporate Structure",
        description: "Incorporation details, intercorporate relationships, subsidiaries",
        red_flags: ["no corporate structure chart", "missing subsidiary disclosure", "incorrect jurisdiction of incorporation"],
      },
      {
        id: "general_development",
        label: "General Development of Business",
        description: "3-year history of significant developments",
        red_flags: ["less than 3 years of history", "missing material events", "no milestones discussed"],
      },
      {
        id: "description_of_business",
        label: "Description of Business",
        description: "Narrative of business activities, products/services, competitive conditions",
        red_flags: ["vague business description", "no competitive landscape", "missing revenue drivers"],
      },
      {
        id: "risk_factors",
        label: "Risk Factors",
        description: "Material risks to the business — issuer-specific, not boilerplate",
        red_flags: ["generic boilerplate risks", "no issuer-specific risks", "missing regulatory risks"],
      },
      {
        id: "dividends",
        label: "Dividends",
        description: "Dividend policy and history, restrictions on dividend payments",
        red_flags: ["no dividend policy disclosed", "missing restriction disclosure"],
      },
      {
        id: "capital_structure",
        label: "Capital Structure",
        description: "Description of all securities in the capital structure",
        red_flags: ["incomplete capital structure", "missing rights and restrictions", "no voting rights disclosure"],
      },
      {
        id: "market_for_securities",
        label: "Market for Securities",
        description: "Trading price and volume data for listed securities",
        red_flags: ["missing price/volume table", "incomplete trading data", "wrong date range"],
      },
      {
        id: "directors_officers",
        label: "Directors & Officers",
        description: "Names, municipalities, positions, principal occupations for past 5 years",
        red_flags: ["missing 5-year occupation history", "incomplete director profiles", "no cease trade order disclosure"],
      },
      {
        id: "audit_committee",
        label: "Audit Committee",
        description: "Composition, independence, financial literacy, charter",
        red_flags: ["missing audit committee charter", "independence not confirmed", "financial literacy not addressed"],
      },
      {
        id: "legal_proceedings",
        label: "Legal Proceedings & Regulatory Actions",
        description: "Material legal proceedings and regulatory actions",
        red_flags: ["no legal proceedings disclosure", "missing regulatory actions"],
      },
      {
        id: "interests_of_experts",
        label: "Interests of Experts",
        description: "Disclosure of interests held by experts named in the AIF",
        red_flags: ["no expert interests disclosed", "missing auditor independence statement"],
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
