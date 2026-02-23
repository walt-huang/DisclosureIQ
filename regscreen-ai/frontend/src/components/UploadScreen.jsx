import { useState, useRef } from "react";

export default function UploadScreen({ docType, onUpload, isProcessing, processingStep }) {
  const [file, setFile] = useState(null);
  const [jurisdiction, setJurisdiction] = useState("BC");
  const [reviewerName, setReviewerName] = useState("");
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef();

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type === "application/pdf") setFile(f);
  }

  function handleSubmit() {
    if (!file || !reviewerName.trim()) return;
    onUpload(file, jurisdiction, reviewerName.trim());
  }

  if (isProcessing) {
    return (
      <div className="processing-screen">
        <div className="processing-inner">
          <div className="processing-spinner" />
          <div className="processing-title">Analysing Document</div>
          <div className="processing-step">{processingStep}</div>
          <div className="processing-doc">{file?.name}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="upload-screen">
      <div className="upload-header">
        <div className="upload-eyebrow">{docType.regulatory_reference} · {docType.form}</div>
        <h1 className="upload-title">{docType.display_name}<br />Review</h1>
        <p className="upload-desc">{docType.description}</p>
      </div>

      <div className="upload-form">
        {/* Drop zone */}
        <div
          className={`dropzone ${dragging ? "dropzone--active" : ""} ${file ? "dropzone--filled" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            onChange={(e) => setFile(e.target.files[0])}
          />
          {file ? (
            <div className="dropzone-filled">
              <div className="file-icon">PDF</div>
              <div className="file-name">{file.name}</div>
              <div className="file-size">{(file.size / 1024).toFixed(0)} KB · Click to replace</div>
            </div>
          ) : (
            <div className="dropzone-empty">
              <div className="drop-icon">↑</div>
              <div className="drop-label">Drop PDF here or click to browse</div>
              <div className="drop-sub">Supports Form 45-106F2 and similar OM structures</div>
            </div>
          )}
        </div>

        {/* Reviewer details */}
        <div className="form-row">
          <div className="form-field">
            <label className="form-label">Reviewer Name</label>
            <input
              className="form-input"
              type="text"
              placeholder="e.g. Jane Smith"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label className="form-label">Jurisdiction</label>
            <select
              className="form-input form-select"
              value={jurisdiction}
              onChange={(e) => setJurisdiction(e.target.value)}
            >
              {docType.jurisdictions?.map((j) => (
                <option key={j} value={j}>{j}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          className={`btn-primary ${(!file || !reviewerName.trim()) ? "btn-primary--disabled" : ""}`}
          onClick={handleSubmit}
          disabled={!file || !reviewerName.trim()}
        >
          Run Compliance Review →
        </button>

        {/* Required sections preview */}
        <div className="sections-preview">
          <div className="sections-preview-title">Checking {docType.required_sections.length} Required Sections</div>
          <div className="sections-grid">
            {docType.required_sections.map((s) => (
              <div key={s.id} className="section-chip">{s.label}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
