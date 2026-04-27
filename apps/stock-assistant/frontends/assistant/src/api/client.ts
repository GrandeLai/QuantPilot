/**
 * Minimal advisor API client helpers.
 */
export interface AdvisorOverviewPayload {
  net_worth: number;
  cash_ratio: number;
  positions: Array<Record<string, unknown>>;
  generated_at: string;
}

export interface AdvisorEvidence {
  source: string;
  summary: string;
  observed_at: string;
}

export interface AdvisorCard {
  type: string;
  subject: string;
  recommendation: string;
  confidence: number;
  evidence: AdvisorEvidence[];
  risk_notes: string[];
  freshness?: string;
}

export interface AdvisorCryptoResearchSummary {
  symbol: string;
  base_timeframe?: string;
  market_regime: string;
  recommended_strategy_ids: string[];
  recommended_timeframes: string[];
  parameter_search_ready: boolean;
}

export interface AdvisorCryptoOptimizationSummary {
  symbol: string;
  strategy_id: string;
  best_params: Record<string, number>;
}

async function getJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

/**
 * Fetches the portfolio overview payload for the investment assistant.
 */
export async function fetchOverview<T>(): Promise<T> {
  return getJson<T>("/api/advisor/overview");
}

/**
 * Fetches the opportunity list payload for the investment assistant.
 */
export async function fetchOpportunities<T>(): Promise<T> {
  return getJson<T>("/api/advisor/opportunities");
}

/**
 * Fetches crypto opportunity cards for a specific symbol.
 */
export async function fetchCryptoOpportunities<T>(symbol: string): Promise<T> {
  return getJson<T>(`/api/advisor/crypto/opportunities?symbol=${encodeURIComponent(symbol)}`);
}

/**
 * Fetches crypto risk cards for a specific symbol.
 */
export async function fetchCryptoRisks<T>(symbol: string): Promise<T> {
  return getJson<T>(`/api/advisor/crypto/risks?symbol=${encodeURIComponent(symbol)}`);
}

/**
 * Fetches the latest cached crypto research summary for a specific symbol.
 */
export async function fetchCryptoResearchLatest<T>(symbol: string): Promise<T> {
  return getJson<T>(
    `/api/crypto/research/latest?symbol=${encodeURIComponent(symbol)}&base_timeframe=15m`,
  );
}

/**
 * Fetches the current crypto optimization summary for a specific symbol.
 */
export async function fetchCryptoResearchOptimization<T>(symbol: string): Promise<T> {
  return getJson<T>("/api/crypto/research/optimize", {
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
}

/**
 * Fetches the latest cached crypto optimization summary for a specific symbol.
 */
export async function fetchCryptoResearchLatestOptimization<T>(symbol: string, strategyId: string): Promise<T> {
  return getJson<T>(
    `/api/crypto/research/optimize/latest?symbol=${encodeURIComponent(symbol)}&base_timeframe=15m&strategy_id=${encodeURIComponent(strategyId)}`,
  );
}
