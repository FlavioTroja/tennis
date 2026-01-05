import { ValueBet } from "@/types/value-bet";

interface Props {
  bets: ValueBet[];
}

export default function ValueBetTable({ bets }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border border-gray-200">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2">Match</th>
            <th className="p-2">Side</th>
            <th className="p-2">Odds</th>
            <th className="p-2">Edge</th>
            <th className="p-2">Start</th>
          </tr>
        </thead>
        <tbody>
          {bets.map((b) => (
            <tr key={b.match_id} className="border-t">
              <td className="p-2">
                {b.player_a} vs {b.player_b}
              </td>
              <td className="p-2 font-bold">{b.bet_side}</td>
              <td className="p-2">
                {b.bet_side === "A" ? b.odds_a : b.odds_b}
              </td>
              <td className="p-2 text-green-600">
                {(Math.max(b.edge_a, b.edge_b) * 100).toFixed(1)}%
              </td>
              <td className="p-2">
                {new Date(b.commence_time).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
