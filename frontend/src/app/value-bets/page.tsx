import ValueBetCard from "@/components/ValueBetCard";
import { fetchValueBets } from "@/lib/api";

export default async function ValueBetsPage() {
  const bets = await fetchValueBets();

  return (
    <main className="max-w-4xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-bold">🎾 Value Bets</h1>

      {bets.length === 0 && (
        <p className="text-gray-500">Nessuna value bet disponibile</p>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {bets.map((bet: any) => (
          <ValueBetCard key={bet.match_id} bet={bet} />
        ))}
      </div>
    </main>
  );
}
