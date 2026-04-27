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

export interface CryptoResearchWindowMetric {
  train_start: number;
  train_end: number;
  test_start: number;
  test_end: number;
  accuracy: number;
  strategy_return: number;
}

export interface CryptoResearchSummary {
  symbol: string;
  base_timeframe: string;
  higher_timeframes: string[];
  rows: number;
  dataset_version: string;
  feature_count: number;
  feature_columns: string[];
  validation_windows: number;
  window_metrics: CryptoResearchWindowMetric[];
  mean_accuracy: number;
  mean_strategy_return: number;
  latest_class_signal: number;
  latest_class_probabilities: Record<string, number>;
  feature_importance: Record<string, number>;
  reversal_probability: number;
  reversal_signal: string;
  reversal_evidence: string[];
  market_regime: string;
  recommended_strategy_ids: string[];
  recommended_timeframes: string[];
  parameter_search_ready: boolean;
}

export interface CryptoResearchOptimizationSummary {
  symbol: string;
  strategy_id: string;
  base_timeframe: string;
  higher_timeframes: string[];
  best_params: Record<string, number>;
  window_count: number;
  mean_accuracy: number;
  mean_strategy_return: number;
  max_drawdown: number;
  window_metrics: CryptoResearchWindowMetric[];
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

export async function fetchCryptoResearchSummary(symbol: string): Promise<CryptoResearchSummary> {
  const res = await fetch(`${BASE}/crypto/research/train`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol,
      base_timeframe: "15m",
      higher_timeframes: ["1h", "4h", "1d", "1w"],
      limit: 180,
      validation: {
        train_size: 60,
        test_size: 20,
        step_size: 20,
        embargo_size: 2,
      },
    }),
  });
  if (!res.ok) throw new Error(`获取加密研究摘要失败 (${res.status}): ${await res.text()}`);
  return (await res.json()) as CryptoResearchSummary;
}

export async function fetchCryptoResearchLatestSummary(symbol: string): Promise<CryptoResearchSummary> {
  const res = await fetch(
    `${BASE}/crypto/research/latest?symbol=${encodeURIComponent(symbol)}&base_timeframe=15m`
  );
  if (!res.ok) throw new Error(`获取加密最新研究摘要失败 (${res.status}): ${await res.text()}`);
  return (await res.json()) as CryptoResearchSummary;
}

export async function fetchCryptoResearchOptimization(
  symbol: string,
): Promise<CryptoResearchOptimizationSummary> {
  const res = await fetch(`${BASE}/crypto/research/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol,
      base_timeframe: "15m",
      higher_timeframes: ["1h", "4h", "1d", "1w"],
      limit: 180,
      param_grid: {
        fast_period: [5, 8],
        slow_period: [20, 30],
        vwap_window: [10, 20],
        trailing_stop_pct: [0.02, 0.03],
        max_hold_bars: [24, 48],
      },
    }),
  });
  if (!res.ok) throw new Error(`获取加密参数优化失败 (${res.status}): ${await res.text()}`);
  return (await res.json()) as CryptoResearchOptimizationSummary;
}

export async function fetchCryptoResearchLatestOptimization(
  symbol: string,
  strategyId: string,
): Promise<CryptoResearchOptimizationSummary> {
  const res = await fetch(
    `${BASE}/crypto/research/optimize/latest?symbol=${encodeURIComponent(symbol)}&base_timeframe=15m&strategy_id=${encodeURIComponent(strategyId)}`,
  );
  if (!res.ok) throw new Error(`获取加密最新优化结果失败 (${res.status}): ${await res.text()}`);
  return (await res.json()) as CryptoResearchOptimizationSummary;
}

// ── 因子目录 ──────────────────────────────────────────────────────────────────

export interface FactorInfo {
  name: string;
  category: string;
  source: string;
  window: number | null;
  description: string;
  range_hint: string | null;
}

export async function fetchFactorCatalog(): Promise<FactorInfo[]> {
  const res = await fetch(`${BASE}/factors/catalog`);
  if (!res.ok) throw new Error(`获取因子目录失败 (${res.status})`);
  return (await res.json()) as FactorInfo[];
}

// ── 量化研究（参数化版本） ─────────────────────────────────────────────────────

export interface QuantResearchTrainRequest {
  symbol: string;
  base_timeframe?: string;
  higher_timeframes?: string[];
  limit?: number;
  validation: {
    train_size: number;
    test_size: number;
    step_size: number;
    embargo_size?: number;
  };
}

export async function runQuantResearchTrain(
  req: QuantResearchTrainRequest,
): Promise<CryptoResearchSummary> {
  const body = {
    symbol: req.symbol,
    base_timeframe: req.base_timeframe ?? "15m",
    higher_timeframes: req.higher_timeframes ?? ["1h", "4h", "1d"],
    limit: req.limit ?? 300,
    validation: {
      train_size: req.validation.train_size,
      test_size: req.validation.test_size,
      step_size: req.validation.step_size,
      embargo_size: req.validation.embargo_size ?? 2,
    },
  };
  const res = await fetch(`${BASE}/crypto/research/train`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`训练失败 (${res.status}): ${await res.text()}`);
  return (await res.json()) as CryptoResearchSummary;
}

export interface QuantResearchOptimizeRequest {
  symbol: string;
  base_timeframe?: string;
  higher_timeframes?: string[];
  limit?: number;
  param_grid: Record<string, number[]>;
}

export async function runQuantResearchOptimize(
  req: QuantResearchOptimizeRequest,
): Promise<CryptoResearchOptimizationSummary> {
  const body = {
    symbol: req.symbol,
    base_timeframe: req.base_timeframe ?? "15m",
    higher_timeframes: req.higher_timeframes ?? ["1h", "4h", "1d"],
    limit: req.limit ?? 300,
    param_grid: req.param_grid,
  };
  const res = await fetch(`${BASE}/crypto/research/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`优化失败 (${res.status}): ${await res.text()}`);
  return (await res.json()) as CryptoResearchOptimizationSummary;
}

// ── AutoPilot Pipeline ──────────────────────────────────────────────────────

export interface PipelineRunRequest {
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
}

export interface PipelineStepState {
  name: string;
  label: string;
  status: "pending" | "running" | "done" | "error" | "skipped";
  message: string;
}

export interface PipelineWindowMetric {
  window: number;
  accuracy: number;
  strategy_return: number;
  train_size: number;
  test_size: number;
}

export interface PipelineResult {
  feature_count?: number;
  validation_windows?: number;
  mean_accuracy?: number;
  mean_strategy_return?: number;
  latest_class_signal?: number;
  feature_importance?: Record<string, number>;
  window_metrics?: PipelineWindowMetric[];
  market_regime?: string;
  reversal_probability?: number;
  reversal_signal?: string;
  reversal_evidence?: string[];
  recommended_strategy_ids?: string[];
  signal_action?: string;
  signal_confidence?: number;
  signal_published?: boolean;
}

export interface PipelineJobState {
  job_id: string;
  status: "pending" | "running" | "done" | "error";
  current_step: string;
  steps: PipelineStepState[];
  error: string;
  result: PipelineResult;
  created_at: string;
  finished_at: string;
}

export async function startPipeline(req: PipelineRunRequest): Promise<{ job_id: string }> {
  const r = await fetch("/api/pipeline/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ job_id: string }>;
}

export async function getPipelineJob(jobId: string): Promise<PipelineJobState> {
  const r = await fetch(`/api/pipeline/jobs/${jobId}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<PipelineJobState>;
}
