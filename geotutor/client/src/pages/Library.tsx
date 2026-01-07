import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { trpc } from "@/lib/trpc";
import { Loader2, ArrowLeft, BookMarked, Trash2, Image as ImageIcon } from "lucide-react";
import { useLocation } from "wouter";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";

export default function Library() {
  const { user, loading: authLoading } = useAuth();
  const [, setLocation] = useLocation();
  const utils = trpc.useUtils();

  const { data: savedContent, isLoading } = trpc.library.getSaved.useQuery(undefined, {
    enabled: !!user,
  });

  const deleteMutation = trpc.library.delete.useMutation({
    onSuccess: () => {
      toast.success("Removed from library");
      utils.library.getSaved.invalidate();
    },
    onError: (error) => {
      toast.error("Failed to remove", {
        description: error.message,
      });
    },
  });

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const handleDelete = (id: number) => {
    if (confirm("Are you sure you want to remove this from your library?")) {
      deleteMutation.mutate({ id });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-4 flex items-center justify-between">
          <Button variant="ghost" onClick={() => setLocation("/")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <h1 className="text-xl font-semibold">My Library</h1>
          <div className="w-24"></div>
        </div>
      </header>

      <main className="container py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-foreground">Saved Content</h2>
            <p className="text-muted-foreground">Access your saved questions, answers, and visual explanations</p>
          </div>

          {isLoading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-1/4" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-5/6 mt-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {savedContent && savedContent.length > 0 && (
            <div className="space-y-4">
              {savedContent.map((item) => (
                <Card key={item.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-lg line-clamp-2">{item.questionText}</CardTitle>
                        <CardDescription className="flex items-center gap-4 mt-2">
                          <span>Saved {formatDistanceToNow(new Date(item.savedAt), { addSuffix: true })}</span>
                          {item.includeVisual && (
                            <span className="flex items-center gap-1 text-primary">
                              <ImageIcon className="w-3 h-3" />
                              {item.visualType}
                            </span>
                          )}
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDelete(item.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {item.answerText && <p className="text-sm text-muted-foreground line-clamp-3">{item.answerText.substring(0, 200)}...</p>}

                    {item.tags && (
                      <div className="flex flex-wrap gap-2">
                        {item.tags.split(",").map((tag, idx) => (
                          <Badge key={idx} variant="secondary">
                            {tag.trim()}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {item.notes && (
                      <div className="p-3 bg-muted/50 rounded-md">
                        <p className="text-sm font-medium mb-1">Your Notes:</p>
                        <p className="text-sm text-muted-foreground">{item.notes}</p>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          setLocation(
                            `/ask?q=${encodeURIComponent(item.questionText || "")}&visual=${item.includeVisual}&type=${item.visualType || ""}`
                          );
                        }}
                      >
                        View Full Answer
                      </Button>
                      {item.visualUrl && (
                        <Button size="sm" variant="outline" onClick={() => window.open(item.visualUrl || "", "_blank")}>
                          View Visual
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {savedContent && savedContent.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <BookMarked className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Saved Content</h3>
                <p className="text-muted-foreground mb-4">Save questions and answers to your library for easy access later</p>
                <Button onClick={() => setLocation("/")}>Start Learning</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
