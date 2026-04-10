/**
 * 系统面板 — 合并：价格告警 / 插件管理
 */
import { useState } from "react";
import AlertsPanel from "./AlertsPanel";
import PluginPanel from "./PluginPanel";

type Sub = "alerts" | "plugins";

const SUBS: { key: Sub; label: string }[] = [
  { key: "alerts", label: "价格告警" },
  { key: "plugins", label: "插件管理" },
];

export default function SystemPanel() {
  const [sub, setSub] = useState<Sub>("alerts");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid #1e293b", paddingBottom: 8 }}>
        {SUBS.map((s) => (
          <button
            key={s.key}
            onClick={() => setSub(s.key)}
            style={{
              padding: "4px 14px",
              fontSize: 12,
              borderRadius: 4,
              border: "none",
              cursor: "pointer",
              background: sub === s.key ? "#1e3a5f" : "transparent",
              color: sub === s.key ? "#60a5fa" : "#64748b",
              fontWeight: sub === s.key ? 600 : 400,
            }}
          >
            {s.label}
          </button>
        ))}
      </div>
      {sub === "alerts" && <AlertsPanel />}
      {sub === "plugins" && <PluginPanel />}
    </div>
  );
}
