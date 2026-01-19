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

  // UI only
  _isNew?: boolean;
  _edgeChanged?: boolean;
}
