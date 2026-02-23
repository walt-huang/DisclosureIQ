import { useState } from "react";

const STATUS_COLOR = {
  present: "status--present",
  incomplete: "status--incomplete",
  missing: "status--missing",
};

const STATUS_LABEL = {
  present: "✓ Present",
  incomplete: "△ Incomplete",
  missing: "✗ Missing",
};

const SEVERITY_COLOR = {
  high: "sev--high",
  medium: "sev--medium",
  low: "sev--low",
};

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="conf-bar-wrap" title={`Confidence: ${pct}%`}>
      <div className="conf-bar">
        <div className="conf-bar-fill" style={{ width: `${pct}%`, opacity: 0.4 + value * 0.6 }} />
      </div>
      <span className="conf-label">{pct}%</span>
    </div>
  );
}

function FlagCard({ flag, flagId, action, note, onAction }) {
  const [localNote, setLocalNote] = useState(note || "");
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`flag-card ${action ? `flag-card--${action}` : ""}`}>
      <div className="flag-card-header" onClick={() => setExpanded(!expanded)}>
        <div className="flag-card-left">
          <span className={`sev-badge ${SEVERITY_COLOR[flag.severity]}`}>{flag.severity?.toUpperCase()}</span>
          <span className="flag-type">{flag.flag_type?.replace(/_/g, " ")}</span>
        </div>
        <div className="flag-card-right">
          <ConfidenceBar value={flag.confidence} />
          <span className="expand-toggle">{expanded ? "▲" : "▼"}</span>
        </div>
      </div>

      {expanded && (
        <div className="flag-card-body">
          {flag.triggering_passage && (
            <div className="passage-block">
              <div className="passage-label">Triggering Passage</div>
              <blockquote className="passage-text">"{flag.triggering_passage}"</blockquote>
            </div>
          )}
          {flag.regulatory_basis && (
            <div className="reg-basis">
              <span className="reg-basis-label">Regulatory Basis:</span> {flag.regulatory_basis}
            </div>
          )}
          {flag.suggested_action && (
            <div className="suggested-action">
              <span className="suggested-label">Suggested Action:</span> {flag.suggested_action}
            </div>
          )}
          <div className="reviewer-actions">
            <textarea
              className="note-input"
              placeholder="Add reviewer note..."
              value={localNote}
              onChange={(e) => setLocalNote(e.target.value)}
            />
            <div className="action-buttons">
              <button
                className={`action-btn action-btn--confirm ${action === "confirmed" ? "action-btn--active" : ""}`}
                onClick={() => onAction(flagId, "confirmed", localNote)}
              >
                ✓ Confirm Flag
              </button>
              <button
                className={`action-btn action-btn--dismiss ${action === "dismissed" ? "action-btn--active" : ""}`}
                onClick={() => onAction(flagId, "dismissed", localNote)}
              >
                ✗ Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {action && (
        <div className="flag-card-status">
          {action === "confirmed" ? "✓ Confirmed by reviewer" : "✗ Dismissed by reviewer"}
          {localNote && ` — ${localNote}`}
        </div>
      )}
    </div>
  );
}

export default function ReviewDashboard({ session, onAction, onSignOff, onNewReview }) {
  const [activeTab, setActiveTab] = useState("completeness");

  const { completeness = [], red_flags = [], risks = [], summary = {}, reviewer_actions, reviewer_notes } = session;

  const allFlags = red_flags.map((f) => f.flag_id);
  const reviewedCount = allFlags.filter((id) => reviewer_actions[id]).length;
  const totalFlags = allFlags.length;
  const allReviewed = totalFlags > 0 && reviewedCount === totalFlags;

  const presentCount = completeness.filter((s) => s.status === "present").length;
  const missingCount = completeness.filter((s) => s.status === "missing").length;
  const incompleteCount = completeness.filter((s) => s.status === "incomplete").length;

  return (
    <div className="dashboard">
      {/* Summary bar */}
      <div className="summary-bar">
        <div className="summary-item">
          <div className="summary-val">{session.doc_type.display_name}</div>
          <div className="summary-key">Document Type</div>
        </div>
        <div className="summary-divider" />
        <div className="summary-item">
          <div className="summary-val">{summary.issuer_name || "—"}</div>
          <div className="summary-key">Issuer</div>
        </div>
        <div className="summary-divider" />
        <div className="summary-item">
          <div className="summary-val">{session.jurisdiction}</div>
          <div className="summary-key">Jurisdiction</div>
        </div>
        <div className="summary-divider" />
        <div className="summary-item">
          <div className={`summary-val summary-val--${summary.overall_completeness?.replace("_", "-") || "unknown"}`}>
            {summary.overall_completeness?.replace(/_/g, " ") || "—"}
          </div>
          <div className="summary-key">Completeness</div>
        </div>
        <div className="summary-divider" />
        <div className="summary-item">
          <div className="summary-val">{reviewedCount}/{totalFlags}</div>
          <div className="summary-key">Flags Reviewed</div>
        </div>
        <div className="summary-actions">
          <button className="btn-secondary" onClick={onNewReview}>← New Review</button>
          <button
            className={`btn-primary ${!allReviewed ? "btn-primary--disabled" : ""}`}
            onClick={onSignOff}
            disabled={!allReviewed}
            title={!allReviewed ? `Review all ${totalFlags - reviewedCount} remaining flags first` : ""}
          >
            Sign Off →
          </button>
        </div>
      </div>

      {/* Key highlights */}
      {summary.key_highlights?.length > 0 && (
        <div className="highlights-bar">
          {summary.key_highlights.map((h, i) => (
            <div key={i} className="highlight-chip">
              <span className="highlight-bullet">▸</span> {h}
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="tab-bar">
        <button className={`tab ${activeTab === "completeness" ? "tab--active" : ""}`} onClick={() => setActiveTab("completeness")}>
          Completeness
          <span className="tab-count">{presentCount}✓ {missingCount}✗</span>
        </button>
        <button className={`tab ${activeTab === "flags" ? "tab--active" : ""}`} onClick={() => setActiveTab("flags")}>
          Red Flags
          <span className="tab-count">{red_flags.filter(f => f.severity === "high").length} high</span>
        </button>
        <button className={`tab ${activeTab === "risks" ? "tab--active" : ""}`} onClick={() => setActiveTab("risks")}>
          Risk Factors
          <span className="tab-count">{risks.length} found</span>
        </button>
      </div>

      {/* Tab content */}
      <div className="tab-content">
        {/* COMPLETENESS TAB */}
        {activeTab === "completeness" && (
          <div className="completeness-table">
            <div className="table-header">
              <span>Section</span>
              <span>Status</span>
              <span>Confidence</span>
              <span>Notes</span>
            </div>
            {completeness.map((s) => (
              <div key={s.section_id} className="table-row">
                <div className="table-cell">
                  <div className="section-label">{s.label}</div>
                  {s.triggering_passage && (
                    <div className="section-passage">"{s.triggering_passage.substring(0, 100)}..."</div>
                  )}
                </div>
                <div className="table-cell">
                  <span className={`status-badge ${STATUS_COLOR[s.status]}`}>
                    {STATUS_LABEL[s.status]}
                  </span>
                </div>
                <div className="table-cell">
                  <ConfidenceBar value={s.confidence} />
                </div>
                <div className="table-cell table-cell--notes">{s.notes}</div>
              </div>
            ))}
          </div>
        )}

        {/* RED FLAGS TAB */}
        {activeTab === "flags" && (
          <div className="flags-list">
            {red_flags.length === 0 && (
              <div className="empty-state">No red flags detected in this document.</div>
            )}
            {red_flags.map((flag) => (
              <FlagCard
                key={flag.flag_id}
                flag={flag}
                flagId={flag.flag_id}
                action={reviewer_actions[flag.flag_id]}
                note={reviewer_notes[flag.flag_id]}
                onAction={onAction}
              />
            ))}
            {totalFlags > 0 && (
              <div className="review-progress">
                <div className="review-progress-bar">
                  <div
                    className="review-progress-fill"
                    style={{ width: `${(reviewedCount / totalFlags) * 100}%` }}
                  />
                </div>
                <span className="review-progress-label">{reviewedCount} of {totalFlags} flags reviewed</span>
              </div>
            )}
          </div>
        )}

        {/* RISKS TAB */}
        {activeTab === "risks" && (
          <div className="risks-list">
            {risks.length === 0 && (
              <div className="empty-state">No risk factors extracted from this document.</div>
            )}
            {risks.map((risk) => (
              <div key={risk.risk_id} className={`risk-card ${risk.is_boilerplate ? "risk-card--boilerplate" : ""}`}>
                <div className="risk-card-header">
                  <span className={`sev-badge ${SEVERITY_COLOR[risk.severity]}`}>{risk.severity?.toUpperCase()}</span>
                  <span className="risk-category">{risk.category?.replace(/_/g, " ")}</span>
                  {risk.is_boilerplate && <span className="boilerplate-badge">⚠ Boilerplate</span>}
                  <ConfidenceBar value={risk.confidence} />
                </div>
                <div className="risk-summary">{risk.summary}</div>
                {risk.verbatim_passage && (
                  <blockquote className="passage-text small">"{risk.verbatim_passage.substring(0, 200)}..."</blockquote>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
