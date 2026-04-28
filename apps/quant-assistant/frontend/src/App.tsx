/**
 * QuantPilot Quant Assistant 研究前端.
 *
 * Phase E: 接入 Rust quant-assistant (port 8002) HTTP API.
 * - 回测面板 → POST /api/backtest/run
 * - 优化面板 → POST /api/optimize
 */

import { useState } from "react";
import { BarChart3, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import BacktestPanel from "@/components/BacktestPanel";
import OptimizationPanel from "@/components/OptimizationPanel";

// ── Tab 定义 ──────────────────────────────────────────────────────────────────

type TabId = "backtest" | "optimize";

interface Tab {
  id: TabId;
  label: string;
  icon: React.ElementType;
}

const TABS: Tab[] = [
  { id: "backtest", label: "回测", icon: BarChart3 },
  { id: "optimize", label: "参数优化", icon: Settings2 },
];

// ── 主应用 ────────────────────────────────────────────────────────────────────

export function App() {
  const [activeTab, setActiveTab] = useState<TabId>("backtest");

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      {/* ── 顶部导航栏 */}
      <header className="sticky top-0 z-50 border-b border-[#30363d] bg-[#0d1117]/95 backdrop-blur-sm">
        <div className="max-w-[1400px] mx-auto px-6 flex items-center justify-between h-14">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold text-white tracking-tight">QuantPilot</span>
            <span className="text-[10px] font-bold text-[#8b949e] border border-[#30363d] rounded-full px-2 py-0.5 uppercase tracking-wider">
              Quant Research
            </span>
          </div>

          {/* Tabs */}
          <nav className="flex items-center gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-1.5 px-4 h-9 rounded-lg text-xs font-semibold transition-all",
                  activeTab === tab.id
                    ? "bg-white text-black"
                    : "text-[#8b949e] hover:text-white hover:bg-[#161b22]",
                )}
              >
                <tab.icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            ))}
          </nav>

          {/* 后端状态 */}
          <div className="flex items-center gap-2 text-[10px] text-[#8b949e]">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
            Rust backend · port 8002
          </div>
        </div>
      </header>

      {/* ── 面板内容 */}
      <div className="max-w-[1400px] mx-auto px-6 py-6">
        {activeTab === "backtest" && <BacktestPanel />}
        {activeTab === "optimize" && <OptimizationPanel />}
      </div>
    </div>
  );
}
