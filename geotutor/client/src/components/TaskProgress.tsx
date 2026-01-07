import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Circle } from "lucide-react";
import { trpc } from "@/lib/trpc";

interface TaskProgressProps {
    projectId: number;
}

export function TaskProgress({ projectId }: TaskProgressProps) {
    const { data: project } = trpc.projects.getById.useQuery(projectId);
    const { data: questions } = trpc.qa.listByProject.useQuery(projectId);

    if (!project) return null;

    const objectives = project.objectives || [];
    const completedCount = questions?.length || 0;
    const totalObjectives = objectives.length || 8; // Default to 8 if no objectives set

    return (
        <Card className="border bg-card">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold">{project.title}</CardTitle>
                    <span className="text-sm font-medium text-muted-foreground">
                        {completedCount} / {totalObjectives}
                    </span>
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {project.description && (
                    <p className="text-sm text-muted-foreground">{project.description}</p>
                )}

                {objectives.length > 0 && (
                    <div className="space-y-2">
                        <h4 className="text-xs font-medium text-muted-foreground uppercase">
                            Task progress
                        </h4>
                        <div className="space-y-1.5">
                            {objectives.slice(0, 5).map((objective, idx) => {
                                const isCompleted = idx < completedCount;
                                return (
                                    <div key={idx} className="flex items-start gap-2 text-sm">
                                        {isCompleted ? (
                                            <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                                        ) : (
                                            <Circle className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                                        )}
                                        <span className={isCompleted ? "text-foreground" : "text-muted-foreground"}>
                                            {objective}
                                        </span>
                                    </div>
                                );
                            })}
                            {objectives.length > 5 && (
                                <p className="text-xs text-muted-foreground pl-6">
                                    +{objectives.length - 5} more objectives
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {project.initialContext && (
                    <div className="pt-2 mt-2 border-t">
                        <h4 className="text-xs font-medium text-muted-foreground uppercase mb-1">
                            Initial Context
                        </h4>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                            {project.initialContext}
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
