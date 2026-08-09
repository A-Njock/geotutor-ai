import { useCallback, useEffect, useRef, useState } from "react";
import { readSessionData, saveSessionData } from "@/components/modes/registry";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, ArrowUp } from "lucide-react";
import { GroundedAnswer } from "./GroundedAnswer";
import { FeedbackButtons } from "@/components/FeedbackButtons";
import { useGroundedAsk } from "./useGroundedAsk";
import { GroundedResult } from "./types";
import { ModeSelector } from "@/components/modes/ModeSelector";
import { DEFAULT_MODE, type ModeId } from "@/components/modes/registry";

// Single-page conversation: question -> answer -> follow-ups, all in one
// scrollable thread with the input pinned under the latest answer.

interface Turn {
  question: string;
  result: GroundedResult | null;
  error: string | null;
}

interface SavedAskThread {
  turns: Turn[];
  history: { role: string; content: string }[];
  prevPaths: string[];
}

export function AskChat({
  initialQuestion,
  mode = DEFAULT_MODE,
  sessionId,
}: {
  initialQuestion: string;
  mode?: ModeId;
  sessionId?: string;
}) {
  const restored = (sessionId && !initialQuestion)
    ? readSessionData<SavedAskThread>(sessionId)
    : null;
  const [turns, setTurns] = useState<Turn[]>(restored?.turns ?? []);
  const [input, setInput] = useState("");
  const { ask, isLoading, stage } = useGroundedAsk();
  const historyRef = useRef<{ role: string; content: string }[]>(restored?.history ?? []);
  const prevPathsRef = useRef<string[]>(restored?.prevPaths ?? []);
  const bottomRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);

  // keep the saved copy current so a later history click restores everything
  useEffect(() => {
    if (sessionId && turns.length > 0) {
      saveSessionData(sessionId, {
        turns,
        history: historyRef.current,
        prevPaths: prevPathsRef.current,
      } satisfies SavedAskThread);
    }
  }, [sessionId, turns]);

  const submit = useCallback(
    async (q: string) => {
      const question = q.trim();
      if (!question) return;
      setTurns((t) => [...t, { question, result: null, error: null }]);
      const res = await ask(question, historyRef.current, prevPathsRef.current);
      setTurns((t) => {
        const copy = [...t];
        const last = copy[copy.length - 1];
        copy[copy.length - 1] = res.data
          ? { ...last, result: res.data }
          : { ...last, error: res.error || "The tutor could not answer." };
        return copy;
      });
      if (res.data) {
        const answerText = res.data.sub_answers
          .map((s) => s.answer_markdown)
          .join("\n\n");
        historyRef.current = [
          ...historyRef.current,
          { role: "user", content: question },
          { role: "assistant", content: answerText.slice(0, 1500) },
        ].slice(-8);
        prevPathsRef.current = res.data.strata.map((s) => s.rel_path);
      }
    },
    [ask]
  );

  // fire the question typed on the landing screen
  useEffect(() => {
    if (!startedRef.current && initialQuestion) {
      startedRef.current = true;
      submit(initialQuestion);
    }
  }, [initialQuestion, submit]);

  // keep the newest content in view
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, isLoading]);

  const handleSend = () => {
    if (isLoading || input.trim().length < 3) return;
    const q = input;
    setInput("");
    submit(q);
  };

  return (
    <div className="w-full max-w-3xl mx-auto flex flex-col gap-6 pb-6">
      {turns.map((turn, i) => (
        <div key={i} className="flex flex-col gap-4">
          {/* user bubble */}
          <div className="self-end max-w-[85%] bg-blue-50 border border-blue-200 rounded-2xl rounded-br-sm px-5 py-3 text-[15px] text-gray-900">
            {turn.question}
          </div>

          {/* answer / loading / error */}
          {turn.result ? (
            <div className="flex flex-col gap-1">
              <GroundedAnswer result={turn.result} />
              <FeedbackButtons
                mode="chat"
                question={turn.question}
                answer={turn.result.sub_answers
                  .map((s) => s.answer_markdown)
                  .join("\n\n")}
              />
            </div>
          ) : turn.error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm">
              <p className="text-red-800 font-medium m-0">The tutor could not answer</p>
              <p className="text-red-600 m-0 mt-1">{turn.error}</p>
            </div>
          ) : (
            <div className="flex items-center gap-3 text-gray-500 text-sm py-4">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              {stage}
            </div>
          )}
        </div>
      ))}

      {/* follow-up input, pinned under the latest answer */}
      <div className="sticky bottom-4">
        <Card className="border-2 shadow-md bg-white">
          <CardContent className="p-3 space-y-2">
            <div className="flex items-center">
              {/* the thread's mode is fixed: start a new task to change it */}
              <ModeSelector value={mode} onChange={() => {}} locked />
            </div>
            <div className="relative">
              <Textarea
                placeholder="Ask a follow-up question..."
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
                  disabled={isLoading || input.trim().length < 3}
                  size="icon"
                  className="h-8 w-8 rounded-full"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ArrowUp className="w-4 h-4" />
                  )}
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
