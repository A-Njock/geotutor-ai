import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Loader2, User, LogOut, Mic, ArrowUp } from "lucide-react";
import { getLoginUrl } from "@/const";
import { useState } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";
import { GeoTutorLogo } from "@/components/GeoTutorLogo";
import { Sidebar } from "@/components/Sidebar";
import { TaskProgress } from "@/components/TaskProgress";
import { toast } from "sonner";

export default function Home() {
  const { user, loading, isAuthenticated, logout } = useAuth();
  const [, setLocation] = useLocation();
  const [questionText, setQuestionText] = useState("");
  const [includeVisual, setIncludeVisual] = useState(false);
  const [visualType, setVisualType] = useState<string>("flowchart");
  const [isAsking, setIsAsking] = useState(false);
  const [showNewProject, setShowNewProject] = useState(false);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [newProjectData, setNewProjectData] = useState({
    title: "",
    description: "",
    initialContext: "",
    objectives: "",
  });

  const askMutation = trpc.qa.ask.useMutation({
    onSuccess: (data) => {
      setIsAsking(false);
      setQuestionText("");
      setLocation(`/ask/${data.answerId}`);
    },
    onError: (error) => {
      setIsAsking(false);
      toast.error(error.message || "Failed to get answer");
    },
  });

  const createProjectMutation = trpc.projects.create.useMutation({
    onSuccess: (data) => {
      toast.success("Learning project created!");
      setShowNewProject(false);
      setNewProjectData({ title: "", description: "", initialContext: "", objectives: "" });
      setSelectedProject(data.projectId);
    },
    onError: (error) => {
      toast.error(error.message || "Failed to create project");
    },
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Check if guest session exists
    const isGuest = localStorage.getItem("geotutor-guest-session");
    if (isGuest) {
      // Guest user, continue to main app by not returning early
    } else {
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col items-center justify-center px-4">
          <div className="max-w-md text-center space-y-8">
            <div className="space-y-4">
              <GeoTutorLogo className="w-16 h-16 mx-auto" />
              <h1 className="text-4xl font-bold text-white">GeoTutor</h1>
              <p className="text-xl text-slate-300">
                AI-Powered Geotechnical Engineering Learning
              </p>
            </div>
            <p className="text-slate-400">
              Get detailed, AI-powered explanations with visual aids to enhance your understanding of geotechnical engineering concepts.
            </p>
            {getLoginUrl() ? (
              <Button size="lg" onClick={() => (window.location.href = getLoginUrl())} className="w-full">
                Sign In to Start Learning
              </Button>
            ) : null}
            <Button
              size="lg"
              variant="outline"
              onClick={() => {
                localStorage.setItem("geotutor-guest-session", "true");
                window.location.reload();
              }}
              className="w-full text-slate-300 border-slate-600 hover:bg-slate-700"
            >
              Continue as Guest
            </Button>
          </div>
        </div>
      );
    }
  }

  const handleAsk = async () => {
    if (!questionText.trim()) {
      toast.error("Please enter a question");
      return;
    }

    // Navigate immediately to the Ask page with question in URL
    // The Ask page will handle SSE streaming directly to Python Brain
    // This bypasses the 60-second Railway gateway timeout
    setIsAsking(true);

    const searchParams = new URLSearchParams({
      q: questionText,
      ...(includeVisual && { visual: "true" }),
      ...(includeVisual && visualType && { type: visualType }),
      ...(selectedProject && { project: selectedProject.toString() }),
    });

    // Navigate immediately instead of waiting for mutation
    setLocation(`/ask?${searchParams.toString()}`);
  };

  const handleCreateProject = async () => {
    if (!newProjectData.title.trim()) {
      toast.error("Project title is required");
      return;
    }

    await createProjectMutation.mutateAsync({
      title: newProjectData.title,
      description: newProjectData.description || undefined,
      initialContext: newProjectData.initialContext || undefined,
      objectives: newProjectData.objectives
        ? newProjectData.objectives.split(",").map((o) => o.trim())
        : undefined,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        onNewTask={() => {/* scroll to input or focus */ }}
        onNewProject={() => setShowNewProject(true)}
        selectedProject={selectedProject}
        onSelectProject={setSelectedProject}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="border-b bg-background px-6 py-3 flex items-center justify-between">
          <div className="flex-1 text-center">
            <h2 className="text-sm font-medium text-muted-foreground">
              GeoTutor 1.6 Lite
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/profile")}>
              <User className="w-4 h-4 mr-2" />
              {user?.name || user?.email}
            </Button>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </header>

        {/* Main Content - Centered like Manus */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-12 flex flex-col items-center justify-center min-h-full">
            {/* Task Progress - shown if project selected */}
            {selectedProject && (
              <div className="w-full mb-8">
                <TaskProgress projectId={selectedProject} />
              </div>
            )}

            {/* Main Heading - Manus Style */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-semibold text-foreground mb-2">
                What can I do for you?
              </h1>
              {selectedProject && (
                <p className="text-sm text-muted-foreground">
                  Asking within your selected learning project context
                </p>
              )}
            </div>

            {/* Main Input Card - Manus Style Centered */}
            <Card className="w-full max-w-2xl border-2 shadow-sm">
              <CardContent className="p-4">
                {/* Question Input */}
                <div className="relative">
                  <Textarea
                    placeholder="Assign a task or ask anything..."
                    value={questionText}
                    onChange={(e) => setQuestionText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="min-h-[60px] resize-none border-0 focus-visible:ring-0 pr-24 text-base"
                  />
                  <div className="absolute bottom-2 right-2 flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 rounded-full"
                    >
                      <Mic className="w-4 h-4" />
                    </Button>
                    <Button
                      onClick={handleAsk}
                      disabled={isAsking || questionText.length < 10}
                      size="icon"
                      className="h-8 w-8 rounded-full"
                    >
                      {isAsking ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <ArrowUp className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Visual Options - Collapsible */}
                <div className="mt-3 pt-3 border-t space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="visual" className="text-sm font-medium cursor-pointer">
                      Include Visual Explanation
                    </Label>
                    <Switch
                      id="visual"
                      checked={includeVisual}
                      onCheckedChange={setIncludeVisual}
                    />
                  </div>

                  {includeVisual && (
                    <div className="space-y-2">
                      <Label htmlFor="visual-type" className="text-sm">
                        Visual Type
                      </Label>
                      <Select value={visualType} onValueChange={setVisualType}>
                        <SelectTrigger id="visual-type" className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="flowchart">Flowchart (Process Flow)</SelectItem>
                          <SelectItem value="diagram">Diagram (Relationships)</SelectItem>
                          <SelectItem value="infographic">Infographic (Data & Stats)</SelectItem>
                          <SelectItem value="illustration">Illustration (Concepts)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>

      {/* New Project Dialog */}
      <Dialog open={showNewProject} onOpenChange={setShowNewProject}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Learning Project</DialogTitle>
            <DialogDescription>
              Set up a new learning project with initial context and objectives to track your progress
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Project Title *</Label>
              <Input
                id="title"
                placeholder="e.g., Soil Mechanics Fundamentals"
                value={newProjectData.title}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, title: e.target.value })
                }
              />
            </div>
            <div>
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                placeholder="Describe your learning goals..."
                value={newProjectData.description}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, description: e.target.value })
                }
                className="min-h-20"
              />
            </div>
            <div>
              <Label htmlFor="context">Initial Context (optional)</Label>
              <Textarea
                id="context"
                placeholder="Provide background information, prerequisites, or what you already know..."
                value={newProjectData.initialContext}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, initialContext: e.target.value })
                }
                className="min-h-24"
              />
            </div>
            <div>
              <Label htmlFor="objectives">Learning Objectives (optional)</Label>
              <Textarea
                id="objectives"
                placeholder="Enter objectives separated by commas (e.g., Understand soil classification, Learn about shear strength, Master consolidation theory)"
                value={newProjectData.objectives}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, objectives: e.target.value })
                }
                className="min-h-24"
              />
              <p className="text-xs text-muted-foreground mt-1">
                These objectives will be tracked as you ask questions in this project
              </p>
            </div>
            <Button
              onClick={handleCreateProject}
              disabled={createProjectMutation.isPending}
              className="w-full"
            >
              {createProjectMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Project"
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
