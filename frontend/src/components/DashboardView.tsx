import React, { useRef } from "react";
import { 
  UploadCloud, FileText, GitCompare, Sparkles, MapPin, 
  HelpCircle, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, Database
} from "lucide-react";

interface DashboardViewProps {
  policies: any[];
  onUpload: (file: File) => void;
  onSeedDemo: () => void;
  setCurrentTab: (tab: string) => void;
  isUploading: boolean;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  policies,
  onUpload,
  onSeedDemo,
  setCurrentTab,
  isUploading
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Top Welcome Hero */}
      <div className="glass-panel" style={{
        padding: "28px 32px",
        background: "linear-gradient(135deg, rgba(14, 165, 233, 0.12) 0%, rgba(19, 29, 53, 0.8) 100%)",
        border: "1px solid rgba(14, 165, 233, 0.2)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <div style={{ maxWidth: "620px" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", color: "var(--teal)", fontSize: "0.8rem", fontWeight: 700, marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            <ShieldCheck size={16} />
            <span>Local-First InsurTech Decision Navigator</span>
          </div>
          <h1 style={{ fontSize: "1.85rem", fontWeight: 700, color: "#ffffff", marginBottom: "10px" }}>
            Understand & Compare Dense Health Insurance Policies
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", lineHeight: 1.6 }}>
            PolicyLens extracts clauses, separates underwriters from bank/hospital distributors,
            evaluates post-purchase disease timelines, and clarifies inter-state cashless hospital networks without cloud storage of your PDFs.
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px", minWidth: "200px" }}>
          <input
            type="file"
            accept=".pdf"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="btn btn-primary"
            style={{ padding: "12px 20px", fontSize: "0.95rem" }}
          >
            <UploadCloud size={18} />
            <span>{isUploading ? "Extracting & Analyzing..." : "Upload Policy PDF"}</span>
          </button>
          
          <button
            onClick={onSeedDemo}
            className="btn btn-secondary"
            style={{ padding: "10px 16px", fontSize: "0.85rem" }}
            title="Load 2 synthetic demo policies for instant evaluation"
          >
            <Database size={15} />
            <span>Load Demo Policies</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px" }}>
        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ color: "var(--text-dim)", fontSize: "0.8rem", fontWeight: 600, textTransform: "uppercase", marginBottom: "6px" }}>
            Uploaded Policies
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#ffffff" }}>
            {policies.length}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
            Stored locally on your laptop
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ color: "var(--text-dim)", fontSize: "0.8rem", fontWeight: 600, textTransform: "uppercase", marginBottom: "6px" }}>
            Analyzed Clauses
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--teal)" }}>
            {policies.reduce((acc, p) => acc + (p.clauses ? p.clauses.length : 6), 0)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
            Indexed with SQLite FTS5
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ color: "var(--text-dim)", fontSize: "0.8rem", fontWeight: 600, textTransform: "uppercase", marginBottom: "6px" }}>
            Distributor Separation
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "var(--primary)" }}>
            Active
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
            Underwriters vs Bank Channels
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ color: "var(--text-dim)", fontSize: "0.8rem", fontWeight: 600, textTransform: "uppercase", marginBottom: "6px" }}>
            Hospital Dataset
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#38bdf8" }}>
            Verified Local
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>
            Synthetic sample TPA list
          </div>
        </div>
      </div>

      {/* Feature Action Grid */}
      <div>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#ffffff", marginBottom: "16px" }}>
          Core Evaluation Capabilities
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "18px" }}>
          <div 
            onClick={() => setCurrentTab("compare")}
            className="glass-panel card-interactive" 
            style={{ padding: "22px", cursor: "pointer", display: "flex", flexDirection: "column", justifyContent: "space-between" }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--primary)", marginBottom: "12px" }}>
                <GitCompare size={22} />
                <h3 style={{ fontSize: "1.05rem", fontWeight: 600, color: "#ffffff" }}>Policy Comparison</h3>
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", lineHeight: 1.5, marginBottom: "16px" }}>
                Side-by-side comparison isolating room rent caps, PED waiting periods, co-pay clauses, and trade-offs.
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--primary)", fontSize: "0.8rem", fontWeight: 600 }}>
              <span>Compare Policies</span>
              <ArrowRight size={14} />
            </div>
          </div>

          <div 
            onClick={() => setCurrentTab("scenarios")}
            className="glass-panel card-interactive" 
            style={{ padding: "22px", cursor: "pointer", display: "flex", flexDirection: "column", justifyContent: "space-between" }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "var(--teal)", marginBottom: "12px" }}>
                <HelpCircle size={22} />
                <h3 style={{ fontSize: "1.05rem", fontWeight: 600, color: "#ffffff" }}>Claim Scenarios</h3>
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", lineHeight: 1.5, marginBottom: "16px" }}>
                Evaluate real scenarios: illness diagnosed 2 years post-purchase, or Karnataka purchase with Maharashtra hospitalization.
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--teal)", fontSize: "0.8rem", fontWeight: 600 }}>
              <span>Run Scenario Checker</span>
              <ArrowRight size={14} />
            </div>
          </div>

          <div 
            onClick={() => setCurrentTab("chat")}
            className="glass-panel card-interactive" 
            style={{ padding: "22px", cursor: "pointer", display: "flex", flexDirection: "column", justifyContent: "space-between" }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#a855f7", marginBottom: "12px" }}>
                <Sparkles size={22} />
                <h3 style={{ fontSize: "1.05rem", fontWeight: 600, color: "#ffffff" }}>Ask PolicyLens</h3>
              </div>
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", lineHeight: 1.5, marginBottom: "16px" }}>
                Evidence-grounded assistant that answers strictly using retrieved page citations [Policy, page X] with 4 structured sections.
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#a855f7", fontSize: "0.8rem", fontWeight: 600 }}>
              <span>Launch Assistant</span>
              <ArrowRight size={14} />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity / Policy List Preview */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#ffffff" }}>
            Current Documents
          </h2>
          {policies.length > 0 && (
            <button 
              onClick={() => setCurrentTab("policies")}
              style={{ background: "none", border: "none", color: "var(--primary)", fontSize: "0.85rem", fontWeight: 600, cursor: "pointer" }}
            >
              View All ({policies.length}) →
            </button>
          )}
        </div>

        {policies.length === 0 ? (
          <div className="glass-panel" style={{ padding: "40px 20px", textAlign: "center" }}>
            <FileText size={36} color="var(--text-dim)" style={{ marginBottom: "12px" }} />
            <div style={{ fontSize: "1rem", fontWeight: 600, color: "#ffffff", marginBottom: "6px" }}>
              No policy documents loaded yet
            </div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: "460px", margin: "0 auto 18px" }}>
              Click <strong>"Load Demo Policies"</strong> above to load two synthetic policies with differing terms, or upload your own PDF document.
            </p>
            <button onClick={onSeedDemo} className="btn btn-primary" style={{ fontSize: "0.85rem" }}>
              Load Demo Policies Now
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {policies.slice(0, 3).map((pol) => (
              <div 
                key={pol.id}
                className="glass-panel"
                style={{ padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                  <div style={{ background: "rgba(14, 165, 233, 0.12)", padding: "10px", borderRadius: "8px" }}>
                    <FileText size={20} color="var(--primary)" />
                  </div>
                  <div>
                    <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#ffffff" }}>
                      {pol.product_name}
                    </div>
                    <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                      Risk Underwriter: <strong style={{ color: "#e2e8f0" }}>{pol.insurer_name}</strong> | Channel: <em>{pol.distributor_name}</em>
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <span className="badge badge-found">
                    <CheckCircle2 size={12} />
                    {pol.extraction_status}
                  </span>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
                    {pol.page_count} Pages
                  </div>
                  <button
                    onClick={() => setCurrentTab("policies")}
                    className="btn btn-secondary"
                    style={{ fontSize: "0.8rem", padding: "6px 12px" }}
                  >
                    Inspect Clauses
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
