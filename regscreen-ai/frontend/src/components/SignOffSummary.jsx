export default function SignOffSummary({ session, onNewReview }) {
  const { completeness = [], red_flags = [], risks = [], summary = {}, reviewer_actions, reviewer_notes } = session;

  const confirmed = red_flags.filter((f) => reviewer_actions[f.flag_id] === "confirmed");
  const dismissed = red_flags.filter((f) => reviewer_actions[f.flag_id] === "dismissed");
  const highFlags = red_flags.filter((f) => f.severity === "high");
  const missingCount = completeness.filter((s) => s.status === "missing").length;

  function handlePrint() {
    window.print();
  }

  return (
    <div className="signoff-screen">
      <div className="signoff-card">
        <div className="signoff-header">
          <div className="signoff-stamp">REVIEWED</div>
          <div className="signoff-title">Compliance Review Sign-Off</div>
          <div className="signoff-sub">Disclosure-IQ · Canadian Capital Markets Compliance Platform</div>
        </div>

        <div className="signoff-meta-grid">
          <div className="meta-item">
            <div className="meta-label">Document Type</div>
            <div className="meta-val">{session.doc_type.display_name}</div>
          </div>
          <div className="meta-item">
            <div className="meta-label">Regulatory Reference</div>
            <div className="meta-val">{session.doc_type.regulatory_reference} · {session.doc_type.form}</div>
          </div>
          <div className="meta-item">
            <div className="meta-label">Issuer</div>
            <div className="meta-val">{summary.issuer_name || "—"}</div>
          </div>
          <div className="meta-item">
            <div className="meta-label">Jurisdiction</div>
            <div className="meta-val">{session.jurisdiction}</div>
          </div>
          <div className="meta-item">
            <div className="meta-label">Reviewer</div>
            <div className="meta-val">{session.reviewer_name}</div>
          </div>
          <div className="meta-item">
            <div className="meta-label">Review Completed</div>
            <div className="meta-val">{new Date(session.signed_off_at).toLocaleString("en-CA")}</div>
          </div>
        </div>

        <div className="signoff-stats">
          <div className="stat-box">
            <div className="stat-num">{completeness.filter(s => s.status === "present").length}/{completeness.length}</div>
            <div className="stat-label">Sections Present</div>
          </div>
          <div className="stat-box stat-box--warn">
            <div className="stat-num">{missingCount}</div>
            <div className="stat-label">Missing Sections</div>
          </div>
          <div className="stat-box stat-box--danger">
            <div className="stat-num">{highFlags.length}</div>
            <div className="stat-label">High Severity Flags</div>
          </div>
          <div className="stat-box stat-box--ok">
            <div className="stat-num">{confirmed.length}</div>
            <div className="stat-label">Flags Confirmed</div>
          </div>
          <div className="stat-box">
            <div className="stat-num">{dismissed.length}</div>
            <div className="stat-label">Flags Dismissed</div>
          </div>
          <div className="stat-box">
            <div className="stat-num">{risks.filter(r => r.is_boilerplate).length}</div>
            <div className="stat-label">Boilerplate Risks</div>
          </div>
        </div>

        {/* Confirmed flags detail */}
        {confirmed.length > 0 && (
          <div className="signoff-section">
            <div className="signoff-section-title">Confirmed Flags — Requires Issuer Action</div>
            {confirmed.map((flag) => (
              <div key={flag.flag_id} className="signoff-flag confirmed">
                <div className="signoff-flag-header">
                  <span className="signoff-flag-type">{flag.flag_type?.replace(/_/g, " ")}</span>
                  <span className="signoff-flag-sev">{flag.severity?.toUpperCase()}</span>
                </div>
                {reviewer_notes[flag.flag_id] && (
                  <div className="signoff-flag-note">Reviewer note: {reviewer_notes[flag.flag_id]}</div>
                )}
                <div className="signoff-flag-basis">{flag.regulatory_basis}</div>
              </div>
            ))}
          </div>
        )}

        {/* Dismissed flags */}
        {dismissed.length > 0 && (
          <div className="signoff-section">
            <div className="signoff-section-title">Dismissed Flags</div>
            {dismissed.map((flag) => (
              <div key={flag.flag_id} className="signoff-flag dismissed">
                <div className="signoff-flag-header">
                  <span className="signoff-flag-type">{flag.flag_type?.replace(/_/g, " ")}</span>
                </div>
                {reviewer_notes[flag.flag_id] && (
                  <div className="signoff-flag-note">Reviewer note: {reviewer_notes[flag.flag_id]}</div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="signoff-signature">
          <div className="sig-line" />
          <div className="sig-name">{session.reviewer_name}</div>
          <div className="sig-date">{new Date(session.signed_off_at).toLocaleDateString("en-CA", { year: "numeric", month: "long", day: "numeric" })}</div>
        </div>

        <div className="signoff-disclaimer">
          This review was generated with AI-assisted analysis (Disclosure-IQ) and confirmed by a human reviewer. 
          It does not constitute legal advice or a qualified opinion under applicable securities legislation. 
          All flagged items should be reviewed with qualified legal counsel before filing.
        </div>
      </div>

      <div className="signoff-actions">
        <button className="btn-secondary" onClick={handlePrint}>Print / Save as PDF</button>
        <button className="btn-primary" onClick={onNewReview}>← Start New Review</button>
      </div>
    </div>
  );
}
