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
import { useState } from "react";
import { GeoTutorLogo } from "@/components/GeoTutorLogo";

export default function Ask() {
  const { user } = useAuth();
  const [, setLocation] = useLocation();
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [tags, setTags] = useState("");
  const [notes, setNotes] = useState("");

  // Parse query params
  const params = new URLSearchParams(window.location.search);
  const questionText = params.get("q") || "";
  const includeVisual = params.get("visual") === "true";
  const visualType = params.get("type") || undefined;

  // Ask question mutation
  const askMutation = trpc.qa.ask.useMutation({
    onError: (error) => {
      toast.error("Failed to generate answer", {
        description: error.message,
      });
    },
  });

  // Save to library mutation
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

  // Trigger question on mount
  useState(() => {
    if (questionText && !askMutation.data && !askMutation.isPending) {
      askMutation.mutate({
        questionText,
        includeVisual,
        visualType: visualType as any,
      });
    }
  });

  const handleSave = () => {
    if (askMutation.data?.questionId) {
      saveMutation.mutate({
        questionId: askMutation.data.questionId,
        tags,
        notes,
      });
    }
  };

  const handleDownloadVisual = () => {
    if (askMutation.data?.visualUrl) {
      window.open(askMutation.data.visualUrl, "_blank");
    }
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

  if (!user) {
    setLocation("/");
    return null;
  }

  return (
    <div className="min-h-screen bg-white">
      {/* ManuAI-Inspired Header */}
      <header className="border-b border-gray-200 sticky top-0 z-50 bg-white">
        <div className="container py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/")}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <GeoTutorLogo className="w-6 h-6" />
            <span className="font-semibold text-gray-900">GeoTutor</span>
          </div>
          <nav className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/history")}>
              History
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setLocation("/library")}>
              Library
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setLocation("/profile")}>
              {user.name || "Profile"}
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

          {/* Loading State */}
          {askMutation.isPending && (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
                <p className="text-gray-600">Generating your answer...</p>
              </div>
            </div>
          )}

          {/* Answer Display */}
          {askMutation.data && (
            <div className="space-y-8">
              {/* Text Answer */}
              <div className="bg-gray-50 rounded-lg p-8 border border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Answer</h2>
                <div className="prose prose-sm max-w-none">
                  <Streamdown>{askMutation.data.answerText}</Streamdown>
                </div>
              </div>

              {/* Visual Answer */}
              {askMutation.data.visualUrl && (
                <div className="bg-gray-50 rounded-lg p-8 border border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Visual Explanation</h2>
                  <div className="bg-white rounded-lg p-4 border border-gray-200 flex items-center justify-center min-h-96">
                    <img
                      src={askMutation.data.visualUrl}
                      alt="Visual explanation"
                      className="max-w-full max-h-96 object-contain"
                    />
                  </div>
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

                {askMutation.data.visualUrl && (
                  <Button variant="outline" className="gap-2" onClick={handleDownloadVisual}>
                    <Download className="w-4 h-4" />
                    Download Visual
                  </Button>
                )}

                <Button variant="outline" className="gap-2" onClick={handleShare}>
                  <Copy className="w-4 h-4" />
                  Copy Link
                </Button>

                <Button variant="outline" className="gap-2" onClick={handleGenerateExam}>
                  <FileText className="w-4 h-4" />
                  Generate Exam Sheet
                </Button>

                {user.role === "teacher" && (
                  <Button variant="outline" className="gap-2" onClick={handleGenerateSlides}>
                    <Presentation className="w-4 h-4" />
                    Generate Slides
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Error State */}
          {askMutation.isError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <p className="text-red-800">Failed to generate answer. Please try again.</p>
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
