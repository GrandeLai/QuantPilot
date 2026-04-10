/**
 * AI 面板 — 合并：智能问答 / 策略生成
 */
import { useState } from "react";
import LLMChat from "./LLMChat";
import StrategyGeneratorPanel from "./StrategyGeneratorPanel";

type Sub = "chat" | "generate";

const SUBS: { key: Sub; label: string }[] = [
  { key: "chat", label: "智能问答" },
  { key: "generate", label: "生成策略" },
];

export default function AIPanel() {
  const [sub, setSub] = useState<Sub>("chat");

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
      {sub === "chat" && <LLMChat />}
      {sub === "generate" && <StrategyGeneratorPanel />}
    </div>
  );
}
