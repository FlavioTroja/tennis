// Request per predizione match
export interface PredictRequest {
  player_a: string;
  player_b: string;
  surface: "Hard" | "Clay" | "Grass";
  odds_a?: number;
  odds_b?: number;
}

// Dettagli feature per singolo giocatore
export interface PlayerFeatures {
  elo: number;
  surface_wr: number;
  recent_5: number;
  recent_10: number;
  h2h_wins: number;
  rank: number;
  days_rest: number;
  age: number;
  matches_30d: number;
  ace_pct: number;
  df_pct: number;
  first_serve_pct: number;
  first_won_pct: number;
  bp_save_pct: number;
  level_wr: number;
}

// Feature differenziali (A - B)
export interface FeaturesDiff {
  elo_diff: number;
  ranking_diff: number;
  recent_5_diff: number;
  recent_10_diff: number;
  surface_diff: number;
  h2h_diff: number;
  fatigue_diff?: number;
  age_diff?: number;
  workload_diff?: number;
  ace_diff?: number;
  df_diff?: number;
  first_serve_diff?: number;
  first_won_diff?: number;
  bp_save_diff?: number;
  level_exp_diff?: number;
}

// Response dalla API /predict
export interface PredictResponse {
  player_a: string;
  player_b: string;
  surface: string;
  prob_a: number;
  prob_b: number;
  features: FeaturesDiff;
  player_a_details: PlayerFeatures;
  player_b_details: PlayerFeatures;
  edge_a: number | null;
  edge_b: number | null;
  value_bet: string | null;
}

// Per la UI - estensione con stati
export interface PredictResult extends PredictResponse {
  timestamp: Date;
}

// Superficie con label
export const SURFACES = [
  { value: "Hard", label: "Hard Court", emoji: "🔵" },
  { value: "Clay", label: "Clay Court", emoji: "🟠" },
  { value: "Grass", label: "Grass Court", emoji: "🟢" },
] as const;

export type Surface = (typeof SURFACES)[number]["value"];
