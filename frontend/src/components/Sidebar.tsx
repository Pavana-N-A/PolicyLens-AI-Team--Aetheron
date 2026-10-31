import React from "react";
import { 
  Shield, LayoutDashboard, FileText, GitCompare, 
  HelpCircle, MapPin, Settings, LogOut, Sparkles, AlertCircle
} from "lucide-react";

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  user: any;
  onLogout: () => void;
  aiStatus: any;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  user,
  onLogout,
  aiStatus
}) => {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "policies", label: "My Policies", icon: FileText },
    { id: "compare", label: "Compare Policies", icon: GitCompare },
    { id: "scenarios", label: "Claim Scenarios", icon: HelpCircle },
    { id: "chat", label: "Ask PolicyLens", icon: Sparkles },
    { id: "hospitals", label: "Hospital Network", icon: MapPin },
    { id: "settings", label: "AI & System Status", icon: Settings },
  ];

  return (
    <aside style={{
      width: "260px",
      backgroundColor: "var(--bg-sidebar)",
      borderRight: "1px solid var(--border-subtle)",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      padding: "24px 16px",
      minHeight: "100vh"
    }}>
      <div>
        {/* Brand Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px", paddingLeft: "8px" }}>
          <div style={{
            background: "linear-gradient(135deg, #0ea5e9, #0284c7)",
            padding: "8px",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 12px rgba(14, 165, 233, 0.3)"
          }}>
            <Shield size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.2rem", letterSpacing: "-0.02em", color: "#ffffff" }}>
              PolicyLens
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--teal)", fontWeight: 600, letterSpacing: "0.04em" }}>
              INTELLIGENT NAVIGATOR
            </div>
          </div>
        </div>

        {/* AI Notice Badge */}
        <div style={{
          backgroundColor: aiStatus?.status === "configured" ? "rgba(16, 185, 129, 0.1)" : "rgba(245, 158, 11, 0.1)",
          border: `1px solid ${aiStatus?.status === "configured" ? "rgba(16, 185, 129, 0.25)" : "rgba(245, 158, 11, 0.25)"}`,
          borderRadius: "8px",
          padding: "8px 12px",
          marginBottom: "20px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          fontSize: "0.75rem",
          color: aiStatus?.status === "configured" ? "#34d399" : "#fbbf24"
        }}>
          <Sparkles size={14} />
          <div>
            <strong>AI Status:</strong> {aiStatus?.status === "configured" ? "Gemini Connected" : "Local Mode Active"}
          </div>
        </div>

        {/* Navigation Items */}
        <nav style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  fontSize: "0.88rem",
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? "#ffffff" : "var(--text-muted)",
                  backgroundColor: isActive ? "rgba(14, 165, 233, 0.15)" : "transparent",
                  border: isActive ? "1px solid rgba(14, 165, 233, 0.3)" : "1px solid transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                  width: "100%"
                }}
              >
                <Icon size={18} color={isActive ? "var(--primary)" : "var(--text-dim)"} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Info / Logout */}
      <div style={{
        borderTop: "1px solid var(--border-subtle)",
        paddingTop: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 6px" }}>
          <div style={{ overflow: "hidden" }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#ffffff", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
              {user?.name || "Evaluator"}
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
              {user?.email || "judge.demo@policylens.local"}
            </div>
          </div>
          {user?.is_demo && (
            <span className="badge badge-demo" style={{ fontSize: "0.65rem", padding: "2px 6px" }}>
              DEMO
            </span>
          )}
        </div>

        <button
          onClick={onLogout}
          className="btn btn-secondary"
          style={{ width: "100%", fontSize: "0.8rem", padding: "8px" }}
        >
          <LogOut size={15} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
