import React, { useState } from "react";
import { 
  GitCompare, CheckCircle2, AlertCircle, Download, 
  HelpCircle, Shield, ArrowRight, SlidersHorizontal
} from "lucide-react";
import { api } from "../api";

interface ComparisonViewProps {
  policies: any[];
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ policies }) => {
  const [selectedIds, setSelectedIds] = useState<string[]>(
    policies.length >= 2 ? [policies[0].id, policies[1].id] : []
  );
  const [priorityFocus, setPriorityFocus] = useState<string>("balanced");
  const [comparisonResult, setComparisonResult] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const togglePolicy = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length > 2) {
        setSelectedIds(selectedIds.filter(x => x !== id));
      } else {
        alert("Select at least 2 policies for comparison.");
      }
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const runComparison = async () => {
    if (selectedIds.length < 2) {
      alert("Please select at least 2 policies to compare.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.createComparison(selectedIds, priorityFocus);
      setComparisonResult(res);
    } catch (err: any) {
      alert("Comparison failed: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const exportCSV = () => {
    if (!comparisonResult) return;
    const cols = comparisonResult.columns;
    const fieldKeys = Object.keys(cols[0].fields);

    let csvContent = "data:text/csv;charset=utf-8,";
    // Header row
    const header = ["Clause / Field", ...cols.map((c: any) => `"${c.product_name} (${c.insurer_name})"` )].join(",");
    csvContent += header + "\r\n";

    // Data rows
    for (const key of fieldKeys) {
      const label = cols[0].fields[key].label;
      const row = [
        `"${label}"`,
        ...cols.map((c: any) => `"${c.fields[key].value.replace(/"/g, '""')}"`)
      ].join(",");
      csvContent += row + "\r\n";
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `PolicyLens_Comparison_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const fieldKeysList = comparisonResult ? Object.keys(comparisonResult.columns[0].fields) : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "#ffffff", marginBottom: "6px" }}>
          Multi-Policy Side-by-Side Comparison
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          Normalize dense contract wording, distinguish risk underwriters from distributor channels, and inspect trade-offs.
        </p>
      </div>

      {/* Policy Selector Bar */}
      <div className="glass-panel" style={{ padding: "20px 24px" }}>
        <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#ffffff", marginBottom: "12px" }}>
          1. Select Policies to Compare (minimum 2):
        </div>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "20px" }}>
          {policies.map((p) => {
            const isSelected = selectedIds.includes(p.id);
            return (
              <button
                key={p.id}
                onClick={() => togglePolicy(p.id)}
                className="btn"
                style={{
                  padding: "10px 16px",
                  borderRadius: "8px",
                  backgroundColor: isSelected ? "rgba(14, 165, 233, 0.2)" : "rgba(255, 255, 255, 0.04)",
                  border: isSelected ? "1.5px solid var(--primary)" : "1px solid var(--border-subtle)",
                  color: isSelected ? "#ffffff" : "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  fontSize: "0.85rem"
                }}
              >
                <div style={{
                  width: "16px",
                  height: "16px",
                  borderRadius: "4px",
                  border: isSelected ? "none" : "1px solid var(--text-dim)",
                  backgroundColor: isSelected ? "var(--primary)" : "transparent",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  {isSelected && <CheckCircle2 size={13} color="#ffffff" />}
                </div>
                <div style={{ textAlign: "left" }}>
                  <div style={{ fontWeight: 600 }}>{p.product_name}</div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>
                    Carrier: {p.insurer_name}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Priority Focus */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "0.85rem", color: "var(--text-dim)", fontWeight: 500 }}>
              Evaluation Priority:
            </span>
            <select
              value={priorityFocus}
              onChange={(e) => setPriorityFocus(e.target.value)}
              style={{
                backgroundColor: "#0a0f1d",
                color: "#ffffff",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "8px 12px",
                fontSize: "0.85rem"
              }}
            >
              <option value="balanced">Balanced Evaluation</option>
              <option value="shorter_waiting_period">Shorter Waiting Periods (PED & specific)</option>
              <option value="lower_copay">Lowest Out-of-Pocket (No Co-pay / No Capping)</option>
              <option value="higher_coverage">Comprehensive In-Patient & Room Rent</option>
            </select>
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={runComparison}
              disabled={isLoading || selectedIds.length < 2}
              className="btn btn-primary"
              style={{ fontSize: "0.88rem", padding: "10px 20px" }}
            >
              <GitCompare size={16} />
              <span>{isLoading ? "Analyzing Trade-offs..." : "Compare Side-by-Side"}</span>
            </button>

            {comparisonResult && (
              <button
                onClick={exportCSV}
                className="btn btn-secondary"
                style={{ fontSize: "0.85rem" }}
              >
                <Download size={15} />
                <span>Export CSV</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Trade-off Insights Summary */}
      {comparisonResult && (
        <div className="glass-panel" style={{
          padding: "24px 28px",
          background: "linear-gradient(135deg, rgba(20, 184, 166, 0.08) 0%, rgba(19, 29, 53, 0.7) 100%)",
          border: "1px solid rgba(20, 184, 166, 0.25)"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--teal)", fontWeight: 700, fontSize: "0.85rem", textTransform: "uppercase", marginBottom: "12px" }}>
            <SlidersHorizontal size={18} />
            <span>Comparative Trade-off & Channel Analysis</span>
          </div>

          <div style={{
            color: "#e2e8f0",
            fontSize: "0.9rem",
            lineHeight: 1.7,
            whiteSpace: "pre-line"
          }}>
            {comparisonResult.tradeoff_summary}
          </div>
        </div>
      )}

      {/* Side by Side Comparison Table */}
      {comparisonResult ? (
        <div className="glass-panel" style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
            <thead>
              <tr style={{ backgroundColor: "#0b1224", borderBottom: "2px solid var(--border-subtle)" }}>
                <th style={{ padding: "16px 20px", textAlign: "left", width: "240px", color: "var(--text-muted)", fontWeight: 600 }}>
                  Policy Clause / Field
                </th>
                {comparisonResult.columns.map((col: any) => (
                  <th key={col.policy_id} style={{ padding: "16px 20px", textAlign: "left", color: "#ffffff", fontWeight: 700, borderLeft: "1px solid var(--border-subtle)" }}>
                    <div style={{ fontSize: "1rem", color: "#38bdf8" }}>{col.product_name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 500, marginTop: "2px" }}>
                      Risk Underwriter: <strong style={{ color: "#ffffff" }}>{col.insurer_name}</strong>
                    </div>
                    <div style={{ fontSize: "0.72rem", color: "var(--teal)", fontWeight: 500 }}>
                      Channel: {col.distributor_name}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fieldKeysList.map((fKey, idx) => {
                const label = comparisonResult.columns[0].fields[fKey].label;
                const isEven = idx % 2 === 0;

                return (
                  <tr 
                    key={fKey}
                    style={{
                      backgroundColor: isEven ? "rgba(255, 255, 255, 0.015)" : "transparent",
                      borderBottom: "1px solid rgba(255, 255, 255, 0.05)"
                    }}
                  >
                    <td style={{ padding: "14px 20px", fontWeight: 600, color: "#e2e8f0" }}>
                      {label}
                    </td>

                    {comparisonResult.columns.map((col: any) => {
                      const f = col.fields[fKey];
                      const isFound = f.status === "Found in policy";
                      return (
                        <td key={col.policy_id} style={{ padding: "14px 20px", borderLeft: "1px solid var(--border-subtle)", verticalAlign: "top" }}>
                          <div style={{ fontWeight: 600, color: isFound ? "#ffffff" : "var(--text-dim)", marginBottom: "4px" }}>
                            {f.value}
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                            {f.evidence}
                          </div>
                          {f.source_page && (
                            <span style={{ display: "inline-block", marginTop: "4px", fontSize: "0.68rem", color: "var(--primary)", fontWeight: 600 }}>
                              Page {f.source_page}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: "60px 20px", textAlign: "center" }}>
          <GitCompare size={42} color="var(--text-dim)" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "#ffffff", marginBottom: "8px" }}>
            Ready to Compare Policies
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: "440px", margin: "0 auto 20px" }}>
            Select at least two policies above and click <strong>"Compare Side-by-Side"</strong> to view a side-by-side breakdown of coverage, limits, and exclusions.
          </p>
          <button 
            onClick={runComparison}
            disabled={selectedIds.length < 2}
            className="btn btn-primary"
          >
            Run Comparison Now
          </button>
        </div>
      )}
    </div>
  );
};
