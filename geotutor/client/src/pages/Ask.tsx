import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { trpc } from "@/lib/trpc";
import { Loader2, Save, Download, Share2, Copy, FileText, Presentation, ArrowLeft, Sparkles } from "lucide-react";
import { useLocation } from "wouter";
import { Streamdown } from "streamdown";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useState, useEffect } from "react";
import { GeoTutorLogo } from "@/components/GeoTutorLogo";
import { ThinkingProcess, usePythonBrainStream } from "@/components/ThinkingProcess";

export default function Ask() {
  const { user } = useAuth();
  const [, setLocation] = useLocation();
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [tags, setTags] = useState("");
  const [notes, setNotes] = useState("");
  const [hasStartedStream, setHasStartedStream] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);

  // Parse query params
  const params = new URLSearchParams(window.location.search);
  const questionText = params.get("q") || "";
  const includeVisual = params.get("visual") === "true";
  const visualType = params.get("type") || undefined;
  const projectId = params.get("project") ? parseInt(params.get("project")!) : undefined;
  const isTeacherMode = params.get("mode") === "teacher";

  // Fetch project details if projectId is provided
  const { data: project } = trpc.projects.getById.useQuery(projectId!, {
    enabled: !!projectId
  });

  // Use the Python Brain SSE stream for real-time progress
  const { events, isStreaming, result, error, startStream } = usePythonBrainStream();

  // Save to library mutation (still using tRPC for database operations)
  const saveMutation = trpc.library.save.useMutation({
    onSuccess: () => {
      toast.success("Saved to library");
      setSaveDialogOpen(false);
      setTags("");
      setNotes("");
    },
    onError: (error) => {
      toast.error("Failed to save", {
        description: error.message,
      });
    },
  });

  // Build context from project and conversation history
  const buildContext = () => {
    const parts: string[] = [];

    // Add project context
    if (project) {
      parts.push("=== PROJECT CONTEXT ===");
      parts.push("Project: " + project.title);
      if (project.description) parts.push("Description: " + project.description);
      if (project.objectives?.length) parts.push("Objectives: " + project.objectives.join(", "));
      if (project.initialContext) parts.push("Background: " + project.initialContext);
      parts.push("");
    }

    // Add conversation history (last 5 exchanges)
    if (conversationHistory.length > 0) {
      parts.push("=== PREVIOUS CONVERSATION ===");
      conversationHistory.slice(-10).forEach(msg => {
        const roleLabel = msg.role === 'user' ? 'User' : 'Assistant';
        const content = msg.content.length > 500 ? msg.content.substring(0, 500) + '...' : msg.content;
        parts.push(roleLabel + ": " + content);
      });
      parts.push("");
    }

    return parts.length > 0 ? parts.join("\n") : undefined;
  };

  // Start streaming on mount (wait for project data if projectId exists)
  useEffect(() => {
    // Don't start if we're waiting for project data
    const shouldWaitForProject = projectId && !project;

    if (questionText && !hasStartedStream && !result && !error && !shouldWaitForProject) {
      setHasStartedStream(true);

      // Add current question to history
      setConversationHistory(prev => [...prev, { role: 'user', content: questionText }]);

      startStream({
        question: questionText,
        context: buildContext(),
        includeVisual,
        visualType,
      });
    }
  }, [questionText, hasStartedStream, result, error, includeVisual, visualType, startStream, projectId, project]);

  // Add assistant response to history when stream completes
  useEffect(() => {
    if (result && !isStreaming && conversationHistory[conversationHistory.length - 1]?.role === 'user') {
      setConversationHistory(prev => [...prev, { role: 'assistant', content: result.answer }]);
    }
  }, [result, isStreaming]);

  const handleSave = () => {
    // Note: For now, saving requires a questionId from the database
    // With streaming, we'd need a separate endpoint to save
    toast.info("Saving with streaming is being implemented...");
  };

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    toast.success("Link copied to clipboard");
  };

  const handleGenerateExam = async () => {
    if (!result?.answer || !questionText) {
      toast.error("No answer to generate exam from");
      return;
    }

    toast.info("Generating exam sheet...");

    try {
      const apiUrl = import.meta.env.VITE_PYTHON_BRAIN_API_URL || "http://localhost:8000";
      const response = await fetch(apiUrl + "/generate-exam", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: questionText,
          num_questions: 5,
          context: result.answer
        })
      });

      if (!response.ok) throw new Error("Failed to generate exam");

      const data = await response.json();
      if (data.success) {
        toast.success("Exam sheet generated!", { description: "Check your downloads folder" });
        // If there's a file path, could trigger download here
      } else {
        toast.error("Exam generation failed");
      }
    } catch (err) {
      toast.error("Failed to generate exam sheet");
    }
  };

  const handleGenerateSlides = () => {
    toast.info("Presentation slide generation coming soon!");
  };

  // Allow both authenticated users and guest sessions
  const isGuest = typeof window !== 'undefined' && localStorage.getItem("geotutor-guest-session");
  if (!user && !isGuest) {
    setLocation("/");
    return null;
  }

  // Determine the answer text from the stream result
  const answerText = result?.critique || result?.answer || "";
  const isLoading = isStreaming;
  const hasResult = !!result;
  const hasError = !!error;

  return (
    <div className="min-h-screen bg-white">
      {/* ManuAI-Inspired Header */}
      <header className="border-b border-gray-200 sticky top-0 z-50 bg-white">
        <div className="container py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/")}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <GeoTutorLogo size="sm" showText={true} />
          </div>
          <nav className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/history")}>
              History
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setLocation("/library")}>
              Library
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setLocation("/profile")}>
              {user?.name || "Profile"}
            </Button>
          </nav>
        </div>
      </header>

      <main className="container py-8">
        <div className="max-w-4xl mx-auto">
          {/* Question Display */}
          <div className="mb-8">
            <div className="inline-block px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium mb-3">
              <Sparkles className="w-3 h-3 inline mr-1" />
              Your Question
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{questionText}</h1>
          </div>

          {/* Thinking Process Display - Shows during streaming */}
          {(isLoading || events.length > 0) && (
            <div className="mb-8">
              <ThinkingProcess
                isActive={isLoading}
                events={events}
              />
            </div>
          )}

          {/* Legacy Loading State (fallback if no events) */}
          {isLoading && events.length === 0 && (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
                <p className="text-gray-600">Connecting to multi-agent system...</p>
              </div>
            </div>
          )}

          {/* Answer Display */}
          {hasResult && (
            <div className="space-y-8">
              {/* Text Answer */}
              <div className="bg-gray-50 rounded-lg p-8 border border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Answer</h2>
                <div className="prose prose-sm max-w-none">
                  <Streamdown>{answerText}</Streamdown>
                </div>
              </div>

              {/* Visual Explanation - if generated */}
              {result?.visualBase64 && (
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-8 border border-blue-200">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <span className="text-2xl">🎨</span>
                    Visual Explanation
                  </h2>
                  <div className="flex justify-center">
                    <img
                      src={`data:image/png;base64,${result.visualBase64}`}
                      alt="Generated pedagogical visual"
                      className="max-w-full rounded-lg shadow-lg border border-gray-200"
                    />
                  </div>
                  <p className="text-sm text-gray-500 text-center mt-3">
                    AI-generated pedagogical illustration
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3">
                <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="gap-2">
                      <Save className="w-4 h-4" />
                      Save to Library
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Save to Library</DialogTitle>
                      <DialogDescription>Add tags and notes to organize your saved content</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="tags">Tags (comma-separated)</Label>
                        <Input
                          id="tags"
                          placeholder="e.g., bearing capacity, soil mechanics"
                          value={tags}
                          onChange={(e) => setTags(e.target.value)}
                        />
                      </div>
                      <div>
                        <Label htmlFor="notes">Notes</Label>
                        <Textarea
                          id="notes"
                          placeholder="Add any notes or context..."
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          rows={4}
                        />
                      </div>
                      <Button onClick={handleSave} disabled={saveMutation.isPending} className="w-full">
                        {saveMutation.isPending ? "Saving..." : "Save"}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>

                <Button variant="outline" className="gap-2" onClick={handleShare}>
                  <Copy className="w-4 h-4" />
                  Copy Link
                </Button>

                {isTeacherMode && (
                  <Button variant="outline" className="gap-2" onClick={handleGenerateExam}>
                    <Download className="w-4 h-4" />
                    Download Exam Sheet
                  </Button>
                )}

                {user?.role === "teacher" && (
                  <Button variant="outline" className="gap-2" onClick={handleGenerateSlides}>
                    <Presentation className="w-4 h-4" />
                    Generate Slides
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Error State */}
          {hasError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <p className="text-red-800 font-medium">Failed to generate answer</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <Button onClick={() => setLocation("/")} className="mt-4">
                Back to Home
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
