"use client";

import { predictMatch } from "@/lib/api";
import { PredictResponse } from "@/lib/types";
import { useState } from "react";

export default function PredictForm() {
  const [playerA, setPlayerA] = useState("");
  const [playerB, setPlayerB] = useState("");
  const [surface, setSurface] = useState("hard");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await predictMatch({
        player_a: playerA,
        player_b: playerB,
        surface,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message ?? "Errore");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input
        className="w-full border p-2 rounded"
        placeholder="Player A"
        value={playerA}
        onChange={(e) => setPlayerA(e.target.value)}
        required
      />

      <input
        className="w-full border p-2 rounded"
        placeholder="Player B"
        value={playerB}
        onChange={(e) => setPlayerB(e.target.value)}
        required
      />

      <select
        className="w-full border p-2 rounded"
        value={surface}
        onChange={(e) => setSurface(e.target.value)}
      >
        <option value="hard">Hard</option>
        <option value="clay">Clay</option>
        <option value="grass">Grass</option>
      </select>

      <button
        className="bg-black text-white px-4 py-2 rounded w-full"
        disabled={loading}
      >
        {loading ? "Calcolo..." : "Predict"}
      </button>

      {error && <p className="text-red-600">{error}</p>}

      {result && (
        <div className="border p-4 rounded mt-4">
          <p>
            <strong>{result.player_a}</strong>:{" "}
            {(result.player_a_win_probability * 100).toFixed(1)}%
          </p>
          <p>
            <strong>{result.player_b}</strong>:{" "}
            {(result.player_b_win_probability * 100).toFixed(1)}%
          </p>
          <p className="text-sm text-gray-500">Elo diff: {result.elo_diff}</p>
        </div>
      )}
    </form>
  );
}
