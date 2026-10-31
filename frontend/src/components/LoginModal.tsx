import React, { useState } from "react";
import { Shield, Eye, EyeOff, Lock, Mail, ArrowRight, Sparkles } from "lucide-react";
import { api } from "../api";

interface LoginModalProps {
  onSuccess: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      if (isRegister) {
        await api.register(email, password, name);
        // Then login
        await api.login(email, password);
      } else {
        await api.login(email, password);
      }
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setIsLoading(true);
    try {
      await api.demoLogin();
      onSuccess();
    } catch (err: any) {
      setError("Demo login error: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(10, 15, 29, 0.92)",
      backdropFilter: "blur(12px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 2000,
      padding: "20px"
    }}>
      <div className="glass-panel" style={{
        width: "440px",
        padding: "36px 32px",
        backgroundColor: "#0e162a",
        border: "1px solid rgba(14, 165, 233, 0.3)",
        boxShadow: "0 20px 40px rgba(0,0,0,0.5)"
      }}>
        {/* Brand */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div style={{
            display: "inline-flex",
            background: "linear-gradient(135deg, #0ea5e9, #0284c7)",
            padding: "12px",
            borderRadius: "14px",
            marginBottom: "12px",
            boxShadow: "0 6px 20px rgba(14, 165, 233, 0.4)"
          }}>
            <Shield size={28} color="#ffffff" />
          </div>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#ffffff", marginBottom: "4px" }}>
            PolicyLens
          </h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Intelligent Health Insurance Understanding & Risk Navigator
          </p>
        </div>

        {/* Demo Login Button for Judges */}
        <div style={{
          backgroundColor: "rgba(14, 165, 233, 0.1)",
          border: "1px dashed rgba(14, 165, 233, 0.4)",
          borderRadius: "10px",
          padding: "16px",
          marginBottom: "24px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "0.78rem", color: "var(--teal)", fontWeight: 700, textTransform: "uppercase", marginBottom: "4px" }}>
            Hackathon Evaluators & Judges
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "12px" }}>
            One-click access with seeded demo credentials (no manual registration needed).
          </p>
          <button
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="btn btn-primary"
            style={{ width: "100%", padding: "10px", fontSize: "0.85rem" }}
          >
            <Sparkles size={16} />
            <span>Instant Demo Login</span>
          </button>
        </div>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
          <div style={{ flex: 1, height: "1px", backgroundColor: "var(--border-subtle)" }} />
          <span style={{ fontSize: "0.72rem", color: "var(--text-dim)", textTransform: "uppercase" }}>Or Account Login</span>
          <div style={{ flex: 1, height: "1px", backgroundColor: "var(--border-subtle)" }} />
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            padding: "10px 14px",
            backgroundColor: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "6px",
            color: "#f87171",
            fontSize: "0.8rem",
            marginBottom: "16px"
          }}>
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {isRegister && (
            <div>
              <label style={{ fontSize: "0.75rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
                Full Name:
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Policyholder Name"
                style={{ width: "100%", padding: "9px 12px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
            </div>
          )}

          <div>
            <label style={{ fontSize: "0.75rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
              Email Address:
            </label>
            <div style={{ position: "relative" }}>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                style={{ width: "100%", padding: "9px 12px 9px 34px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
              <Mail size={15} color="var(--text-dim)" style={{ position: "absolute", left: "10px", top: "12px" }} />
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.75rem", color: "var(--text-dim)", display: "block", marginBottom: "4px" }}>
              Password:
            </label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                style={{ width: "100%", padding: "9px 34px", background: "#0a0f1d", border: "1px solid var(--border-subtle)", borderRadius: "6px", color: "#ffffff", fontSize: "0.85rem" }}
              />
              <Lock size={15} color="var(--text-dim)" style={{ position: "absolute", left: "10px", top: "12px" }} />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: "absolute", right: "10px", top: "10px", background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer" }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-secondary"
            style={{ width: "100%", padding: "10px", marginTop: "6px" }}
          >
            {isRegister ? "Create Local Account" : "Sign In to PolicyLens"}
          </button>
        </form>

        {/* Toggle Register / Login */}
        <div style={{ textAlign: "center", marginTop: "18px", fontSize: "0.8rem", color: "var(--text-dim)" }}>
          {isRegister ? (
            <span>Already have an account? <strong onClick={() => setIsRegister(false)} style={{ color: "var(--primary)", cursor: "pointer" }}>Sign in</strong></span>
          ) : (
            <span>Don't have an account? <strong onClick={() => setIsRegister(true)} style={{ color: "var(--primary)", cursor: "pointer" }}>Register</strong></span>
          )}
        </div>
      </div>
    </div>
  );
};
