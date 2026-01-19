import { ValueBet } from "@/types/value-bet";

interface Props {
  bets: ValueBet[];
}

export default function ValueBetTable({ bets }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th>Match</th>
            <th>Side</th>
            <th>Edge</th>
            <th>Odds</th>
            <th>Start</th>
          </tr>
        </thead>

        <tbody>
          {bets.map((b) => (
            <tr
              key={`${b.match_id}-${b.bet_side}`}
              className={[
                "border-b transition-colors",
                b._isNew && "bg-green-50 animate-pulse",
                b._edgeChanged && "bg-yellow-50",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <td>
                {b.player_a} vs {b.player_b}
              </td>
              <td className="font-bold">{b.bet_side}</td>
              <td>{(b.bet_side === "A" ? b.edge_a : b.edge_b).toFixed(3)}</td>
              <td>{(b.bet_side === "A" ? b.odds_a : b.odds_b).toFixed(2)}</td>
              <td>{new Date(b.commence_time).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
