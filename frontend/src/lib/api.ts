import { PredictRequest, PredictResponse, ValueBet } from "@/types";
import { API_BASE_URL } from "./config";

/**
 * API Error con dettagli
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Fetch wrapper con error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE_URL}${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const data = await res.json();
      detail = data.detail || data.message;
    } catch {
      detail = await res.text();
    }
    throw new ApiError(
      `API Error: ${res.status}`,
      res.status,
      detail
    );
  }

  return res.json();
}

/**
 * Predizione match
 */
export async function predictMatch(
  payload: PredictRequest
): Promise<PredictResponse> {
  return fetchApi<PredictResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Fetch value bets (via Next.js API route per evitare CORS)
 */
export async function fetchValueBets(): Promise<ValueBet[]> {
  const res = await fetch("/api/value-bets", { cache: "no-store" });
  if (!res.ok) {
    throw new ApiError("Failed to fetch value bets", res.status);
  }
  return res.json();
}

/**
 * Health check del backend
 */
export async function checkHealth(): Promise<{
  status: string;
  model_loaded: boolean;
  features: string[];
}> {
  return fetchApi("/model/health");
}

/**
 * Info sul modello
 */
export async function getModelInfo(): Promise<{
  model_path: string;
  features: string[];
  model_type: string;
  base_estimator?: string;
}> {
  return fetchApi("/model/info");
}
