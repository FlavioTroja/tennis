"use client";

import { useState } from "react";
import { predictMatch } from "@/lib/api";
import {
  PredictResponse,
  PredictRequest,
  SURFACES,
  Surface,
} from "@/types";
import PlayerAutocomplete from "./PlayerAutocomplete";

// Componente per mostrare una statistica
function StatRow({
  label,
  valueA,
  valueB,
  format = "number",
  higherIsBetter = true,
}: {
  label: string;
  valueA: number;
  valueB: number;
  format?: "number" | "percent" | "rank";
  higherIsBetter?: boolean;
}) {
  const formatValue = (v: number) => {
    if (format === "percent") return `${(v * 100).toFixed(1)}%`;
    if (format === "rank") return `#${v}`;
    return v.toFixed(1);
  };

  const aWins = higherIsBetter ? valueA > valueB : valueA < valueB;
  const bWins = higherIsBetter ? valueB > valueA : valueB < valueA;

  return (
    <div className="grid grid-cols-3 gap-2 py-2 border-b border-gray-100 text-sm">
      <div className={`text-right ${aWins ? "font-semibold text-green-600" : ""}`}>
        {formatValue(valueA)}
      </div>
      <div className="text-center text-gray-500">{label}</div>
      <div className={`text-left ${bWins ? "font-semibold text-green-600" : ""}`}>
        {formatValue(valueB)}
      </div>
    </div>
  );
}

// Componente per confronto giocatori
function PlayerComparison({
  result,
}: {
  result: PredictResponse;
}) {
  const a = result.player_a_details;
  const b = result.player_b_details;

  return (
    <div className="mt-6 border rounded-lg overflow-hidden">
      {/* Header con probabilità */}
      <div className="grid grid-cols-3 bg-gray-50 p-4">
        <div className="text-center">
          <div className="font-bold text-lg">{result.player_a}</div>
          <div className="text-3xl font-bold text-blue-600">
            {(result.prob_a * 100).toFixed(1)}%
          </div>
        </div>
        <div className="flex items-center justify-center text-gray-400 text-xl">
          vs
        </div>
        <div className="text-center">
          <div className="font-bold text-lg">{result.player_b}</div>
          <div className="text-3xl font-bold text-red-600">
            {(result.prob_b * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Probability bar */}
      <div className="h-2 flex">
        <div
          className="bg-blue-500 transition-all duration-500"
          style={{ width: `${result.prob_a * 100}%` }}
        />
        <div
          className="bg-red-500 transition-all duration-500"
          style={{ width: `${result.prob_b * 100}%` }}
        />
      </div>

      {/* Stats comparison */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-700 mb-2 text-center">
          📊 Confronto Statistiche
        </h3>

        <StatRow label="Elo" valueA={a.elo} valueB={b.elo} />
        <StatRow label="Ranking" valueA={a.rank} valueB={b.rank} format="rank" higherIsBetter={false} />
        <StatRow label="Form (5)" valueA={a.recent_5} valueB={b.recent_5} format="percent" />
        <StatRow label="Form (10)" valueA={a.recent_10} valueB={b.recent_10} format="percent" />
        <StatRow label="Surface WR" valueA={a.surface_wr} valueB={b.surface_wr} format="percent" />
        <StatRow label="H2H Wins" valueA={a.h2h_wins} valueB={b.h2h_wins} />
        
        {a.age > 0 && (
          <>
            <div className="mt-4 mb-2 text-xs text-gray-400 text-center uppercase tracking-wide">
              Condizione Fisica
            </div>
            <StatRow label="Età" valueA={a.age} valueB={b.age} higherIsBetter={false} />
            <StatRow label="Giorni riposo" valueA={a.days_rest} valueB={b.days_rest} />
            <StatRow label="Match 30gg" valueA={a.matches_30d} valueB={b.matches_30d} higherIsBetter={false} />
          </>
        )}

        {a.ace_pct > 0 && (
          <>
            <div className="mt-4 mb-2 text-xs text-gray-400 text-center uppercase tracking-wide">
              Statistiche Servizio
            </div>
            <StatRow label="Ace %" valueA={a.ace_pct} valueB={b.ace_pct} format="percent" />
            <StatRow label="DF %" valueA={a.df_pct} valueB={b.df_pct} format="percent" higherIsBetter={false} />
            <StatRow label="1st Serve %" valueA={a.first_serve_pct} valueB={b.first_serve_pct} format="percent" />
            <StatRow label="1st Won %" valueA={a.first_won_pct} valueB={b.first_won_pct} format="percent" />
            <StatRow label="BP Save %" valueA={a.bp_save_pct} valueB={b.bp_save_pct} format="percent" />
          </>
        )}
      </div>

      {/* Value bet indicator */}
      {result.value_bet && result.value_bet !== "NO VALUE" && (
        <div className="bg-green-50 border-t border-green-200 p-4">
          <div className="text-center">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full font-semibold">
              💰 {result.value_bet}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PredictForm() {
  const [playerA, setPlayerA] = useState("");
  const [playerB, setPlayerB] = useState("");
  const [surface, setSurface] = useState<Surface>("Hard");
  const [oddsA, setOddsA] = useState<string>("");
  const [oddsB, setOddsB] = useState<string>("");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: PredictRequest = {
        player_a: playerA.trim(),
        player_b: playerB.trim(),
        surface,
      };

      // Aggiungi odds se presenti
      if (oddsA) payload.odds_a = parseFloat(oddsA);
      if (oddsB) payload.odds_b = parseFloat(oddsB);

      const res = await predictMatch(payload);
      setResult(res);
    } catch (err: any) {
      setError(err.detail || err.message || "Errore nella predizione");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function swapPlayers() {
    setPlayerA(playerB);
    setPlayerB(playerA);
    setOddsA(oddsB);
    setOddsB(oddsA);
    setResult(null);
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        {/* Player inputs */}
        <div className="grid grid-cols-[1fr,auto,1fr] gap-2 items-end">
          <PlayerAutocomplete
            label="Player A"
            value={playerA}
            onChange={setPlayerA}
            placeholder="es. Novak Djokovic"
          />

          <button
            type="button"
            onClick={swapPlayers}
            className="mb-1 p-3 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Scambia giocatori"
          >
            ⇄
          </button>

          <PlayerAutocomplete
            label="Player B"
            value={playerB}
            onChange={setPlayerB}
            placeholder="es. Carlos Alcaraz"
          />
        </div>

        {/* Surface selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Superficie
          </label>
          <div className="grid grid-cols-3 gap-2">
            {SURFACES.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setSurface(s.value)}
                className={`p-3 rounded-lg border-2 transition-all ${
                  surface === s.value
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <span className="text-xl">{s.emoji}</span>
                <span className="ml-2">{s.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Odds inputs (optional) */}
        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Quote bookmaker (opzionale - per calcolo value bet)
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <input
                type="number"
                step="0.01"
                min="1"
                className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Quota Player A (es. 1.65)"
                value={oddsA}
                onChange={(e) => setOddsA(e.target.value)}
              />
            </div>
            <div>
              <input
                type="number"
                step="0.01"
                min="1"
                className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Quota Player B (es. 2.30)"
                value={oddsB}
                onChange={(e) => setOddsB(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading || !playerA || !playerB}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-lg font-semibold text-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Calcolo in corso...
            </span>
          ) : (
            "🎾 Calcola Predizione"
          )}
        </button>
      </form>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <strong>Errore:</strong> {error}
        </div>
      )}

      {/* Results */}
      {result && <PlayerComparison result={result} />}
    </div>
  );
}
