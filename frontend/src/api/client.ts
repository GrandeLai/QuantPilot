/**
 * QuantPilot API client — 封装所有后端接口调用.
 * 使用 Vite dev-proxy：/api/* → http://127.0.0.1:8000/*
 */

const BASE = "/api";

// ── 数据模型 ─────────────────────────────────────────────────────────────────

export interface OhlcBar {
  symbol: string;
  timeframe: string;
  timestamp: string; // ISO 8601
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OhlcvResponse {
  symbol: string;
  timeframe: string;
  count: number;
  bars: OhlcBar[];
}

// key = indicator field name (e.g. "ema", "bb_upper"), value = aligned array
export type IndicatorSeries = Record<string, (number | null)[]>;

export interface TemplateSummary {
  id: string;
  name: string;
  description: string;
  version: string;
  default_params: Record<string, unknown>;
}

export interface StrategyMeta {
  id: string;
  name: string;
  description: string;
  tags: string[];
  params: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface StrategyRecord {
  meta: StrategyMeta;
  code: string;
}

// ── 数据接口 ─────────────────────────────────────────────────────────────────

export async function fetchBars(
  symbol: string,
  timeframe: string,
  limit = 300,
): Promise<OhlcBar[]> {
  const url = `${BASE}/data/bars?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`获取K线失败 (${res.status}): ${await res.text()}`);
  const json = (await res.json()) as OhlcvResponse;
  return json.bars;
}

export async function triggerFetch(
  symbol: string,
  timeframe: string,
  start: string,
): Promise<void> {
  const res = await fetch(`${BASE}/data/fetch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, timeframe, start, source: "auto" }),
  });
  if (!res.ok) throw new Error(`数据拉取失败 (${res.status})`);
}

// ── 指标接口 ─────────────────────────────────────────────────────────────────

export async function fetchBatchIndicators(
  bars: OhlcBar[],
  indicators: string[],
): Promise<Record<string, IndicatorSeries>> {
  const res = await fetch(`${BASE}/indicators/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bars, indicators }),
  });
  if (!res.ok) throw new Error(`批量指标计算失败 (${res.status})`);
  const json = (await res.json()) as { indicators: Record<string, IndicatorSeries> };
  return json.indicators;
}

// ── 策略接口 ─────────────────────────────────────────────────────────────────

export async function listTemplates(): Promise<TemplateSummary[]> {
  const res = await fetch(`${BASE}/strategies/templates`);
  if (!res.ok) throw new Error("获取模板列表失败");
  const json = (await res.json()) as { templates: TemplateSummary[] };
  return json.templates;
}

export async function getTemplateCode(templateId: string): Promise<string> {
  const res = await fetch(`${BASE}/strategies/templates/${templateId}/code`);
  if (!res.ok) throw new Error("获取模板代码失败");
  const json = (await res.json()) as { code: string };
  return json.code;
}

export async function listStrategies(): Promise<StrategyMeta[]> {
  const res = await fetch(`${BASE}/strategies`);
  if (!res.ok) throw new Error("获取策略列表失败");
  const json = (await res.json()) as { strategies: StrategyMeta[] };
  return json.strategies;
}

export async function getStrategy(id: string): Promise<StrategyRecord> {
  const res = await fetch(`${BASE}/strategies/${id}`);
  if (!res.ok) throw new Error("获取策略失败");
  return (await res.json()) as StrategyRecord;
}

export async function createStrategy(
  name: string,
  description: string,
  code: string,
): Promise<{ id: string }> {
  const res = await fetch(`${BASE}/strategies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description, code }),
  });
  if (!res.ok) throw new Error("创建策略失败");
  return (await res.json()) as { id: string };
}

export async function updateStrategy(
  id: string,
  updates: { name?: string; description?: string; code?: string },
): Promise<void> {
  const res = await fetch(`${BASE}/strategies/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("更新策略失败");
}

export async function deleteStrategy(id: string): Promise<void> {
  const res = await fetch(`${BASE}/strategies/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("删除策略失败");
}
