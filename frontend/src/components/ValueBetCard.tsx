import EdgeBadge from "./EdgeBadge";

interface Props {
  bet: any;
}

export default function ValueBetCard({ bet }: Props) {
  const isA = bet.bet_side === "A";

  const pickedPlayer = isA ? bet.player_a : bet.player_b;
  const pickedEdge = isA ? bet.edge_a : bet.edge_b;
  const pickedOdds = isA ? bet.odds_a : bet.odds_b;
  const pickedProb = isA ? bet.prob_a : bet.prob_b;

  return (
    <div className="rounded-xl border p-4 shadow-sm bg-white space-y-2">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold">
          {bet.player_a} vs {bet.player_b}
        </h3>
        <EdgeBadge edge={pickedEdge} />
      </div>

      <p className="text-sm text-gray-500">
        {new Date(bet.commence_time).toLocaleString()}
      </p>

      <div className="mt-2">
        <p className="text-sm">
          🎯 Pick: <strong>{pickedPlayer}</strong>
        </p>
        <p className="text-sm">
          Prob: {(pickedProb * 100).toFixed(1)}% · Odds: {pickedOdds}
        </p>
      </div>
    </div>
  );
}
