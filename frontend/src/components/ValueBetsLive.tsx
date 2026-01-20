"use client";

import { useEffect, useRef, useState } from "react";
import { fetchValueBets } from "@/lib/api";
import { ValueBet } from "@/types";
import ValueBetTable from "./ValueBetTable";

type Status = "idle" | "loading" | "ok" | "error";

interface Props {
  initialBets: ValueBet[];
  pollIntervalMs?: number;
}

export default function ValueBetsLive({
  initialBets,
  pollIntervalMs = 15000,
}: Props) {
  const [bets, setBets] = useState<ValueBet[]>(initialBets);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const backoffRef = useRef(pollIntervalMs);

  async function refresh() {
    // Skip if page not visible
    if (typeof document !== "undefined" && document.visibilityState !== "visible") {
      scheduleNext();
      return;
    }

    setStatus("loading");

    try {
      const data = await fetchValueBets();
      
      setBets((prev) => {
        const prevMap = new Map(
          prev.map((b) => [`${b.match_id}_${b.bet_side}`, b])
        );

        return data.map((b) => {
          const key = `${b.match_id}_${b.bet_side}`;
          const old = prevMap.get(key);

          return {
            ...b,
            _isNew: !old,
            _edgeChanged: old
              ? Math.abs(
                  (b.bet_side === "A" ? b.edge_a : b.edge_b) -
                    (b.bet_side === "A" ? old.edge_a : old.edge_b)
                ) > 0.01
              : false,
          };
        });
      });

      setLastUpdated(new Date());
      setStatus("ok");
      setError(null);
      backoffRef.current = pollIntervalMs;
    } catch (e: any) {
      setStatus("error");
      setError(e?.message ?? "Errore di connessione");
      // Exponential backoff on error
      backoffRef.current = Math.min(backoffRef.current * 2, 60000);
    }

    scheduleNext();
  }

  function scheduleNext() {
    timerRef.current = setTimeout(refresh, backoffRef.current);
  }

  useEffect(() => {
    // Initial refresh
    refresh();

    // Refresh when tab becomes visible
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        backoffRef.current = pollIntervalMs;
        refresh();
      }
    };

    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4">
      {/* Status bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <span
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              status === "loading"
                ? "bg-gray-100 text-gray-600"
                : status === "ok"
                ? "bg-green-100 text-green-700"
                : status === "error"
                ? "bg-red-100 text-red-700"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {status === "loading" && (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
            )}
            {status === "ok" && <span className="w-2 h-2 bg-green-500 rounded-full" />}
            {status === "error" && <span className="w-2 h-2 bg-red-500 rounded-full" />}
            
            {status === "loading" && "Aggiornamento..."}
            {status === "ok" && "Live"}
            {status === "error" && "Errore"}
            {status === "idle" && "In attesa"}
          </span>

          {/* Last updated */}
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Ultimo update: {lastUpdated.toLocaleTimeString("it-IT")}
            </span>
          )}
        </div>

        {/* Refresh button */}
        <button
          onClick={() => {
            backoffRef.current = pollIntervalMs;
            refresh();
          }}
          disabled={status === "loading"}
          className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm font-medium"
        >
          <svg
            className={`w-4 h-4 ${status === "loading" ? "animate-spin" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Aggiorna
        </button>
      </div>

      {/* Error message */}
      {status === "error" && error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <strong>Errore:</strong> {error}
        </div>
      )}

      {/* Table */}
      <ValueBetTable bets={bets} />
    </div>
  );
}
