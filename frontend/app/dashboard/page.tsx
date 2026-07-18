"use client";

import { useEffect, useState, useRef } from "react";
import { 
  Activity, 
  ShieldAlert, 
  Clock, 
  MapPin, 
  Search,
  Loader2,
  Filter,
  Send, 
  CheckCircle,
  Download,
  Sun,
  Moon,
  TrendingUp,
  TrendingDown,
  X,
  MessageCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { LineChart, Line, Tooltip, ResponsiveContainer } from "recharts";
import InteractiveMap from "@/components/InteractiveMap";

const ZONE_ID_MAP: Record<string, string> = {
  "Zone 1 - North": "Z01",
  "Zone 2 - North East": "Z02",
  "Zone 3 - East": "Z03",
  "Zone 4 - South East": "Z04",
  "Zone 5 - South": "Z05",
  "Zone 6 - South West": "Z06",
  "Zone 7 - West": "Z07",
  "Zone 8 - North West": "Z08",
  "Zone 9 - Central": "Z09",
  "Zone 10 - District 4": "Z10",
  "Zone 11 - South Zone": "Z11",
  "Zone 12 - Outer": "Z12",
};

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
    complaint_volume_change?: string;
    maternal_appointment_change?: string;
    data_freshness: string;
  };
};

type ChatMessage = {
  sender: "user" | "bot";
  text: string;
};

type AlertModal = {
  zone: string;
  content: string;
} | null;

type TrendModal = {
  zone: string;
  metric: string;
  data: { date: string; value: number }[];
} | null;

export default function DashboardPage() {
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { sender: "bot", text: "Hi! I'm the CityPulse Health chat agent. Ask me anything about current health risks." }
  ]);
  const [sendingChat, setSendingChat] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [alertModal, setAlertModal] = useState<AlertModal>(null);
  const [trendModal, setTrendModal] = useState<TrendModal>(null);
  const [alertLoading, setAlertLoading] = useState(false);
  const [trendLoading, setTrendLoading] = useState(false);

  const mockTrendData = [
    { day: "Mon", complaints: 120 },
    { day: "Tue", complaints: 132 },
    { day: "Wed", complaints: 145 },
    { day: "Thu", complaints: 155 },
    { day: "Fri", complaints: 170 },
    { day: "Sat", complaints: 210 },
    { day: "Sun", complaints: 250 },
  ];

  const [trendData, setTrendData] = useState<any[]>(mockTrendData);
  const [isExporting, setIsExporting] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [theme, setTheme] = useState<string>("dark-theme");

  useEffect(() => {
    document.documentElement.classList.remove("light-theme", "dark-theme");
    document.documentElement.classList.add(theme);
  }, [theme]);

  useEffect(() => {
    if (isChatOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, isChatOpen]);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        setLoading(true);
        const res = await fetch("/api/briefing", { cache: "no-store" });
        if (!res.ok) throw new Error("Failed to capture server parameters.");
        const json = await res.json();
        setData(json);

        if (json.summary?.complaint_volume_change) {
          const changeStr = json.summary.complaint_volume_change;
          const match = changeStr.match(/([+-]?\d+)/);
          const pct = match ? parseInt(match[1], 10) : 0;
          const start = 120;
          const end = start * (1 + pct / 100);
          setTrendData([
            { day: "Mon", complaints: start },
            { day: "Tue", complaints: Math.round(start + (end - start) * 0.1) },
            { day: "Wed", complaints: Math.round(start + (end - start) * 0.3) },
            { day: "Thu", complaints: Math.round(start + (end - start) * 0.5) },
            { day: "Fri", complaints: Math.round(start + (end - start) * 0.7) },
            { day: "Sat", complaints: Math.round(start + (end - start) * 0.85) },
            { day: "Sun", complaints: Math.round(end) },
          ]);
        }
        setError("");
      } catch (err: any) {
        setError(err.message || "Something went wrong.");
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

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
    } catch {
      setChatMessages(prev => [...prev, { sender: "bot", text: "Unable to sync with live backend analysis engine." }]);
    } finally {
      setSendingChat(false);
    }
  };

  const handleDraftOutreach = async (anomaly: Anomaly) => {
    const zoneId = ZONE_ID_MAP[anomaly.zone] || "Z07";
    setAlertLoading(true);
    try {
      const res = await fetch(`/api/alert/${zoneId}/${anomaly.type}`);
      const result = await res.json();
      setAlertModal({ zone: anomaly.zone, content: result.alert_draft });
    } catch {
      setAlertModal({ zone: anomaly.zone, content: "Unable to generate alert. Please try again." });
    } finally {
      setAlertLoading(false);
    }
  };

  const handleViewTrend = async (anomaly: Anomaly) => {
    const zoneId = ZONE_ID_MAP[anomaly.zone] || "Z07";
    const metric =
      anomaly.type === "DENGUE_RISK" ? "dengue_risk"
      : anomaly.type === "CLINIC_OVERLOAD" ? "utilization"
      : "maternal";
    setTrendLoading(true);
    try {
      const res = await fetch(`/api/trends/${zoneId}/${metric}`);
      const result = await res.json();
      const chartData = (result.data || []).map((d: any) => ({
        date: d.date,
        value: metric === "maternal" ? Math.round(d.value) : Math.round(d.value * 100),
      }));
      setTrendModal({ zone: anomaly.zone, metric, data: chartData });
    } catch {
      setTrendModal({ zone: anomaly.zone, metric, data: [] });
    } finally {
      setTrendLoading(false);
    }
  };

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

  const handleZoneClick = (zone: string) => {
    setSelectedZone(zone);
  };

  const filteredAnomalies = activeFilter === "ALL"
    ? data?.anomalies || []
    : (data?.anomalies || []).filter(a => a.type === activeFilter);

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  const getTrendLabel = (metric: string) => {
    if (metric === "dengue_risk") return "Dengue Outbreak Probability (%)";
    if (metric === "utilization") return "Clinic Utilization (%)";
    return "Maternal Appointments";
  };

  const getTrendTitle = (metric: string) => {
    if (metric === "dengue_risk") return "Dengue Risk Trend";
    if (metric === "utilization") return "Clinic Utilization Trend";
    return "Maternal Care Trend";
  };

  const getTrendColor = (metric: string) => {
    if (metric === "dengue_risk") return "var(--danger)";
    if (metric === "utilization") return "var(--warning)";
    return "var(--info)";
  };

  if (loading) {
    return (
      <div className="page-container flex-column flex-center justify-center" style={{ minHeight: "80vh", gap: "16px" }}>
        <Loader2 className="text-secondary" size={40} style={{ animation: "spin 1s linear infinite" }} />
        <p>Parsing CityPulse Health parameters across data layers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container flex-column flex-center justify-center text-danger" style={{ minHeight: "80vh" }}>
        <h3>Dashboard Sync Failed</h3>
        <p>{error}</p>
        <button className="btn btn-primary" style={{ marginTop: "16px" }} onClick={() => window.location.reload()}>Retry Handshake</button>
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
          <button
            className="btn btn-secondary flex-center gap-8"
            style={{ padding: "8px" }}
            onClick={() => setTheme(theme === "dark-theme" ? "light-theme" : "dark-theme")}
          >
            {theme === "dark-theme" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            className="btn btn-secondary flex-center gap-8"
            style={{ padding: "8px 16px" }}
            onClick={() => {
              setIsExporting(true);
              setTimeout(() => setIsExporting(false), 2000);
            }}
            disabled={isExporting}
          >
            {isExporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {isExporting ? "Generating PDF..." : "Export Briefing"}
          </button>
          <div className="badge badge-danger gap-8" style={{ padding: "8px 16px" }}>
            <ShieldAlert size={14} />
            <span>{data?.anomalies?.length || 0} Critical Interventions</span>
          </div>
        </div>
      </header>

      <main className="flex-column gap-24" style={{ paddingBottom: "320px" }}>

        {/* FILTERS */}
        <div className="flex-center gap-12" style={{ marginBottom: "8px" }}>
          <Filter size={16} className="text-secondary" />
          {(["ALL", "DENGUE_RISK", "CLINIC_OVERLOAD", "MATERNAL_CARE_DROP"] as const).map((f) => (
            <button
              key={f}
              className={`badge ${activeFilter === f
                ? f === "ALL" ? "badge-primary"
                : f === "DENGUE_RISK" ? "badge-danger"
                : f === "CLINIC_OVERLOAD" ? "badge-warning"
                : "badge-info"
                : "badge-secondary"}`}
              onClick={() => setActiveFilter(f)}
              style={{ cursor: "pointer", border: activeFilter === f ? "none" : "1px solid rgba(255,255,255,0.1)" }}
            >
              {f === "ALL" ? "All Zones" : f === "DENGUE_RISK" ? "Dengue Risk" : f === "CLINIC_OVERLOAD" ? "Clinic Overload" : "Maternal Care"}
            </button>
          ))}
        </div>

        <motion.div variants={containerVariants} initial="hidden" animate="show" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>

            {/* LEFT COLUMN */}
            <div className="flex-column gap-24">
              <motion.section variants={itemVariants} className="card morning-card card-padding" style={{ borderLeft: "4px solid var(--primary)" }}>
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
              </motion.section>

              <motion.section variants={itemVariants} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "20px" }}>
                <div className="card card-padding">
                  <small className="text-muted">Tracking Coverage Profile</small>
                  <h2 style={{ fontSize: "2rem", margin: "4px 0" }}>{data?.summary?.total_zones_monitored || 12} / 12</h2>
                  <small className="badge badge-success" style={{ fontSize: "0.7rem" }}>{data?.summary?.data_freshness || "Zones Synced"}</small>
                </div>
                <div className="card card-padding">
                  <small className="text-muted">Targeted Remediation</small>
                  <h2 className="text-danger" style={{ fontSize: "2rem", margin: "4px 0" }}>{data?.anomalies?.length || 0}</h2>
                  <small className="text-danger" style={{ fontWeight: "600", fontSize: "0.7rem" }}>Pending Review</small>
                </div>
              </motion.section>

              <div style={{ marginTop: "8px", marginBottom: "-8px" }}>
                <h4 className="text-secondary" style={{ letterSpacing: "1px", fontSize: "0.85rem", fontWeight: "700", textTransform: "uppercase" }}>RECOMMENDED REMEDIATION STEPS</h4>
              </div>

              <motion.section variants={containerVariants} className="flex-column gap-16">
                <AnimatePresence>
                  {data?.actions.map((action, idx) => (
                    <motion.div
                      key={idx}
                      variants={itemVariants}
                      initial="hidden"
                      animate="show"
                      exit={{ opacity: 0, scale: 0.9 }}
                      layout
                      className="card card-padding flex-center gap-12"
                      style={{ borderLeft: "4px solid var(--secondary)" }}
                    >
                      <div className="badge badge-info" style={{ borderRadius: "8px", minWidth: "32px" }}>{idx + 1}</div>
                      <p className="text-primary" style={{ margin: 0, fontWeight: "500" }}>{action}</p>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.section>
            </div>

            {/* RIGHT COLUMN */}
            <motion.div variants={itemVariants} className="flex-column gap-24" style={{ height: "100%" }}>
              <InteractiveMap
                anomalies={data?.anomalies || []}
                activeFilter={activeFilter}
                onZoneClick={handleZoneClick}
                totalZones={data?.summary?.total_zones_monitored || 12}
              />

              <motion.section variants={itemVariants} className="card card-padding" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <h4 style={{ color: "var(--text-secondary)", fontSize: "0.85rem", letterSpacing: "1px", fontWeight: 700, margin: 0 }}>SYSTEM SIGNALS OVERVIEW</h4>

                <div className="flex-between" style={{ borderBottom: "1px solid rgba(0,0,0,0.05)", paddingBottom: "12px" }}>
                  <div className="flex-center gap-12">
                    <div style={{ padding: "8px", background: "rgba(37, 99, 235, 0.1)", borderRadius: "8px" }}><Activity size={16} color="var(--primary)" /></div>
                    <span style={{ fontWeight: "500", fontSize: "0.95rem" }}>Signals Processed Overnight</span>
                  </div>
                  <strong style={{ fontSize: "1.1rem" }}>{data?.summary?.signals_processed_overnight || "--"}</strong>
                </div>

                <div className="flex-between" style={{ borderBottom: "1px solid rgba(0,0,0,0.05)", paddingBottom: "12px" }}>
                  <div className="flex-center gap-12">
                    <div style={{ padding: "8px", background: "rgba(245, 158, 11, 0.1)", borderRadius: "8px" }}><TrendingUp size={16} color="var(--warning)" /></div>
                    <span style={{ fontWeight: "500", fontSize: "0.95rem" }}>Complaint Volume Trajectory</span>
                  </div>
                  <strong className="text-warning" style={{ fontSize: "1.1rem" }}>{data?.summary?.complaint_volume_change || "--"}</strong>
                </div>

                <div style={{ width: "100%", height: "80px", marginTop: "-8px", marginBottom: "8px" }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData}>
                      <Tooltip
                        contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", fontSize: "0.85rem", color: "var(--text-primary)" }}
                        itemStyle={{ color: "var(--warning)" }}
                        formatter={(value: any) => [`${value} complaints`, "Volume"]}
                        labelStyle={{ color: "var(--text-secondary)", marginBottom: "4px" }}
                      />
                      <Line type="monotone" dataKey="complaints" stroke="var(--warning)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="flex-between">
                  <div className="flex-center gap-12">
                    <div style={{ padding: "8px", background: "rgba(59, 130, 246, 0.1)", borderRadius: "8px" }}><TrendingDown size={16} color="var(--info)" /></div>
                    <span style={{ fontWeight: "500", fontSize: "0.95rem" }}>Maternal Appointments</span>
                  </div>
                  <strong className="text-info" style={{ fontSize: "1.1rem" }}>{data?.summary?.maternal_appointment_change || "--"}</strong>
                </div>
              </motion.section>
            </motion.div>
          </div>

          {/* ANOMALIES */}
          <motion.div variants={itemVariants} style={{ marginTop: "16px", marginBottom: "-8px" }}>
            <h4 className="text-secondary" style={{ letterSpacing: "1px", fontSize: "0.85rem", fontWeight: "700", textTransform: "uppercase" }}>Anomalies Detected</h4>
          </motion.div>

          <motion.section variants={containerVariants} className="flex-column gap-16">
            <AnimatePresence>
              {filteredAnomalies && filteredAnomalies.length > 0 ? (
                filteredAnomalies.map((anomaly, idx) => {
                  const details = getAnomalyDetails(anomaly);
                  return (
                    <motion.div
                      key={idx}
                      variants={itemVariants}
                      initial="hidden"
                      animate="show"
                      exit={{ opacity: 0, scale: 0.9 }}
                      layout
                      className="card card-padding flex-between"
                      style={{ borderLeft: `4px solid ${details.borderStyle}`, background: details.bgStyle }}
                    >
                      <div className="flex-column gap-8" style={{ maxWidth: "70%" }}>
                        <div className="flex-center gap-12">
                          <Activity size={16} style={{ color: details.borderStyle }} />
                          <h4 style={{ margin: 0, color: "var(--text-primary)" }}>{details.title}</h4>
                        </div>
                        <p style={{ margin: 0, fontSize: "0.92rem", color: "var(--text-secondary)" }}>{details.desc}</p>
                        <small className="flex-center gap-8" style={{ marginTop: "4px" }}>
                          <MapPin size={12} /> {anomaly.zone}
                          <Clock size={12} style={{ marginLeft: "8px" }} /> Detected today
                        </small>
                      </div>
                      <div className="flex-center gap-12">
                        <button
                          className="btn btn-secondary"
                          style={{ fontSize: "0.85rem", padding: "8px 14px" }}
                          disabled={trendLoading}
                          onClick={() => handleViewTrend(anomaly)}
                        >
                          {trendLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : "View trend"}
                        </button>
                        <button
                          className="btn btn-primary"
                          style={{ fontSize: "0.85rem", padding: "8px 14px", background: details.borderStyle }}
                          disabled={alertLoading}
                          onClick={() => handleDraftOutreach(anomaly)}
                        >
                          {alertLoading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : "Draft outreach ↗"}
                        </button>
                      </div>
                    </motion.div>
                  );
                })
              ) : (
                <motion.div variants={itemVariants} className="card card-padding flex-column flex-center justify-center gap-16" style={{ minHeight: "200px" }}>
                  <div style={{ padding: "16px", background: "rgba(16, 185, 129, 0.1)", borderRadius: "50%" }}>
                    <CheckCircle size={32} color="#10B981" />
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <h3 style={{ margin: "0 0 8px 0" }}>All Clear</h3>
                    <p style={{ margin: 0, color: "var(--text-secondary)" }}>No active anomalies detected for this filter.</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>

        </motion.div>
      </main>

      {/* ALERT MODAL */}
      <AnimatePresence>
        {alertModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setAlertModal(null)}
              style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 200 }}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                position: "fixed", top: "50%", left: "50%",
                transform: "translate(-50%, -50%)",
                background: "var(--surface)", borderRadius: "16px",
                padding: "32px", width: "520px", maxWidth: "90vw",
                zIndex: 201, boxShadow: "0 25px 60px rgba(0,0,0,0.3)"
              }}
            >
              <div className="flex-between" style={{ marginBottom: "16px" }}>
                <h3 style={{ margin: 0 }}>Field Alert — {alertModal.zone}</h3>
                <button onClick={() => setAlertModal(null)} className="btn btn-secondary" style={{ padding: "6px", borderRadius: "50%" }}>
                  <X size={18} />
                </button>
              </div>
              <pre style={{
                background: "rgba(255,255,255,0.05)", padding: "16px",
                borderRadius: "10px", fontSize: "0.88rem", lineHeight: "1.7",
                whiteSpace: "pre-wrap", color: "var(--text-primary)",
                border: "1px solid var(--border)", fontFamily: "inherit",
                maxHeight: "320px", overflowY: "auto"
              }}>
                {alertModal.content}
              </pre>
              <div className="flex-center gap-12" style={{ marginTop: "16px", justifyContent: "flex-end" }}>
                <button className="btn btn-secondary" onClick={() => setAlertModal(null)}>Close</button>
                <button
                  className="btn btn-primary"
                  onClick={() => navigator.clipboard.writeText(alertModal.content)}
                >
                  Copy to clipboard
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* TREND MODAL */}
      <AnimatePresence>
        {trendModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setTrendModal(null)}
              style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 200 }}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                position: "fixed", top: "50%", left: "50%",
                transform: "translate(-50%, -50%)",
                background: "var(--surface)", borderRadius: "16px",
                padding: "32px", width: "560px", maxWidth: "90vw",
                zIndex: 201, boxShadow: "0 25px 60px rgba(0,0,0,0.3)"
              }}
            >
              <div className="flex-between" style={{ marginBottom: "24px" }}>
                <div>
                  <h3 style={{ margin: "0 0 4px 0" }}>{getTrendTitle(trendModal.metric)}</h3>
                  <small className="text-secondary">{trendModal.zone} — Last 7 days · Live BigQuery data</small>
                </div>
                <button onClick={() => setTrendModal(null)} className="btn btn-secondary" style={{ padding: "6px", borderRadius: "50%" }}>
                  <X size={18} />
                </button>
              </div>
              {trendModal.data.length === 0 ? (
                <p className="text-secondary" style={{ textAlign: "center", padding: "40px 0" }}>No historical data available for this period.</p>
              ) : (
                <div style={{ width: "100%", height: "200px" }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendModal.data}>
                      <Tooltip
                        contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", fontSize: "0.85rem" }}
                        formatter={(value: any) => [
                          trendModal.metric === "maternal" ? `${value} appointments` : `${value}%`,
                          getTrendLabel(trendModal.metric)
                        ]}
                        labelFormatter={(label) => `Date: ${label}`}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={getTrendColor(trendModal.metric)}
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: getTrendColor(trendModal.metric) }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
              <div style={{ marginTop: "16px", textAlign: "right" }}>
                <button className="btn btn-secondary" onClick={() => setTrendModal(null)}>Close</button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* CHAT FAB */}
      <div style={{ position: "fixed", bottom: "32px", right: "32px", zIndex: 101, display: "flex", alignItems: "center", gap: "16px" }}>
        <AnimatePresence>
          {!isChatOpen && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="chat-tooltip-glass pulse-bounce"
            >
              Ask CityPulse AI ✨
            </motion.div>
          )}
        </AnimatePresence>
        <button
          className={!isChatOpen ? "fab-highlight" : ""}
          onClick={() => setIsChatOpen(!isChatOpen)}
          style={{
            width: "68px", height: "68px", borderRadius: "50%", padding: 0,
            background: "var(--sidebar)", border: "none",
            boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
            display: "flex", justifyContent: "center", alignItems: "center",
            cursor: "pointer", transition: "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = "scale(1.1) rotate(5deg)";
            e.currentTarget.style.boxShadow = "0 15px 35px rgba(37,99,235,0.4)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = "scale(1) rotate(0deg)";
            e.currentTarget.style.boxShadow = "0 10px 25px rgba(0,0,0,0.2)";
          }}
        >
          {isChatOpen ? <X size={30} color="white" /> : <MessageCircle size={30} color="white" />}
        </button>
      </div>

      {/* CHAT DRAWER */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            style={{
              position: "fixed", bottom: "112px", right: "32px",
              width: "100%", maxWidth: "400px",
              background: "var(--sidebar)", padding: "20px",
              borderRadius: "24px", boxShadow: "0 15px 50px rgba(0,0,0,0.2)", zIndex: 100
            }}
          >
            <div style={{ maxHeight: "300px", overflowY: "auto", marginBottom: "16px", display: "flex", flexDirection: "column", gap: "8px", paddingRight: "4px" }}>
              {chatMessages.map((msg, idx) => (
                <div key={idx} style={{
                  alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
                  background: msg.sender === "user" ? "var(--sidebar-active)" : "rgba(255,255,255,0.1)",
                  color: "white", padding: "10px 14px", borderRadius: "16px",
                  fontSize: "0.95rem", maxWidth: "85%"
                }}>
                  {msg.text}
                </div>
              ))}
              {sendingChat && (
                <small style={{ color: "rgba(255,255,255,0.5)", alignSelf: "flex-start", padding: "8px" }} className="flex-center gap-8">
                  <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> Agent processing context signals...
                </small>
              )}
              <div ref={chatEndRef} />
            </div>
            <form onSubmit={handleSendMessage} className="card" style={{ background: "rgba(255,255,255,0.08)", padding: "8px 14px", borderRadius: "100px", border: "1px solid rgba(255,255,255,0.15)" }}>
              <div className="flex-between gap-12">
                <input
                  type="text"
                  placeholder="Ask anything..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={sendingChat}
                  style={{ background: "transparent", border: "none", color: "white", padding: "8px", width: "100%", boxShadow: "none", outline: "none" }}
                />
                <button type="submit" disabled={sendingChat || !chatInput.trim()} className="btn btn-primary" style={{
                  borderRadius: "50%", width: "42px", height: "42px", padding: "0",
                  background: "var(--primary)", opacity: !chatInput.trim() ? 0.5 : 1,
                  display: "flex", justifyContent: "center", alignItems: "center",
                  border: "none", cursor: "pointer"
                }}>
                  <Send size={16} color="white" />
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ZONE SLIDE-OVER */}
      <AnimatePresence>
        {selectedZone && (
          <SlideOverContent
            selectedZone={selectedZone}
            setSelectedZone={setSelectedZone}
            data={data}
            getAnomalyDetails={getAnomalyDetails}
            setChatInput={setChatInput}
            setIsChatOpen={setIsChatOpen}
          />
        )}
      </AnimatePresence>

    </div>
  );
}

function SlideOverContent({ selectedZone, setSelectedZone, data, getAnomalyDetails, setChatInput, setIsChatOpen }: any) {
  const selectedZoneAnomalies = data?.anomalies?.filter((a: any) =>
    a.zone === selectedZone || a.zone.startsWith(`${selectedZone} -`) || a.zone.startsWith(`${selectedZone} `)
  ) || [];

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={() => setSelectedZone(null)}
        style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.4)", zIndex: 40 }}
      />
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        style={{
          position: "fixed", top: 0, right: 0, bottom: 0, width: "400px",
          background: "var(--surface)", boxShadow: "-10px 0 30px rgba(0,0,0,0.1)",
          zIndex: 50, padding: "32px", overflowY: "auto", borderLeft: "1px solid var(--border)"
        }}
      >
        <div className="flex-between" style={{ marginBottom: "24px" }}>
          <h2 style={{ margin: 0 }}>{selectedZone} Details</h2>
          <button onClick={() => setSelectedZone(null)} className="btn btn-secondary" style={{ padding: "8px", borderRadius: "50%" }}>
            <X size={20} />
          </button>
        </div>

        <div className="flex-column gap-24">
          <div className="card card-padding flex-between">
            <div>
              <small className="text-muted">Current Status</small>
              <h3 style={{ margin: "4px 0 0 0" }}>
                {selectedZoneAnomalies.length ? "Anomalies Detected" : "Operating Normally"}
              </h3>
            </div>
            {selectedZoneAnomalies.length
              ? <ShieldAlert size={28} className="text-danger" />
              : <CheckCircle size={28} color="#10B981" />}
          </div>

          <div>
            <h4 style={{ color: "var(--text-secondary)", marginBottom: "12px", textTransform: "uppercase", fontSize: "0.85rem", letterSpacing: "1px" }}>Active Anomalies</h4>
            {selectedZoneAnomalies.length === 0 ? (
              <p className="text-muted" style={{ fontSize: "0.95rem" }}>No active issues for this zone.</p>
            ) : (
              <div className="flex-column gap-12">
                {selectedZoneAnomalies.map((anomaly: any, idx: number) => {
                  const details = getAnomalyDetails(anomaly);
                  return (
                    <div key={idx} style={{ padding: "16px", background: details.bgStyle, borderLeft: `4px solid ${details.borderStyle}`, borderRadius: "8px" }}>
                      <h4 style={{ margin: "0 0 4px 0", color: "var(--text-primary)" }}>{details.title}</h4>
                      <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>{details.desc}</p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div>
            <h4 style={{ color: "var(--text-secondary)", marginBottom: "12px", textTransform: "uppercase", fontSize: "0.85rem", letterSpacing: "1px" }}>Quick Actions</h4>
            <div className="flex-column gap-12">
              <button
                className="btn btn-primary flex-center justify-center gap-8"
                style={{ width: "100%", padding: "12px" }}
                onClick={() => {
                  setSelectedZone(null);
                  setChatInput(`Dispatch a field team to ${selectedZone}`);
                  setIsChatOpen(true);
                }}
              >
                <Activity size={16} /> Dispatch Field Team
              </button>
              <button
                className="btn btn-secondary flex-center justify-center gap-8"
                style={{ width: "100%", padding: "12px" }}
                onClick={() => {
                  setSelectedZone(null);
                  setChatInput(`Run deep diagnostics for ${selectedZone}`);
                  setIsChatOpen(true);
                }}
              >
                <Search size={16} /> Run Deep Diagnostics
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </>
  );
}
