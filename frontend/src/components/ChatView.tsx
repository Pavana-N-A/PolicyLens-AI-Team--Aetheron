import React, { useState, useEffect, useRef } from "react";
import { 
  Sparkles, Send, FileText, CheckCircle2, AlertCircle, 
  HelpCircle, Shield, ExternalLink, Bot, User as UserIcon
} from "lucide-react";
import { api } from "../api";

interface ChatViewProps {
  policies: any[];
  user: any;
  aiStatus: any;
}

export const ChatView: React.FC<ChatViewProps> = ({ policies, user, aiStatus }) => {
  const [messages, setMessages] = useState<any[]>([
    {
      id: "welcome",
      role: "assistant",
      message_text: `### Welcome to PolicyLens Assistant
I am your domain-grounded insurance understanding companion. I can help explain dense contract terms, waiting periods, room-rent sub-limits, and claims procedures.

**STRICT EVIDENCE POLICY:** For policy-specific claims, I retrieve matching clauses directly from your uploaded documents and cite exact page numbers. If a clause was not found in your pages, I will tell you frankly.`,
      sources: []
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedPolicyId, setSelectedPolicyId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim()) return;

    const userMsg = {
      id: "u_" + Date.now(),
      role: "user",
      message_text: text,
      sources: []
    };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const res = await api.sendChatMessage(text, undefined, selectedPolicyId || undefined);
      setMessages(prev => [...prev, res]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: "err_" + Date.now(),
          role: "assistant",
          message_text: `### System Notice\nEncountered an issue processing your query: ${err.message}. Please check your connection or retry.`,
          sources: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const sampleQuestionChips = [
    "I was healthy when I bought the policy but was diagnosed with a disease two years later. Which clauses matter?",
    "I bought this policy in Karnataka but need treatment in Maharashtra. What should I check?",
    "Is this hospital cashless or should I use reimbursement?",
    "What are the room-rent limits and does proportionate deduction apply?",
    "What is the pre-existing disease (PED) waiting period?"
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)", gap: "16px" }}>
      {/* Header Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: "1.7rem", fontWeight: 700, color: "#ffffff", marginBottom: "4px" }}>
            Ask PolicyLens Assistant
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Evidence-grounded explanations powered by SQLite FTS5 clause retrieval and Gemini synthesis.
          </p>
        </div>

        {/* Policy Scope Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "0.82rem", color: "var(--text-dim)" }}>Focus Policy:</span>
          <select
            value={selectedPolicyId}
            onChange={(e) => setSelectedPolicyId(e.target.value)}
            style={{
              padding: "8px 12px",
              backgroundColor: "#0a0f1d",
              color: "#ffffff",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              fontSize: "0.82rem"
            }}
          >
            <option value="">All Uploaded Policies</option>
            {policies.map(p => (
              <option key={p.id} value={p.id}>
                {p.product_name} ({p.insurer_name})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Consent / Free-Tier Privacy Notice */}
      <div style={{
        padding: "10px 16px",
        backgroundColor: "rgba(14, 165, 233, 0.08)",
        borderRadius: "8px",
        border: "1px solid rgba(14, 165, 233, 0.2)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: "0.78rem",
        color: "#94a3b8"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Shield size={15} color="var(--primary)" />
          <span>
            <strong>Privacy Protection:</strong> Uploaded PDFs remain strictly on this laptop. Only targeted clause excerpts are sent for synthesis. Real sensitive personal identifiers should not be submitted to free-tier AI.
          </span>
        </div>
        <span className="badge badge-found" style={{ fontSize: "0.68rem" }}>
          {aiStatus?.status === "configured" ? "Gemini Ready" : "Local Rules Active"}
        </span>
      </div>

      {/* Chat Messages Area */}
      <div className="glass-panel" style={{
        flex: 1,
        overflowY: "auto",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "18px"
      }}>
        {messages.map((m) => {
          const isUser = m.role === "user";
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: isUser ? "flex-end" : "flex-start",
                gap: "6px"
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.75rem", color: "var(--text-dim)" }}>
                {isUser ? (
                  <>
                    <span>You</span>
                    <UserIcon size={13} />
                  </>
                ) : (
                  <>
                    <Bot size={13} color="var(--primary)" />
                    <span style={{ color: "var(--primary)", fontWeight: 600 }}>PolicyLens Assistant</span>
                  </>
                )}
              </div>

              <div style={{
                maxWidth: "85%",
                padding: "16px 20px",
                borderRadius: "12px",
                backgroundColor: isUser ? "rgba(14, 165, 233, 0.18)" : "#0b1224",
                border: isUser ? "1px solid rgba(14, 165, 233, 0.35)" : "1px solid var(--border-subtle)",
                color: "#f8fafc",
                fontSize: "0.88rem",
                lineHeight: 1.6
              }}>
                {/* Render structured message content */}
                {isUser ? (
                  <div style={{ whiteSpace: "pre-wrap" }}>{m.message_text}</div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {m.message_text.split("\n\n").map((block: string, bIdx: number) => {
                      const trimmed = block.trim();
                      if (trimmed.startsWith("**Answer:**")) {
                        return (
                          <div key={bIdx} style={{ fontSize: "0.95rem", color: "#ffffff", fontWeight: 500 }}>
                            <span style={{ color: "var(--primary)", fontWeight: 700 }}>Answer: </span>
                            {trimmed.replace("**Answer:**", "").trim()}
                          </div>
                        );
                      }
                      if (trimmed.startsWith("**Policy reference:**")) {
                        return (
                          <div key={bIdx} style={{
                            padding: "6px 12px",
                            backgroundColor: "rgba(14, 165, 233, 0.08)",
                            borderLeft: "3px solid var(--primary)",
                            borderRadius: "4px",
                            fontSize: "0.82rem",
                            color: "var(--teal)"
                          }}>
                            <strong>Policy Reference: </strong>
                            {trimmed.replace("**Policy reference:**", "").trim()}
                          </div>
                        );
                      }
                      if (trimmed.startsWith("**Important condition:**")) {
                        return (
                          <div key={bIdx} style={{
                            padding: "6px 12px",
                            backgroundColor: "rgba(245, 158, 11, 0.08)",
                            borderLeft: "3px solid #f59e0b",
                            borderRadius: "4px",
                            fontSize: "0.82rem",
                            color: "#fbbf24"
                          }}>
                            <strong>Important Condition: </strong>
                            {trimmed.replace("**Important condition:**", "").trim()}
                          </div>
                        );
                      }
                      return (
                        <div key={bIdx} style={{ whiteSpace: "pre-wrap" }}>
                          {trimmed}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Sources / Page Citations */}
                {m.sources && m.sources.length > 0 && (
                  <div style={{
                    marginTop: "14px",
                    paddingTop: "12px",
                    borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px"
                  }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--teal)", textTransform: "uppercase" }}>
                      Document Citations & Page References:
                    </div>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      {m.sources.map((s: any, idx: number) => (
                        <div
                          key={idx}
                          style={{
                            padding: "4px 8px",
                            backgroundColor: "rgba(255, 255, 255, 0.04)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: "6px",
                            fontSize: "0.72rem",
                            color: "var(--primary)"
                          }}
                        >
                          <strong>[{s.policy_name}, Page {s.page_number}]</strong>: <em>{s.snippet}</em>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)", fontSize: "0.82rem", fontStyle: "italic" }}>
            <Sparkles size={16} color="var(--primary)" />
            <span>PolicyLens Gemini Assistant is analyzing your policy terms...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Question Chips */}
      <div style={{ display: "flex", gap: "8px", overflowX: "auto", paddingBottom: "4px" }}>
        {[
          "What is the accidental death benefit in this policy?",
          "What is the sum insured?",
          "What is the waiting period?",
          "What are the major exclusions?",
          "Is diabetes covered?",
          "What is the difference between cashless and reimbursement?",
          "Can I receive treatment in another state?",
          "What happens if the policy does not mention the requested information?"
        ].map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(chip)}
            style={{
              padding: "6px 12px",
              backgroundColor: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "9999px",
              color: "var(--text-muted)",
              fontSize: "0.75rem",
              whiteSpace: "nowrap",
              cursor: "pointer",
              transition: "all 0.15s ease"
            }}
            onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--primary)")}
            onMouseOut={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="glass-panel" style={{ padding: "8px 12px", display: "flex", gap: "10px", alignItems: "center" }}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Ask a question about coverage, waiting periods, room rent, cashless, or post-purchase diagnosis..."
          style={{
            flex: 1,
            padding: "10px 14px",
            backgroundColor: "transparent",
            border: "none",
            color: "#ffffff",
            fontSize: "0.9rem",
            outline: "none"
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={isLoading || !inputMessage.trim()}
          className="btn btn-primary"
          style={{ padding: "10px 18px" }}
        >
          <Send size={16} />
          <span>Ask</span>
        </button>
      </div>
    </div>
  );
};
