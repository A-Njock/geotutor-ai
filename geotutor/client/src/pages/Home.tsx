import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Loader2, User, LogOut, Mic, ArrowUp, Menu } from "lucide-react";
import { getLoginUrl } from "@/const";
import { useState } from "react";
import { useLocation } from "wouter";
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";
import { GeoTutorLogo } from "@/components/GeoTutorLogo";
import { Sidebar } from "@/components/Sidebar";
import { TaskProgress } from "@/components/TaskProgress";
import { AskChat } from "@/components/askmode/AskChat";
import { DesignChat } from "@/components/designmode/DesignChat";

import { ModeSelector } from "@/components/modes/ModeSelector";
import { DEFAULT_MODE, recordSession, type ModeId, type SessionEntry } from "@/components/modes/registry";
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
  const [userMode, setUserMode] = useState<"student" | "teacher">("student");
  const [chatQuestion, setChatQuestion] = useState<string | null>(null);
  // set when the thread belongs to a history session (new or reopened)
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionMode, setSessionMode] = useState<ModeId | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [mode, setMode] = useState<ModeId>(DEFAULT_MODE);
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
              <div className="flex justify-center">
                <GeoTutorLogo size="lg" showText={true} className="scale-150" textColor="text-slate-100" />
              </div>
              <p className="text-xl text-slate-300">
                AI-Powered Geotechnical Engineering Learning
              </p>
            </div>
            <p className="text-slate-400">
              Get detailed, AI-powered explanations with visual aids to enhance your understanding of geotechnical engineering concepts.
            </p>
            <p className="text-sm text-slate-500 font-mono">
              Created by <a href="https://geoinvention.com/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-300 transition-colors underline decoration-slate-700 underline-offset-4">GeoInvention.com</a>
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

    // Visual explanations still use the classic multi-agent page (chat mode only)
    if (includeVisual && mode === "chat") {
      setIsAsking(true);
      const searchParams = new URLSearchParams({
        q: questionText,
        visual: "true",
        classic: "1",
        ...(visualType && { type: visualType }),
        ...(selectedProject && { project: selectedProject.toString() }),
        ...(userMode === "teacher" && { mode: "teacher" }),
      });
      setLocation(`/ask?${searchParams.toString()}`);
      return;
    }

    // Grounded Ask mode: the answer appears right here, on this page
    const entry = recordSession(mode, questionText);
    setSessionId(entry.id);
    setSessionMode(mode);
    setChatQuestion(questionText);
    setQuestionText("");
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
        mobileOpen={sidebarOpen}
        onMobileClose={() => setSidebarOpen(false)}
        // a new task returns to the composer, where the mode can be chosen again
        onNewTask={() => {
          setChatQuestion(null);
          setSessionId(null);
          setSessionMode(null);
          setSidebarOpen(false);
        }}
        // a history click reopens that conversation from its saved thread
        onOpenSession={(s) => {
          setSessionMode(s.mode);
          setSessionId(s.id);
          setChatQuestion(null);
          setSidebarOpen(false);
        }}
        onNewProject={() => setShowNewProject(true)}
        selectedProject={selectedProject}
        onSelectProject={setSelectedProject}
        userMode={userMode}
        onModeChange={setUserMode}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="border-b bg-background px-3 sm:px-6 py-3 flex items-center justify-between">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden shrink-0"
            aria-label="Open menu"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </Button>
          <div className="flex-1 text-center">
            <h2 className="text-sm font-medium text-muted-foreground">
              GeoTutor 1.6 Lite
            </h2>
          </div>
          <div className="flex items-center gap-2 min-w-0">
            <Button variant="ghost" size="sm" onClick={() => setLocation("/profile")}>
              <User className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline truncate max-w-[160px]">
                {user?.name || user?.email}
              </span>
            </Button>
            <Button variant="ghost" size="sm" onClick={() => {
              localStorage.removeItem("geotutor-guest-session");
              logout();
              window.location.reload();
            }}>
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </header>

        {/* Main Content - Centered like Manus */}
        <main className="flex-1 overflow-y-auto">
          {/* Conversation thread: replaces the hero once a question is asked
              or a history entry is reopened */}
          {chatQuestion !== null || sessionId ? (
            <div className="px-3 sm:px-6 py-8">
              {(sessionMode ?? mode) === "design" ? (
                <DesignChat key={sessionId ?? "new"}
                  initialQuestion={chatQuestion ?? ""}
                  sessionId={sessionId ?? undefined} />
              ) : (
                <AskChat key={sessionId ?? "new"}
                  initialQuestion={chatQuestion ?? ""}
                  mode={sessionMode ?? mode}
                  sessionId={sessionId ?? undefined} />
              )}
            </div>
          ) : (
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 flex flex-col items-center justify-center min-h-full">
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

                {/* Mode selector + options */}
                <div className="mt-3 pt-3 border-t space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <ModeSelector value={mode} onChange={setMode} />
                  </div>

                  {/* one friendly line describing what the selected mode does */}
                  {mode === "design" && (
                    <p className="m-0 text-[13px] text-muted-foreground">
                      I can assist you in designing: foundations, piles,
                      retaining walls, slope analysis, excavations, soil
                      phases, and more. Describe your problem and I will
                      solve it step by step.
                    </p>
                  )}
                  {mode === "chat" && (
                    <p className="m-0 text-[13px] text-muted-foreground">
                      Let's chat about geotechnical engineering: I can help
                      you deepen your knowledge, find the right formula, etc.
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
          )}
        </main>
      </div>

      {/* New Project Dialog */}
      <Dialog open={showNewProject} onOpenChange={setShowNewProject}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{userMode === "teacher" ? "Create New Teaching Project" : "Create New Learning Project"}</DialogTitle>
            <DialogDescription>
              {userMode === "teacher"
                ? "Set up a new teaching project with course materials and teaching objectives"
                : "Set up a new learning project with initial context and objectives to track your progress"}
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
                placeholder={userMode === "teacher" ? "Describe the course objectives and target audience..." : "Describe your learning goals..."}
                value={newProjectData.description}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, description: e.target.value })
                }
                className="min-h-20"
              />
            </div>
            <div>
              <Label htmlFor="context">{userMode === "teacher" ? "Course Materials (optional)" : "Initial Context (optional)"}</Label>
              <Textarea
                id="context"
                placeholder={userMode === "teacher" ? "Provide course syllabus, reference materials, or key concepts to cover..." : "Provide background information, prerequisites, or what you already know..."}
                value={newProjectData.initialContext}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, initialContext: e.target.value })
                }
                className="min-h-24"
              />
            </div>
            <div>
              <Label htmlFor="objectives">{userMode === "teacher" ? "Teaching Objectives (optional)" : "Learning Objectives (optional)"}</Label>
              <Textarea
                id="objectives"
                placeholder={userMode === "teacher"
                  ? "Enter teaching objectives separated by commas (e.g., Explain soil classification clearly, Demonstrate shear strength concepts, Help students master consolidation theory)"
                  : "Enter objectives separated by commas (e.g., Understand soil classification, Learn about shear strength, Master consolidation theory)"}
                value={newProjectData.objectives}
                onChange={(e) =>
                  setNewProjectData({ ...newProjectData, objectives: e.target.value })
                }
                className="min-h-24"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {userMode === "teacher"
                  ? "These objectives will help guide your teaching questions and resources"
                  : "These objectives will be tracked as you ask questions in this project"}
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
