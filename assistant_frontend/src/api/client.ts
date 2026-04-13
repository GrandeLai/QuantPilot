/**
 * Minimal advisor API client helpers.
 */
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
