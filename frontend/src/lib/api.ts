import { PredictRequest, PredictResponse } from "@/types/predict";
import { ValueBet } from "@/types/value-bet";
import { API_BASE_URL } from "./config";

export async function predictMatch(
  payload: PredictRequest
): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err);
  }

  return res.json();
}

export async function fetchValueBets(): Promise<ValueBet[]> {
  const res = await fetch(`${API_BASE_URL}/value-bets`, {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch value bets");
  }

  return res.json();
}
