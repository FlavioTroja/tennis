"use client";

import ValueBetTable from "@/components/ValueBetTable";
import { fetchValueBets } from "@/lib/api";
import { ValueBet } from "@/types/value-bet";
import { useEffect, useRef, useState } from "react";

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
    if (document.visibilityState !== "visible") {
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
      setError(e?.message ?? "Errore backend");
      backoffRef.current = Math.min(backoffRef.current * 2, 60000);
    }

    scheduleNext();
  }

  function scheduleNext() {
    timerRef.current = setTimeout(refresh, backoffRef.current);
  }

  useEffect(() => {
    refresh();

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
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 text-sm">
        <span
          className={[
            "px-2 py-1 rounded border",
            status === "loading" && "border-gray-400",
            status === "ok" && "border-green-600 text-green-700",
            status === "error" && "border-red-600 text-red-700",
          ].join(" ")}
        >
          {status === "loading" && "Aggiornamento…"}
          {status === "ok" && "Live"}
          {status === "error" && "Errore"}
        </span>

        {lastUpdated && (
          <span className="text-gray-500">
            Ultimo update: {lastUpdated.toLocaleTimeString()}
          </span>
        )}

        <button
          onClick={refresh}
          className="ml-auto px-3 py-1 rounded bg-black text-white"
        >
          Aggiorna ora
        </button>
      </div>

      {status === "error" && (
        <div className="p-3 border border-red-200 bg-red-50 text-red-700 rounded">
          {error}
        </div>
      )}

      {bets.length === 0 ? (
        <p className="text-gray-500">Nessuna value bet disponibile</p>
      ) : (
        <ValueBetTable bets={bets} />
      )}
    </div>
  );
}
