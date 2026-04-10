/**
 * 模拟盘控制面板 — mock-pro 设计 + 真实 API.
 */
import { useState, useEffect, useCallback, type ComponentType } from "react";
import {
  Wallet,
  Briefcase,
  ArrowLeftRight,
  CandlestickChart,
  Target,
  Clock,
  Trash2,
  ShieldCheck,
  Activity,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Session {
  session_id: string;
  symbol: string;
  timeframe: string;
  cash: number;
  portfolio_value: number;
  positions: Record<string, { quantity: number; avg_price: number }>;
  trades_count: number;
  bars_processed: number;
  last_bar_at: string | null;
}

export default function PaperTradingPanel() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [form, setForm] = useState({
    session_id: "demo",
    symbol: "AAPL",
    timeframe: "1d",
    initial_cash: "100000",
  });
  const [msg, setMsg] = useState<"success" | string | null>(null);
  const [creating, setCreating] = useState(false);

  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch("/api/paper/sessions");
      const json = (await res.json()) as { sessions: Session[] };
      setSessions(json.sessions ?? []);
    } catch {
      // backend not available
    }
  }, []);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  const loadSelected = async (id: string) => {
    setActiveSessionId(id);
    try {
      const res = await fetch(`/api/paper/sessions/${id}`);
      if (res.ok) setActiveSession((await res.json()) as Session);
    } catch {
      // ignore
    }
  };

  const createSession = async () => {
    setCreating(true);
    setMsg(null);
    try {
      const res = await fetch("/api/paper/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: form.session_id,
          symbol: form.symbol,
          timeframe: form.timeframe,
          initial_cash: parseFloat(form.initial_cash),
        }),
      });
      if (res.ok) {
        setMsg("success");
        await loadSessions();
        await loadSelected(form.session_id);
      } else {
        const err = (await res.json()) as { detail: string };
        setMsg(`错误: ${err.detail}`);
      }
    } catch {
      setMsg("创建失败，请检查后端连接");
    } finally {
      setCreating(false);
    }
  };

  const deleteSession = async (id: string) => {
    try {
      await fetch(`/api/paper/sessions/${id}`, { method: "DELETE" });
    } catch {
      // ignore
    }
    if (activeSessionId === id) {
      setActiveSessionId("");
      setActiveSession(null);
    }
    await loadSessions();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-8 items-start">
      {/* ── Left Sidebar ─────────────────────────────── */}
      <div className="space-y-6">
        {/* New Session Form */}
        <Card className="border-border bg-card/30 backdrop-blur-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-bold">新建模拟盘</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                会话名称
              </label>
              <Input
                value={form.session_id}
                onChange={(e) =>
                  setForm({ ...form, session_id: e.target.value })
                }
                className="bg-background/50 border-border"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                标的代码
              </label>
              <Input
                value={form.symbol}
                onChange={(e) =>
                  setForm({ ...form, symbol: e.target.value.toUpperCase() })
                }
                placeholder="如 AAPL、BTCUSDT"
                className="bg-background/50 border-border"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                周期
              </label>
              <Select
                value={form.timeframe}
                onValueChange={(val) => val && setForm({ ...form, timeframe: val })}
              >
                <SelectTrigger className="bg-background/50 border-border w-full">
                  <SelectValue placeholder="选择周期" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1m">1m</SelectItem>
                  <SelectItem value="5m">5m</SelectItem>
                  <SelectItem value="15m">15m</SelectItem>
                  <SelectItem value="1h">1h</SelectItem>
                  <SelectItem value="4h">4h</SelectItem>
                  <SelectItem value="1d">1d</SelectItem>
                  <SelectItem value="1w">1w</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                初始资金
              </label>
              <Input
                type="number"
                value={form.initial_cash}
                onChange={(e) =>
                  setForm({ ...form, initial_cash: e.target.value })
                }
                className="bg-background/50 border-border"
              />
            </div>

            <Button
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-bold h-11 shadow-lg shadow-primary/20"
              onClick={() => void createSession()}
              disabled={creating}
            >
              {creating ? "创建中…" : "创建"}
            </Button>

            {msg === "success" && (
              <div className="flex items-center gap-2 text-xs text-emerald-500 font-medium">
                <ShieldCheck className="w-4 h-4" />
                会话已创建
              </div>
            )}
            {msg !== null && msg !== "success" && (
              <div className="text-xs text-destructive">{msg}</div>
            )}
          </CardContent>
        </Card>

        {/* Active Sessions List */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold px-1">活跃会话</h3>
          <ScrollArea className="h-[300px] pr-2">
            <div className="space-y-2">
              {sessions.length === 0 && (
                <p className="text-xs text-muted-foreground px-1 py-2">
                  暂无会话，请先创建
                </p>
              )}
              {sessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => void loadSelected(session.session_id)}
                  className={`w-full flex items-center justify-between p-4 rounded-xl border transition-all group text-left ${
                    activeSessionId === session.session_id
                      ? "bg-primary/10 border-primary/50 text-foreground"
                      : "bg-card/30 border-border hover:border-primary/30 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full shrink-0 ${
                        activeSessionId === session.session_id
                          ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                          : "bg-muted-foreground/30"
                      }`}
                    />
                    <span className="font-medium text-sm truncate">
                      {session.session_id} — {session.symbol}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge
                      variant="outline"
                      className="text-[10px] uppercase tracking-tighter opacity-50 group-hover:opacity-100"
                    >
                      {session.timeframe}
                    </Badge>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        void deleteSession(session.session_id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive/80 transition-all p-1 rounded"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* ── Right Dashboard ───────────────────────────── */}
      <div>
        <AnimatePresence mode="wait">
          {activeSession ? (
            <motion.div
              key={activeSession.session_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="space-y-6"
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tight">
                  {activeSession.session_id}
                </h2>
                <Button
                  variant="destructive"
                  size="sm"
                  className="h-8 px-4 font-bold"
                  onClick={() => void deleteSession(activeSession.session_id)}
                >
                  删除
                </Button>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                <MetricCard
                  label="现金"
                  value={`¥${activeSession.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                  icon={Wallet}
                />
                <MetricCard
                  label="组合价值"
                  value={`¥${activeSession.portfolio_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                  icon={Briefcase}
                />
                <MetricCard
                  label="成交笔数"
                  value={activeSession.trades_count.toString()}
                  icon={ArrowLeftRight}
                />
                <MetricCard
                  label="处理K线"
                  value={activeSession.bars_processed.toString()}
                  icon={CandlestickChart}
                />
                <MetricCard
                  label="标的"
                  value={activeSession.symbol}
                  icon={Target}
                />
                <MetricCard
                  label="周期"
                  value={activeSession.timeframe}
                  icon={Clock}
                />
              </div>

              {/* Positions Table */}
              {Object.keys(activeSession.positions).length > 0 && (
                <Card className="border-border bg-card/40">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                      当前持仓
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-muted-foreground border-b border-border">
                          <th className="text-left pb-2 font-medium">标的</th>
                          <th className="text-right pb-2 font-medium">数量</th>
                          <th className="text-right pb-2 font-medium">均价</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(activeSession.positions).map(
                          ([sym, pos]) => (
                            <tr
                              key={sym}
                              className="border-t border-border/50 text-foreground/80"
                            >
                              <td className="py-2 font-mono">{sym}</td>
                              <td className="py-2 text-right font-mono">
                                {pos.quantity}
                              </td>
                              <td className="py-2 text-right font-mono">
                                {pos.avg_price.toFixed(4)}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </CardContent>
                </Card>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-[400px] flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed border-border rounded-3xl"
            >
              <Activity className="w-12 h-12 mb-4 opacity-20" />
              <p className="font-medium">选择或创建一个会话以开始</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: ComponentType<{ className?: string }>;
}) {
  return (
    <Card className="bg-card/40 border-border hover:border-primary/30 transition-colors group">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-muted-foreground">
            {label}
          </span>
          <div className="p-2 rounded-lg bg-muted/50 text-muted-foreground group-hover:text-primary transition-colors">
            <Icon className="w-4 h-4" />
          </div>
        </div>
        <div className="text-3xl font-bold tracking-tight font-mono">
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
