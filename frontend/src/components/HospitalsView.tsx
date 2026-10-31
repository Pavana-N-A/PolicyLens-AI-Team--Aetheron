import React, { useState, useEffect } from "react";
import { 
  MapPin, Search, UploadCloud, AlertCircle, CheckCircle2, 
  Building2, ShieldAlert, FileText, Info
} from "lucide-react";
import { api } from "../api";

export const HospitalsView: React.FC = () => {
  const [searchParams, setSearchParams] = useState({ city: "", name: "", state: "" });
  const [results, setResults] = useState<any[]>([]);
  const [meta, setMeta] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const performSearch = async () => {
    setIsLoading(true);
    try {
      const data = await api.searchHospitals(searchParams);
      setResults(data.results || []);
      setMeta({
        total: data.total_found,
        provider: data.data_source_provider,
        verified: data.last_verified_date,
        isSynthetic: data.is_synthetic
      });
    } catch (err: any) {
      alert("Search failed: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    performSearch();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div>
        <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "#ffffff", marginBottom: "6px" }}>
          Hospital Network & Cashless Access Navigator
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          Query locally imported TPA/insurer hospital records. Understand network pre-auth cashless vs non-network reimbursement pathways.
        </p>
      </div>

      {/* Mandatory Regulatory & Live Data Disclaimer Banner */}
      <div style={{
        padding: "16px 20px",
        backgroundColor: "rgba(245, 158, 11, 0.08)",
        borderRadius: "10px",
        border: "1px solid rgba(245, 158, 11, 0.25)",
        display: "flex",
        alignItems: "flex-start",
        gap: "12px",
        fontSize: "0.85rem",
        color: "#fbbf24",
        lineHeight: 1.5
      }}>
        <ShieldAlert size={22} style={{ flexShrink: 0, marginTop: "2px" }} />
        <div>
          <strong>SYNTHETIC DEMO DATA NOTICE:</strong> Hospital empanelment records displayed here are from a local sample feed. A static policy PDF alone cannot guarantee the current live network status of an individual hospital. Always confirm active empanelment directly with the hospital's TPA desk prior to admission.
        </div>
      </div>

      {/* Search Bar */}
      <div className="glass-panel" style={{ padding: "20px 24px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: "12px", alignItems: "flex-end" }}>
          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
              Hospital Name:
            </label>
            <input
              type="text"
              placeholder="e.g. Apollo, Lilavati, Fortis..."
              value={searchParams.name}
              onChange={(e) => setSearchParams({ ...searchParams, name: e.target.value })}
              style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
              City:
            </label>
            <input
              type="text"
              placeholder="e.g. Bengaluru, Mumbai, Pune..."
              value={searchParams.city}
              onChange={(e) => setSearchParams({ ...searchParams, city: e.target.value })}
              style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
            />
          </div>

          <div>
            <label style={{ fontSize: "0.78rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
              State:
            </label>
            <input
              type="text"
              placeholder="e.g. Karnataka, Maharashtra..."
              value={searchParams.state}
              onChange={(e) => setSearchParams({ ...searchParams, state: e.target.value })}
              style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
            />
          </div>

          <button
            onClick={performSearch}
            disabled={isLoading}
            className="btn btn-primary"
            style={{ padding: "9px 20px" }}
          >
            <Search size={16} />
            <span>{isLoading ? "Searching..." : "Search"}</span>
          </button>
        </div>

        {meta && (
          <div style={{ display: "flex", gap: "16px", marginTop: "14px", fontSize: "0.75rem", color: "var(--text-dim)" }}>
            <span>Source: <strong style={{ color: "#ffffff" }}>{meta.provider}</strong></span>
            <span>Dataset Verification: <strong style={{ color: "#38bdf8" }}>{meta.verified}</strong></span>
            <span>Found: <strong style={{ color: "#ffffff" }}>{meta.total}</strong></span>
          </div>
        )}
      </div>

      {/* Hospital Results */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {results.map((h) => {
          const isCashless = h.network_type.toLowerCase().includes("cashless");
          return (
            <div
              key={h.id}
              className="glass-panel"
              style={{
                padding: "18px 22px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{
                  background: isCashless ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                  padding: "12px",
                  borderRadius: "8px"
                }}>
                  <Building2 size={22} color={isCashless ? "var(--teal)" : "#fbbf24"} />
                </div>

                <div>
                  <div style={{ fontSize: "1rem", fontWeight: 700, color: "#ffffff", marginBottom: "2px" }}>
                    {h.hospital_name}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "flex", gap: "12px" }}>
                    <span>{h.city}, {h.state} ({h.pincode})</span>
                    <span>Category: <strong>{h.tier_category}</strong></span>
                  </div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: "4px" }}>
                    {h.notes}
                  </div>
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <span className={isCashless ? "badge badge-found" : "badge badge-review"}>
                  {h.network_type}
                </span>
                <div style={{ fontSize: "0.7rem", color: "var(--text-dim)", marginTop: "4px" }}>
                  Source: {h.provider_name}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
