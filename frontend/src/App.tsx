import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { DashboardView } from "./components/DashboardView";
import { PoliciesView } from "./components/PoliciesView";
import { ComparisonView } from "./components/ComparisonView";
import { ScenariosView } from "./components/ScenariosView";
import { ChatView } from "./components/ChatView";
import { HospitalsView } from "./components/HospitalsView";
import { SettingsView } from "./components/SettingsView";
import { LoginModal } from "./components/LoginModal";
import { api } from "./api";

export function App() {
  const [user, setUser] = useState<any | null>(null);
  const [policies, setPolicies] = useState<any[]>([]);
  const [currentTab, setCurrentTab] = useState<string>("dashboard");
  const [aiStatus, setAiStatus] = useState<any | null>(null);
  const [ocrStatus, setOcrStatus] = useState<any | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);

  const fetchInitialData = async () => {
    try {
      const u = await api.getMe();
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setAuthLoading(false);
    }

    try {
      const [pList, ai, ocr] = await Promise.all([
        api.getPolicies().catch(() => []),
        api.getAiHealth().catch(() => ({ status: "not configured" })),
        api.getOcrHealth().catch(() => ({ active_engine: "PyMuPDF" }))
      ]);
      setPolicies(pList);
      setAiStatus(ai);
      setOcrStatus(ocr);
    } catch (e) {
      console.error("Initial load error:", e);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    try {
      await api.uploadPolicy(file);
      const updated = await api.getPolicies();
      setPolicies(updated);
      alert(`Policy "${file.name}" uploaded, extracted, and indexed successfully!`);
    } catch (err: any) {
      alert("Upload failed: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSeedDemo = async () => {
    setIsUploading(true);
    try {
      await api.seedDemo();
      const updated = await api.getPolicies();
      setPolicies(updated);
      alert("Two synthetic demo policies (CareSecure Direct & Canara HealthProtect) loaded successfully!");
    } catch (err: any) {
      alert("Seeding failed: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
    setPolicies([]);
  };

  if (authLoading) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "var(--bg-main)",
        color: "var(--text-muted)",
        fontFamily: "var(--font-heading)"
      }}>
        Initializing PolicyLens...
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "var(--bg-main)" }}>
      {/* If not logged in, show clean modal with instant demo login option */}
      {!user && (
        <LoginModal onSuccess={fetchInitialData} />
      )}

      {/* Main Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        user={user}
        onLogout={handleLogout}
        aiStatus={aiStatus}
      />

      {/* Main Content Area */}
      <main style={{
        flex: 1,
        padding: "36px 40px",
        overflowY: "auto",
        maxHeight: "100vh"
      }}>
        {currentTab === "dashboard" && (
          <DashboardView
            policies={policies}
            onUpload={handleUpload}
            onSeedDemo={handleSeedDemo}
            setCurrentTab={setCurrentTab}
            isUploading={isUploading}
          />
        )}

        {currentTab === "policies" && (
          <PoliciesView
            policies={policies}
            onUpload={handleUpload}
            onRefresh={async () => {
              const updated = await api.getPolicies();
              setPolicies(updated);
            }}
            onSeedDemo={handleSeedDemo}
            isUploading={isUploading}
          />
        )}

        {currentTab === "compare" && (
          <ComparisonView policies={policies} />
        )}

        {currentTab === "scenarios" && (
          <ScenariosView policies={policies} />
        )}

        {currentTab === "chat" && (
          <ChatView
            policies={policies}
            user={user}
            aiStatus={aiStatus}
          />
        )}

        {currentTab === "hospitals" && (
          <HospitalsView />
        )}

        {currentTab === "settings" && (
          <SettingsView
            user={user}
            aiStatus={aiStatus}
            ocrStatus={ocrStatus}
            onRefresh={fetchInitialData}
          />
        )}
      </main>
    </div>
  );
}

export default App;
