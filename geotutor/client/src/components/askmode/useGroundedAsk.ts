import { useCallback, useRef, useState } from "react";
import { GroundedResult } from "./types";

// Calls POST /ask-grounded on the Python brain and tracks loading stages.

// friendly progress lines only: never describe the machinery behind them
const STAGES = [
  "Reading your question…",
  "Gathering the relevant material…",
  "Working through it…",
  "Writing your answer…",
];

export function useGroundedAsk() {
  const [result, setResult] = useState<GroundedResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [stage, setStage] = useState(STAGES[0]);
  const stageTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const ask = useCallback(
    async (
      question: string,
      history: { role: string; content: string }[] = [],
      prevStrataPaths: string[] = []
    ) => {
      setIsLoading(true);
      setError(null);
      setResult(null);
      let i = 0;
      setStage(STAGES[0]);
      stageTimer.current = setInterval(() => {
        i = Math.min(i + 1, STAGES.length - 1);
        setStage(STAGES[i]);
      }, 6000);
      try {
        const apiUrl = import.meta.env.VITE_PYTHON_BRAIN_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/ask-grounded`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question,
            history,
            prev_strata_paths: prevStrataPaths,
          }),
        });
        if (!res.ok) {
          const detail = await res.text();
          throw new Error(`Brain returned ${res.status}: ${detail.slice(0, 300)}`);
        }
        const data: GroundedResult = await res.json();
        setResult(data);
        return { data, error: null as string | null };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
        return { data: null as GroundedResult | null, error: msg };
      } finally {
        if (stageTimer.current) clearInterval(stageTimer.current);
        setIsLoading(false);
      }
    },
    []
  );

  return { ask, result, error, isLoading, stage };
}
