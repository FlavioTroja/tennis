import ValueBetTable from "@/components/ValueBetTable";
import { fetchValueBets } from "@/lib/api";

export default async function ValueBetsPage() {
  const valueBets = await fetchValueBets();

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-6">🎾 Value Bets</h1>

      {valueBets.length === 0 ? (
        <p className="text-gray-500">Nessuna value bet disponibile</p>
      ) : (
        <ValueBetTable bets={valueBets} />
      )}
    </main>
  );
}
