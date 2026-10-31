import React, { useState } from "react";
import { 
  X, CheckCircle2, AlertCircle, FileText, Edit2, 
  Save, Shield, MapPin, Clock, DollarSign, ChevronRight
} from "lucide-react";
import { api } from "../api";

interface PolicyDetailModalProps {
  policy: any;
  onClose: () => void;
  onRefresh: () => void;
}

export const PolicyDetailModal: React.FC<PolicyDetailModalProps> = ({
  policy,
  onClose,
  onRefresh
}) => {
  const [activeTab, setActiveTab] = useState<"clauses" | "fields" | "pages">("clauses");
  const [editingClauseId, setEditingClauseId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ heading: "", verbatim_text: "", plain_summary: "" });
  const [isSaving, setIsSaving] = useState(false);

  const startEdit = (c: any) => {
    setEditingClauseId(c.id);
    setEditForm({
      heading: c.heading,
      verbatim_text: c.verbatim_text,
      plain_summary: c.plain_summary
    });
  };

  const handleSave = async (clauseId: string) => {
    setIsSaving(true);
    try {
      await api.updateClause(policy.id, clauseId, editForm);
      setEditingClauseId(null);
      onRefresh();
    } catch (err: any) {
      alert("Failed to update clause: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Found in policy":
        return <span className="badge badge-found"><CheckCircle2 size={11} /> Found</span>;
      case "Not found in uploaded document":
        return <span className="badge badge-not-found">Not Found in PDF</span>;
      case "Ambiguous – review needed":
      case "Review needed":
        return <span className="badge badge-review"><AlertCircle size={11} /> Review Needed</span>;
      default:
        return <span className="badge badge-found">{status}</span>;
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(10, 15, 29, 0.85)",
      backdropFilter: "blur(8px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
      padding: "20px"
    }}>
      <div className="glass-panel" style={{
        width: "900px",
        maxWidth: "95vw",
        maxHeight: "90vh",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#0e162a",
        border: "1px solid rgba(14, 165, 233, 0.25)",
        overflow: "hidden"
      }}>
        {/* Header */}
        <div style={{
          padding: "20px 24px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          backgroundColor: "rgba(14, 165, 233, 0.05)"
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#ffffff" }}>
                {policy.product_name}
              </h2>
              {policy.is_demo && <span className="badge badge-demo">Synthetic Demo</span>}
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", display: "flex", gap: "16px", flexWrap: "wrap" }}>
              <span>Risk Underwriter: <strong style={{ color: "#38bdf8" }}>{policy.insurer_name}</strong></span>
              <span>Distribution Channel: <strong style={{ color: "#e2e8f0" }}>{policy.distributor_name}</strong></span>
              <span>Pages: <strong>{policy.page_count}</strong></span>
              <span>OCR: <strong>{policy.ocr_used ? "Used (Scanned)" : "Digital Direct"}</strong></span>
            </div>
          </div>
          <button 
            onClick={onClose} 
            style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", padding: "4px" }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div style={{
          display: "flex",
          gap: "8px",
          padding: "12px 24px",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "#0b1224"
        }}>
          <button
            onClick={() => setActiveTab("clauses")}
            className="btn"
            style={{
              padding: "6px 14px",
              fontSize: "0.82rem",
              backgroundColor: activeTab === "clauses" ? "rgba(14, 165, 233, 0.2)" : "transparent",
              color: activeTab === "clauses" ? "#38bdf8" : "var(--text-muted)",
              border: activeTab === "clauses" ? "1px solid rgba(14, 165, 233, 0.4)" : "1px solid transparent"
            }}
          >
            Extracted Policy Clauses ({policy.clauses?.length || 0})
          </button>

          <button
            onClick={() => setActiveTab("fields")}
            className="btn"
            style={{
              padding: "6px 14px",
              fontSize: "0.82rem",
              backgroundColor: activeTab === "fields" ? "rgba(14, 165, 233, 0.2)" : "transparent",
              color: activeTab === "fields" ? "#38bdf8" : "var(--text-muted)",
              border: activeTab === "fields" ? "1px solid rgba(14, 165, 233, 0.4)" : "1px solid transparent"
            }}
          >
            Normalized Comparison Fields ({policy.fields?.length || 0})
          </button>

          <button
            onClick={() => setActiveTab("pages")}
            className="btn"
            style={{
              padding: "6px 14px",
              fontSize: "0.82rem",
              backgroundColor: activeTab === "pages" ? "rgba(14, 165, 233, 0.2)" : "transparent",
              color: activeTab === "pages" ? "#38bdf8" : "var(--text-muted)",
              border: activeTab === "pages" ? "1px solid rgba(14, 165, 233, 0.4)" : "1px solid transparent"
            }}
          >
            Page Inspection & OCR Confidence
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {activeTab === "clauses" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {policy.clauses && policy.clauses.map((c: any) => {
                const isEditing = editingClauseId === c.id;
                return (
                  <div 
                    key={c.id} 
                    className="glass-panel" 
                    style={{ padding: "16px", border: "1px solid rgba(255, 255, 255, 0.08)" }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--teal)", textTransform: "uppercase" }}>
                          {c.category}
                        </span>
                        <div style={{ fontWeight: 600, fontSize: "0.95rem", color: "#ffffff" }}>
                          {c.heading}
                        </div>
                      </div>

                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                          Page {c.page_number}
                        </span>
                        {getStatusBadge(c.extraction_status)}
                        {!isEditing && (
                          <button
                            onClick={() => startEdit(c)}
                            style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", display: "flex", alignItems: "center", gap: "4px", fontSize: "0.75rem" }}
                          >
                            <Edit2 size={13} />
                            <span>Edit</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {isEditing ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "10px" }}>
                        <div>
                          <label style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Heading:</label>
                          <input
                            type="text"
                            value={editForm.heading}
                            onChange={(e) => setEditForm({ ...editForm, heading: e.target.value })}
                            style={{ width: "100%", padding: "6px 10px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff" }}
                          />
                        </div>
                        <div>
                          <label style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Verbatim Clause Text:</label>
                          <textarea
                            rows={3}
                            value={editForm.verbatim_text}
                            onChange={(e) => setEditForm({ ...editForm, verbatim_text: e.target.value })}
                            style={{ width: "100%", padding: "6px 10px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
                          />
                        </div>
                        <div>
                          <label style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>Plain Explanation:</label>
                          <textarea
                            rows={2}
                            value={editForm.plain_summary}
                            onChange={(e) => setEditForm({ ...editForm, plain_summary: e.target.value })}
                            style={{ width: "100%", padding: "6px 10px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
                          />
                        </div>
                        <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
                          <button onClick={() => setEditingClauseId(null)} className="btn btn-secondary" style={{ fontSize: "0.78rem" }}>
                            Cancel
                          </button>
                          <button onClick={() => handleSave(c.id)} disabled={isSaving} className="btn btn-primary" style={{ fontSize: "0.78rem" }}>
                            <Save size={14} />
                            <span>Save Changes</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div style={{ fontSize: "0.84rem", color: "var(--text-muted)", marginBottom: "8px", lineHeight: 1.5 }}>
                          <strong style={{ color: "#e2e8f0" }}>Plain Explanation: </strong>
                          {c.plain_summary}
                        </div>
                        <div style={{
                          fontSize: "0.78rem",
                          color: "var(--text-dim)",
                          backgroundColor: "#070c18",
                          padding: "8px 12px",
                          borderRadius: "6px",
                          borderLeft: "3px solid var(--primary)",
                          fontFamily: "monospace"
                        }}>
                          "{c.verbatim_text}"
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === "fields" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {policy.fields && policy.fields.map((f: any) => (
                <div 
                  key={f.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 16px",
                    backgroundColor: "rgba(255, 255, 255, 0.02)",
                    borderRadius: "8px",
                    border: "1px solid var(--border-subtle)"
                  }}
                >
                  <div style={{ maxWidth: "450px" }}>
                    <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "#ffffff", marginBottom: "2px" }}>
                      {f.field_label}
                    </div>
                    <div style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>
                      {f.evidence_snippet}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "12px", textAlign: "right" }}>
                    <div>
                      <div style={{ fontSize: "0.88rem", fontWeight: 600, color: "#38bdf8" }}>
                        {f.normalized_value}
                      </div>
                      {f.source_page && (
                        <div style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>
                          Page {f.source_page}
                        </div>
                      )}
                    </div>
                    {getStatusBadge(f.status)}
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "pages" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {policy.pages && policy.pages.map((p: any) => (
                <div 
                  key={p.id}
                  className="glass-panel"
                  style={{ padding: "16px" }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#ffffff" }}>
                      Page {p.page_number}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span className="badge badge-found" style={{ fontSize: "0.7rem" }}>
                        Method: {p.extraction_method}
                      </span>
                      <span style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>
                        Confidence: {Math.round((p.ocr_confidence || 1) * 100)}%
                      </span>
                      {p.needs_review && (
                        <span className="badge badge-review" style={{ fontSize: "0.7rem" }}>
                          Needs Manual Review
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                    maxHeight: "150px",
                    overflowY: "auto",
                    backgroundColor: "#070c18",
                    padding: "10px",
                    borderRadius: "6px",
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.4
                  }}>
                    {p.extracted_text}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
