/**
 * AI 助手聊天面板 — SSE 流式输出.
 */
import { useState, useRef, useEffect } from "react";
import { cn } from "../lib/utils";
import { Send } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  available: boolean;
}

const FALLBACK_MODELS: ModelInfo[] = [
  { id: "gpt-4o", name: "GPT-4o", provider: "openai", available: false },
  { id: "claude-sonnet-4-6", name: "Claude Sonnet 4.6", provider: "anthropic", available: false },
  { id: "deepseek/deepseek-chat", name: "DeepSeek Chat", provider: "openai", available: false },
];

export default function LLMChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "你好！我是 QuantPilot AI 助手。你可以问我关于股票分析、技术指标、策略建议等问题。",
    },
  ]);
  const [input, setInput] = useState("");
  const [models, setModels] = useState<ModelInfo[]>(FALLBACK_MODELS);
  const [model, setModel] = useState("gpt-4o");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch("/api/llm/models");
        if (res.ok) {
          const data = (await res.json()) as { models: ModelInfo[] };
          if (data.models.length > 0) {
            setModels(data.models);
            // 优先选择第一个 available 的模型
            const first = data.models.find((m) => m.available);
            if (first) setModel(first.id);
          }
        }
      } catch { /* 静默 */ }
    })();
  }, []);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const newHistory: Message[] = [...messages, { role: "user", content: text }];
    setMessages(newHistory);
    setLoading(true);

    const assistantIdx = newHistory.length;
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const res = await fetch("/api/llm/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newHistory.map((m) => ({ role: m.role, content: m.content })),
          model,
        }),
      });

      if (!res.ok || !res.body) {
        setMessages((prev) => {
          const copy = [...prev];
          copy[assistantIdx] = {
            role: "assistant",
            content: "请求失败，请检查后端是否启动并配置了 API Key。",
          };
          return copy;
        });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            setMessages((prev) => {
              const copy = [...prev];
              copy[assistantIdx] = {
                role: "assistant",
                content: (copy[assistantIdx]?.content ?? "") + data,
              };
              return copy;
            });
          }
        }
      }
    } catch (e) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[assistantIdx] = {
          role: "assistant",
          content: `错误: ${String(e)}`,
        };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="flex flex-col"
      style={{ height: "calc(100vh - 130px)" }}
    >
      {/* ── 模型选择栏 ────────────────────────────── */}
      <div className="flex items-center gap-2 pb-3 border-b border-[#2A2D35] mb-4 shrink-0">
        <span className="text-[10px] font-mono uppercase tracking-wider text-[#8E9299]">
          模型
        </span>
        <div className="flex gap-1.5 flex-wrap">
          {models.map((m) => (
            <button
              key={m.id}
              onClick={() => setModel(m.id)}
              title={m.available ? `${m.name} (已配置)` : `${m.name} (未配置 API Key)`}
              className={cn(
                "px-3 py-1 text-[11px] rounded-lg border transition-colors flex items-center gap-1.5",
                model === m.id
                  ? "bg-blue-600 border-blue-600 text-white font-semibold"
                  : "bg-[#1C1E22] border-[#2A2D35] text-[#8E9299] hover:text-white",
                !m.available && "opacity-50",
              )}
            >
              <span
                className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0",
                  m.available ? "bg-green-400" : "bg-gray-600",
                )}
              />
              {m.name.split(" ")[0]}
            </button>
          ))}
        </div>
      </div>

      {/* ── 消息历史 ──────────────────────────────── */}
      <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-3 pr-1">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            <div
              className={cn(
                "max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words",
                msg.role === "user"
                  ? "bg-blue-600/30 text-white rounded-br-sm"
                  : "bg-[#1C1E22] border border-[#2A2D35] text-[#E1E4E8] rounded-bl-sm",
              )}
            >
              {msg.content ||
                (loading && i === messages.length - 1 ? (
                  <span className="inline-block w-2 h-4 bg-[#8E9299] animate-pulse rounded-sm" />
                ) : (
                  ""
                ))}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* ── 输入区 ────────────────────────────────── */}
      <div className="flex gap-3 mt-4 pt-4 border-t border-[#2A2D35] shrink-0">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          placeholder="输入问题，如：分析 AAPL 的 RSI 指标… (Enter 发送，Shift+Enter 换行)"
          rows={2}
          className="flex-1 bg-[#1C1E22] border border-[#2A2D35] rounded-xl px-4 py-3 text-sm text-white placeholder-[#4A4D55] outline-none focus:border-[#4A4D55] resize-none transition-colors font-sans"
        />
        <button
          onClick={() => void send()}
          disabled={loading || !input.trim()}
          className="px-5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors disabled:opacity-40 disabled:cursor-default self-stretch flex items-center gap-2"
        >
          {loading ? (
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>
    </div>
  );
}
