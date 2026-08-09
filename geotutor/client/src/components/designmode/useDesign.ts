import { useCallback, useState } from "react";
import { DesignAnalysis, DesignSolution } from "./types";

// Two-phase flow against the Python design brain:
// /design/analyze may return clarification questions; /design/solve runs the
// deterministic pipeline. The analysis object is passed back verbatim so the
// server stays stateless.

const API = () =>
  (import.meta.env.VITE_PYTHON_BRAIN_API_URL as string) || "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Design brain returned ${res.status}: ${detail.slice(0, 300)}`);
  }
  return res.json();
}

export function useDesign() {
  const [isLoading, setIsLoading] = useState(false);
  const [stage, setStage] = useState("");

  const analyze = useCallback(async (problem: string) => {
    setIsLoading(true);
    setStage("Reading your problem…");
    try {
      // defer_skeptic: the frame check runs during solve, in parallel with
      // the narration call, so the reader waits one model round-trip less
      const data = await post<DesignAnalysis>("/design/analyze",
        { problem, defer_skeptic: true });
      return { data, error: null as string | null };
    } catch (e) {
      return { data: null as DesignAnalysis | null, error: e instanceof Error ? e.message : String(e) };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const solve = useCallback(
    async (problem: string, analysis: DesignAnalysis, answers: Record<string, string> | null) => {
      setIsLoading(true);
      setStage("Solving your problem step by step…");
      try {
        const data = await post<DesignSolution>("/design/solve", { problem, analysis, answers });
        return { data, error: null as string | null };
      } catch (e) {
        return { data: null as DesignSolution | null, error: e instanceof Error ? e.message : String(e) };
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const followup = useCallback(
    async (problem: string, context: string, question: string) => {
      setIsLoading(true);
      setStage("Answering from the solved steps…");
      try {
        const data = await post<{ ok: boolean; answer: string }>(
          "/design/followup", { problem, context, question });
        return { data, error: null as string | null };
      } catch (e) {
        return { data: null as { ok: boolean; answer: string } | null,
                 error: e instanceof Error ? e.message : String(e) };
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { analyze, solve, followup, isLoading, stage };
}
