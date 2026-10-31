import React, { useState, useRef } from "react";
import { 
  FileText, UploadCloud, Trash2, Eye, RefreshCw, 
  CheckCircle2, AlertTriangle, Clock, ShieldCheck, Database
} from "lucide-react";
import { api } from "../api";
import { PolicyDetailModal } from "./PolicyDetailModal";

interface PoliciesViewProps {
  policies: any[];
  onUpload: (file: File) => void;
  onRefresh: () => void;
  onSeedDemo: () => void;
  isUploading: boolean;
}

export const PoliciesView: React.FC<PoliciesViewProps> = ({
  policies,
  onUpload,
  onRefresh,
  onSeedDemo,
  isUploading
}) => {
  const [selectedPolicy, setSelectedPolicy] = useState<any | null>(null);
  const [searchFilter, setSearchFilter] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleOpenDetail = async (p: any) => {
    try {
      const full = await api.getPolicy(p.id);
      setSelectedPolicy(full);
    } catch (err) {
      alert("Error loading policy details");
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete "${name}"? This removes the PDF and all extracted clauses.`)) {
      try {
        await api.deletePolicy(id);
        onRefresh();
      } catch (err: any) {
        alert("Delete failed: " + err.message);
      }
    }
  };

  const handleReanalyze = async (id: string) => {
    try {
      await api.getPolicies(); // trigger or call reanalyze
      onRefresh();
    } catch (err: any) {
      alert("Reanalysis failed");
    }
  };

  const filtered = policies.filter(p => 
    p.product_name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    p.insurer_name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    p.distributor_name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* View Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "#ffffff", marginBottom: "6px" }}>
            My Policy Documents
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Uploaded contract PDFs processed with PyMuPDF digital extraction, local OCR fallback, and structured clause indexing.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="file"
            accept=".pdf"
            ref={fileInputRef}
            onChange={(e) => e.target.files && onUpload(e.target.files[0])}
            style={{ display: "none" }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="btn btn-primary"
            style={{ fontSize: "0.85rem" }}
          >
            <UploadCloud size={16} />
            <span>{isUploading ? "Processing PDF..." : "Upload New PDF"}</span>
          </button>

          <button
            onClick={onSeedDemo}
            className="btn btn-secondary"
            style={{ fontSize: "0.85rem" }}
          >
            <Database size={15} />
            <span>Load Demo Policies</span>
          </button>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="glass-panel" style={{ padding: "12px 18px", display: "flex", gap: "12px", alignItems: "center" }}>
        <input
          type="text"
          placeholder="Filter by policy name, underwriter (e.g. Care, Star Health), or distribution channel (e.g. Bank)..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            color: "#ffffff",
            fontSize: "0.9rem",
            outline: "none"
          }}
        />
        <span style={{ fontSize: "0.78rem", color: "var(--text-dim)" }}>
          Showing {filtered.length} of {policies.length}
        </span>
      </div>

      {/* Policies List */}
      {filtered.length === 0 ? (
        <div className="glass-panel" style={{ padding: "50px 20px", textAlign: "center" }}>
          <FileText size={40} color="var(--text-dim)" style={{ marginBottom: "14px" }} />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#ffffff", marginBottom: "8px" }}>
            No matching policy documents
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: "420px", margin: "0 auto 16px" }}>
            Upload a health insurance policy PDF to extract clauses, or load synthetic demo policies.
          </p>
          <button onClick={onSeedDemo} className="btn btn-primary" style={{ fontSize: "0.85rem" }}>
            Load Demo Policies
          </button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {filtered.map((pol) => (
            <div 
              key={pol.id}
              className="glass-panel card-interactive"
              style={{
                padding: "20px 24px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "18px" }}>
                <div style={{
                  background: "rgba(14, 165, 233, 0.15)",
                  padding: "14px",
                  borderRadius: "10px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <FileText size={24} color="var(--primary)" />
                </div>

                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                    <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff" }}>
                      {pol.product_name}
                    </div>
                    {pol.is_demo && (
                      <span className="badge badge-demo" style={{ fontSize: "0.68rem" }}>
                        Synthetic Demo
                      </span>
                    )}
                    <span className="badge badge-found" style={{ fontSize: "0.68rem" }}>
                      {pol.extraction_status}
                    </span>
                  </div>

                  <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", display: "flex", gap: "16px", flexWrap: "wrap" }}>
                    <span>Risk Carrier: <strong style={{ color: "#38bdf8" }}>{pol.insurer_name}</strong></span>
                    <span>Channel: <strong style={{ color: "#e2e8f0" }}>{pol.distributor_name}</strong></span>
                    <span>Pages: <strong>{pol.page_count}</strong></span>
                    <span>Extraction: <strong>{pol.ocr_used ? "Hybrid OCR" : "Digital Text"}</strong></span>
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <button
                  onClick={() => handleOpenDetail(pol)}
                  className="btn btn-primary"
                  style={{ fontSize: "0.82rem", padding: "8px 14px" }}
                >
                  <Eye size={15} />
                  <span>Inspect Clauses</span>
                </button>

                <button
                  onClick={() => handleDelete(pol.id, pol.product_name)}
                  className="btn btn-danger"
                  style={{ padding: "8px 12px" }}
                  title="Delete Policy"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {selectedPolicy && (
        <PolicyDetailModal
          policy={selectedPolicy}
          onClose={() => setSelectedPolicy(null)}
          onRefresh={async () => {
            const updated = await api.getPolicy(selectedPolicy.id);
            setSelectedPolicy(updated);
            onRefresh();
          }}
        />
      )}
    </div>
  );
};
