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
