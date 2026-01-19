import ValueBetsLive from "@/components/ValueBetsLive";

// NB: qui NON possiamo usare fetchValueBets() perché usa /api/value-bets
// quindi chiamiamo direttamente il backend server-side oppure il proxy con absolute URL.
// Per semplicità: chiamata server-side al backend.
async function fetchInitialValueBets() {
  const baseUrl = process.env.API_BASE_URL || "http://localhost:8000";
  const res = await fetch(`${baseUrl}/value-bets`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export default async function ValueBetsPage() {
  const initialBets = await fetchInitialValueBets();

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-6">🎾 Value Bets</h1>
      <ValueBetsLive initialBets={initialBets} pollIntervalMs={15000} />
    </main>
  );
}
