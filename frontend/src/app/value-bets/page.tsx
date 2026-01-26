import ValueBetsLive from "@/components/ValueBetsLive";

async function fetchInitialValueBets() {
  const baseUrl = process.env.API_BASE_URL;
  try {
    const res = await fetch(`${baseUrl}/value-bets`, {
      cache: "no-store",
      next: { revalidate: 0 },
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function ValueBetsPage() {
  const initialBets = await fetchInitialValueBets();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">💰 Value Bets</h1>
        <p className="text-gray-600">
          Opportunità di betting dove il nostro modello rileva un edge positivo
          rispetto alle quote dei bookmaker.
        </p>
      </div>

      {/* Info cards */}
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-sm text-gray-500 mb-1">Edge Minimo</div>
          <div className="text-2xl font-bold text-gray-900">3%</div>
          <div className="text-xs text-gray-500">Soglia per value bet</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-sm text-gray-500 mb-1">Aggiornamento</div>
          <div className="text-2xl font-bold text-gray-900">15s</div>
          <div className="text-xs text-gray-500">Polling automatico</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <div className="text-sm text-gray-500 mb-1">Value Bets Attive</div>
          <div className="text-2xl font-bold text-blue-600">
            {initialBets.length}
          </div>
          <div className="text-xs text-gray-500">In questo momento</div>
        </div>
      </div>

      {/* Value bets table */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <ValueBetsLive initialBets={initialBets} pollIntervalMs={15000} />
      </div>

      {/* Disclaimer */}
      <div className="mt-8 bg-amber-50 border border-amber-200 rounded-xl p-4">
        <h3 className="font-semibold text-amber-900 mb-2">⚠️ Disclaimer</h3>
        <p className="text-sm text-amber-800">
          Le value bet sono calcolate in base al nostro modello ML e non
          garantiscono profitto. Il betting sportivo comporta rischi finanziari.
          Gioca responsabilmente e solo con denaro che puoi permetterti di
          perdere.
        </p>
      </div>
    </div>
  );
}
