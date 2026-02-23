export default function Sidebar({ registry, activeDocType, onSelect }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">RS</div>
        <div className="logo-text">
          <span className="logo-title">RegScreen</span>
          <span className="logo-sub">Capital Markets AI</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {Object.entries(registry).map(([category, docs]) => (
          <div key={category} className="nav-group">
            <div className="nav-category">{category}</div>
            {docs.map((doc) => (
              <button
                key={doc.id}
                className={`nav-item ${doc.status === "coming_soon" ? "nav-item--disabled" : ""} ${activeDocType === doc.id ? "nav-item--active" : ""}`}
                onClick={() => doc.status === "live" && onSelect(doc.id)}
                disabled={doc.status === "coming_soon"}
              >
                <div className="nav-item-main">
                  <span className="nav-item-name">{doc.display_name}</span>
                  {doc.status === "coming_soon" && (
                    <span className="nav-badge">Soon</span>
                  )}
                  {doc.status === "live" && activeDocType === doc.id && (
                    <span className="nav-badge nav-badge--live">Active</span>
                  )}
                </div>
                <span className="nav-item-form">{doc.form}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-tag">BCSC · CSA · NI Compliant</div>
      </div>
    </aside>
  );
}
