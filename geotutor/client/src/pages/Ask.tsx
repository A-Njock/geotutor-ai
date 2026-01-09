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

  // Parse query params
  const params = new URLSearchParams(window.location.search);
  const questionText = params.get("q") || "";
  const includeVisual = params.get("visual") === "true";
  const visualType = params.get("type") || undefined;

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

  // Start streaming on mount
  useEffect(() => {
    if (questionText && !hasStartedStream && !result && !error) {
      setHasStartedStream(true);
      startStream({
        question: questionText,
        includeVisual,
        visualType,
      });
    }
  }, [questionText, hasStartedStream, result, error, includeVisual, visualType, startStream]);

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

  const handleGenerateExam = () => {
    toast.info("Exam sheet generation coming soon!");
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

                <Button variant="outline" className="gap-2" onClick={handleGenerateExam}>
                  <FileText className="w-4 h-4" />
                  Generate Exam Sheet
                </Button>

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
