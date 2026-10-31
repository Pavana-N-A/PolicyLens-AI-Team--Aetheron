const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001/api";

function getHeaders(): HeadersInit {
  const token = localStorage.getItem("policylens_token");
  const headers: HeadersInit = {
    "Accept": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Auth
  async register(email: string, password: string, name?: string) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify({ email, password, name })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Registration failed");
    return res.json();
  },

  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Login failed");
    const data = await res.json();
    if (data.token) localStorage.setItem("policylens_token", data.token);
    return data;
  },

  async demoLogin() {
    const res = await fetch(`${API_BASE}/auth/demo-login`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Demo login failed");
    const data = await res.json();
    if (data.token) localStorage.setItem("policylens_token", data.token);
    return data;
  },

  async logout() {
    localStorage.removeItem("policylens_token");
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", headers: getHeaders() });
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Unauthorized");
    return res.json();
  },

  async updateConsent(consent: boolean) {
    const res = await fetch(`${API_BASE}/auth/consent`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify({ consent })
    });
    return res.json();
  },

  // Policies
  async getPolicies() {
    const res = await fetch(`${API_BASE}/policies`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load policies");
    return res.json();
  },

  async getPolicy(id: string) {
    const res = await fetch(`${API_BASE}/policies/${id}`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Policy not found");
    return res.json();
  },

  async uploadPolicy(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("policylens_token");
    const res = await fetch(`${API_BASE}/policies/upload`, {
      method: "POST",
      headers: token ? { "Authorization": `Bearer ${token}` } : {},
      body: formData
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
    return res.json();
  },

  async deletePolicy(id: string) {
    const res = await fetch(`${API_BASE}/policies/${id}`, {
      method: "DELETE",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Delete failed");
    return res.json();
  },

  async seedDemo() {
    const res = await fetch(`${API_BASE}/policies/seed-demo`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Seeding demo failed");
    return res.json();
  },

  async updateClause(policyId: string, clauseId: string, data: any) {
    const res = await fetch(`${API_BASE}/policies/${policyId}/clauses/${clauseId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Clause update failed");
    return res.json();
  },

  // Comparisons
  async createComparison(policyIds: string[], priorityFocus: string) {
    const res = await fetch(`${API_BASE}/comparisons`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify({ policy_ids: policyIds, priority_focus: priorityFocus })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Comparison failed");
    return res.json();
  },

  // Scenarios
  async analyzeDisease(payload: any) {
    const res = await fetch(`${API_BASE}/scenarios/disease`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Analysis failed");
    return res.json();
  },

  async analyzeGeography(payload: any) {
    const res = await fetch(`${API_BASE}/scenarios/geography`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Analysis failed");
    return res.json();
  },

  // Chat
  async sendChatMessage(message: string, sessionId?: string, policyId?: string) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getHeaders() },
      body: JSON.stringify({ message, session_id: sessionId, policy_id: policyId })
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Chat error");
    return res.json();
  },

  async getChatSessions() {
    const res = await fetch(`${API_BASE}/chat/sessions`, { headers: getHeaders() });
    return res.json();
  },

  async getChatSession(id: string) {
    const res = await fetch(`${API_BASE}/chat/sessions/${id}`, { headers: getHeaders() });
    return res.json();
  },

  // Hospitals
  async searchHospitals(params: { city?: string; name?: string; state?: string }) {
    const query = new URLSearchParams();
    if (params.city) query.set("city", params.city);
    if (params.name) query.set("name", params.name);
    if (params.state) query.set("state", params.state);
    const res = await fetch(`${API_BASE}/hospitals/search?${query.toString()}`, { headers: getHeaders() });
    return res.json();
  },

  // Health
  async getAiHealth() {
    const res = await fetch(`${API_BASE}/health/ai`);
    return res.json();
  },

  async getOcrHealth() {
    const res = await fetch(`${API_BASE}/health/ocr`);
    return res.json();
  }
};
