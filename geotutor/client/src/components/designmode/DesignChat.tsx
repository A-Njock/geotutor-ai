import { useCallback, useEffect, useRef, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, ArrowUp } from "lucide-react";
import { ModeSelector } from "@/components/modes/ModeSelector";
import { readSessionData, saveSessionData } from "@/components/modes/registry";
import { ClarifyCard } from "./ClarifyCard";
import { StepPlayer } from "./StepPlayer";
import { useDesign } from "./useDesign";
import { DesignAnalysis, DesignSolution } from "./types";

// Mode 2 thread: problem -> (clarifications) -> interactive step-by-step
// solution. The figure is always the deterministic parametric diagram,
// rendered client-side from the solver's parameters.

interface DesignTurn {
  problem: string;          // what the user typed (shown in the bubble)
  fullProblem?: string;     // problem sent to the solver (with added info)
  analysis: DesignAnalysis | null;
  solution: DesignSolution | null;
  followupAnswer?: string;  // set when this turn is a follow-up Q&A
  error: string | null;
  waitingClarify: boolean;
}

// a short question about the solved problem, not a new problem statement
const FOLLOWUP_START_RE = /^(why|how|what|which|explain|can |could |does|do |is |are |should|would|will|and if)/i;
// number-with-unit tokens: several of these mean a full problem statement
const NUM_UNIT_RE = /\d+(?:\.\d+)?\s*(?:m2\/(?:year|yr|s)|kn\/m3|kn\/m³|kn\/m\^3|kpa|mpa|kn|mm|cm|m\b|degrees?|deg\b|%|percent)/gi;

function looksLikeFollowup(typed: string): boolean {
  const unitCount = (typed.match(NUM_UNIT_RE) || []).length;
  if (FOLLOWUP_START_RE.test(typed)) return unitCount <= 2;
  return typed.includes("?") && unitCount <= 1;
}

function stepsAsContext(sol: DesignSolution): string {
  const lines: string[] = [];
  for (const s of sol.steps) {
    let line = `- ${s.title}`;
    if (s.substitution_tex) line += ` | ${s.substitution_tex}`;
    else if (s.equation_tex) line += ` | ${s.equation_tex}`;
    if (s.result?.display) line += ` => ${s.result.display}`;
    lines.push(line);
  }
  for (const c of sol.conclusions ?? []) {
    lines.push(`ANSWER: ${c.quantity} = ${c.value} ${c.unit} (${c.governing})`);
  }
  return lines.join("\n");
}

export function DesignChat({ initialQuestion, sessionId }: {
  initialQuestion: string; sessionId?: string;
}) {
  const [turns, setTurns] = useState<DesignTurn[]>(() => {
    // reopened from history: restore the saved conversation
    if (sessionId && !initialQuestion) {
      const saved = readSessionData<DesignTurn[]>(sessionId);
      if (saved && Array.isArray(saved)) return saved;
    }
    return [];
  });
  const [input, setInput] = useState("");
  const { analyze, solve, followup, isLoading, stage } = useDesign();
  const bottomRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);

  // keep the saved copy current so a later history click restores everything
  useEffect(() => {
    if (sessionId && turns.length > 0) saveSessionData(sessionId, turns);
  }, [sessionId, turns]);

  const runSolve = useCallback(
    async (problem: string, analysis: DesignAnalysis, answers: Record<string, string> | null) => {
      const res = await solve(problem, analysis, answers);
      setTurns((t) => {
        const copy = [...t];
        const last = { ...copy[copy.length - 1], waitingClarify: false };
        if (res.data?.ok) last.solution = res.data;
        else last.error = res.data?.message || res.error || "The solver could not finish.";
        copy[copy.length - 1] = last;
        return copy;
      });
      return res.data;
    },
    [solve]
  );

  const submit = useCallback(
    async (q: string, prev?: DesignTurn) => {
      const typed = q.trim();
      if (!typed) return;

      // 1) follow-up question about a solved problem: answer from the
      //    frozen steps, no re-solving
      if (prev?.solution && typed.length < 260 && looksLikeFollowup(typed)) {
        setTurns((t) => [...t, { problem: typed, analysis: null, solution: null, error: null, waitingClarify: false }]);
        const fu = await followup(prev.fullProblem || prev.problem,
                                  stepsAsContext(prev.solution), typed);
        setTurns((t) => {
          const copy = [...t];
          const last = { ...copy[copy.length - 1] };
          if (fu.data?.ok) last.followupAnswer = fu.data.answer;
          else last.error = (fu.data as { message?: string } | null)?.message
            || fu.error || "The follow-up could not be answered.";
          copy[copy.length - 1] = last;
          return copy;
        });
        return;
      }

      // 2) the previous attempt failed or is waiting on input, and the new
      //    message is not a full problem: treat it as ADDITIONAL INFORMATION
      //    and re-analyse the combined statement
      const augmenting = prev && (prev.error || prev.waitingClarify) && typed.length < 260;
      const problem = augmenting
        ? `${prev!.fullProblem || prev!.problem}\nAdditional information: ${typed}`
        : typed;

      setTurns((t) => [...t, { problem: typed, fullProblem: problem, analysis: null, solution: null, error: null, waitingClarify: false }]);
      const res = await analyze(problem);
      if (!res.data || !res.data.ok) {
        setTurns((t) => {
          const copy = [...t];
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            error: (res.data as { message?: string } | null)?.message || res.error || "Analysis failed.",
          };
          return copy;
        });
        return;
      }
      const analysis = res.data;
      setTurns((t) => {
        const copy = [...t];
        copy[copy.length - 1] = {
          ...copy[copy.length - 1],
          analysis,
          waitingClarify: analysis.questions.length > 0,
        };
        return copy;
      });
      if (analysis.questions.length === 0) {
        await runSolve(problem, analysis, null);
      }
    },
    [analyze, runSolve]
  );

  useEffect(() => {
    if (!startedRef.current && initialQuestion) {
      startedRef.current = true;
      submit(initialQuestion);
    }
  }, [initialQuestion, submit]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, isLoading]);

  const handleSend = () => {
    if (isLoading || input.trim().length < 3) return;
    const q = input;
    setInput("");
    submit(q, turns[turns.length - 1]);
  };

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-6 pb-6">
      {turns.map((turn, i) => (
        <div key={i} className="flex flex-col gap-4">
          <div className="self-end max-w-[85%] bg-blue-50 border border-blue-200 rounded-2xl rounded-br-sm px-5 py-3 text-[15px] text-gray-900">
            {turn.problem}
          </div>

          {turn.analysis && i === turns.length - 1 && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              {turn.analysis.methods.length > 0 && (
                <span className="rounded-full border border-border bg-muted/40 px-2.5 py-1">
                  Applicable: {turn.analysis.methods.map((m) => m.method).join(", ")}
                </span>
              )}
              {turn.analysis.skeptic && (
                <span
                  className={`rounded-full border px-2.5 py-1 ${turn.analysis.skeptic.agrees
                    ? "border-primary/30 bg-primary/5 text-primary"
                    : "border-destructive/30 bg-destructive/5 text-destructive"}`}
                  title={turn.analysis.skeptic.reason}
                >
                  {turn.analysis.skeptic.agrees ? "Frame verified" : "Frame disputed"}
                </span>
              )}
            </div>
          )}

          {turn.waitingClarify && turn.analysis && (
            <ClarifyCard
              questions={turn.analysis.questions}
              disabled={isLoading}
              onSubmit={(answers) => runSolve(turn.fullProblem || turn.problem, turn.analysis!, answers)}
            />
          )}

          {turn.followupAnswer && (
            <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-primary/20 bg-primary/5 px-5 py-3 text-[15px] leading-relaxed text-foreground">
              {turn.followupAnswer}
            </div>
          )}

          {turn.solution && <StepPlayer solution={turn.solution} />}

          {turn.error && (
            /maintenance/i.test(turn.error) ? (
              <div className="bg-sky-50 border border-sky-200 rounded-lg p-4 text-sm">
                <p className="text-sky-900 font-medium m-0">Temporarily unavailable</p>
                <p className="text-sky-800 m-0 mt-1">{turn.error}</p>
              </div>
            ) : /missing|needs/i.test(turn.error) ? (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm">
                <p className="text-amber-900 font-medium m-0">More information needed</p>
                <p className="text-amber-800 m-0 mt-1">{turn.error}</p>
                <p className="text-amber-700/80 m-0 mt-2 text-xs">
                  Add the missing details as a message below and the problem will be re-read with them.
                </p>
              </div>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm">
                <p className="text-red-800 font-medium m-0">GeoTutor can't do this one yet</p>
                <p className="text-red-600 m-0 mt-1">{turn.error}</p>
              </div>
            )
          )}

          {i === turns.length - 1 && isLoading && (
            <div className="flex items-center gap-3 text-gray-500 text-sm py-4">
              <Loader2 className="w-5 h-5 animate-spin text-chart-2" />
              {stage}
            </div>
          )}
        </div>
      ))}

      {/* next problem, pinned under the latest solution */}
      <div className="sticky bottom-4">
        <Card className="border-2 shadow-md bg-white">
          <CardContent className="p-3 space-y-2">
            <div className="flex items-center">
              <ModeSelector value="design" onChange={() => {}} locked />
            </div>
            <div className="relative">
              <Textarea
                placeholder="Describe another design problem..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="min-h-[48px] resize-none border-0 focus-visible:ring-0 pr-14 text-base"
                disabled={isLoading}
              />
              <div className="absolute bottom-1.5 right-1.5">
                <Button
                  onClick={handleSend}
                  disabled={isLoading || input.trim().length < 10}
                  size="icon"
                  className="h-8 w-8 rounded-full"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowUp className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div ref={bottomRef} />
    </div>
  );
}
