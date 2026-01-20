"use client";

import PredictForm from "@/components/PredictForm";

export default function PredictPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🎯 Match Prediction
        </h1>
        <p className="text-gray-600">
          Inserisci i nomi dei giocatori per ottenere la predizione basata su ML
        </p>
      </div>

      {/* Form Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <PredictForm />
      </div>

      {/* Tips */}
      <div className="mt-8 bg-blue-50 rounded-xl p-6">
        <h3 className="font-semibold text-blue-900 mb-3">💡 Suggerimenti</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>
            • Usa il nome completo del giocatore come appare nei dati ATP (es.
            &quot;Novak Djokovic&quot;, &quot;Carlos Alcaraz&quot;)
          </li>
          <li>
            • La superficie influenza significativamente le predizioni - Nadal su
            Clay vs Hard può avere probabilità molto diverse
          </li>
          <li>
            • Aggiungi le quote dei bookmaker per vedere se c&apos;è una value bet
          </li>
          <li>
            • Il modello considera 15+ feature tra cui Elo, form recente, H2H e
            statistiche servizio
          </li>
        </ul>
      </div>
    </div>
  );
}
