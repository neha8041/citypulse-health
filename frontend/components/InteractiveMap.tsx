"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Anomaly = {
  type: string;
  zone: string; // e.g. "Zone 1"
};

type InteractiveMapProps = {
  anomalies: Anomaly[];
  activeFilter: string | null;
  onZoneClick: (zone: string) => void;
  totalZones?: number;
};

export default function InteractiveMap({ anomalies, activeFilter, onZoneClick, totalZones = 12 }: InteractiveMapProps) {
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, text: "" });

  const { zones, svgWidth, svgHeight } = useMemo(() => {
    const cols = 4;
    const boxSize = 100;
    const padding = 10;
    
    const rows = Math.ceil(totalZones / cols);
    const generated = [];
    
    for (let i = 0; i < totalZones; i++) {
      const row = Math.floor(i / cols);
      const col = i % cols;
      generated.push({
        id: `Zone ${i + 1}`,
        x: padding + col * (boxSize + padding),
        y: padding + row * (boxSize + padding),
      });
    }
    
    return {
      zones: generated,
      svgWidth: cols * (boxSize + padding) + padding,
      svgHeight: rows * (boxSize + padding) + padding
    };
  }, [totalZones]);
  
  
  const getZoneColor = (zoneAnomalies: Anomaly[]) => {
    if (zoneAnomalies.length === 0) return "rgba(0, 0, 0, 0.04)"; // Normal/Safe
    
    const hasDengue = zoneAnomalies.some(a => a.type === "DENGUE_RISK");
    const hasClinic = zoneAnomalies.some(a => a.type === "CLINIC_OVERLOAD");
    const hasMaternal = zoneAnomalies.some(a => a.type === "MATERNAL_CARE_DROP");

    if (activeFilter && activeFilter !== "ALL") {
      if (activeFilter === "DENGUE_RISK" && hasDengue) return "rgba(239, 68, 68, 0.8)"; // Red
      if (activeFilter === "CLINIC_OVERLOAD" && hasClinic) return "rgba(245, 158, 11, 0.8)"; // Amber
      if (activeFilter === "MATERNAL_CARE_DROP" && hasMaternal) return "rgba(59, 130, 246, 0.8)"; // Blue
      return "var(--map-dim)"; // Doesn't match filter, dim it
    }

    if (hasDengue) return "rgba(239, 68, 68, 0.8)"; 
    if (hasClinic) return "rgba(245, 158, 11, 0.8)"; 
    if (hasMaternal) return "rgba(59, 130, 246, 0.8)";
    
    return "var(--map-empty)";
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="card card-padding" 
      style={{ position: "relative", width: "100%", height: "auto", overflow: "hidden" }}
    >
      <h4 style={{ marginBottom: "4px", color: "var(--text-secondary)", fontSize: "0.85rem", letterSpacing: "1px", fontWeight: 700 }}>LIVE CITY HEATMAP</h4>
      <p style={{ margin: "0 0 16px 0", fontSize: "0.8rem", color: "var(--text-secondary)" }}>Hover/Click on the zones to see more detailed info.</p>
      
      <svg width="100%" height="auto" viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="xMidYMid meet" style={{ display: "block" }}>
        {zones.map((zone) => {
          const zoneAnomalies = anomalies?.filter(a => 
            a.zone === zone.id || a.zone.startsWith(`${zone.id} -`) || a.zone.startsWith(`${zone.id} `)
          ) || [];
          
          const color = getZoneColor(zoneAnomalies);
          const isHighRisk = color.includes("239, 68, 68") || color.includes("245, 158, 11");

          const getIssueText = () => {
            if (zoneAnomalies.length === 0) return "No Issues";
            const types = zoneAnomalies.map(a => {
              if (a.type === "DENGUE_RISK") return "Dengue";
              if (a.type === "CLINIC_OVERLOAD") return "Overload";
              if (a.type === "MATERNAL_CARE_DROP") return "Maternal";
              return a.type;
            });
            const uniqueTypes = Array.from(new Set(types));
            if (uniqueTypes.length > 1) return "Multiple Risks";
            return uniqueTypes[0] + (uniqueTypes[0] === "Overload" ? "" : " Risk");
          };

          const getTooltipText = () => {
            if (zoneAnomalies.length === 0) return `${zone.id}\nStatus: No issues detected.`;
            const riskNames = zoneAnomalies.map(a => {
              if (a.type === "DENGUE_RISK") return "Dengue Risk";
              if (a.type === "CLINIC_OVERLOAD") return "Clinic Overload";
              if (a.type === "MATERNAL_CARE_DROP") return "Maternal Care Drop";
              return a.type;
            });
            return `${zone.id}\nActive Risks:\n- ` + riskNames.join("\n- ");
          };

          return (
            <g 
              key={zone.id} 
              onClick={() => onZoneClick(zone.id)} 
              style={{ cursor: "pointer" }}
              onMouseMove={(e) => {
                setTooltip({
                  show: true,
                  x: e.clientX,
                  y: e.clientY,
                  text: getTooltipText()
                });
              }}
              onMouseLeave={() => setTooltip(prev => ({ ...prev, show: false }))}
            >
              <motion.rect
                className={isHighRisk ? "pulse-danger" : ""}
                x={zone.x}
                y={zone.y}
                width="100"
                height="100"
                rx="12"
                fill={color}
                stroke={color.startsWith("var") ? "var(--border)" : "rgba(255, 255, 255, 0.2)"}
                strokeWidth="1"
                initial={{ opacity: 0 }}
                animate={{ 
                  opacity: isHighRisk ? [0.6, 1, 0.6] : 1, 
                }}
                transition={{ 
                  opacity: {
                    duration: 1.5,
                    repeat: isHighRisk ? Infinity : 0,
                    ease: "easeInOut"
                  }
                }}
                whileHover={{ stroke: "rgba(255,255,255,0.4)" }}
              />
              <text 
                x={zone.x + 50} 
                y={zone.y + 45} 
                textAnchor="middle" 
                fill={color === "var(--map-dim)" ? "var(--text-muted)" : (zoneAnomalies.length === 0 ? "var(--text-primary)" : "white")} 
                fontSize="14" 
                fontWeight="600"
                style={{ pointerEvents: "none" }}
              >
                {zone.id}
              </text>
              <text 
                x={zone.x + 50} 
                y={zone.y + 65} 
                textAnchor="middle" 
                fill={color === "var(--map-dim)" ? "var(--text-muted)" : (zoneAnomalies.length === 0 ? "var(--text-secondary)" : "rgba(255,255,255,0.9)")} 
                fontSize="11" 
                fontWeight="500"
                style={{ pointerEvents: "none" }}
              >
                {getIssueText()}
              </text>
            </g>
          );
        })}
      </svg>

      {/* CUSTOM FLOATING TOOLTIP */}
      <AnimatePresence>
        {tooltip.show && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.1 }}
            style={{
              position: "fixed",
              top: tooltip.y + 15,
              left: tooltip.x + 15,
              background: "rgba(15, 23, 42, 0.95)",
              color: "white",
              padding: "10px 14px",
              borderRadius: "8px",
              fontSize: "0.85rem",
              zIndex: 9999,
              pointerEvents: "none",
              whiteSpace: "pre-line",
              boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
              fontWeight: 500,
              lineHeight: "1.5"
            }}
          >
            {tooltip.text}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
