import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { HelpCircle } from "lucide-react";
import { ClarifyQuestion } from "./types";

// The clarify loop: the solver asks only when the missing information would
// change the method or the result. One card, all questions, one submit.

export function ClarifyCard({
  questions, onSubmit, disabled,
}: {
  questions: ClarifyQuestion[];
  onSubmit: (answers: Record<string, string>) => void;
  disabled?: boolean;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [custom, setCustom] = useState<Record<string, string>>({});

  const value = (q: ClarifyQuestion) =>
    answers[q.id] === "__custom__" ? custom[q.id] || "" : answers[q.id] || "";
  const complete = questions.every((q) => value(q).trim().length > 0);

  return (
    <Card className="border-2 border-chart-2/30 bg-chart-2/5">
      <CardContent className="p-5 space-y-5">
        <div className="flex items-center gap-2 text-chart-2 font-medium">
          <HelpCircle className="w-4 h-4" />
          Before solving, the analysis needs your input
        </div>
        {questions.map((q) => (
          <div key={q.id} className="space-y-2">
            <p className="text-sm text-foreground m-0">{q.question}</p>
            <div className="flex flex-wrap gap-2">
              {q.options.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => setAnswers((a) => ({ ...a, [q.id]: o.value }))}
                  className={[
                    "rounded-full border px-3 py-1.5 text-xs transition-colors",
                    answers[q.id] === o.value
                      ? "bg-chart-2 text-white border-chart-2"
                      : "bg-background text-muted-foreground border-border hover:border-chart-2/50",
                  ].join(" ")}
                >
                  {o.label}
                </button>
              ))}
              {q.allow_custom && (
                <button
                  type="button"
                  onClick={() => setAnswers((a) => ({ ...a, [q.id]: "__custom__" }))}
                  className={[
                    "rounded-full border px-3 py-1.5 text-xs transition-colors",
                    answers[q.id] === "__custom__"
                      ? "bg-chart-2 text-white border-chart-2"
                      : "bg-background text-muted-foreground border-border hover:border-chart-2/50",
                  ].join(" ")}
                >
                  Other value…
                </button>
              )}
            </div>
            {answers[q.id] === "__custom__" && (
              <Input
                placeholder={q.custom_hint || "Enter a value"}
                value={custom[q.id] || ""}
                onChange={(e) => setCustom((c) => ({ ...c, [q.id]: e.target.value }))}
                className="max-w-56 h-8 text-sm"
              />
            )}
          </div>
        ))}
        <Button
          size="sm"
          disabled={!complete || disabled}
          onClick={() => {
            const out: Record<string, string> = {};
            questions.forEach((q) => { out[q.id] = value(q); });
            onSubmit(out);
          }}
        >
          Solve with these choices
        </Button>
      </CardContent>
    </Card>
  );
}
