/**
 * LLM 驱动策略代码生成面板.
 */
import { useState } from "react";
import { Sparkles } from "lucide-react";
import { cn } from "../lib/utils";

const MODELS = ["gpt-4o", "claude-3-5-sonnet-20241022", "deepseek/deepseek-chat"];

export default function StrategyGeneratorPanel() {
  const [description, setDescription] = useState("");
  const [model, setModel] = useState("gpt-4o");
  const [result, setResult] = useState<{
    code: string;
    explanation: string;
    name: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/llm/generate-strategy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, model }),
      });
      if (!res.ok) {
        const e = (await res.json()) as { detail: string };
        setError(e.detail);
        return;
      }
      setResult(
        (await res.json()) as { code: string; explanation: string; name: string },
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      {/* ── 生成表单 ──────────────────────────────── */}
      <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <Sparkles size={18} className="text-[#8E9299]" />
          <p className="text-sm font-semibold text-white">自然语言策略生成</p>
        </div>

        {/* 模型选择 */}
        <div className="flex gap-1.5 mb-4">
          {MODELS.map((m) => (
            <button
              key={m}
              onClick={() => setModel(m)}
              className={cn(
                "px-3 py-1 text-[11px] rounded-lg border transition-colors",
                model === m
                  ? "bg-blue-600 border-blue-600 text-white font-semibold"
                  : "bg-[#1C1E22] border-[#2A2D35] text-[#8E9299] hover:text-white",
              )}
            >
              {(m.split("/").pop() ?? m).split("-")[0]}
            </button>
          ))}
        </div>

        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="描述你的策略逻辑，例如：当 RSI 低于 30 时买入，当 RSI 高于 70 时卖出，持仓不超过总资金的 20%"
          rows={4}
          className="w-full bg-[#1C1E22] border border-[#2A2D35] rounded-xl px-4 py-3 text-sm text-white placeholder-[#4A4D55] outline-none focus:border-[#4A4D55] resize-y transition-colors font-sans"
        />

        <div className="flex items-center gap-4 mt-4">
          <button
            onClick={() => void generate()}
            disabled={loading || !description.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-default"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles size={15} />
            )}
            {loading ? "生成中…" : "生成策略代码"}
          </button>
          {error && (
            <p className="text-xs text-[#FF4D4D]">{error}</p>
          )}
        </div>
      </div>

      {/* ── 生成结果 ──────────────────────────────── */}
      {result && (
        <div className="bg-[#151619] border border-[#2A2D35] rounded-xl p-6">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <p className="text-sm font-semibold text-white">{result.name}</p>
              <p className="text-xs text-[#8E9299] mt-1 leading-relaxed">
                {result.explanation}
              </p>
            </div>
          </div>

          <pre className="bg-[#0B0C0E] border border-[#2A2D35] rounded-xl p-5 text-xs text-[#8E9299] overflow-x-auto leading-relaxed custom-scrollbar"
            style={{ fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}
          >
            {result.code}
          </pre>
        </div>
      )}
    </div>
  );
}
