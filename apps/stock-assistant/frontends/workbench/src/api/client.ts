/**
 * QuantPilot API client — 封装所有后端接口调用.
 * 使用 Vite dev-proxy：/api/* → http://127.0.0.1:8001/*
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

// ── Risk Engine（phaseF.1.5）─────────────────────────────────────────────────

export type VolRegime = "low" | "normal" | "high" | "crisis";
export type DecayAlertLevel = "green" | "yellow" | "red";
export type VarMethod = "historical" | "parametric" | "both";

export interface VolTargetResult {
  realized_vol: number;
  target_vol: number;
  scale_factor: number;
  regime: VolRegime;
}

export interface SharpeDecayResult {
  recent_sharpe: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number;
  alert_level: DecayAlertLevel;
  n_baseline_samples: number;
}

export interface VarResult {
  n_samples: number;
  worst_loss: number;
  method: VarMethod;
  var_95?: number;
  var_99?: number;
  cvar_95?: number;
  cvar_99?: number;
  parametric_var_95?: number;
  parametric_var_99?: number;
}

export interface RiskSummaryResult {
  n_samples: number;
  vol_target: VolTargetResult;
  sharpe_decay: SharpeDecayResult | null;
  var: VarResult;
}

export interface KellyResult {
  full_kelly: number;
  fractional_kelly: number;
  capped_kelly: number;
  mode: "binary" | "returns";
  fraction: number;
  cap: number;
}

async function postRisk<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}/risk/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<T>;
}

export function fetchRiskSummary(returns: number[]): Promise<RiskSummaryResult> {
  return postRisk<RiskSummaryResult>("summary", { returns });
}

export function fetchRiskKellyBinary(
  winRate: number,
  payoffRatio: number,
  fraction = 0.25,
  cap = 0.25,
): Promise<KellyResult> {
  return postRisk<KellyResult>("kelly", {
    mode: "binary",
    win_rate: winRate,
    payoff_ratio: payoffRatio,
    fraction,
    cap,
  });
}

export function fetchRiskKellyFromReturns(
  returns: number[],
  fraction = 0.25,
  cap = 0.25,
): Promise<KellyResult> {
  return postRisk<KellyResult>("kelly", {
    mode: "returns",
    returns,
    fraction,
    cap,
  });
}

// ── Crypto Derivatives（phaseF.1.13）────────────────────────────────────────

export interface FundingRateLite {
  exchange: "binance" | "okx";
  symbol: string;
  raw_symbol: string;
  funding_rate: number;
  next_funding_time: string | null;
  timestamp: string;
}

export interface OpenInterestLite {
  exchange: "binance" | "okx";
  symbol: string;
  raw_symbol: string;
  open_interest: number;
  open_interest_value: number | null;
  timestamp: string;
}

export interface CryptoDerivsSnapshot {
  asset: string;
  timestamp: string;
  funding: { binance: FundingRateLite | null; okx: FundingRateLite | null };
  open_interest: { binance: OpenInterestLite | null; okx: OpenInterestLite | null };
  errors: Record<string, string>;
}

export interface FundingStats {
  mean: number;
  std: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

export interface FundingExtremeSignal {
  z_score: number;
  percentile: number;
  signal: "contrarian_short" | "contrarian_long" | "neutral";
}

export interface FundingStatsResult {
  stats: FundingStats;
  n_samples: number;
  signal: FundingExtremeSignal | null;
}

export interface ETFFlowExtremeSignal {
  z_score: number;
  percentile: number;
  signal: "large_inflow" | "large_outflow" | "neutral";
}

export interface ETFFlowStatsResult {
  stats: FundingStats & { n_samples: number };
  signal: ETFFlowExtremeSignal | null;
}

async function postCryptoDerivs<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}/crypto-derivs/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<T>;
}

export function fetchCryptoDerivsSnapshot(asset = "BTC"): Promise<CryptoDerivsSnapshot> {
  return postCryptoDerivs<CryptoDerivsSnapshot>("snapshot", { asset });
}

export function fetchFundingStats(
  history: number[],
  current: number | null = null,
  zThreshold = 2.0,
): Promise<FundingStatsResult> {
  return postCryptoDerivs<FundingStatsResult>("funding-stats", {
    history,
    current,
    z_threshold: zThreshold,
  });
}

export function fetchETFFlowStats(
  history: number[],
  current: number | null = null,
  zThreshold = 2.0,
): Promise<ETFFlowStatsResult> {
  return postCryptoDerivs<ETFFlowStatsResult>("etf-flow-stats", {
    history,
    current,
    z_threshold: zThreshold,
  });
}

// ── GEX (Dealer Gamma Exposure) ──────────────────────────────────────────────

export interface GEXByStrike {
  strike: number;
  call_oi: number;
  put_oi: number;
  call_gex: number;
  put_gex: number;
  net_gex: number;
  gamma: number;
  dte: number;
}

export interface GEXSnapshot {
  ticker: string;
  spot: number;
  snapshot_time: string;
  gex_by_strike: GEXByStrike[];
  net_gex_total: number;
  gamma_flip_level: number | null;
  major_magnet: number | null;
  high_vol_trigger: number | null;
}

export interface GEXLevels {
  ticker: string;
  spot: number;
  snapshot_time: string;
  net_gex_total: number;
  gamma_flip_level: number | null;
  major_magnet: number | null;
  high_vol_trigger: number | null;
}

async function getGex<T>(path: string, params: Record<string, string | number>): Promise<T> {
  const qs = new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)]),
  ).toString();
  const r = await fetch(`${BASE}/options/gex/${path}?${qs}`);
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<T>;
}

export function fetchGEXSnapshot(
  ticker = "SPY",
  maxDte = 45,
  minOi = 10,
): Promise<GEXSnapshot> {
  return getGex<GEXSnapshot>("snapshot", { ticker, max_dte: maxDte, min_oi: minOi });
}

export function fetchGEXLevels(
  ticker = "SPY",
  maxDte = 45,
  minOi = 10,
): Promise<GEXLevels> {
  return getGex<GEXLevels>("levels", { ticker, max_dte: maxDte, min_oi: minOi });
}

// ── SEC 事件流（8-K diff + Form 4 集群）────────────────────────────────────

export interface SECEightKItem {
  item_number: string;
  item_title: string;
  text_snippet: string;
}

export interface SECParagraphDiff {
  diff_type: "added" | "removed" | "modified" | "unchanged";
  old_text: string | null;
  new_text: string | null;
  similarity: number;
}

export interface SECItemDiff {
  item_number: string;
  item_title: string;
  has_material_change: boolean;
  change_score: number;
  paragraphs: SECParagraphDiff[];
}

export interface SECDiffSummary {
  has_diff: boolean;
  has_material_change?: boolean;
  overall_change_score?: number;
  changed_items?: string[];
}

export interface SECInsiderTransaction {
  insider_name: string;
  insider_title: string;
  transaction_date: string;
  transaction_type: string;
  shares: number;
  price_per_share: number;
  total_value: number;
  is_10b5_1_plan: boolean;
}

export interface SECInsiderCluster {
  window_start: string;
  window_end: string;
  insider_count: number;
  total_value: number;
  avg_price: number;
  signal_strength: number;
  key_roles: string[];
  transactions: SECInsiderTransaction[];
}

export interface SECSummary {
  ticker: string;
  generated_at: string;
  latest_8k: {
    filed_date?: string;
    accession_number?: string;
    items?: SECEightKItem[];
  };
  "8k_diff": SECDiffSummary;
  insider_clusters: SECInsiderCluster[];
}

export async function fetchSECSummary(ticker: string): Promise<SECSummary> {
  const r = await fetch(`${BASE}/sec/summary?ticker=${encodeURIComponent(ticker)}`);
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<SECSummary>;
}

// ---------------------------------------------------------------------------
// TLH（税务亏损收割）类型定义（Phase F.3）
// ---------------------------------------------------------------------------

export interface TaxLotInput {
  ticker: string;
  quantity: number;
  cost_basis: number;
  acquisition_date: string; // "YYYY-MM-DD"
  lot_id?: string;
}

export interface TLHCandidate {
  ticker: string;
  lot_id: string;
  quantity: number;
  cost_basis: number;
  acquisition_date: string;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  holding_days: number;
  is_long_term: boolean;
  replacement_tickers: string[];
  wash_sale_risk: boolean;
}

export interface TLHScanResponse {
  candidates: TLHCandidate[];
  estimated_tax_saving: number;
  generated_at: string;
}

export interface TLHReplacementResponse {
  ticker: string;
  replacements: string[];
}

export async function fetchTLHScan(
  lots: TaxLotInput[],
  current_prices: Record<string, number>,
  recent_purchases?: Record<string, string>,
): Promise<TLHScanResponse> {
  const r = await fetch(`${BASE}/tlh/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lots, current_prices, recent_purchases: recent_purchases ?? {} }),
  });
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<TLHScanResponse>;
}

// ---------------------------------------------------------------------------
// 基本面信号类型（Phase F.4 — PEAD + Piotroski）
// ---------------------------------------------------------------------------

export interface EarningsSurprise {
  ticker: string;
  quarter: string;
  eps_actual: number;
  eps_estimate: number;
  eps_difference: number;
  surprise_pct: number;
}

export type SurpriseMagnitude =
  | "large_beat"
  | "beat"
  | "inline"
  | "miss"
  | "large_miss";

export interface PEADSignal {
  ticker: string;
  surprise_magnitude: SurpriseMagnitude;
  signal_strength: number;
  historical_drift_7d: number | null;
  historical_drift_30d: number | null;
  historical_drift_60d: number | null;
  latest_surprise: EarningsSurprise;
}

export interface PiotroskiScore {
  ticker: string;
  score: number;
  grade: "strong" | "moderate" | "weak";
  signals: Record<string, boolean>;
  as_of_date: string;
  interpretation: string;
}

export interface FundamentalSummary {
  ticker: string;
  pead: PEADSignal | null;
  piotroski: PiotroskiScore | null;
}

export async function fetchFundamentalSummary(
  ticker: string,
): Promise<FundamentalSummary> {
  const r = await fetch(
    `${BASE}/fundamental/summary?ticker=${encodeURIComponent(ticker)}`,
  );
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<FundamentalSummary>;
}

// ---------------------------------------------------------------------------
// Quant Signals — Beneish M-Score + Russell Rebalancing Preview (Phase F.5)
// ---------------------------------------------------------------------------

export interface BeneishMScoreData {
  ticker: string;
  m_score: number;
  risk_level: "safe" | "grey" | "manipulator";
  ratios: Record<string, number>;
  interpretation: string;
  as_of_date: string;
}

export interface RussellMembershipData {
  ticker: string;
  market_cap_usd: number;
  estimated_rank: number | null;
  current_index:
    | "Russell 1000"
    | "Russell 2000"
    | "Outside Russell 3000"
    | "Unknown";
  proximity_score: number;
  rebalance_signal:
    | "likely_add_1000"
    | "likely_drop_1000"
    | "likely_add_2000"
    | "likely_drop_2000"
    | "stable"
    | "unknown";
}

export interface QuantSignalsSummary {
  ticker: string;
  beneish: BeneishMScoreData | null;
  russell: RussellMembershipData | null;
}

export async function fetchQuantSignalsSummary(
  ticker: string,
): Promise<QuantSignalsSummary> {
  const r = await fetch(
    `${BASE}/quant-signals/summary?ticker=${encodeURIComponent(ticker)}`,
  );
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<QuantSignalsSummary>;
}

// ---------------------------------------------------------------------------
// EPS Revision Momentum — analyst estimate revisions (Phase F.6)
// ---------------------------------------------------------------------------

export type RevisionDirection =
  | "strong_upgrade"
  | "upgrade"
  | "neutral"
  | "downgrade"
  | "strong_downgrade";

export interface EpsRevisionPeriodData {
  period: string;
  period_label: string;
  up_7d: number;
  down_7d: number;
  up_30d: number;
  down_30d: number;
  revision_score_7d: number;
  revision_score_30d: number;
  direction: RevisionDirection;
}

export interface AnalystTargetsData {
  current_price: number | null;
  target_mean: number | null;
  target_median: number | null;
  target_high: number | null;
  target_low: number | null;
  upside_pct: number | null;
}

export interface EpsRevisionMomentumData {
  ticker: string;
  periods: EpsRevisionPeriodData[];
  targets: AnalystTargetsData | null;
  overall_direction: RevisionDirection;
  as_of_date: string;
}

export async function fetchEpsRevisionSummary(
  ticker: string,
): Promise<EpsRevisionMomentumData> {
  const r = await fetch(
    `${BASE}/eps-revision/summary?ticker=${encodeURIComponent(ticker)}`,
  );
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<EpsRevisionMomentumData>;
}

// ---------------------------------------------------------------------------
// Token Unlock Calendar — crypto vesting unlock events (Phase F.7)
// ---------------------------------------------------------------------------

export type UnlockSignal =
  | "high_risk"
  | "moderate_risk"
  | "low_risk"
  | "post_unlock_rebound";

export interface TokenUnlockEventData {
  protocol: string;
  symbol: string;
  unlock_date: string;
  days_until_unlock: number;
  unlock_tokens: number;
  unlock_usd: number | null;
  unlock_pct_circulating: number;
  category: string;
  sell_pressure_score: number;
  signal: UnlockSignal;
}

export interface TokenUnlockCalendarData {
  as_of_date: string;
  events: TokenUnlockEventData[];
  total_events: number;
  high_risk_count: number;
}

export async function fetchTokenUnlocks(
  days = 30,
): Promise<TokenUnlockCalendarData> {
  const r = await fetch(`${BASE}/token-unlocks/upcoming?days=${days}`);
  if (!r.ok) {
    const text = await r.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail ?? text);
    } catch {
      throw new Error(text || `HTTP ${r.status}`);
    }
  }
  return r.json() as Promise<TokenUnlockCalendarData>;
}
