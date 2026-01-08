/**
 * Python Brain API Client
 * HTTP client to communicate with the Python multi-agent brain system
 */

interface BrainQuestionRequest {
    question: string;
    context?: string;
    visualType?: string;
    includeVisual: boolean;
}

interface BrainQuestionResponse {
    answer: string;
    critique: string;
    mindmapPath?: string;
    context?: string;
    plan?: string;
    success: boolean;
    error?: string;
}

const PYTHON_BRAIN_API_URL = process.env.PYTHON_BRAIN_API_URL || "http://localhost:8000";

// Timeout for multi-agent processing (5 minutes = 300,000ms)
// The multi-agent consensus takes 2-3 minutes with 3 LLM agents
const BRAIN_REQUEST_TIMEOUT_MS = 5 * 60 * 1000;

// Shorter timeout for health checks (10 seconds)
const HEALTH_CHECK_TIMEOUT_MS = 10 * 1000;

/**
 * Call the Python brain to answer a question using multi-agent consensus
 * Extended timeout to accommodate multi-agent deliberation process
 */
export async function askPythonBrain(request: BrainQuestionRequest): Promise<BrainQuestionResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), BRAIN_REQUEST_TIMEOUT_MS);

    try {
        console.log("[Python Brain] Starting request with 5-minute timeout...");

        const response = await fetch(`${PYTHON_BRAIN_API_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(request),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Python Brain API error: ${response.statusText}`);
        }

        const data: BrainQuestionResponse = await response.json();

        if (!data.success) {
            throw new Error(data.error || "Python Brain returned error");
        }

        console.log("[Python Brain] Request completed successfully");
        return data;
    } catch (error) {
        clearTimeout(timeoutId);

        if (error instanceof Error && error.name === 'AbortError') {
            console.error("[Python Brain] Request timed out after 5 minutes");
            throw new Error("Python Brain request timed out - the multi-agent system is taking too long");
        }

        console.error("[Python Brain] Error calling API:", error);
        throw error;
    }
}

/**
 * Check if Python Brain API is available
 */
export async function checkPythonBrainHealth(): Promise<boolean> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT_MS);

    try {
        const response = await fetch(`${PYTHON_BRAIN_API_URL}/`, {
            method: "GET",
            signal: controller.signal,
        });

        clearTimeout(timeoutId);
        return response.ok;
    } catch (error) {
        clearTimeout(timeoutId);
        console.error("[Python Brain] Health check failed:", error);
        return false;
    }
}

/**
 * Generate exam using Python Brain
 */
export async function generateExamWithBrain(topic: string, numQuestions: number = 5): Promise<string> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), BRAIN_REQUEST_TIMEOUT_MS);

    try {
        const response = await fetch(`${PYTHON_BRAIN_API_URL}/generate-exam?topic=${encodeURIComponent(topic)}&num_questions=${numQuestions}`, {
            method: "POST",
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`Exam generation failed: ${response.statusText}`);
        }

        const data = await response.json();
        return data.examContent || "";
    } catch (error) {
        clearTimeout(timeoutId);

        if (error instanceof Error && error.name === 'AbortError') {
            throw new Error("Exam generation timed out");
        }

        console.error("[Python Brain] Exam generation error:", error);
        throw error;
    }
}
