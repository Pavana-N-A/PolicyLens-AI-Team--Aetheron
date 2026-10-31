import React, { useState } from "react";
import { 
  Settings, Sparkles, Shield, Eye, CheckCircle2, 
  AlertTriangle, HardDrive, Cpu, RefreshCw
} from "lucide-react";
import { api } from "../api";

interface SettingsViewProps {
  user: any;
  aiStatus: any;
  ocrStatus: any;
  onRefresh: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  user,
  aiStatus,
  ocrStatus,
  onRefresh
}) => {
  const [consent, setConsent] = useState(user?.gemini_consent ?? true);
  const [isUpdating, setIsUpdating] = useState(false);

  const toggleConsent = async (val: boolean) => {
    setIsUpdating(true);
    try {
      await api.updateConsent(val);
      setConsent(val);
      onRefresh();
    } catch (err: any) {
      alert("Failed to update consent");
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "880px" }}>
      <div>
        <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "#ffffff", marginBottom: "6px" }}>
          System Architecture, AI & Privacy Settings
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          Review local-first runtime status, Google Gemini API connection, OCR pipelines, and privacy consent controls.
        </p>
      </div>

      {/* AI Connection Card */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Sparkles size={22} color="var(--primary)" />
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
              Google Gemini AI Synthesis
            </h3>
          </div>
          <span className={aiStatus?.status === "configured" ? "badge badge-found" : "badge badge-review"}>
            {aiStatus?.status === "configured" ? "API Key Configured" : "Not Configured (Local Rules Active)"}
          </span>
        </div>

        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.6, marginBottom: "16px" }}>
          PolicyLens uses the official <code>google-genai</code> Python SDK on the FastAPI backend. The API key is stored exclusively inside <code>prototype/backend/.env</code> and is never delivered to the client browser.
        </div>

        <div style={{
          backgroundColor: "#080d1a",
          padding: "14px 18px",
          borderRadius: "8px",
          border: "1px solid var(--border-subtle)",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          fontSize: "0.82rem"
        }}>
          <div><strong>Configured Model:</strong> <span style={{ color: "var(--teal)" }}>{aiStatus?.model || "gemini-2.5-flash"}</span></div>
          <div><strong>Backend Endpoint:</strong> <code>POST /api/chat</code> (Server-to-Server API)</div>
          <div><strong>Prompt Grounding:</strong> SQLite FTS5 retrieves matching page chunks before model invocation.</div>
        </div>

        {/* Free-tier Privacy Notice & Consent Toggle */}
        <div style={{ marginTop: "20px", borderTop: "1px solid var(--border-subtle)", paddingTop: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
            <div>
              <div style={{ fontWeight: 600, color: "#ffffff", fontSize: "0.9rem", marginBottom: "4px" }}>
                Send Extracted Excerpts to Google Gemini
              </div>
              <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", lineHeight: 1.5, maxWidth: "580px" }}>
                Under Google AI Studio free tier terms, submitted text may be processed to improve products. Do NOT submit real customer names, phone numbers, or confidential health records. When toggled OFF, PolicyLens uses its local deterministic analyzer.
              </div>
            </div>

            <button
              onClick={() => toggleConsent(!consent)}
              disabled={isUpdating}
              className={consent ? "btn btn-primary" : "btn btn-secondary"}
              style={{ fontSize: "0.8rem", padding: "8px 16px", minWidth: "130px" }}
            >
              {consent ? "Consent Granted" : "Consent Disabled"}
            </button>
          </div>
        </div>
      </div>

      {/* OCR Engine Card */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Cpu size={22} color="var(--teal)" />
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
              Local OCR Extraction Pipeline
            </h3>
          </div>
          <span className="badge badge-found">
            Active: {ocrStatus?.active_engine || "PyMuPDF Direct"}
          </span>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.6, marginBottom: "16px" }}>
          PolicyLens uses a hybrid pipeline: standard digital PDFs are extracted directly via PyMuPDF page-by-page. Pages with low or unreadable text are routed to local OCR behind the swappable <code>ocr_service.py</code> interface.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", fontSize: "0.8rem" }}>
          <div style={{ backgroundColor: "#080d1a", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--text-dim)", marginBottom: "4px" }}>PyMuPDF Digital</div>
            <div style={{ fontWeight: 600, color: "var(--teal)" }}>Connected (Default)</div>
          </div>

          <div style={{ backgroundColor: "#080d1a", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--text-dim)", marginBottom: "4px" }}>Tesseract OCR</div>
            <div style={{ fontWeight: 600, color: ocrStatus?.tesseract ? "var(--teal)" : "var(--text-dim)" }}>
              {ocrStatus?.tesseract ? "Detected" : "Optional Fallback"}
            </div>
          </div>

          <div style={{ backgroundColor: "#080d1a", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--text-dim)", marginBottom: "4px" }}>PaddleOCR 3.x</div>
            <div style={{ fontWeight: 600, color: ocrStatus?.paddleocr ? "var(--teal)" : "var(--text-dim)" }}>
              {ocrStatus?.paddleocr ? "Detected" : "Swappable Interface"}
            </div>
          </div>
        </div>
      </div>

      {/* Local Storage Card */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
          <HardDrive size={22} color="#38bdf8" />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#ffffff" }}>
            Local Storage & Database Architecture
          </h3>
        </div>

        <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.6, marginBottom: "14px" }}>
          All data remains strictly on your Windows laptop. No paid cloud databases (Firebase, Supabase, Pinecone, or S3) are used:
        </div>

        <ul style={{ paddingLeft: "20px", fontSize: "0.82rem", color: "#e2e8f0", lineHeight: 1.7 }}>
          <li><strong>SQLite Database:</strong> <code>prototype/backend/data/db/policylens.db</code></li>
          <li><strong>Original PDFs:</strong> <code>prototype/backend/data/uploads/&lt;user_id&gt;/</code></li>
          <li><strong>Hospital List CSVs:</strong> <code>prototype/backend/data/hospital_lists/</code></li>
          <li><strong>Full-Text Index:</strong> SQLite FTS5 table <code>policy_fts</code></li>
        </ul>
      </div>
    </div>
  );
};
