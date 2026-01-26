// API Configuration

// Backend URL - per chiamate client-side
// In production, use /api (nginx proxies to backend)
// In development, can override with NEXT_PUBLIC_API_BASE_URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

// Polling intervals
export const VALUE_BETS_POLL_INTERVAL = 15000; // 15 seconds

// Edge thresholds
export const MIN_EDGE_THRESHOLD = 0.03; // 3%

// Feature list (per riferimento)
export const FEATURES = [
  "elo_diff",
  "ranking_diff",
  "recent_5_diff",
  "recent_10_diff",
  "surface_diff",
  "h2h_diff",
  "fatigue_diff",
  "age_diff",
  "workload_diff",
  "ace_diff",
  "df_diff",
  "first_serve_diff",
  "first_won_diff",
  "bp_save_diff",
  "level_exp_diff",
] as const;
