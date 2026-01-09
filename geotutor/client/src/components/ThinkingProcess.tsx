import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Check, Loader2, AlertCircle, Brain, BookOpen, Users, Scale, FileCheck } from "lucide-react";

/**
 * Progress event from the Python Brain SSE stream
 */
export interface ThinkingEvent {
    type: "progress" | "result" | "error";
    stage?: "retrieving" | "collecting" | "ranking" | "synthesizing" | "reviewing";
    agent?: string;
    status?: "started" | "done" | "error";
    detail?: string;
    // For result type
    answer?: string;
    critique?: string;
    success?: boolean;
    // For error type
    message?: string;
}

interface ThinkingProcessProps {
    /** Whether the thinking process is active */
    isActive: boolean;
    /** Current events to display */
    events: ThinkingEvent[];
    /** Optional className */
    className?: string;
}

// Stage configuration with icons and labels
const STAGE_CONFIG = {
    retrieving: {
        icon: BookOpen,
        label: "Retrieving Context",
        description: "Searching knowledge base...",
    },
    collecting: {
        icon: Users,
        label: "Collecting Solutions",
        description: "AI agents generating answers...",
    },
    ranking: {
        icon: Scale,
        label: "Peer Evaluation",
        description: "Agents reviewing each other's work...",
    },
    synthesizing: {
        icon: Brain,
        label: "Synthesizing Answer",
        description: "Combining best insights...",
    },
    reviewing: {
        icon: FileCheck,
        label: "Final Review",
        description: "Quality checking the answer...",
    },
};

// Agent colors for visual distinction
const AGENT_COLORS: Record<string, string> = {
    "Member_GPT": "text-green-600 bg-green-100",
    "Member_DeepSeek": "text-blue-600 bg-blue-100",
    "Member_Mistral": "text-purple-600 bg-purple-100",
    "Librarian": "text-amber-600 bg-amber-100",
    "Chair": "text-indigo-600 bg-indigo-100",
    "Critic": "text-rose-600 bg-rose-100",
    "system": "text-gray-600 bg-gray-100",
};

/**
 * ThinkingProcess component displays real-time agent progress
 * during the multi-agent consensus process.
 */
export function ThinkingProcess({ isActive, events, className }: ThinkingProcessProps) {
    // Track which stages are complete
    const [completedStages, setCompletedStages] = useState<Set<string>>(new Set());
    const [currentStage, setCurrentStage] = useState<string | null>(null);
    // Track agent statuses PER STAGE to avoid cross-stage pollution
    const [stageAgentStatuses, setStageAgentStatuses] = useState<Record<string, Record<string, { status: string; detail?: string }>>>({});

    // Process events to update state
    useEffect(() => {
        const newCompleted = new Set<string>();
        // Map: stage -> { agent -> status }
        const newStageAgents: Record<string, Record<string, { status: string; detail?: string }>> = {};
        let lastStage: string | null = null;
        let hasResult = false;

        for (const event of events) {
            if (event.type === "result") {
                hasResult = true;
            }

            if (event.type === "progress" && event.stage) {
                lastStage = event.stage;

                // Initialize stage if needed
                if (!newStageAgents[event.stage]) {
                    newStageAgents[event.stage] = {};
                }

                if (event.agent && event.agent !== "system") {
                    newStageAgents[event.stage][event.agent] = {
                        status: event.status || "started",
                        detail: event.detail,
                    };
                }

                if (event.status === "done" && event.agent === "system") {
                    newCompleted.add(event.stage);
                }
            }
        }

        // If we got a result, mark all stages as complete
        if (hasResult) {
            const allStages = ["retrieving", "collecting", "ranking", "synthesizing", "reviewing"];
            allStages.forEach(s => newCompleted.add(s));
            // Also mark all agents in each stage as done
            for (const stageKey of Object.keys(newStageAgents)) {
                for (const agentKey of Object.keys(newStageAgents[stageKey])) {
                    newStageAgents[stageKey][agentKey].status = "done";
                }
            }
        }

        setCompletedStages(newCompleted);
        setCurrentStage(hasResult ? null : lastStage);
        setStageAgentStatuses(newStageAgents);
    }, [events]);

    if (!isActive && events.length === 0) {
        return null;
    }

    const stages = Object.entries(STAGE_CONFIG);

    return (
        <div className={cn("rounded-lg border bg-gradient-to-br from-slate-50 to-blue-50 p-4 shadow-sm", className)}>
            <div className="flex items-center gap-2 mb-4">
                <Brain className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Multi-Agent Thinking Process</h3>
                {isActive && (
                    <span className="ml-auto flex items-center gap-1 text-xs text-blue-600 font-medium">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Processing...
                    </span>
                )}
            </div>

            {/* Stage Progress */}
            <div className="space-y-2">
                {stages.map(([stageKey, config], index) => {
                    const isComplete = completedStages.has(stageKey);
                    const isCurrent = currentStage === stageKey && !isComplete;
                    const isUpcoming = !isComplete && !isCurrent &&
                        (currentStage ? stages.findIndex(([k]) => k === currentStage) < index : true);

                    const StageIcon = config.icon;

                    return (
                        <div
                            key={stageKey}
                            className={cn(
                                "flex items-start gap-3 p-2 rounded-md transition-all duration-300",
                                isComplete && "bg-green-50",
                                isCurrent && "bg-blue-50 ring-1 ring-blue-200",
                                isUpcoming && "opacity-50"
                            )}
                        >
                            {/* Status Icon */}
                            <div className={cn(
                                "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5",
                                isComplete && "bg-green-500 text-white",
                                isCurrent && "bg-blue-500 text-white",
                                isUpcoming && "bg-gray-200 text-gray-400"
                            )}>
                                {isComplete ? (
                                    <Check className="w-4 h-4" />
                                ) : isCurrent ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <StageIcon className="w-3 h-3" />
                                )}
                            </div>

                            {/* Stage Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className={cn(
                                        "font-medium text-sm",
                                        isComplete && "text-green-700",
                                        isCurrent && "text-blue-700",
                                        isUpcoming && "text-gray-500"
                                    )}>
                                        {config.label}
                                    </span>
                                </div>

                                {/* Agent pills for current stage */}
                                {(isCurrent || isComplete) && stageAgentStatuses[stageKey] && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                        {Object.entries(stageAgentStatuses[stageKey])
                                            .map(([agent, agentStatus]) => {
                                                const colorClass = AGENT_COLORS[agent] || AGENT_COLORS.system;
                                                const status = agentStatus.status;
                                                return (
                                                    <span
                                                        key={agent}
                                                        className={cn(
                                                            "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium",
                                                            colorClass
                                                        )}
                                                    >
                                                        {status === "started" && <Loader2 className="w-2 h-2 animate-spin" />}
                                                        {status === "done" && <Check className="w-2 h-2" />}
                                                        {status === "error" && <AlertCircle className="w-2 h-2" />}
                                                        {agent.replace("Member_", "")}
                                                    </span>
                                                );
                                            })}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Error Display */}
            {events.some(e => e.type === "error") && (
                <div className="mt-3 p-2 bg-red-50 rounded-md border border-red-200">
                    <div className="flex items-center gap-2 text-red-700">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm font-medium">Error occurred</span>
                    </div>
                    <p className="text-xs text-red-600 mt-1">
                        {events.find(e => e.type === "error")?.message || "Unknown error"}
                    </p>
                </div>
            )}
        </div>
    );
}

/**
 * Custom hook to connect to the Python Brain SSE stream
 */
export function usePythonBrainStream() {
    const [events, setEvents] = useState<ThinkingEvent[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [result, setResult] = useState<{ answer: string; critique: string } | null>(null);
    const [error, setError] = useState<string | null>(null);

    const startStream = async (request: {
        question: string;
        context?: string;
        visualType?: string;
        includeVisual: boolean;
    }) => {
        // Reset state
        setEvents([]);
        setIsStreaming(true);
        setResult(null);
        setError(null);

        const apiUrl = import.meta.env.VITE_PYTHON_BRAIN_API_URL || "http://localhost:8000";

        try {
            const response = await fetch(`${apiUrl}/ask-stream`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                body: JSON.stringify(request),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.statusText}`);
            }

            if (!response.body) {
                throw new Error("No response body for streaming");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const eventData = JSON.parse(line.slice(6)) as ThinkingEvent;

                            setEvents(prev => [...prev, eventData]);

                            if (eventData.type === "result") {
                                setResult({
                                    answer: eventData.answer || "",
                                    critique: eventData.critique || "",
                                });
                                setIsStreaming(false);
                                return;
                            }

                            if (eventData.type === "error") {
                                setError(eventData.message || "Unknown error");
                                setIsStreaming(false);
                                return;
                            }
                        } catch (e) {
                            console.warn("Failed to parse SSE event:", line);
                        }
                    }
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Stream connection failed");
            setIsStreaming(false);
        }
    };

    return {
        events,
        isStreaming,
        result,
        error,
        startStream,
    };
}
