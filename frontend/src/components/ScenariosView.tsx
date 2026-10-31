import React, { useState } from "react";
import { 
  HelpCircle, Calendar, MapPin, AlertTriangle, CheckCircle2, 
  ArrowRight, ShieldAlert, FileText, ChevronRight, ListChecks
} from "lucide-react";
import { api } from "../api";

interface ScenariosViewProps {
  policies: any[];
}

export const ScenariosView: React.FC<ScenariosViewProps> = ({ policies }) => {
  const [activeScenario, setActiveScenario] = useState<"disease" | "geography">("disease");
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>(policies[0]?.id || "");
  
  // Disease Form state
  const [diseaseForm, setDiseaseForm] = useState({
    policy_start_date: "2023-01-01",
    first_diagnosis_date: "2025-06-01",
    disease_name: "Gall bladder stones & laparoscopic cholecystectomy",
    continuous_renewals: "yes",
    pre_existing_or_treated_prior: "no"
  });

  // Geo Form state
  const [geoForm, setGeoForm] = useState({
    policy_state: "Karnataka",
    treatment_state: "Maharashtra",
    hospital_name: "Lilavati Hospital Mumbai"
  });

  const [diseaseResult, setDiseaseResult] = useState<any | null>(null);
  const [geoResult, setGeoResult] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleDiseaseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPolicyId) {
      alert("Please select a policy.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.analyzeDisease({
        policy_id: selectedPolicyId,
        ...diseaseForm
      });
      setDiseaseResult(res);
    } catch (err: any) {
      alert("Analysis failed: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGeoSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPolicyId) {
      alert("Please select a policy.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await api.analyzeGeography({
        policy_id: selectedPolicyId,
        ...geoForm
      });
      setGeoResult(res);
    } catch (err: any) {
      alert("Analysis failed: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      <div>
        <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "#ffffff", marginBottom: "6px" }}>
          Guided Claim-Readiness & Legal Scenario Checker
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          Explore key real-world scenarios: post-purchase diagnoses, PED waiting periods, and interstate treatment validity vs cashless hospital networks.
        </p>
      </div>

      {/* Scenario Selector Tabs */}
      <div style={{ display: "flex", gap: "12px" }}>
        <button
          onClick={() => setActiveScenario("disease")}
          className="btn"
          style={{
            flex: 1,
            padding: "14px 20px",
            justifyContent: "flex-start",
            backgroundColor: activeScenario === "disease" ? "rgba(14, 165, 233, 0.15)" : "var(--bg-card)",
            border: activeScenario === "disease" ? "1.5px solid var(--primary)" : "1px solid var(--border-subtle)",
            color: activeScenario === "disease" ? "#ffffff" : "var(--text-muted)"
          }}
        >
          <Calendar size={20} color={activeScenario === "disease" ? "var(--primary)" : "var(--text-dim)"} />
          <div style={{ textAlign: "left" }}>
            <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>
              Scenario 1: Diagnosed 2-3 Years After Purchase
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
              Is it pre-existing? Which waiting periods and exclusions apply?
            </div>
          </div>
        </button>

        <button
          onClick={() => setActiveScenario("geography")}
          className="btn"
          style={{
            flex: 1,
            padding: "14px 20px",
            justifyContent: "flex-start",
            backgroundColor: activeScenario === "geography" ? "rgba(20, 184, 166, 0.15)" : "var(--bg-card)",
            border: activeScenario === "geography" ? "1.5px solid var(--teal)" : "1px solid var(--border-subtle)",
            color: activeScenario === "geography" ? "#ffffff" : "var(--text-muted)"
          }}
        >
          <MapPin size={20} color={activeScenario === "geography" ? "var(--teal)" : "var(--text-dim)"} />
          <div style={{ textAlign: "left" }}>
            <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>
              Scenario 2: Inter-State Treatment (Karnataka → Maharashtra)
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
              Territorial scope vs Cashless Network availability breakdown
            </div>
          </div>
        </button>
      </div>

      {/* Policy Picker */}
      <div className="glass-panel" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: "16px" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#ffffff" }}>
          Target Policy:
        </span>
        <select
          value={selectedPolicyId}
          onChange={(e) => setSelectedPolicyId(e.target.value)}
          style={{
            flex: 1,
            padding: "8px 12px",
            backgroundColor: "#0a0f1d",
            color: "#ffffff",
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px",
            fontSize: "0.88rem"
          }}
        >
          {policies.map(p => (
            <option key={p.id} value={p.id}>
              {p.product_name} ({p.insurer_name} – via {p.distributor_name})
            </option>
          ))}
        </select>
      </div>

      {/* Scenario 1: Disease Diagnosis Checker */}
      {activeScenario === "disease" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: "24px" }}>
          {/* Form */}
          <form onSubmit={handleDiseaseSubmit} className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
              Chronology & Disease Input
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                Condition / Treatment Name:
              </label>
              <input
                type="text"
                value={diseaseForm.disease_name}
                onChange={(e) => setDiseaseForm({ ...diseaseForm, disease_name: e.target.value })}
                placeholder="e.g. Gall bladder stones, Cataract, Knee replacement"
                style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                  Policy Start Date:
                </label>
                <input
                  type="date"
                  value={diseaseForm.policy_start_date}
                  onChange={(e) => setDiseaseForm({ ...diseaseForm, policy_start_date: e.target.value })}
                  style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                  First Diagnosis Date:
                </label>
                <input
                  type="date"
                  value={diseaseForm.first_diagnosis_date}
                  onChange={(e) => setDiseaseForm({ ...diseaseForm, first_diagnosis_date: e.target.value })}
                  style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                Has the policy been renewed continuously without break?
              </label>
              <select
                value={diseaseForm.continuous_renewals}
                onChange={(e) => setDiseaseForm({ ...diseaseForm, continuous_renewals: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              >
                <option value="yes">Yes – Continuous on-time renewals</option>
                <option value="no">No – There was a gap in premium payment</option>
                <option value="not_sure">Not sure / Renewal pending</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                Was this condition diagnosed or treated prior to purchase?
              </label>
              <select
                value={diseaseForm.pre_existing_or_treated_prior}
                onChange={(e) => setDiseaseForm({ ...diseaseForm, pre_existing_or_treated_prior: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              >
                <option value="no">No – Diagnosed for the first time post-purchase</option>
                <option value="yes">Yes – Had symptoms / prior medical consultation</option>
                <option value="not_sure">Not sure</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
              style={{ marginTop: "10px", padding: "10px" }}
            >
              {isLoading ? "Evaluating Policy Clauses..." : "Evaluate Scenario"}
            </button>
          </form>

          {/* Results Panel */}
          <div className="glass-panel" style={{ padding: "24px", overflowY: "auto", maxHeight: "650px" }}>
            {diseaseResult ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
                <div>
                  <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--teal)", textTransform: "uppercase", marginBottom: "4px" }}>
                    Pre-Existing Disease Assessment
                  </div>
                  <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", lineHeight: 1.4 }}>
                    {diseaseResult.is_ped_assessment}
                  </div>
                </div>

                <div style={{
                  padding: "12px 16px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(14, 165, 233, 0.08)",
                  borderLeft: "4px solid var(--primary)",
                  fontSize: "0.85rem",
                  color: "#e2e8f0",
                  lineHeight: 1.6
                }}>
                  {diseaseResult.waiting_period_analysis}
                </div>

                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.6, whiteSpace: "pre-line" }}>
                  {diseaseResult.plain_explanation}
                </div>

                {/* Missing Facts to Verify */}
                <div style={{ backgroundColor: "#0b1224", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#fbbf24", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <AlertTriangle size={15} />
                    <span>Important Facts You Must Verify:</span>
                  </div>
                  <ul style={{ paddingLeft: "20px", fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                    {diseaseResult.missing_facts_to_verify.map((item: string, idx: number) => (
                      <li key={idx} style={{ marginBottom: "4px" }}>{item}</li>
                    ))}
                  </ul>
                </div>

                {/* Suggested Questions */}
                <div style={{ backgroundColor: "#0b1224", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--teal)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <ListChecks size={15} />
                    <span>Exact Questions to Ask Insurer / TPA:</span>
                  </div>
                  <ul style={{ paddingLeft: "20px", fontSize: "0.8rem", color: "#e2e8f0", lineHeight: 1.5 }}>
                    {diseaseResult.suggested_questions.map((q: string, idx: number) => (
                      <li key={idx} style={{ marginBottom: "6px" }}>"{q}"</li>
                    ))}
                  </ul>
                </div>

                <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontStyle: "italic", borderTop: "1px solid var(--border-subtle)", paddingTop: "10px" }}>
                  {diseaseResult.disclaimer}
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "60px 20px" }}>
                <Calendar size={36} color="var(--text-dim)" style={{ marginBottom: "12px" }} />
                <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#ffffff", marginBottom: "6px" }}>
                  No scenario evaluated yet
                </div>
                <p style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
                  Fill in policy inception and diagnosis dates on the left and click "Evaluate Scenario".
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scenario 2: Interstate & Hospital Explanation */}
      {activeScenario === "geography" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.3fr", gap: "24px" }}>
          {/* Form */}
          <form onSubmit={handleGeoSubmit} className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ fontSize: "1.05rem", fontWeight: 700, color: "#ffffff", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
              Geographical & Hospital Inputs
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                Policy Purchase / Residence State:
              </label>
              <input
                type="text"
                value={geoForm.policy_state}
                onChange={(e) => setGeoForm({ ...geoForm, policy_state: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                State Where Hospitalization Is Needed:
              </label>
              <input
                type="text"
                value={geoForm.treatment_state}
                onChange={(e) => setGeoForm({ ...geoForm, treatment_state: e.target.value })}
                style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                Proposed Treating Hospital Name:
              </label>
              <input
                type="text"
                value={geoForm.hospital_name}
                onChange={(e) => setGeoForm({ ...geoForm, hospital_name: e.target.value })}
                placeholder="e.g. Lilavati Hospital Mumbai, Fortis Hospital"
                style={{ width: "100%", padding: "8px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary"
              style={{ marginTop: "10px", padding: "10px" }}
            >
              {isLoading ? "Checking Territorial Scope..." : "Analyze State & Network Rules"}
            </button>
          </form>

          {/* Geo Results Panel */}
          <div className="glass-panel" style={{ padding: "24px", overflowY: "auto", maxHeight: "650px" }}>
            {geoResult ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
                <div style={{ fontSize: "0.85rem", color: "#e2e8f0", lineHeight: 1.7, whiteSpace: "pre-line" }}>
                  {geoResult.territorial_scope_analysis}
                </div>

                <div style={{
                  padding: "14px",
                  borderRadius: "8px",
                  backgroundColor: "rgba(20, 184, 166, 0.08)",
                  border: "1px solid rgba(20, 184, 166, 0.2)",
                  fontSize: "0.82rem",
                  color: "#e2e8f0",
                  lineHeight: 1.6,
                  whiteSpace: "pre-line"
                }}>
                  {geoResult.cashless_vs_reimbursement}
                </div>

                <div style={{ backgroundColor: "#0b1224", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--primary)", marginBottom: "8px" }}>
                    Policyholder Action Checklist:
                  </div>
                  <ul style={{ paddingLeft: "20px", fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                    {geoResult.action_checklist.map((item: string, idx: number) => (
                      <li key={idx} style={{ marginBottom: "6px" }}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", fontStyle: "italic", borderTop: "1px solid var(--border-subtle)", paddingTop: "10px" }}>
                  {geoResult.disclaimer}
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "60px 20px" }}>
                <MapPin size={36} color="var(--text-dim)" style={{ marginBottom: "12px" }} />
                <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#ffffff", marginBottom: "6px" }}>
                  No inter-state check run yet
                </div>
                <p style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
                  Set the purchase and treatment states on the left to inspect territorial coverage vs cashless hospital network rules.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
