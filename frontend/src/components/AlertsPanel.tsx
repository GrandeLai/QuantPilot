/**
 * 告警规则管理面板.
 */
import { useState, useEffect, useCallback } from "react";
import { cn } from "../lib/utils";

interface AlertRule {
  id: string;
  name: string;
  conditions: Array<{ symbol: string; condition_type: string; threshold: number }>;
  cooldown_seconds: number;
  enabled: boolean;
}

interface AlertEvent {
  rule_id: string;
  rule_name: string;
  symbol: string;
  condition_type: string;
  current_value: number;
  threshold: number;
  fired_at: string;
  message: string;
}

const CONDITION_TYPES = [
  "price_above",
  "price_below",
  "pct_change_above",
  "pct_change_below",
];

export default function AlertsPanel() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [form, setForm] = useState({
    name: "",
    symbol: "",
    condition_type: "price_above",
    threshold: "",
    cooldown: "3600",
  });
  const [msg, setMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [rulesRes, eventsRes] = await Promise.all([
        fetch("/api/alerts/rules"),
        fetch("/api/alerts/events?limit=20"),
      ]);
      const rj = (await rulesRes.json()) as { rules: AlertRule[] };
      const ej = (await eventsRes.json()) as { events: AlertEvent[] };
      setRules(rj.rules ?? []);
      setEvents(ej.events ?? []);
    } catch (_) {}
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const createRule = async () => {
    const res = await fetch("/api/alerts/rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.name,
        conditions: [
          {
            symbol: form.symbol,
            condition_type: form.condition_type,
            threshold: parseFloat(form.threshold),
          },
        ],
        cooldown_seconds: parseInt(form.cooldown),
      }),
    });
    if (res.ok) {
      setMsg("规则创建成功");
      void loadData();
    } else {
      setMsg("创建失败");
    }
  };

  const deleteRule = async (id: string) => {
    await fetch(`/api/alerts/rules/${id}`, { method: "DELETE" });
    void loadData();
  };

  return (
    <div className="flex gap-4">
      {/* ── 左侧：创建规则 ────────────────────────── */}
      <div className="w-72 shrink-0 bg-[#151619] border border-[#2A2D35] rounded-xl p-5 flex flex-col gap-3">
        <p className="text-xs font-mono uppercase tracking-wider text-[#8E9299]">
          新建告警规则
        </p>

        {(
          [
            ["name", "规则名称", "text"],
            ["symbol", "标的代码 (如 AAPL)", "text"],
            ["threshold", "阈值", "text"],
            ["cooldown", "冷却时间 (秒)", "text"],
          ] as [keyof typeof form, string, string][]
        ).map(([k, placeholder]) => (
          <input
            key={k}
            placeholder={placeholder}
            value={form[k]}
            onChange={(e) => setForm((p) => ({ ...p, [k]: e.target.value }))}
            className="w-full bg-[#1C1E22] border border-[#2A2D35] rounded-lg px-3 py-1.5 text-xs text-white placeholder-[#4A4D55] outline-none focus:border-[#4A4D55] transition-colors"
          />
        ))}

        <select
          value={form.condition_type}
          onChange={(e) => setForm((p) => ({ ...p, condition_type: e.target.value }))}
          className="w-full bg-[#1C1E22] border border-[#2A2D35] rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-[#4A4D55] transition-colors"
        >
          {CONDITION_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <button
          onClick={() => void createRule()}
          className="py-2 bg-amber-500 hover:bg-amber-400 text-black rounded-lg text-xs font-semibold transition-colors"
        >
          创建规则
        </button>

        {msg && (
          <p
            className={cn(
              "text-xs",
              msg.includes("成功") ? "text-[#00C087]" : "text-[#FF4D4D]",
            )}
          >
            {msg}
          </p>
        )}

        {/* 已有规则列表 */}
        {rules.length > 0 && (
          <div className="pt-3 border-t border-[#2A2D35] flex flex-col gap-1">
            <p className="text-[10px] font-mono uppercase tracking-wider text-[#8E9299] mb-1">
              已有规则 ({rules.length})
            </p>
            {rules.map((r) => (
              <div
                key={r.id}
                className="flex justify-between items-center py-1"
              >
                <span className="text-xs text-[#8E9299] truncate">{r.name}</span>
                <button
                  onClick={() => void deleteRule(r.id)}
                  className="ml-2 text-[#4A4D55] hover:text-[#FF4D4D] transition-colors text-sm shrink-0"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── 右侧：触发事件 ────────────────────────── */}
      <div className="flex-1 bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
        <p className="text-xs font-mono uppercase tracking-wider text-[#8E9299] mb-5">
          最近触发事件
        </p>

        {events.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-[#4A4D55] text-sm">
            暂无触发记录
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {events.map((e, i) => (
              <div
                key={i}
                className="px-4 py-3 bg-[#1C1E22] rounded-xl border-l-2 border-amber-500"
              >
                <p className="text-sm font-semibold text-white">{e.rule_name}</p>
                <p className="text-xs text-[#8E9299] mt-1">{e.message}</p>
                <p className="text-[10px] text-[#4A4D55] mt-1">
                  {new Date(e.fired_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
