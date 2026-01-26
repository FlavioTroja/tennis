// API Configuration

// Backend URL - per chiamate client-side
export const API_BASE_URL = process.env.API_BASE_URL;

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
