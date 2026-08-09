import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";

// Small passive rating row under every answer. A click stores the
// question and the answer it rated; thumbs-down feeds the maintainer's
// feedback report. One rating per answer, then a quiet thank-you.

const API = () =>
  (import.meta.env.VITE_PYTHON_BRAIN_API_URL as string) || "http://localhost:8000";

export function FeedbackButtons({
  mode,
  question,
  answer,
  className = "",
}: {
  mode: "chat" | "design";
  question: string;
  answer: string;
  className?: string;
}) {
  const [rated, setRated] = useState<"up" | "down" | null>(null);

  const send = (rating: "up" | "down") => {
    if (rated) return;
    setRated(rating);
    // fire-and-forget: a rating must never block or break the conversation
    fetch(`${API()}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, rating, question, answer }),
    }).catch(() => {});
  };

  if (rated) {
    return (
      <p className={`m-0 text-xs text-muted-foreground ${className}`}>
        {rated === "up"
          ? "Thank you for the feedback."
          : "Thank you, this answer was flagged for review."}
      </p>
    );
  }
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <span className="text-xs text-muted-foreground mr-1">Was this helpful?</span>
      <button
        type="button"
        aria-label="Helpful"
        onClick={() => send("up")}
        className="rounded-md p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
      >
        <ThumbsUp className="h-4 w-4" />
      </button>
      <button
        type="button"
        aria-label="Not helpful"
        onClick={() => send("down")}
        className="rounded-md p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
      >
        <ThumbsDown className="h-4 w-4" />
      </button>
    </div>
  );
}
