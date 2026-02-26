import { useState, useRef } from "react";
import { DOCUMENT_REGISTRY, REGISTRY_BY_CATEGORY } from "./config/documentRegistry";
import Sidebar from "./components/Sidebar";
import UploadScreen from "./components/UploadScreen";
import ReviewDashboard from "./components/ReviewDashboard";
import SignOffSummary from "./components/SignOffSummary";
import "./styles.css";

export default function App() {
  const [activeDocType, setActiveDocType] = useState("offering_memorandum");
  const [screen, setScreen] = useState("upload"); // upload | reviewing | signoff
  const [reviewSession, setReviewSession] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");

  const docType = DOCUMENT_REGISTRY[activeDocType];

  async function handleUpload(file, jurisdiction, reviewerName) {
    setIsProcessing(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type_id", activeDocType);
    formData.append("jurisdiction", jurisdiction);
    formData.append("reviewer_name", reviewerName);

    const steps = [
      "Extracting text from PDF...",
      "Chunking document...",
      "Running completeness check...",
      "Extracting risk factors...",
      "Scanning for red flags...",
      "Generating executive summary...",
      "Building review checklist...",
    ];

    // Simulate step progression for UX
    let stepIdx = 0;
    setProcessingStep(steps[0]);
    const stepInterval = setInterval(() => {
      stepIdx = Math.min(stepIdx + 1, steps.length - 1);
      setProcessingStep(steps[stepIdx]);
    }, 1200);

    try {
      const res = await fetch("/api/review", {
        method: "POST",
        body: formData,
      });

      clearInterval(stepInterval);

      if (!res.ok) throw new Error("Review failed");
      const data = await res.json();

      setReviewSession({
        ...data,
        reviewer_name: reviewerName,
        jurisdiction,
        doc_type: docType,
        reviewer_actions: {},
        reviewer_notes: {},
        started_at: new Date().toISOString(),
      });
      setScreen("reviewing");
    } catch (err) {
      clearInterval(stepInterval);
      alert("Error processing document: " + err.message);
    } finally {
      setIsProcessing(false);
      setProcessingStep("");
    }
  }

  function handleReviewerAction(flagId, action, note) {
    setReviewSession((prev) => ({
      ...prev,
      reviewer_actions: { ...prev.reviewer_actions, [flagId]: action },
      reviewer_notes: { ...prev.reviewer_notes, [flagId]: note || "" },
    }));
  }

  function handleSignOff() {
    setReviewSession((prev) => ({
      ...prev,
      signed_off_at: new Date().toISOString(),
    }));
    setScreen("signoff");
  }

  function handleNewReview() {
    setReviewSession(null);
    setScreen("upload");
  }

  return (
    <div className="app-shell">
      <Sidebar
        registry={REGISTRY_BY_CATEGORY}
        activeDocType={activeDocType}
        onSelect={(id) => {
          setActiveDocType(id);
          setScreen("upload");
          setReviewSession(null);
        }}
      />

      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            <span className="wordmark">Disclosure-IQ</span>

          </div>
          <div className="top-bar-right">
            <span className="top-bar-tag">Canadian Capital Markets · {docType.regulatory_reference}</span>
          </div>
        </header>

        <div className="screen-area">
          {screen === "upload" && (
            <UploadScreen
              docType={docType}
              onUpload={handleUpload}
              isProcessing={isProcessing}
              processingStep={processingStep}
            />
          )}
          {screen === "reviewing" && reviewSession && (
            <ReviewDashboard
              session={reviewSession}
              onAction={handleReviewerAction}
              onSignOff={handleSignOff}
              onNewReview={handleNewReview}
            />
          )}
          {screen === "signoff" && reviewSession && (
            <SignOffSummary
              session={reviewSession}
              onNewReview={handleNewReview}
            />
          )}
        </div>
      </main>
    </div>
  );
}
