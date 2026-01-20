import {
  ValueBet,
  getEdge,
  getOdds,
  getProb,
  getBetPlayer,
  getEdgeLevel,
  EDGE_COLORS,
} from "@/types/value-bet";

interface Props {
  bets: ValueBet[];
}

function EdgeBadge({ edge }: { edge: number }) {
  const level = getEdgeLevel(edge);
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${EDGE_COLORS[level]}`}
    >
      {(edge * 100).toFixed(1)}%
    </span>
  );
}

export default function ValueBetTable({ bets }: Props) {
  if (bets.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <div className="text-4xl mb-4">🔍</div>
        <p>Nessuna value bet disponibile al momento</p>
        <p className="text-sm mt-2">
          Le value bet appaiono quando il nostro modello rileva un edge ≥ 3%
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-semibold text-gray-600 text-sm">
              Match
            </th>
            <th className="text-left py-3 px-4 font-semibold text-gray-600 text-sm">
              Bet On
            </th>
            <th className="text-center py-3 px-4 font-semibold text-gray-600 text-sm">
              Prob ML
            </th>
            <th className="text-center py-3 px-4 font-semibold text-gray-600 text-sm">
              Odds
            </th>
            <th className="text-center py-3 px-4 font-semibold text-gray-600 text-sm">
              Edge
            </th>
            <th className="text-right py-3 px-4 font-semibold text-gray-600 text-sm">
              Inizio
            </th>
          </tr>
        </thead>

        <tbody>
          {bets.map((bet) => {
            const edge = getEdge(bet);
            const odds = getOdds(bet);
            const prob = getProb(bet);
            const betPlayer = getBetPlayer(bet);

            return (
              <tr
                key={`${bet.match_id}-${bet.bet_side}`}
                className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  bet._isNew ? "bg-green-50 animate-pulse" : ""
                } ${bet._edgeChanged ? "bg-yellow-50" : ""}`}
              >
                <td className="py-4 px-4">
                  <div className="font-medium text-gray-900">
                    {bet.player_a}
                  </div>
                  <div className="text-gray-500 text-sm">
                    vs {bet.player_b}
                  </div>
                </td>

                <td className="py-4 px-4">
                  <span className="inline-flex items-center gap-2">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                        bet.bet_side === "A" ? "bg-blue-500" : "bg-red-500"
                      }`}
                    >
                      {bet.bet_side}
                    </span>
                    <span className="font-medium">{betPlayer}</span>
                  </span>
                </td>

                <td className="py-4 px-4 text-center">
                  <span className="font-mono">{(prob * 100).toFixed(1)}%</span>
                </td>

                <td className="py-4 px-4 text-center">
                  <span className="font-mono font-semibold">{odds.toFixed(2)}</span>
                </td>

                <td className="py-4 px-4 text-center">
                  <EdgeBadge edge={edge} />
                </td>

                <td className="py-4 px-4 text-right text-sm text-gray-500">
                  {new Date(bet.commence_time).toLocaleDateString("it-IT", {
                    day: "2-digit",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
