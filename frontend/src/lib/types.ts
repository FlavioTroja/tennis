export interface PredictRequest {
  player_a: string;
  player_b: string;
  surface: string;
}

export interface PredictResponse {
  player_a: string;
  player_b: string;
  surface: string;
  player_a_win_probability: number;
  player_b_win_probability: number;
  elo_diff: number;
}

export interface ValueBet {
  match_id: string;
  commence_time: string;

  player_a: string;
  player_b: string;
  surface: string;

  prob_a: number;
  prob_b: number;

  odds_a: number;
  odds_b: number;

  edge_a: number;
  edge_b: number;

  bet_side: "A" | "B";
}
