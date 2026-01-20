import Link from "next/link";

// Card component
function FeatureCard({
  href,
  icon,
  title,
  description,
  color,
}: {
  href: string;
  icon: string;
  title: string;
  description: string;
  color: string;
}) {
  return (
    <Link
      href={href}
      className="group block p-6 bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:shadow-lg transition-all"
    >
      <div
        className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl mb-4 ${color}`}
      >
        {icon}
      </div>
      <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 transition-colors">
        {title}
      </h3>
      <p className="mt-2 text-gray-600 text-sm">{description}</p>
    </Link>
  );
}

// Stats card
function StatCard({
  label,
  value,
  subtext,
}: {
  label: string;
  value: string;
  subtext?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="text-sm text-gray-500 uppercase tracking-wide">{label}</div>
      <div className="mt-2 text-3xl font-bold text-gray-900">{value}</div>
      {subtext && <div className="mt-1 text-sm text-gray-500">{subtext}</div>}
    </div>
  );
}

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          🎾 Tennis<span className="text-blue-600">ML</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Predizioni match di tennis basate su Machine Learning con 15+ feature
          analizzate: Elo rating, statistiche servizio, form recente e molto altro.
        </p>
      </div>

      {/* Feature cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <FeatureCard
          href="/predict"
          icon="🎯"
          title="Match Prediction"
          description="Inserisci due giocatori e ottieni la probabilità di vittoria con breakdown completo delle statistiche."
          color="bg-blue-100 text-blue-600"
        />
        <FeatureCard
          href="/value-bets"
          icon="💰"
          title="Value Bets"
          description="Trova opportunità di betting dove le nostre probabilità superano quelle implicite dei bookmaker."
          color="bg-green-100 text-green-600"
        />
        <FeatureCard
          href="/predict"
          icon="📊"
          title="Confronto Statistiche"
          description="Analisi dettagliata head-to-head: Elo, form, superficie, servizio e molto altro."
          color="bg-purple-100 text-purple-600"
        />
      </div>

      {/* Feature list */}
      <div className="bg-white rounded-xl border border-gray-200 p-8 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          📈 Feature del Modello
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-blue-500">⚡</span> Rating & Ranking
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Elo rating per superficie</li>
              <li>• ATP/WTA ranking</li>
              <li>• Head-to-head storico</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-green-500">📈</span> Form & Condizione
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Win rate ultimi 5/10 match</li>
              <li>• Giorni di riposo</li>
              <li>• Carico di lavoro (match 30gg)</li>
              <li>• Età giocatore</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-orange-500">🎾</span> Statistiche Servizio
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Percentuale ace</li>
              <li>• Double faults</li>
              <li>• Prima di servizio</li>
              <li>• Break point salvati</li>
            </ul>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center">
        <Link
          href="/predict"
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/25"
        >
          🎯 Inizia una Predizione
        </Link>
      </div>
    </div>
  );
}
