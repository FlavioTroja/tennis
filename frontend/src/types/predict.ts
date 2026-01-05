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
