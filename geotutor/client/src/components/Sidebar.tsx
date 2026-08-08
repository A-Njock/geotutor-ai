import { Button } from "@/components/ui/button";
import { GeoTutorLogo } from "@/components/GeoTutorLogo";
import { Plus, FolderKanban, Loader2, MessageSquare, ChevronDown, GraduationCap, Users } from "lucide-react";
import { useLocation } from "wouter";
import { ScrollArea } from "@/components/ui/scroll-area";
import { trpc } from "@/lib/trpc";
import { useEffect, useState } from "react";
import { getMode, readSessions, type SessionEntry } from "@/components/modes/registry";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

interface SidebarProps {
    onNewTask: () => void;
    onNewProject: () => void;
    onOpenSession?: (s: SessionEntry) => void;
    selectedProject: number | null;
    onSelectProject: (id: number | null) => void;
    userMode: "student" | "teacher";
    onModeChange: (mode: "student" | "teacher") => void;
}

export function Sidebar({ onNewTask, onNewProject, onOpenSession, selectedProject, onSelectProject, userMode, onModeChange }: SidebarProps) {
    const [location, setLocation] = useLocation();
    const [showModeMenu, setShowModeMenu] = useState(false);
    const [showCodeDialog, setShowCodeDialog] = useState(false);
    const [accessCode, setAccessCode] = useState("");

    // Check if user is a guest (skip auth-required queries for guests)
    const isGuestSession = typeof window !== 'undefined' && localStorage.getItem("geotutor-guest-session");

    const { data: projects, isLoading: projectsLoading } = trpc.projects.list.useQuery(undefined, { enabled: !isGuestSession });
    const { data: recentTasks, isLoading: tasksLoading } = trpc.qa.getHistory.useQuery(undefined, { enabled: !isGuestSession });

    // Local session log: works for guests too and carries the mode each task ran in
    const [sessions, setSessions] = useState<SessionEntry[]>([]);
    useEffect(() => {
        const refresh = () => setSessions(readSessions());
        refresh();
        window.addEventListener("geotutor-sessions-changed", refresh);
        window.addEventListener("storage", refresh);
        return () => {
            window.removeEventListener("geotutor-sessions-changed", refresh);
            window.removeEventListener("storage", refresh);
        };
    }, []);

    const handleModeSwitch = (mode: "student" | "teacher") => {
        if (mode === "teacher") {
            setShowCodeDialog(true);
            setShowModeMenu(false);
        } else {
            onModeChange("student");
            setShowModeMenu(false);
        }
    };

    const handleAccessCodeSubmit = () => {
        // TODO: Validate access code with backend
        const TEACHER_CODE = "GEOTUTOR2024"; // This should be validated server-side
        if (accessCode === TEACHER_CODE) {
            onModeChange("teacher");
            setShowCodeDialog(false);
            setAccessCode("");
            toast.success("Teacher mode activated!");
        } else {
            toast.error("Invalid access code");
        }
    };

    return (
        <>
            <div className="w-60 border-r bg-sidebar border-sidebar-border flex flex-col h-screen">
                {/* Logo & App Name */}
                <div className="p-4 border-b border-sidebar-border">
                    <GeoTutorLogo size="md" showText={true} />
                </div>

                {/* New Task Action */}
                <div className="p-3">
                    <Button
                        onClick={onNewTask}
                        className="w-full justify-start gap-2"
                        variant="ghost"
                        size="sm"
                    >
                        <Plus className="w-4 h-4" />
                        New task
                    </Button>
                </div>

                {/* Projects Section */}
                <div className="border-t border-sidebar-border">
                    <div className="px-3 py-2">
                        <span className="text-xs font-medium text-sidebar-foreground/70">{userMode === "teacher" ? "Your Teaching Projects" : "Your Learning Projects"}</span>
                    </div>

                    <ScrollArea className="max-h-48 px-3">
                        <div className="space-y-1 pb-2">
                            {/* New Project Button */}
                            <button
                                onClick={onNewProject}
                                className="w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors hover:bg-sidebar-accent/50 text-primary font-medium"
                            >
                                <div className="flex items-center gap-1">
                                    <Plus className="w-3.5 h-3.5 flex-shrink-0" />
                                    <span>New project</span>
                                </div>
                            </button>

                            {projectsLoading ? (
                                <div className="flex items-center justify-center py-4">
                                    <Loader2 className="w-4 h-4 animate-spin text-sidebar-foreground/50" />
                                </div>
                            ) : projects && projects.length > 0 ? (
                                projects.map((project) => (
                                    <button
                                        key={project.id}
                                        onClick={() => onSelectProject(project.id === selectedProject ? null : project.id)}
                                        className={`w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${selectedProject === project.id
                                            ? "bg-sidebar-accent text-sidebar-accent-foreground"
                                            : "hover:bg-sidebar-accent/50 text-sidebar-foreground"
                                            }`}
                                    >
                                        <div className="flex items-center gap-1">
                                            <FolderKanban className="w-3.5 h-3.5 flex-shrink-0" />
                                            <span className="truncate flex-1">{project.title}</span>
                                        </div>
                                    </button>
                                ))
                            ) : (
                                <div className="text-xs text-sidebar-foreground/50 text-center py-4">
                                    No projects yet
                                </div>
                            )}
                        </div>
                    </ScrollArea>
                </div>

                {/* All Tasks - History Section */}
                <div className="flex-1 overflow-hidden flex flex-col border-t border-sidebar-border">
                    <div className="px-3 py-2 flex items-center justify-between">
                        <span className="text-xs font-medium text-sidebar-foreground/70">All tasks</span>
                        <Button
                            onClick={() => setLocation("/history")}
                            size="icon"
                            variant="ghost"
                            className="h-5 w-5"
                            title="View all"
                        >
                            <span className="text-xs">→</span>
                        </Button>
                    </div>

                    <ScrollArea className="flex-1 px-3">
                        <div className="space-y-1 pb-4">
                            {/* Local sessions first: each tagged with the mode it ran in */}
                            {sessions.map((s) => {
                                const mode = getMode(s.mode);
                                const Icon = mode.icon;
                                return (
                                    <button
                                        key={s.id}
                                        type="button"
                                        onClick={() => onOpenSession?.(s)}
                                        className="w-full text-left px-2 py-1.5 rounded-md text-xs hover:bg-sidebar-accent/50 text-sidebar-foreground cursor-pointer"
                                    >
                                        <div className="flex items-start gap-1.5">
                                            <Icon className={`w-3 h-3 flex-shrink-0 mt-0.5 ${mode.accent}`} />
                                            <div className="flex-1 min-w-0">
                                                <div className="line-clamp-2">{s.title}</div>
                                                <span className={`inline-block mt-1 rounded-full border px-1.5 text-[9px] uppercase tracking-wide ${mode.tag}`}>
                                                    {mode.label}
                                                </span>
                                            </div>
                                        </div>
                                    </button>
                                );
                            })}

                            {tasksLoading ? (
                                <div className="flex items-center justify-center py-4">
                                    <Loader2 className="w-4 h-4 animate-spin text-sidebar-foreground/50" />
                                </div>
                            ) : recentTasks && recentTasks.length > 0 ? (
                                // the panel shows at most the 5 most recent
                                // tasks; the full history stays on /history
                                recentTasks.slice(0, Math.max(0, 5 - sessions.length)).map((task) => (
                                    <button
                                        key={task.id}
                                        onClick={() => setLocation(`/ask/${task.id}`)}
                                        className="w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors hover:bg-sidebar-accent/50 text-sidebar-foreground"
                                    >
                                        <div className="flex items-start gap-1">
                                            <MessageSquare className="w-3 h-3 flex-shrink-0 mt-0.5" />
                                            <span className="truncate flex-1 line-clamp-2">{task.questionText}</span>
                                        </div>
                                    </button>
                                ))
                            ) : sessions.length === 0 ? (
                                <div className="text-xs text-sidebar-foreground/50 text-center py-4">
                                    No tasks yet
                                </div>
                            ) : null}
                        </div>
                    </ScrollArea>
                </div>

                {/* User Mode Selector */}
                <div className="border-t border-sidebar-border p-3">
                    <div className="relative">
                        <button
                            onClick={() => setShowModeMenu(!showModeMenu)}
                            className="w-full flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-sidebar-accent/50 transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                {userMode === "student" ? (
                                    <GraduationCap className="w-4 h-4 text-primary" />
                                ) : (
                                    <Users className="w-4 h-4 text-chart-1" />
                                )}
                                <span className="text-sm font-medium">
                                    {userMode === "student" ? "Student Mode" : "Teacher Mode"}
                                </span>
                            </div>
                            <ChevronDown className={`w-3 h-3 transition-transform ${showModeMenu ? "rotate-180" : ""}`} />
                        </button>

                        {/* Mode Menu */}
                        {showModeMenu && (
                            <div className="absolute bottom-full left-0 right-0 mb-1 bg-background border border-border rounded-md shadow-lg overflow-hidden">
                                <button
                                    onClick={() => handleModeSwitch("student")}
                                    className="w-full flex items-center gap-2 px-3 py-2 hover:bg-muted text-sm transition-colors text-left"
                                >
                                    <GraduationCap className="w-4 h-4" />
                                    <span>Student Mode</span>
                                </button>
                                <button
                                    onClick={() => handleModeSwitch("teacher")}
                                    className="w-full flex items-center gap-2 px-3 py-2 hover:bg-muted text-sm transition-colors text-left border-t border-border"
                                >
                                    <Users className="w-4 h-4" />
                                    <span>Teacher Mode</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Teacher Access Code Dialog */}
            <Dialog open={showCodeDialog} onOpenChange={setShowCodeDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Teacher Mode Access</DialogTitle>
                        <DialogDescription>
                            Please enter your teacher access code to unlock teacher features.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="access-code">Access Code</Label>
                            <Input
                                id="access-code"
                                type="password"
                                placeholder="Enter access code"
                                value={accessCode}
                                onChange={(e) => setAccessCode(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        handleAccessCodeSubmit();
                                    }
                                }}
                            />
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setShowCodeDialog(false);
                                    setAccessCode("");
                                }}
                                className="flex-1"
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleAccessCodeSubmit}
                                disabled={!accessCode}
                                className="flex-1"
                            >
                                Activate
                            </Button>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    );
}

