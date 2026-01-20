// Value bet dal backend
export interface ValueBet {
  match_id: string;
  commence_time: string;
  player_a: string;
  player_b: string;
  prob_a: number;
  prob_b: number;
  odds_a: number;
  odds_b: number;
  edge_a: number;
  edge_b: number;
  bet_side: "A" | "B";

  // UI state (aggiunto dal frontend)
  _isNew?: boolean;
  _edgeChanged?: boolean;
}

// Helpers
export function getEdge(bet: ValueBet): number {
  return bet.bet_side === "A" ? bet.edge_a : bet.edge_b;
}

export function getOdds(bet: ValueBet): number {
  return bet.bet_side === "A" ? bet.odds_a : bet.odds_b;
}

export function getProb(bet: ValueBet): number {
  return bet.bet_side === "A" ? bet.prob_a : bet.prob_b;
}

export function getBetPlayer(bet: ValueBet): string {
  return bet.bet_side === "A" ? bet.player_a : bet.player_b;
}

// Edge level per styling
export type EdgeLevel = "low" | "medium" | "high" | "very-high";

export function getEdgeLevel(edge: number): EdgeLevel {
  if (edge >= 0.10) return "very-high";
  if (edge >= 0.07) return "high";
  if (edge >= 0.05) return "medium";
  return "low";
}

export const EDGE_COLORS: Record<EdgeLevel, string> = {
  low: "text-yellow-600 bg-yellow-50",
  medium: "text-orange-600 bg-orange-50",
  high: "text-green-600 bg-green-50",
  "very-high": "text-emerald-700 bg-emerald-100",
};
