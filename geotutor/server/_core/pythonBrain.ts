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

/**
 * Call the Python brain to answer a question using multi-agent consensus
 */
export async function askPythonBrain(request: BrainQuestionRequest): Promise<BrainQuestionResponse> {
    try {
        const response = await fetch(`${PYTHON_BRAIN_API_URL}/ask`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Python Brain API error: ${response.statusText}`);
        }

        const data: BrainQuestionResponse = await response.json();

        if (!data.success) {
            throw new Error(data.error || "Python Brain returned error");
        }

        return data;
    } catch (error) {
        console.error("[Python Brain] Error calling API:", error);
        throw error;
    }
}

/**
 * Check if Python Brain API is available
 */
export async function checkPythonBrainHealth(): Promise<boolean> {
    try {
        const response = await fetch(`${PYTHON_BRAIN_API_URL}/`, {
            method: "GET",
        });
        return response.ok;
    } catch (error) {
        console.error("[Python Brain] Health check failed:", error);
        return false;
    }
}

/**
 * Generate exam using Python Brain
 */
export async function generateExamWithBrain(topic: string, numQuestions: number = 5): Promise<string> {
    try {
        const response = await fetch(`${PYTHON_BRAIN_API_URL}/generate-exam?topic=${encodeURIComponent(topic)}&num_questions=${numQuestions}`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error(`Exam generation failed: ${response.statusText}`);
        }

        const data = await response.json();
        return data.examContent || "";
    } catch (error) {
        console.error("[Python Brain] Exam generation error:", error);
        throw error;
    }
}
