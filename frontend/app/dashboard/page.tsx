"use client";

import { useEffect, useState } from "react";
import { 
  Activity, 
  ShieldAlert, 
  Clock, 
  MapPin, 
  Send, 
  Sliders, 
  Bell, 
  Search,
  Loader2 
} from "lucide-react";

type Anomaly = {
  type: "DENGUE_RISK" | "CLINIC_OVERLOAD" | "MATERNAL_CARE_DROP";
  zone: string;
  title?: string;
  description?: string;
  time?: string;
  badge?: string;
  badgeStyle?: string;
  cardStyle?: string;
  actionText?: string;
  secActionText?: string;
  // Dynamic parameters from the active backend attributes
  dengue_outbreak_probability?: string;
  utilization?: string;
  drop_percentage?: string;
  appointments_this_week?: number;
};

type BriefingResponse = {
  morning_briefing: string;
  explanation: string;
  actions: string[];
  anomaly_count?: number;
  anomalies?: Anomaly[];
  summary?: {
    date: string;
    total_zones_monitored: number;
    signals_processed_overnight: number;
    highest_outbreak_probability: string;
    data_freshness: string;
  };
};

type ChatMessage = {
  sender: "user" | "bot";
  text: string;
};

export default function DashboardPage() {
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { sender: "bot", text: "Hi! I'm the CityPulse Health chat agent. Ask me anything about current health risks." }
  ]);
  const [sendingChat, setSendingChat] = useState(false);

  // 1. Fetch live metrics and briefing summary on component load
  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const res = await fetch("/api/briefing", { cache: "no-store" });
        if (!res.ok) throw new Error("Failed to capture server parameters.");
        
        const json = await res.json();
        setData(json);
        setError("");
      } catch (err: any) {
        setError(err.message || "Something went wrong.");
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  // 2. Submit user contextual queries to the agent backend
  const handleSendMessage = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!chatInput.trim() || sendingChat) return;

    const userMessage = chatInput.trim();
    setChatMessages(prev => [...prev, { sender: "user", text: userMessage }]);
    setChatInput("");
    setSendingChat(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      });

      if (!res.ok) throw new Error("Agent connection error.");
      const replyData = await res.json();
      
      setChatMessages(prev => [...prev, { sender: "bot", text: replyData.reply || "No clear agent analysis returned." }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: "bot", text: "Unable to sync with live backend analysis engine." }]);
    } finally {
      setSendingChat(false);
    }
  };

  // Helper utility mapping semantic styles onto dynamically fetched metrics
  const getAnomalyDetails = (anomaly: Anomaly) => {
    switch (anomaly.type) {
      case "DENGUE_RISK":
        return {
          title: "Dengue Outbreak Risk Rising",
          desc: `Outbreak probability path evaluated at ${anomaly.dengue_outbreak_probability || "elevated levels"}. Vector monitoring protocol active.`,
          badge: "High Risk",
          bgStyle: "var(--danger-bg)",
          borderStyle: "var(--danger)"
        };
      case "CLINIC_OVERLOAD":
        return {
          title: "Clinic Capacity Warning",
          desc: `District operational utilization metric spiked to ${anomaly.utilization || "critical loads"}. Rerouting non-critical patients.`,
          badge: "Medium Risk",
          bgStyle: "var(--warning-bg)",
          borderStyle: "var(--warning)"
        };
      case "MATERNAL_CARE_DROP":
        return {
          title: "Maternal Care Visits Dropped",
          desc: `Anomalous decrease observed (${anomaly.drop_percentage || "attention threshold tracking"}). Community outreach dispatched.`,
          badge: "Needs Attention",
          bgStyle: "var(--info-bg)",
          borderStyle: "var(--info)"
        };
      default:
        return {
          title: "Unclassified System Signal",
          desc: "System operational variation tracking active outside typical parameters.",
          badge: "Review Needed",
          bgStyle: "var(--surface-hover)",
          borderStyle: "var(--text-secondary)"
        };
    }
  };

  if (loading) {
    return (
      <div className="page-container flex-column flex-center justify-center" style={{ minHeight: '80vh', gap: '16px' }}>
        <Loader2 className="text-secondary" size={40} style={{ animation: "spin 1s linear infinite" }} />
        <p>Parsing CityPulse Health parameters across data layers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container flex-column flex-center justify-center text-danger" style={{ minHeight: '80vh' }}>
        <h3>Dashboard Sync Failed</h3>
        <p>{error}</p>
        <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => window.location.reload()}>Retry Handshake</button>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* HEADER BAR */}
      <header className="flex-between" style={{ marginBottom: "32px" }}>
        <div className="flex-column gap-8">
          <small style={{ fontSize: "0.85rem", letterSpacing: "0.5px" }}>Active Session Summary Monitor</small>
          <h1>Good morning, Dr. Sharma</h1>
        </div>
        <div className="flex-center gap-16">
          <div className="badge badge-danger gap-8" style={{ padding: "8px 16px" }}>
            <ShieldAlert size={14} />
            <span>{data?.actions?.length || 0} Critical Interventions</span>
          </div>
          <button className="btn btn-secondary" style={{ padding: "10px", borderRadius: "50%" }}><Bell size={18} /></button>
          <button className="btn btn-secondary" style={{ padding: "10px", borderRadius: "50%" }}><Sliders size={18} /></button>
        </div>
      </header>

      <main className="flex-column gap-24" style={{ paddingBottom: "320px" }}>
        
        {/* MORNING BRIEFING ROW */}
        <section className="card morning-card card-padding" style={{ borderLeft: "4px solid var(--primary)" }}>
          <div className="flex-between" style={{ marginBottom: "12px" }}>
            <h4 style={{ color: "var(--primary)", fontWeight: "700" }}>MORNING HEALTH BRIEFING</h4>
            <span className="badge badge-info" style={{ background: "rgba(37, 99, 235, 0.1)", color: "var(--primary)" }}>LIVE AGENT COMPILATION</span>
          </div>
          <p className="text-primary" style={{ fontSize: "1.1rem", fontWeight: "500", lineHeight: "1.7" }}>
            "{data?.morning_briefing}"
          </p>
          <div style={{ marginTop: "12px", borderTop: "1px solid rgba(0,0,0,0.05)", paddingTop: "12px" }}>
            <small className="text-secondary" style={{ fontWeight: "600" }}>System Evaluation Data Profile:</small>
            <p style={{ fontSize: "0.95rem" }}>{data?.explanation}</p>
          </div>
        </section>

        {/* METRICS ROW */}
        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "20px" }}>
          <div className="card card-padding">
            <small className="text-muted">Tracking Coverage Profile</small>
            <h2 style={{ fontSize: "2rem", margin: "4px 0" }}>12 / 12</h2>
            <small className="badge badge-success" style={{ fontSize: "0.7rem" }}>Zones Synced</small>
          </div>
          <div className="card card-padding">
            <small className="text-muted">Targeted Remediation Protocols</small>
            <h2 className="text-danger" style={{ fontSize: "2rem", margin: "4px 0" }}>{data?.actions.length}</h2>
            <small className="text-danger" style={{ fontWeight: "600" }}>Pending Acknowledgement</small>
          </div>
        </section>

        {/* DYNAMIC COMPONENT ACTIONS BLOCK */}
        <div style={{ marginTop: "16px", marginBottom: "-8px" }}>
          <h4 className="text-secondary" style={{ letterSpacing: "1px", fontSize: "0.85rem", fontWeight: "700" }}>RECOMMENDED REMEDIATION STEPS</h4>
        </div>

        <section className="flex-column gap-16">
          {data?.actions.map((action, idx) => (
            <div key={idx} className="card card-padding flex-center gap-12" style={{ borderLeft: "4px solid var(--secondary)" }}>
              <div className="badge badge-info" style={{ borderRadius: "8px", minWidth: "32px" }}>{idx + 1}</div>
              <p className="text-primary" style={{ margin: 0, fontWeight: "500" }}>{action}</p>
            </div>
          ))}
        </section>
      </main>

      {/* CHAT DISPLAY AND SLIDING DRAWER CONTAINER */}
      <div style={{
        position: "fixed",
        bottom: "0",
        left: "50%",
        transform: "translateX(-50%)",
        width: "100%",
        maxWidth: "1000px",
        background: "var(--sidebar)",
        padding: "20px",
        borderTopLeftRadius: "24px",
        borderTopRightRadius: "24px",
        boxShadow: "0 -10px 40px rgba(0,0,0,0.15)",
        zIndex: 100
      }}>
        {/* Message Log view inside the interactive dock */}
        <div style={{ 
          maxHeight: "160px", 
          overflowY: "auto", 
          marginBottom: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          paddingRight: "4px"
        }}>
          {chatMessages.map((msg, idx) => (
            <div key={idx} style={{
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              background: msg.sender === "user" ? "var(--sidebar-active)" : "rgba(255,255,255,0.1)",
              color: "white",
              padding: "8px 14px",
              borderRadius: "12px",
              fontSize: "0.9rem",
              maxWidth: "85%"
            }}>
              {msg.text}
            </div>
          ))}
          {sendingChat && (
            <small style={{ color: "rgba(255,255,255,0.5)", alignSelf: "flex-start" }} className="flex-center gap-8">
              <Loader2 size={12} style={{ animation: "spin 1s linear infinite" }} /> Agent processing context signals...
            </small>
          )}
        </div>

        <form onSubmit={handleSendMessage} className="card" style={{ 
          background: "rgba(255,255,255,0.08)", 
          padding: "6px 12px", 
          borderRadius: "100px",
          border: "1px solid rgba(255,255,255,0.15)"
        }}>
          <div className="flex-between gap-12">
            <Search size={18} style={{ color: "rgba(255,255,255,0.4)", marginLeft: "8px" }} />
            <input 
              type="text" 
              placeholder="Ask anything — 'Which zones have lowest vaccination coverage?'" 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={sendingChat}
              style={{
                background: "transparent",
                border: "none",
                color: "white",
                padding: "8px 4px",
                width: "100%",
                boxShadow: "none"
              }}
            />
            <button type="submit" disabled={sendingChat || !chatInput.trim()} className="btn btn-primary" style={{ 
              borderRadius: "50%", 
              width: "38px", 
              height: "38px", 
              padding: "0",
              background: "var(--sidebar-active)",
              opacity: !chatInput.trim() ? 0.5 : 1
            }}>
              <Send size={14} color="white" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}